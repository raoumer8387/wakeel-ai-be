import asyncio
import json
import uuid
from typing import AsyncGenerator
from app.agent.core.agent import LegalAnalystAgent
from app.agent.document_specialist import DocumentSpecialistAgent
from app.models.case import Case
from app.models.message import Message
from app.models.document import Document
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import datetime

class WakeelOrchestrator:

    def __init__(self):
        self.legal_analyst = LegalAnalystAgent()
        self.document_specialist = DocumentSpecialistAgent()

    async def run_pipeline(
        self,
        user_input: str,
        user_id: str,
        case_id: str,
        db: AsyncSession
    ) -> AsyncGenerator[dict, None]:

        action_log = []

        # ── Event 1: Pipeline start ──────────────────────────
        yield {
            "event": "pipeline_start",
            "message": "Starting Wakeel-AI analysis...",
            "case_id": case_id
        }

        # ── Fetch Case & Chat History ───────────────────────
        case = None
        chat_history_str = user_input
        if db is not None:
            # Get case
            result = await db.execute(select(Case).where(Case.id == case_id))
            case = result.scalar_one_or_none()
            
            # Get messages
            msg_result = await db.execute(select(Message).where(Message.case_id == case_id).order_by(Message.created_at.asc()))
            messages = msg_result.scalars().all()
            
            # Format chat history
            history = []
            for m in messages:
                role_str = "User" if m.role == "user" else "Agent"
                history.append(f"{role_str}: {m.content}")
            if history:
                chat_history_str = "\n".join(history)

        status = case.status if case else "draft"
        legal_brief = case.legal_brief if case else {}
        action_log = case.action_log if case and case.action_log else []

        if status == "awaiting_draft_consent":
            # Check consent
            consents = await self._check_draft_consent(user_input)
            if consents:
                status = "drafting"
                await self._update_case(db, case_id, status="drafting")
                # Continue to Agent 2
            else:
                # User asked a follow-up or said no. Go back to consultation.
                status = "consultation"
                await self._update_case(db, case_id, status="consultation")

        if status in ["draft", "consultation"]:
            # Run Agent 1 in thread (it's synchronous)
            yield {
                "event": "agent1_start",
                "message": "Legal Analyst is typing..."
            }
            
            agent1_res = await asyncio.to_thread(
                self.legal_analyst.analyze,
                user_input,
                chat_history_str
            )

            response_text = agent1_res.get("response", "I'm sorry, I didn't understand.")
            ready_for_drafting = agent1_res.get("ready_for_drafting", False)
            new_brief = agent1_res.get("legal_brief")
            
            if new_brief:
                legal_brief = new_brief
                action_log.append({
                    "step": "agent1_complete",
                    "issue_type": legal_brief.get("issue_type"),
                    "laws_found": len(legal_brief.get("relevant_laws", [])),
                    "confidence": legal_brief.get("confidence_score"),
                    "timestamp": datetime.datetime.utcnow().isoformat()
                })

            # Yield Agent 1 message
            yield {
                "event": "agent1_message",
                "message": response_text,
                "data": {"ready_for_drafting": ready_for_drafting, "legal_brief": legal_brief}
            }

            # Save Agent 1 output to DB
            await self._save_message(
                db, case_id,
                role="agent1",
                content=response_text,
                metadata={"legal_brief": legal_brief, "ready_for_drafting": ready_for_drafting}
            )

            if ready_for_drafting:
                await self._update_case(
                    db, case_id,
                    status="awaiting_draft_consent",
                    issue_type=legal_brief.get("issue_type") if legal_brief else None,
                    title=self._generate_title(legal_brief) if legal_brief else "Legal Case",
                    legal_brief=legal_brief,
                    action_log=action_log
                )
            else:
                await self._update_case(db, case_id, status="consultation", action_log=action_log)

            # Emit complete so frontend re-enables input
            yield {
                "event": "complete",
                "message": "Turn complete",
                "data": {"case_id": case_id}
            }
            return  # Stop pipeline here until user replies

        # ── Event 4: Agent 2 starts ──────────────────────────
        yield {
            "event": "agent2_start",
            "message": "Document Specialist processing details..."
        }

        # Count how many times Agent 2 has already asked questions
        question_round = 0
        if db is not None:
            agent2_msg_result = await db.execute(
                select(Message).where(
                    Message.case_id == case_id,
                    Message.role == "agent2"
                )
            )
            question_round = len(agent2_msg_result.scalars().all())

        # Run Agent 2 in thread (it's synchronous)
        doc_result = await asyncio.to_thread(
            self.document_specialist.process,
            legal_brief,
            chat_history_str,
            case_id,
            question_round
        )

        if doc_result.get("status") == "missing_info":
            question = doc_result.get("question")
            yield {
                "event": "agent2_question",
                "message": question,
                "data": {
                    "missing_fields": doc_result.get("missing_fields"),
                    "filled_fields_count": doc_result.get("filled_fields_count"),
                    "total_fields_count": doc_result.get("total_fields_count")
                }
            }
            # Save the agent's question to the database
            await self._save_message(
                db, case_id,
                role="agent2",
                content=question,
                metadata={"missing_fields": doc_result.get("missing_fields")}
            )
            # Emit complete so frontend re-enables input
            yield {
                "event": "complete",
                "message": "Turn complete",
                "data": {"case_id": case_id}
            }
            return  # Stop pipeline here until user replies

        action_log.append({
            "step": "agent2_complete",
            "document_type": doc_result.get("document_type"),
            "filled_fields": doc_result.get(
                "filled_fields_count"),
            "missing_fields": doc_result.get("missing_fields"),
            "pdf_path": doc_result.get("pdf_path"),
            "timestamp": datetime.datetime.utcnow().isoformat()
        })

        # ── Event 5: Agent 2 done ────────────────────────────
        yield {
            "event": "agent2_done",
            "message": f"{doc_result.get('document_type')} "
                       f"drafted successfully",
            "data": {
                "document_type": doc_result.get(
                    "document_type"),
                "pdf_path": doc_result.get("pdf_path"),
                "missing_fields": doc_result.get(
                    "missing_fields"),
                "filled_fields_count": doc_result.get(
                    "filled_fields_count"),
                "total_fields_count": doc_result.get(
                    "total_fields_count")
            }
        }

        # ── Event 6: Simulation start ────────────────────────
        yield {
            "event": "simulation_start",
            "message": "Submitting to Family Court "
                       "(simulated)..."
        }

        mock_filing = doc_result.get("mock_filing", {})

        action_log.append({
            "step": "mock_filing_complete",
            "case_ref": mock_filing.get("case_ref"),
            "court": mock_filing.get("court"),
            "filed_at": mock_filing.get("filed_at"),
            "timestamp": datetime.datetime.utcnow().isoformat()
        })

        # ── Event 7: Simulation done ─────────────────────────
        yield {
            "event": "simulation_done",
            "message": f"Filed — Ref: "
                       f"{mock_filing.get('case_ref')}",
            "data": mock_filing
        }

        # Save document + update case to filed
        await self._save_document(
            db, case_id,
            doc_type=legal_brief.get("issue_type", ""),
            file_path=doc_result.get("pdf_path", "")
        )
        await self._update_case(
            db, case_id,
            status="filed",
            case_ref=mock_filing.get("case_ref"),
            action_log=action_log
        )

        # ── Event 8: Complete ────────────────────────────────
        yield {
            "event": "complete",
            "message": "Analysis and document generation complete",
            "data": {
                "case_id": case_id,
                "case_ref": mock_filing.get("case_ref"),
                "issue_type": legal_brief.get("issue_type"),
                "document_type": doc_result.get(
                    "document_type"),
                "pdf_ready": True,
                "missing_fields": doc_result.get(
                    "missing_fields"),
                "rights": legal_brief.get("rights"),
                "recommended_action": legal_brief.get(
                    "recommended_action"),
                "jurisdiction": legal_brief.get(
                    "jurisdiction"),
                "reasoning_steps": doc_result.get(
                    "reasoning_steps")
            }
        }

    def _generate_title(self, legal_brief: dict) -> str:
        titles = {
            "khula":        "Khula Petition — Wife Divorce",
            "talaq":        "Talaq Notice — Husband Divorce",
            "maintenance":  "Maintenance Application — Nafaqa",
            "custody":      "Child Custody Petition",
            "dissolution":  "Dissolution of Marriage Suit",
            "dowry":        "Dowry Recovery Application",
            "parents_rights":"Parents Maintenance Application"
        }
        return titles.get(
            legal_brief.get("issue_type", ""), "Legal Case")

    async def _update_case(
        self, db: AsyncSession, case_id: str, **kwargs
    ):
        if db is None:
            return
        result = await db.execute(
            select(Case).where(Case.id == case_id))
        case = result.scalar_one_or_none()
        if case:
            for key, value in kwargs.items():
                setattr(case, key, value)
            case.updated_at = datetime.datetime.utcnow()
            await db.commit()

    async def _check_draft_consent(self, user_input: str) -> bool:
        from langchain_openai import ChatOpenAI
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import JsonOutputParser
        from app.config import settings

        llm = ChatOpenAI(
            model="google/gemini-2.0-flash-001",
            openai_api_key=settings.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
            temperature=0
        )
        prompt = ChatPromptTemplate.from_template("""
        The AI just asked the user if they want to prepare a draft legal document.
        User's reply: "{user_input}"
        
        Did the user consent/agree to prepare the draft?
        Return ONLY valid JSON: {{"consents": true/false}}
        """)
        chain = prompt | llm | JsonOutputParser()
        try:
            import asyncio
            res = await asyncio.to_thread(chain.invoke, {"user_input": user_input})
            return res.get("consents", False)
        except Exception:
            lower = user_input.lower()
            return any(w in lower for w in ["yes", "yeah", "sure", "ok", "please", "do it"])

    async def _save_message(
        self, db: AsyncSession, case_id: str,
        role: str, content: str, metadata: dict
    ):
        if db is None:
            return
        message = Message(
            case_id=case_id,
            role=role,
            content=content,
            metadata_=metadata
        )
        db.add(message)
        await db.commit()

    async def _save_document(
        self, db: AsyncSession, case_id: str,
        doc_type: str, file_path: str
    ):
        if db is None:
            return
        document = Document(
            case_id=case_id,
            type=doc_type,
            file_path=file_path
        )
        db.add(document)
        await db.commit()
