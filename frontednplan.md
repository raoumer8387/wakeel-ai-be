# Integrate New Conversational SSE API into ChatScreen

## Background

The backend has been refactored from a one-shot analysis model to a **stateful, multi-turn conversational pipeline** using Server-Sent Events (SSE). The new API spec (`New_api.md`) defines:

- **Endpoint**: `POST /api/v1/chat/query` — same endpoint, but new event types
- **Key change**: `agent1_done` is **removed**. Instead, `agent1_message` is the primary event for Agent 1's conversational replies (both questions and final analysis)
- **New events**: `agent2_question` (Agent 2 asking for missing info), `agent2_done` (PDF generated), `simulation_start`/`simulation_done` (court filing)
- **`case_id` lifecycle**: Backend generates `case_id` on first message; frontend must capture it from any event's `case_id` field and send it in all subsequent requests
- **Input control**: Input must be **disabled** until the `complete` event fires each turn

## Current State vs. Required State

| Aspect | Current Code | New API Requirement |
|---|---|---|
| Agent 1 response event | Listens for `agent1_done` | Must listen for `agent1_message` |
| Agent 1 message handling | Reads `eventData.data?.brief` from `agent1_done` | Read `eventData.message` from `agent1_message` |
| Step progression | `agent1_done` → jumps to `agent2` step | `agent1_message` should stay on `agent1` step (Agent 1 may send multiple messages) |
| `case_id` capture | From `eventData.data?.case_id` | From `eventData.case_id` (top-level field per spec) |
| SSE event type definition | Includes `agent1_done` | Replace with `agent1_message` |
| Typing indicator text | Generic "Agent is thinking..." | Context-aware: "Legal Analyst is typing..." / "Document Specialist is typing..." |
| Input disabled state | Only while `isTyping` | Must disable until `complete` event (per spec: "Never enable until `complete`") |
| Agent 2 done handling | Fetches documents from separate endpoint | Use `data.pdf_path` from the event payload directly |

## Proposed Changes

### SSE Event Types

#### [MODIFY] [legalService.ts](file:///d:/wakeel-ai-front/src/services/legalService.ts)

- Update the `SSEEvent` type to replace `agent1_done` with `agent1_message`
- Add `case_id` as a top-level field in the SSE event interface (per the new spec)

```diff
 export interface SSEEvent {
-  event: 'pipeline_start' | 'agent1_start' | 'agent1_done' | 'agent2_start' | 'agent2_question' | 'agent2_done' | 'simulation_start' | 'simulation_done' | 'complete' | 'error';
+  event: 'pipeline_start' | 'agent1_start' | 'agent1_message' | 'agent2_start' | 'agent2_question' | 'agent2_done' | 'simulation_start' | 'simulation_done' | 'complete' | 'error';
   message: string;
   data?: any;
+  case_id?: string;
 }
```

---

### Chat Screen — Core SSE Handler Refactor

#### [MODIFY] [ChatScreen.tsx](file:///d:/wakeel-ai-front/src/screens/ChatScreen.tsx)

**1. Replace `agent1_done` handler with `agent1_message` handler**

The old code looks for `agent1_done` and reads `eventData.data?.brief`. The new code must handle `agent1_message` — each one is a separate conversational reply to be rendered as a new chat bubble:

```diff
-            case 'agent1_done':
-              const brief = eventData.data?.brief || eventData.message;
-              currentAgent1Text = brief;
-              setMessages((prev) => {
-                const filtered = prev.filter(m => m.id !== agent1MsgId);
-                return [
-                  ...filtered,
-                  {
-                    id: agent1MsgId,
-                    text: currentAgent1Text,
-                    sender: 'agent1',
-                    timestamp: ...
-                  }
-                ];
-              });
-              setCurrentStep('agent2');
-              break;
+            case 'agent1_message':
+              setMessages((prev) => [
+                ...prev,
+                {
+                  id: Date.now().toString() + '_a1',
+                  text: eventData.message,
+                  sender: 'agent1',
+                  timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
+                }
+              ]);
+              break;
```

Key difference: Each `agent1_message` creates a **new** bubble (the agent may send multiple during consultation). We no longer overwrite a single bubble.

**2. Update `case_id` capture to use top-level `eventData.case_id`**

```diff
-          if (eventData.data?.case_id && !caseId) {
-            setCaseId(eventData.data.case_id);
+          if (eventData.case_id && !caseId) {
+            setCaseId(eventData.case_id);
           }
```

**3. Update typing indicator to be context-aware**

Add a `typingLabel` state that changes based on which agent is active:

| Event | Typing Label |
|---|---|
| `pipeline_start` | "Wakeel is thinking..." |
| `agent1_start` | "Legal Analyst is typing..." |
| `agent2_start` | "Document Specialist is typing..." |
| `simulation_start` | "Submitting to court..." |
| `complete` | (hide indicator) |

**4. Disable input until `complete` event**

Add a `pipelineActive` state that is set to `true` on `sendMessage()` and `false` only on `complete`. The send button and input must be disabled while `pipelineActive === true`.

**5. Update step indicator labels**

The current step labels are "Input → Agent 1 → Agent 2 → Done". Update to more descriptive labels:

- "Start" → "Consultation" → "Drafting" → "Complete"

**6. Handle `agent2_done` with `pdf_path` from event data**

Instead of separately fetching documents via `getCaseDocuments()`, extract `pdf_path` directly from `eventData.data`:

```diff
             case 'agent2_done':
+              const pdfPath = eventData.data?.pdf_path;
               setMessages((prev) => [
                 ...prev,
                 {
                   id: Date.now().toString() + '_a2done',
                   text: eventData.message || 'Your document has been drafted successfully.',
                   sender: 'agent2',
                   timestamp: ...,
                   attachment: pdfPath ? {
                     name: pdfPath.split('/').pop() || 'Legal_Draft.pdf',
                     type: 'PDF',
                     size: 'Download',
                   } : undefined,
                 }
               ]);
               break;
```

**7. Handle `simulation_done` — render `case_ref`**

```diff
             case 'simulation_done':
+              if (eventData.data?.case_ref) {
+                setMessages((prev) => [
+                  ...prev,
+                  {
+                    id: Date.now().toString() + '_sim',
+                    text: `✅ Case filed successfully!\nReference: ${eventData.data.case_ref}`,
+                    sender: 'agent2',
+                    timestamp: ...,
+                  }
+                ]);
+              }
               setCurrentStep('done');
               break;
```

**8. On `complete`, also re-fetch case data to get documents from server**

Keep the existing `loadCaseData` call on `complete` to sync any PDFs that were generated.

---

### Summary of All Changes

| File | Change |
|---|---|
| `legalService.ts` | Replace `agent1_done` → `agent1_message` in SSEEvent type; add `case_id` field |
| `ChatScreen.tsx` | Full SSE handler refactor: new event handling, context-aware typing, input locking, step label updates |

## Verification Plan

### Manual Verification
1. Start a new chat — verify `case_id` is captured from first response
2. Agent 1 should show multiple conversational bubbles during consultation phase
3. After saying "Yes" to drafting, Agent 2 should activate and typing indicator should change
4. `agent2_question` events should render as normal bot bubbles
5. `agent2_done` should show PDF attachment
6. Input should be **disabled** during pipeline processing and re-enabled on `complete`
7. Resuming an existing case from CasesScreen should load history and allow continued chat
