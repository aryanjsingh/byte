# BYTE Project Structure

## 📁 Complete Directory Layout

```
/home/ubuntu/byte/
│
├── 📄 .env                          # Environment variables (GOOGLE_API_KEY)
├── 📄 .gitignore
├── 📄 start.sh                      # Quick start script (runs backend)
│
├── 📚 Documentation Files
│   ├── README_GEMINI_THINKING.md    # Quick start guide
│   ├── IMPLEMENTATION_COMPLETE.md   # Full implementation details
│   ├── GEMINI_THINKING_README.md    # Architecture & troubleshooting
│   ├── ARCHITECTURE_DIAGRAM.md      # Visual flow diagrams
│   └── PROJECT_STRUCTURE.md         # This file
│
├── 🔧 backend/                      # Backend Python API
│   ├── __init__.py
│   ├── requirements.txt             # Python dependencies
│   ├── run.py                       # Easy backend startup script
│   ├── test_setup.py                # Setup verification (5 tests)
│   ├── server.py                    # FastAPI server + WebSocket
│   ├── auth.py                      # JWT authentication (7-day tokens)
│   ├── database.py                  # SQLModel database setup
│   ├── models.py                    # Database models
│   ├── main.py                      # Legacy entry point
│   │
│   ├── ai_engine/                   # AI/Agent logic
│   │   ├── __init__.py
│   │   ├── kb_engine/              # Knowledge base (RAG)
│   │   │   ├── __init__.py
│   │   │   ├── kb_engine.py
│   │   │   └── voice_engine/       # Voice I/O
│   │   │       ├── __init__.py
│   │   │       ├── voice_bridge.py
│   │   │       ├── voice_listener.py
│   │   │       └── voice_speaker.py
│   │   │
│   │   └── our_ai_engine/          # Main agent
│   │       ├── __init__.py
│   │       ├── agent.py            # LangGraph agent + Gemini 2.5 Pro
│   │       ├── gemini_thinking.py  # ⭐ Native SDK wrapper for thinking
│   │       ├── voice_handler.py
│   │       ├── verify_agent.py
│   │       ├── verify_rag.py
│   │       ├── verify_tools.py
│   │       ├── verify_voice.py
│   │       │
│   │       └── tools/               # Agent tools
│   │           ├── __init__.py
│   │           ├── greynoise_tool.py
│   │           ├── phishtank_tool.py
│   │           ├── profile_tools.py
│   │           ├── rag_tool.py
│   │           ├── shodan_tool.py
│   │           └── virustotal_tool.py
│   │
│   └── usermanagement/
│       └── __init__.py
│
└── 🎨 frontend/                     # Next.js Frontend
    ├── package.json
    ├── package-lock.json
    ├── next.config.ts
    ├── tsconfig.json
    ├── postcss.config.mjs
    ├── eslint.config.mjs
    ├── components.json
    ├── .gitignore
    │
    ├── public/                      # Static assets
    │   └── ...
    │
    └── src/
        ├── app/                     # Next.js App Router
        │   ├── page.tsx            # Home page (chat interface)
        │   ├── layout.tsx          # Root layout
        │   ├── globals.css         # Global styles
        │   ├── login/
        │   │   └── page.tsx
        │   ├── signup/
        │   │   └── page.tsx
        │   ├── c/[threadId]/       # Individual chat threads
        │   │   └── page.tsx
        │   └── api/
        │       └── auth/
        │           └── [...nextauth]/
        │               └── route.ts
        │
        ├── components/              # React components
        │   ├── ai-elements/        # ⭐ AI UI components
        │   │   ├── reasoning.tsx   # Thinking/reasoning display
        │   │   ├── message.tsx     # Message components
        │   │   └── shimmer.tsx     # Loading animations
        │   │
        │   ├── chat/               # Chat components
        │   │   ├── ChatInterface.tsx  # ⭐ Main chat (WebSocket)
        │   │   ├── MessageBubble.tsx  # Message display
        │   │   └── InputArea.tsx      # Input + voice
        │   │
        │   ├── layout/              # Layout components
        │   │   ├── Header.tsx
        │   │   └── Sidebar.tsx
        │   │
        │   └── ui/                  # UI primitives
        │       ├── button.tsx
        │       ├── tooltip.tsx
        │       ├── separator.tsx
        │       ├── collapsible.tsx
        │       └── ...
        │
        ├── auth.ts                  # NextAuth configuration
        └── middleware.ts            # Auth middleware
```

