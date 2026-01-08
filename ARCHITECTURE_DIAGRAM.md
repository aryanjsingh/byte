# Gemini Thinking Architecture Flow

## 📊 Complete System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                │
│  (Next.js + React + AI Elements)                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ChatInterface.tsx                                             │
│  ┌───────────────────────────────────────────────┐            │
│  │  1. User types message                        │            │
│  │  2. Send via WebSocket                        │            │
│  │  3. Receive thinking chunks                   │            │
│  │  4. Receive answer chunks                     │            │
│  │  5. Display in MessageBubble                  │            │
│  └───────────────────────────────────────────────┘            │
│                          │                                      │
│  MessageBubble.tsx          ▼                                  │
│  ┌───────────────────────────────────────────┐                │
│  │  Reasoning Component                      │                │
│  │  ├─ Auto-opens on streaming               │                │
│  │  ├─ Shows thinking content                │                │
│  │  └─ Collapses when done                   │                │
│  └───────────────────────────────────────────┘                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                          │
                          │ WebSocket Connection
                          │ ws://localhost:8000/ws/chat?token=...
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                         BACKEND                                 │
│  (FastAPI + LangGraph + Google GenAI SDK)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  server.py - WebSocket Handler                                 │
│  ┌───────────────────────────────────────────────┐            │
│  │  1. Authenticate via JWT                      │            │
│  │  2. Receive user message                      │            │
│  │  3. Load conversation context                 │            │
│  │  4. Call Gemini Thinking Wrapper              │            │
│  │  5. Stream chunks to client                   │            │
│  └───────────────────────────────────────────────┘            │
│                          │                                      │
│                          ▼                                      │
│  agent.py - Context & System Prompt                           │
│  ┌───────────────────────────────────────────────┐            │
│  │  retrieve_context()                           │            │
│  │  ├─ Fetch user profile                        │            │
│  │  ├─ Select mode (simple/turbo)                │            │
│  │  └─ Build system prompt                       │            │
│  └───────────────────────────────────────────────┘            │
│                          │                                      │
│                          ▼                                      │
│  gemini_thinking.py - Native SDK Wrapper                      │
│  ┌───────────────────────────────────────────────┐            │
│  │  generate_with_thinking_stream()              │            │
│  │  ├─ Convert LangChain → Gemini format        │            │
│  │  ├─ Configure thinking (budget=-1)            │            │
│  │  ├─ Stream from Gemini API                    │            │
│  │  └─ Separate thinking vs answer               │            │
│  └───────────────────────────────────────────────┘            │
│                          │                                      │
└──────────────────────────┼──────────────────────────────────────┘
                           │
                           │ HTTPS API Call
                           │ with ThinkingConfig
                           │
                           ▼
      ┌─────────────────────────────────────────────┐
      │       GOOGLE GEMINI 2.5 PRO API             │
      │                                             │
      │  GenerateContentStream                      │
      │  ┌───────────────────────────────────┐     │
      │  │  thinkingConfig:                  │     │
      │  │    includeThoughts: true          │     │
      │  │    thinkingBudget: -1 (dynamic)   │     │
      │  └───────────────────────────────────┘     │
      │                                             │
      │  Response Chunks:                           │
      │  ┌───────────────────────────────────┐     │
      │  │  Part 1: thought=true             │     │
      │  │    → "Let me analyze..."          │     │
      │  │  Part 2: thought=true             │     │
      │  │    → "Breaking this down..."      │     │
      │  │  Part 3: thought=false            │     │
      │  │    → "The answer is..."           │     │
      │  └───────────────────────────────────┘     │
      │                                             │
      └─────────────────────────────────────────────┘
