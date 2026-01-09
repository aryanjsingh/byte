import sys
import os

# Ensure project root is in path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from fastapi import FastAPI, HTTPException, Depends, status, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from contextlib import asynccontextmanager
import json

# Database & Auth
from backend.database import create_db_and_tables, get_session, get_db_session
from backend.models import User, UserSecurityProfile, ConversationLog, ChatThread
from backend.auth import get_password_hash, create_access_token, verify_password, get_current_user
import uuid
from datetime import datetime

# Existing Agent
from backend.ai_engine.our_ai_engine.agent import app as agent_app

# Try to import voice handler, but make it optional
try:
    from backend.ai_engine.our_ai_engine.voice_handler import VoiceWebHandler
    voice_handler = VoiceWebHandler()
    VOICE_ENABLED = True
    print("✅ Voice handler initialized")
except ImportError as e:
    print(f"ℹ️  Voice features disabled (optional): {e}")
    print("   Install 'lightning-whisper-mlx' to enable voice chat - this is optional.")
    voice_handler = None
    VOICE_ENABLED = False

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from fastapi import UploadFile, File, Form

# Import tools router
from backend.tools_api import router as tools_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(title="BYTE Security Agent API", lifespan=lifespan)

# Include tools router
app.include_router(tools_router)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Auth Models ---
class UserCreate(BaseModel):
    email: str
    password: str
    name: str = "User"

class Token(BaseModel):
    access_token: str
    token_type: str

class ChatRequest(BaseModel):
    message: str
    thread_id: str = "new" # "new" or UUID
    mode: str = "simple"  # "simple" or "turbo"

class ChatResponse(BaseModel):
    response: str
    tool_calls: list = []
    thread_id: str
    audio: str | None = None
    transcription: str | None = None

class TTSRequest(BaseModel):
    text: str