## 🔑 Key Files Explained

### Backend

#### Core Files
- **`backend/run.py`** - Easy startup script with environment validation
- **`backend/server.py`** - FastAPI server with WebSocket thinking integration
- **`backend/auth.py`** - JWT auth with 7-day token expiry
- **`backend/requirements.txt`** - All Python dependencies

#### AI Engine
- **`backend/ai_engine/our_ai_engine/agent.py`**
  - LangGraph state graph
  - Gemini 2.5 Pro with streaming
  - Context retrieval & system prompts
  - Tool binding

- **`backend/ai_engine/our_ai_engine/gemini_thinking.py`** ⭐ NEW
  - Native Google GenAI SDK wrapper
  - Async streaming with thinking support
  - Automatic thought/answer separation
  - Message format conversion

#### Tools
- `virustotal_tool.py` - URL/file scanning
- `greynoise_tool.py` - IP reputation checks
- `profile_tools.py` - User profile management

### Frontend

#### Core Components
- **`src/components/chat/ChatInterface.tsx`** ⭐
  - WebSocket connection management
  - Real-time message streaming
  - Thinking + answer state management
  - Comprehensive debugging

- **`src/components/chat/MessageBubble.tsx`**
  - Message rendering with markdown
  - Thinking/reasoning display
  - Tool call badges
  - TTS integration

- **`src/components/ai-elements/reasoning.tsx`** ⭐
  - Collapsible thinking component
  - Auto-opens during streaming
  - Beautiful animations
  - Accessibility features

## 📦 Configuration Files

### Backend
- `.env` - Environment variables (project root)
  ```bash
  GOOGLE_API_KEY=your_key_here
  ```

- `backend/requirements.txt` - Python packages
  - `google-genai` - Native Gemini SDK
  - `langchain-google-genai` - LangChain integration
  - `langgraph` - Agent framework
  - `fastapi` - Web framework
  - `uvicorn` - ASGI server

### Frontend
- `frontend/package.json` - Node.js packages
  - `next` - Framework
  - `ai` - AI SDK
  - `framer-motion` - Animations
  - AI Elements components

## 🚀 Startup Scripts

### Backend
```bash
# From project root
./start.sh

# From backend directory
cd backend && python3 run.py

# Manual
cd backend && python3 server.py
```

### Frontend
```bash
cd frontend && npm run dev
```

### Testing
```bash
cd backend && python3 test_setup.py
```

## 🔄 Data Flow

1. **User Input** → `ChatInterface.tsx`
2. **WebSocket** → `ws://localhost:8000/ws/chat`
3. **Backend** → `server.py` WebSocket handler
4. **Context** → `agent.py` retrieve_context()
5. **Thinking** → `gemini_thinking.py` wrapper
6. **Gemini API** → Native SDK streaming
7. **Response** → Separate thinking + answer chunks
8. **Frontend** → Display in `MessageBubble.tsx`
9. **UI** → `Reasoning` component shows thinking

## 📊 File Counts

- Backend Python files: ~28
- Frontend TypeScript/TSX files: ~15+
- Documentation files: 5
- Configuration files: ~8
- Total: ~56+ files

## 🎯 Important Paths

### For Development
- Backend code: `/home/ubuntu/byte/backend/`
- Frontend code: `/home/ubuntu/byte/frontend/src/`
- AI logic: `/home/ubuntu/byte/backend/ai_engine/`
- UI components: `/home/ubuntu/byte/frontend/src/components/`

### For Configuration
- Environment: `/home/ubuntu/byte/.env`
- Backend deps: `/home/ubuntu/byte/backend/requirements.txt`
- Frontend deps: `/home/ubuntu/byte/frontend/package.json`

### For Documentation
- All docs: `/home/ubuntu/byte/*.md`
- Quick start: `/home/ubuntu/byte/README_GEMINI_THINKING.md`

---

**Last Updated**: After file reorganization ✅