```

## 🔄 Message Flow Diagram

```
USER ACTION                    FRONTEND                BACKEND                  GEMINI API
    │                             │                       │                         │
    │ 1. Type & send message      │                       │                         │
    ├──────────────────────────►  │                       │                         │
    │                             │ 2. WebSocket send     │                         │
    │                             ├──────────────────────►│                         │
    │                             │                       │ 3. Authenticate         │
    │                             │                       ├───┐                     │
    │                             │                       │   │                     │
    │                             │                       ├◄──┘                     │
    │                             │                       │ 4. Get context          │
    │                             │                       ├───┐                     │
    │                             │                       │   │                     │
    │                             │                       ├◄──┘                     │
    │                             │                       │ 5. Call Gemini SDK      │
    │                             │                       ├────────────────────────►│
    │                             │                       │                         │
    │                             │ 6. Thinking chunk     │ 7. Stream thinking      │
    │                             │◄──────────────────────┤◄────────────────────────┤
    │ 8. See thinking appear      │                       │                         │
    │◄────────────────────────────┤                       │                         │
    │                             │                       │                         │
    │                             │ 9. Answer chunk       │ 10. Stream answer       │
    │                             │◄──────────────────────┤◄────────────────────────┤
    │ 11. See answer stream       │                       │                         │
    │◄────────────────────────────┤                       │                         │
    │                             │                       │                         │
    │                             │ 12. Done              │ 13. Stream complete     │
    │                             │◄──────────────────────┤◄────────────────────────┤
    │ 14. Full message displayed  │                       │                         │
    │◄────────────────────────────┤                       │                         │
    │                             │                       │                         │
```

## 📦 Data Format Examples

### WebSocket Messages (Backend → Frontend)

#### Thinking Chunk
```json
{
  "type": "thinking",
  "content": "Let me break this down step by step. First, I need to understand..."
}
```

#### Answer Chunk
```json
{
  "type": "answer",
  "content": "Quantum computing uses quantum mechanics principles..."
}
```

#### Completion
```json
{
  "type": "done",
  "thread_id": "uuid-1234",
  "tool_calls": ["virustotal_scan"]
}
```

### Gemini API Request

```python
config = GenerateContentConfig(
    thinking_config=ThinkingConfig(
        include_thoughts=True,
        thinking_budget=-1  # Dynamic
    )
)

response = client.aio.models.generate_content_stream(
    model="gemini-2.5-pro",
    contents=[...],
    config=config
)
```

### Response Part Structure

```python
for chunk in response:
    for part in chunk.candidates[0].content.parts:
        if part.thought:
            # Thinking content
            thinking = part.text
        else:
            # Answer content
            answer = part.text
```

## 🎯 Key Components

### 1. Frontend WebSocket Client
- **Location**: `frontend/src/components/chat/ChatInterface.tsx`
- **Purpose**: Maintain persistent connection, handle streaming
- **Features**: Auto-reconnect, message queuing, state management

### 2. Backend WebSocket Server
- **Location**: `backend/server.py`
- **Purpose**: Handle connections, authenticate, route messages
- **Features**: JWT auth, thread management, error handling

### 3. Gemini Thinking Wrapper
- **Location**: `backend/ai_engine/our_ai_engine/gemini_thinking.py`
- **Purpose**: Interface with native Google GenAI SDK
- **Features**: Message conversion, streaming, thought extraction

### 4. Agent Context Manager
- **Location**: `backend/ai_engine/our_ai_engine/agent.py`
- **Purpose**: Build system prompts, manage user context
- **Features**: Profile loading, mode switching, tool binding

### 5. Reasoning UI Component
- **Location**: `frontend/src/components/ai-elements/reasoning.tsx`
- **Purpose**: Display thinking process beautifully
- **Features**: Auto-expand/collapse, smooth animations

## 🔐 Security Flow

```
User Login → JWT Token (7 days) → WebSocket Auth → Message Processing
    │             │                     │                  │
    │             │                     │                  └─► Encrypted
    │             │                     └─► Validated           thoughts
    │             └─► Signed with SECRET_KEY
    └─► Password hashed with bcrypt
```

## 📊 Token Flow

```
1. User signup/login
   └─► backend/server.py → create_access_token()
       └─► JWT with 7-day expiry
           └─► Returned to frontend
               └─► Stored in session
                   └─► Sent with WebSocket connection
                       └─► Validated on every message
```

---

**Visual Guide Version**: 1.0  
**Last Updated**: Implementation Complete ✅
