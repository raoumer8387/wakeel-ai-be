import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.database import Base
from app.models.case import Case
from app.models.message import Message
from app.agent.orchestrator import WakeelOrchestrator

async def test():
    print("Setting up test memory database...")
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    
    from app.models.user import User
    import uuid
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    orchestrator = WakeelOrchestrator()
    case_id = "TEST_STATEFUL_001"
    test_user_id = uuid.uuid4()
    
    # ── Turn 1 ──
    print("\n" + "=" * 50)
    print("TURN 1: Initial Problem")
    print("=" * 50)
    input_1 = "I want a Khula. I live in Lahore."
    print(f"USER: {input_1}")
    
    async with async_session() as db:
        # Create and insert dummy user to satisfy FK constraint
        dummy_user = User(
            id=test_user_id,
            name="Sara Ahmed",
            email="sara@example.com",
            phone="03001234567",
            cnic="35201-1111111-1"
        )
        db.add(dummy_user)
        await db.flush()
        
        case = Case(id=case_id, user_id=test_user_id, status="draft")
        db.add(case)
        msg1 = Message(case_id=case_id, role="user", content=input_1)
        db.add(msg1)
        await db.commit()
        
        async for event in orchestrator.run_pipeline(input_1, test_user_id, case_id, db):
            print(f"[{event['event'].upper()}] {event.get('message')}")
            if event['event'] == 'agent2_question':
                print(f"\nAGENT ASKS:\n{event['message']}\n")

    # ── Turn 2 ──
    print("\n" + "=" * 50)
    print("TURN 2: User gives consent to draft")
    print("=" * 50)
    input_2 = "Yes please, make a draft."
    print(f"USER: {input_2}")
    
    async with async_session() as db:
        msg2 = Message(case_id=case_id, role="user", content=input_2)
        db.add(msg2)
        await db.commit()
        
        async for event in orchestrator.run_pipeline(input_2, test_user_id, case_id, db):
            print(f"[{event['event'].upper()}] {event.get('message')}")
            if event['event'] == 'agent2_question':
                print(f"\nAGENT ASKS:\n{event['message']}\n")

    # ── Turn 3 ──
    print("\n" + "=" * 50)
    print("TURN 3: User provides details")
    print("=" * 50)
    input_3 = "My name is Sara Ahmed. My CNIC is 35201-1111111-1. My husband's name is Ali Raza."
    print(f"USER: {input_3}")
    
    async with async_session() as db:
        msg3 = Message(case_id=case_id, role="user", content=input_3)
        db.add(msg3)
        await db.commit()
        
        async for event in orchestrator.run_pipeline(input_3, test_user_id, case_id, db):
            print(f"[{event['event'].upper()}] {event.get('message')}")
            
    print("\nStateful Chat Test Complete!")

if __name__ == "__main__":
    asyncio.run(test())