@app.post("/tts")
async def text_to_speech(request: TTSRequest, current_user: User = Depends(get_current_user)):
    if not VOICE_ENABLED or voice_handler is None:
        raise HTTPException(status_code=503, detail="Voice features not available. Install lightning-whisper-mlx to enable.")
    
    try:
        # Limit text length to avoid overload
        text = request.text[:1000] 
        audio_base64 = voice_handler.synthesize_speech(text)
        if not audio_base64:
            raise HTTPException(status_code=500, detail="Failed to synthesize speech")
        return {"audio": audio_base64}
    except Exception as e:
        print(f"TTS Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "BYTE Backend"}

# --- Knowledge Base Management ---
@app.post("/kb/reinitialize")
async def reinitialize_knowledge_base(current_user: User = Depends(get_current_user)):
    """
    Reinitialize the vector store with documents from the docs folder.
    Call this after adding new .txt files to backend/ai_engine/kb_engine/docs/
    """
    try:
        from backend.ai_engine.kb_engine.kb_engine import initialize_vector_store
        vectordb = initialize_vector_store()
        if vectordb:
            return {"status": "success", "message": "Knowledge base reinitialized successfully"}
        return {"status": "warning", "message": "No documents found to initialize"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reinitialize KB: {str(e)}")

@app.get("/kb/search")
async def search_knowledge_base(
    query: str,
    n_results: int = 5,
    current_user: User = Depends(get_current_user)
):
    """
    Search the knowledge base directly (for testing/debugging).
    """
    try:
        from backend.ai_engine.kb_engine.kb_engine import query_rag
        results = query_rag(query, n_results=n_results)
        return {"query": query, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"KB search failed: {str(e)}")

@app.get("/kb/status")
async def knowledge_base_status(current_user: User = Depends(get_current_user)):
    """
    Get knowledge base status and document count.
    """
    import os
    try:
        docs_dir = os.path.join(os.path.dirname(__file__), "ai_engine/kb_engine/docs")
        db_dir = os.path.join(os.path.dirname(__file__), "ai_engine/kb_engine/db")
        
        doc_files = [f for f in os.listdir(docs_dir) if f.endswith('.txt')] if os.path.exists(docs_dir) else []
        db_exists = os.path.exists(db_dir)
        
        return {
            "status": "ready" if db_exists else "not_initialized",
            "documents": doc_files,
            "document_count": len(doc_files),
            "vector_store_exists": db_exists
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get KB status: {str(e)}")

# --- WebSocket Streaming Chat Route ---
@app.websocket("/ws/chat")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    token: str
):
    """
    WebSocket endpoint for streaming chat with thinking display.
    Token passed as query parameter: ws://host/ws/chat?token=...
    
    NOTE: We don't use Depends(get_session) here because WebSocket connections
    are long-lived and would hold database connections open indefinitely.
    Instead, we create short-lived sessions for each database operation.
    """
    print(f"DEBUG: WebSocket connection attempt. Token partial: {token[:10]}...")
    current_user = None
    user_id = None
    user_email = None
    
    try:
        # Authenticate via token
        from jose import JWTError, jwt
        from backend.auth import SECRET_KEY, ALGORITHM
        
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            email: str = payload.get("sub")
            print(f"DEBUG: Token verified for user: {email}")
            if email is None:
                print("DEBUG: Token payload missing email (sub)")
                await websocket.close(code=1008, reason="Invalid authentication")
                return
        except JWTError as e:
            print(f"DEBUG: JWT Decode Error: {e}")
            await websocket.close(code=1008, reason="Invalid authentication")
            return
        
        # Get user from DB with short-lived session
        with get_db_session() as session:
            statement = select(User).where(User.email == email)
            current_user = session.exec(statement).first()
            if current_user is None:
                print(f"DEBUG: User not found in DB for email: {email}")
                await websocket.close(code=1008, reason="User not found")
                return
            # Store user info we need (detach from session)
            user_id = current_user.id
            user_email = current_user.email
            
        print(f"DEBUG: Accepting WebSocket for {user_email}")
        # Accept WebSocket connection
        await websocket.accept()
        
        # Communication loop
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                request_data = json.loads(data)
                
                user_message = request_data.get("message", "")
                thread_id = request_data.get("thread_id", "new")
                mode = request_data.get("mode", "simple")
                image_data = request_data.get("image_data")  # Base64 encoded image
                image_mime_type = request_data.get("image_mime_type")  # e.g., 'image/jpeg'
                
                if not user_message.strip() and not image_data:
                    await websocket.send_json({"type": "error", "error": "Empty message"})
                    continue
                
                # Handle Thread Creation/Retrieval with short-lived session
                current_thread_id = thread_id
                
                with get_db_session() as session:
                    if current_thread_id == "new" or not current_thread_id:
                        current_thread_id = str(uuid.uuid4())
                        title = user_message[:30] + "..." if len(user_message) > 30 else user_message
                        new_thread = ChatThread(id=current_thread_id, user_id=user_id, title=title)
                        session.add(new_thread)
                        session.commit()
                    else:
                        # Verify thread exists and belongs to user
                        thread = session.get(ChatThread, current_thread_id)
                        if not thread:
                            current_thread_id = str(uuid.uuid4())
                            new_thread = ChatThread(id=current_thread_id, user_id=user_id, title="New Chat")
                            session.add(new_thread)
                            session.commit()
                        elif thread.user_id != user_id:
                            await websocket.send_json({"type": "error", "error": "Not authorized for this thread"})
                            continue
                        else:
                            thread.updated_at = datetime.utcnow()
                            session.add(thread)
                            session.commit()
                
                # Use Native Gemini Agent with proper function calling
                from backend.ai_engine.our_ai_engine.native_gemini_agent import get_native_agent, Message
                
                native_agent = get_native_agent()
                
                # Convert history to Message format
                messages_for_agent = []
                
                # Load Conversation History from DB with short-lived session
                with get_db_session() as session:
                    try:
                        # Fetch last 10 messages for context (reduced from 20 to prevent token overflow)
                        statement = select(ConversationLog).where(
                            ConversationLog.thread_id == current_thread_id
                        ).order_by(ConversationLog.created_at.desc()).limit(10)
                        
                        history_logs = list(reversed(session.exec(statement).all()))
                        
                        for log in history_logs:
                            if log.role == 'user':
                                # Truncate very long user messages
                                content = log.content[:2000] if log.content else ""
                                messages_for_agent.append(Message(role="user", content=content))
                            elif log.role == 'assistant':
                                # Simplify history by just including text content (truncated)
                                if log.content:
                                    # Truncate assistant responses to prevent token overflow
                                    content = log.content[:3000] if len(log.content) > 3000 else log.content
                                    messages_for_agent.append(Message(role="model", content=content))
                    except Exception as e:
                        print(f"⚠️ Failed to load history: {e}")
                
                # Add current user message
                current_message = Message(
                    role="user", 
                    content=user_message,
                    image_data=image_data,
                    image_mime_type=image_mime_type
                )
                messages_for_agent.append(current_message)
                
                print(f"🔥 DEBUG: Starting Native Agent Loop for thread {current_thread_id}")
                
                thinking_content = ""
                answer_content = ""
                tool_calls_list = []
                tool_invocations_list = []  # Track full tool invocations with results
                event_count = 0
                
                try:
                    async for event in native_agent.run_agent_loop(
                        messages=messages_for_agent,
                        user_id=str(user_id),
                        mode=mode,
                        thinking_budget=-1
                    ):
                        event_count += 1
                        msg_type = event["type"]
                        
                        # Handle image_gen tool results specially - send the full base64
                        # but process it before sending to ensure proper format
                        if msg_type == "tool_result" and event.get("tool_name") == "image_gen":
                            result_content = event.get("content", "")
                            if "image_base64" in result_content:
                                try:
                                    parsed = json.loads(result_content)
                                    if parsed.get("type") == "image_gen_result":
                                        # Send the image_gen result with full base64
                                        print(f"📤 WS SEND #{event_count}: image_gen result, base64 len={len(parsed.get('image_base64', ''))}")
                                        await websocket.send_json({
                                            "type": "tool_result",
                                            "tool_name": "image_gen",
                                            "content": result_content  # Full JSON with base64
                                        })
                                        print(f"📤 WS SEND #{event_count}: image_gen SENT!")
                                        
                                        # Store for invocations list
                                        for inv in tool_invocations_list:
                                            if inv["name"] == "image_gen" and inv["result"] is None:
                                                inv["result"] = result_content
                                                inv["status"] = "completed"
                                                break
                                        continue
                                except Exception as e:
                                    print(f"⚠️ Failed to parse image_gen result: {e}")
                        
                        print(f"📤 WS SEND #{event_count}: type={msg_type}, content_len={len(str(event.get('content', '')))}")
                        await websocket.send_json(event)
                        print(f"📤 WS SEND #{event_count}: SENT!")
                        
                        if msg_type == "tool_call":
                            t_name = event["tool_name"]
                            if t_name not in tool_calls_list:
                                tool_calls_list.append(t_name)
                            # Add to invocations list
                            tool_invocations_list.append({
                                "name": t_name,
                                "args": event.get("tool_args", {}),
                                "result": None,
                                "status": "calling"
                            })
                        elif msg_type == "tool_result":
                            # Update the tool invocation with result
                            t_name = event.get("tool_name")
                            result_content = event.get("content", "")
                            
                            for inv in tool_invocations_list:
                                if inv["name"] == t_name and inv["result"] is None:
                                    inv["result"] = result_content
                                    inv["status"] = "completed"
                                    break
                        elif msg_type == "answer":
                             answer_content += event.get("content", "")
                        elif msg_type == "thinking":
                             thinking_content += event.get("content", "")
                    
                    print(f"📤 WS: Stream complete. Total events={event_count}, thinking_len={len(thinking_content)}, answer_len={len(answer_content)}")
                    
                    # Send completion
                    await websocket.send_json({
                        "type": "done",
                        "thread_id": current_thread_id,
                        "tool_calls": tool_calls_list
                    })
                    print(f"📤 WS: Sent 'done' event")
                    
                    # Log to database with short-lived session
                    with get_db_session() as session:
                        log_user = ConversationLog(
                            user_id=user_id,
                            thread_id=current_thread_id,
                            role="user",
                            content=user_message,
                            mode=mode
                        )
                        session.add(log_user)
                        
                        log_ai = ConversationLog(
                            user_id=user_id,
                            thread_id=current_thread_id,
                            role="assistant",
                            content=answer_content,
                            mode=mode,
                            tool_calls=tool_calls_list,
                            thinking=thinking_content if thinking_content else None,
                            tool_invocations=tool_invocations_list if tool_invocations_list else []
                        )
                        session.add(log_ai)
                        session.commit()
                    
                except Exception as e:
                    print(f"❌ Error during agent streaming: {e}")
                    import traceback
                    traceback.print_exc()
                    try:
                        await websocket.send_json({
                            "type": "error",
                            "error": str(e)
                        })
                    except:
                        print(f"WebSocket connection lost during error send, exiting loop")
                        break  # Connection already closed

                    
            except json.JSONDecodeError:
                try:
                    await websocket.send_json({"type": "error", "error": "Invalid JSON"})
                except:
                    print(f"WebSocket connection lost, exiting loop")
                    break
            except WebSocketDisconnect:
                print(f"WebSocket disconnected during message processing")
                break
            except Exception as e:
                print(f"Error processing message: {e}")
                try:
                    await websocket.send_json({"type": "error", "error": str(e)})
                except:
                    # Connection is dead, exit the loop
                    print(f"WebSocket connection lost, exiting loop")
                    break
                
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for user {user_email if user_email else 'unknown'}")
    except Exception as e:
        print(f"WebSocket error: {e}")
        import traceback
        traceback.print_exc()

# --- Auth Routes ---
@app.post("/auth/signup", response_model=Token)
async def signup(user_data: UserCreate, session: Session = Depends(get_session)):
    statement = select(User).where(User.email == user_data.email)
    existing_user = session.exec(statement).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pwd = get_password_hash(user_data.password)
    new_user = User(email=user_data.email, name=user_data.name, password_hash=hashed_pwd)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    
    # Initialize Profile
    new_profile = UserSecurityProfile(user_id=new_user.id)
    session.add(new_profile)
    session.commit()
    
    # Create Token
    access_token = create_access_token(data={"sub": new_user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/auth/login", response_model=Token)
async def login(user_data: UserCreate, session: Session = Depends(get_session)):
    print(f"DEBUG: Login attempt for email: {user_data.email}")
    statement = select(User).where(User.email == user_data.email)
    user = session.exec(statement).first()
    
    if not user:
        print(f"DEBUG: User not found for email: {user_data.email}")
    
    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/auth/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return {"email": current_user.email, "id": current_user.id, "name": current_user.name}

@app.get("/chat/threads")
async def get_threads(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """List all chat threads for the user"""
    statement = select(ChatThread).where(ChatThread.user_id == current_user.id).order_by(ChatThread.updated_at.desc())
    threads = session.exec(statement).all()
    return threads

@app.get("/chat/threads/{thread_id}")
async def get_thread_history(
    thread_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Retrieve history for a specific thread"""
    thread = session.get(ChatThread, thread_id)
    if not thread or thread.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Thread not found")
        
    statement = select(ConversationLog).where(
        ConversationLog.thread_id == thread_id
    ).order_by(ConversationLog.timestamp.asc())
    
    logs = session.exec(statement).all()
    return {"title": thread.title, "messages": logs}
    
@app.delete("/chat/threads/{thread_id}")
async def delete_thread(
    thread_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Delete a specific thread and its history"""
    thread = session.get(ChatThread, thread_id)
    if not thread or thread.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Thread not found")
        
    # Explicitly delete all logs for this thread first to avoid FK constraint errors
    statement = select(ConversationLog).where(ConversationLog.thread_id == thread_id)
    logs = session.exec(statement).all()
    for log in logs:
        session.delete(log)
        
    # Now delete the thread
    session.delete(thread)
    session.commit()
    
    return {"status": "success", "message": "Thread deleted"}
    
# --- Chat History Route ---
@app.get("/chat/history")
async def get_chat_history(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    limit: int = 50
):
    """Retrieve recent chat history for the authenticated user"""
    statement = select(ConversationLog).where(
        ConversationLog.user_id == current_user.id
    ).order_by(ConversationLog.timestamp.desc()).limit(limit)
    
    logs = session.exec(statement).all()
    
    # Reverse to get chronological order
    messages = [
        {
            "role": log.role, 
            "content": log.content, 
            "mode": log.mode,
            "tool_calls": log.tool_calls,
            "timestamp": log.timestamp.isoformat()
        }
        for log in reversed(logs)
    ]
    
    return {"messages": messages}

# --- Chat Route (Protected) ---
@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest, 
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    try:
        print(f"DEBUG: Processing chat request - Mode: {request.mode}")
        # Handle Thread Creation/Retrieval
        current_thread_id = request.thread_id
        
        if current_thread_id == "new" or not current_thread_id:
            current_thread_id = str(uuid.uuid4())
            title = request.message[:30] + "..." if len(request.message) > 30 else request.message
            new_thread = ChatThread(id=current_thread_id, user_id=current_user.id, title=title)
            session.add(new_thread)
            session.commit()
            print(f"DEBUG: Created new thread {current_thread_id}")
        else:
            # Verify thread exists and belongs to user
            thread = session.get(ChatThread, current_thread_id)
            if not thread:
                # Fallback create if invalid ID passed
                current_thread_id = str(uuid.uuid4())
                new_thread = ChatThread(id=current_thread_id, user_id=current_user.id, title="New Chat")
                session.add(new_thread)
                session.commit()
            elif thread.user_id != current_user.id:
                 raise HTTPException(status_code=403, detail="Not authorized for this thread")
            else:
                 # Update timestamp
                 thread.updated_at = datetime.utcnow()
                 session.add(thread)
                 session.commit()

        # Pass user_id to the agent state
        config = {"configurable": {"thread_id": current_thread_id}}
        
        inputs = {
            "messages": [HumanMessage(content=request.message)],
            "user_id": str(current_user.id), # Passing the ID for profile lookup
            "mode": request.mode  # Pass mode to agent
        }
        
        result = agent_app.invoke(inputs, config=config)
        
        # Helper to safely extract text string from message content
        def _get_content_str(content):
            if isinstance(content, str):
                return content
            elif isinstance(content, list):
                text_parts = []
                for part in content:
                    if isinstance(part, dict) and "text" in part:
                        text_parts.append(part["text"])
                    elif hasattr(part, "text"):
                        text_parts.append(part.text)
                    elif isinstance(part, str):
                        text_parts.append(part)
                return "".join(text_parts)
            return str(content)

        final_message = result["messages"][-1]
        response_text = _get_content_str(final_message.content)
        
        # DEBUG: Print response info
        print(f"🔥 DEBUG: final_message type = {type(final_message).__name__}")
        print(f"🔥 DEBUG: response_text = {response_text[:200] if response_text else 'EMPTY'}")
        
        # Extract tools from the result messages
        tool_calls = []
        from langchain_core.messages import AIMessage
        
        # Iterate through ALL messages in the verification/reasoning chain
        for msg in result.get("messages", []):
             if isinstance(msg, AIMessage):
                 # check .tool_calls attribute
                 if msg.tool_calls:
                     for tc in msg.tool_calls:
                         tname = tc.get("name")
                         if tname and tname not in tool_calls:
                             tool_calls.append(tname)
                             
        print(f"🔥 DEBUG: Final tool_calls detected: {tool_calls}")

        # Async: Log conversation to DB
        log_user = ConversationLog(
            user_id=current_user.id, 
            thread_id=current_thread_id, 
            role="user", 
            content=request.message,
            mode=request.mode
        )
        session.add(log_user)
        
        log_ai = ConversationLog(
            user_id=current_user.id, 
            thread_id=current_thread_id, 
            role="assistant", 
            content=response_text,
            mode=request.mode,
            tool_calls=tool_calls
        )
        session.add(log_ai)
        session.commit()

        return ChatResponse(response=response_text, tool_calls=tool_calls, thread_id=current_thread_id)

    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/voice", response_model=ChatResponse)
async def chat_voice(
    audio: UploadFile = File(...),
    thread_id: str = Form("new"),
    mode: str = Form("simple"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    if not VOICE_ENABLED or voice_handler is None:
        raise HTTPException(status_code=503, detail="Voice features not available. Install lightning-whisper-mlx to enable.")
    
    try:
        # 1. Read Audio
        audio_content = await audio.read()
        print(f"DEBUG: Received audio upload - Size: {len(audio_content)} bytes")
        
        if len(audio_content) < 100:
            raise HTTPException(status_code=400, detail="Audio file too small")

        # 2. Transcribe
        user_text = voice_handler.transcribe_audio(audio_content)
        if not user_text:
            print("DEBUG: Transcription empty, returning silent response.")
            return ChatResponse(response="", thread_id=thread_id, tool_calls=[])
            
        print(f"Voice Transcription: {user_text}")

        # 3. Process with Agent (Reusing the same logic as /chat)
        current_thread_id = thread_id
        if current_thread_id == "new" or not current_thread_id:
            current_thread_id = str(uuid.uuid4())
            title = user_text[:30] + "..." if len(user_text) > 30 else user_text
            new_thread = ChatThread(id=current_thread_id, user_id=current_user.id, title=title)
            session.add(new_thread)
            session.commit()
        else:
            thread = session.get(ChatThread, current_thread_id)
            if not thread or thread.user_id != current_user.id:
                # Fallback
                current_thread_id = str(uuid.uuid4())
                new_thread = ChatThread(id=current_thread_id, user_id=current_user.id, title="Voice Chat")
                session.add(new_thread)
                session.commit()
            else:
                thread.updated_at = datetime.utcnow()
                session.add(thread)
                session.commit()

        config = {"configurable": {"thread_id": current_thread_id}}
        inputs = {
            "messages": [HumanMessage(content=user_text)],
            "user_id": str(current_user.id),
            "mode": mode
        }
        
        result = agent_app.invoke(inputs, config=config)
        
        # Helper to safely extract text string from message content
        def _get_content_str(content):
            if isinstance(content, str):
                return content
            elif isinstance(content, list):
                text_parts = []
                for part in content:
                    if isinstance(part, dict) and "text" in part:
                        text_parts.append(part["text"])
                    elif hasattr(part, "text"):
                        text_parts.append(part.text)
                    elif isinstance(part, str):
                        text_parts.append(part)
                return "".join(text_parts)
            return str(content)

        final_message = result["messages"][-1]
        response_text = _get_content_str(final_message.content)
        # Extract tools from the result messages
        tool_calls = []
        from langchain_core.messages import AIMessage
        
        for msg in result.get("messages", []):
             if isinstance(msg, AIMessage):
                 if msg.tool_calls:
                     for tc in msg.tool_calls:
                         tname = tc.get("name")
                         if tname and tname not in tool_calls:
                             tool_calls.append(tname)
        
        print(f"🔥 DEBUG (Voice): tool_calls: {tool_calls}")

        # 4. Synthesize Response
        audio_base64 = voice_handler.synthesize_speech(response_text)
        
        # 5. Log to DB
        log_user = ConversationLog(
            user_id=current_user.id, 
            thread_id=current_thread_id, 
            role="user", 
            content=user_text, 
            mode=mode
        )
        log_ai = ConversationLog(
            user_id=current_user.id, 
            thread_id=current_thread_id, 
            role="assistant", 
            content=response_text, 
            mode=mode,
            tool_calls=tool_calls
        )
        session.add(log_user)
        session.add(log_ai)
        session.commit()

        return ChatResponse(
            response=response_text, 
            thread_id=current_thread_id,
            audio=audio_base64,
            transcription=user_text,
            tool_calls=tool_calls
        )

    except HTTPException as he:
        # Re-raise known HTTP exceptions
        raise he
    except Exception as e:
        print(f"Error in chat_voice: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Accessible on network
    uvicorn.run(app, host="0.0.0.0", port=8000)
