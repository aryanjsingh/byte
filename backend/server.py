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
from backend.database import create_db_and_tables, get_session
from backend.database import create_db_and_tables, get_session
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
    print(f"⚠️  Voice handler not available: {e}")
    print("   Voice features disabled. Install lightning-whisper-mlx to enable.")
    voice_handler = None
    VOICE_ENABLED = False

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from fastapi import UploadFile, File, Form

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(title="BYTE Security Agent API", lifespan=lifespan)

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

# --- WebSocket Streaming Chat Route ---
@app.websocket("/ws/chat")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    token: str,
    session: Session = Depends(get_session)
):
    """
    WebSocket endpoint for streaming chat with thinking display.
    Token passed as query parameter: ws://host/ws/chat?token=...
    """
    print(f"DEBUG: WebSocket connection attempt. Token partial: {token[:10]}...")
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
        
        # Get user from DB
        statement = select(User).where(User.email == email)
        current_user = session.exec(statement).first()
        if current_user is None:
            print(f"DEBUG: User not found in DB for email: {email}")
            await websocket.close(code=1008, reason="User not found")
            return
            
        print(f"DEBUG: Accepting WebSocket for {email}")
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
                
                if not user_message.strip():
                    await websocket.send_json({"type": "error", "error": "Empty message"})
                    continue
                
                # Handle Thread Creation/Retrieval
                current_thread_id = thread_id
                
                if current_thread_id == "new" or not current_thread_id:
                    current_thread_id = str(uuid.uuid4())
                    title = user_message[:30] + "..." if len(user_message) > 30 else user_message
                    new_thread = ChatThread(id=current_thread_id, user_id=current_user.id, title=title)
                    session.add(new_thread)
                    session.commit()
                else:
                    # Verify thread exists and belongs to user
                    thread = session.get(ChatThread, current_thread_id)
                    if not thread:
                        current_thread_id = str(uuid.uuid4())
                        new_thread = ChatThread(id=current_thread_id, user_id=current_user.id, title="New Chat")
                        session.add(new_thread)
                        session.commit()
                    elif thread.user_id != current_user.id:
                        await websocket.send_json({"type": "error", "error": "Not authorized for this thread"})
                        continue
                    else:
                        thread.updated_at = datetime.utcnow()
                        session.add(thread)
                        session.commit()
                
                # Invoke agent with streaming using Gemini Thinking Wrapper
                from backend.ai_engine.our_ai_engine.gemini_thinking import get_thinking_wrapper
                
                thinking_wrapper = get_thinking_wrapper()
                
                # Prepare messages for direct Gemini thinking stream
                # We need to extract the final messages after context retrieval
                config_state = {"configurable": {"thread_id": current_thread_id}}
                inputs_for_context = {
                    "messages": [HumanMessage(content=user_message)],
                    "user_id": str(current_user.id),
                    "mode": mode
                }
                
                # Stream response from agent
                thinking_content = ""
                answer_content = ""
                tool_calls_list = []
                
                try:
                    print(f"🔥 DEBUG: Starting Gemini thinking stream for thread {current_thread_id} in mode {mode}")
                    print(f"   User message: {user_message[:100]}...")
                    print(f"   Thinking wrapper enabled: {thinking_wrapper.thinking_enabled}")
                    
                    chunk_count = 0
                    thinking_chunk_count = 0
                    answer_chunk_count = 0
                    
                    # Use the native thinking wrapper for direct streaming
                    if thinking_wrapper.thinking_enabled:
                        print("✅ Using native Gemini thinking wrapper")
                        
                        # Get the context-enriched messages from retrieve_context node
                        from backend.ai_engine.our_ai_engine.agent import retrieve_context
                        context_state = retrieve_context(inputs_for_context)
                        
                        # Combine system message with user message
                        final_messages = context_state["messages"] + [HumanMessage(content=user_message)]
                        
                        print(f"   Final messages count: {len(final_messages)}")
                        for i, msg in enumerate(final_messages):
                            msg_type = type(msg).__name__
                            preview = (msg.content[:50] + "...") if hasattr(msg, 'content') and msg.content else "EMPTY"
                            print(f"   Msg {i}: {msg_type} - {preview}")
                        
                        # Stream with thinking
                        async for chunk in thinking_wrapper.generate_with_thinking_stream(
                            messages=final_messages,
                            thinking_budget=-1,  # Dynamic thinking
                            include_thoughts=True
                        ):
                            chunk_count += 1
                            chunk_type = chunk.get("type")
                            chunk_content = chunk.get("content", "")
                            
                            print(f"📦 Chunk {chunk_count} - Type: {chunk_type}, Length: {len(chunk_content)}")
                            
                            if chunk_type == "thinking":
                                thinking_chunk_count += 1
                                thinking_content += chunk_content
                                await websocket.send_json({
                                    "type": "thinking",
                                    "content": chunk_content
                                })
                                print(f"   💭 Sent thinking chunk {thinking_chunk_count}")
                                
                            elif chunk_type == "answer":
                                answer_chunk_count += 1
                                answer_content += chunk_content
                                await websocket.send_json({
                                    "type": "answer",
                                    "content": chunk_content
                                })
                                print(f"   💬 Sent answer chunk {answer_chunk_count}")
                                
                            elif chunk_type == "error":
                                print(f"   ❌ Error chunk: {chunk_content}")
                                await websocket.send_json({
                                    "type": "error",
                                    "error": chunk_content
                                })
                                
                    else:
                        # Fallback to LangGraph agent without thinking
                        print("⚠️  Falling back to LangGraph agent (no thinking)")
                        async for chunk in agent_app.astream(inputs_for_context, config=config_state):
                            chunk_count += 1
                            print(f"📦 LangGraph chunk {chunk_count}: {list(chunk.keys())}")
                            
                            for node_name, node_output in chunk.items():
                                if isinstance(node_output, dict) and "messages" in node_output:
                                    messages = node_output["messages"]
                                    
                                    for msg in messages:
                                        if isinstance(msg, AIMessage):
                                            content_str = ""
                                            if isinstance(msg.content, list):
                                                for part in msg.content:
                                                    if isinstance(part, dict) and 'text' in part:
                                                        content_str += part['text']
                                                    elif hasattr(part, 'text'):
                                                        content_str += part.text
                                                    elif isinstance(part, str):
                                                        content_str += part
                                            else:
                                                content_str = msg.content or ""
                                            
                                            # Check for tool calls
                                            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                                                for tc in msg.tool_calls:
                                                    tname = tc.get("name")
                                                    if tname and tname not in tool_calls_list:
                                                        tool_calls_list.append(tname)
                                            
                                            # Send content
                                            if content_str:
                                                await websocket.send_json({
                                                    "type": "answer",
                                                    "content": content_str
                                                })
                                                answer_content += content_str
                    
                    print(f"✅ Stream finished:")
                    print(f"   Total chunks: {chunk_count}")
                    print(f"   Thinking chunks: {thinking_chunk_count}")
                    print(f"   Answer chunks: {answer_chunk_count}")
                    print(f"   Thinking length: {len(thinking_content)}")
                    print(f"   Answer length: {len(answer_content)}")
                    print(f"   Tool calls: {tool_calls_list}")
                    
                    
                    if chunk_count == 0:
                        print("⚠️ WARNING: Agent stream produced ZERO chunks!")
                        await websocket.send_json({
                            "type": "error",
                            "error": "Agent produced no response. Please try again."
                        })
                        continue
                    
                    if not answer_content:
                        print("⚠️ WARNING: Agent stream produced chunks but NO content!")
                        await websocket.send_json({
                            "type": "error",
                            "error": "Agent produced no content. Please try again."
                        })
                        continue
                    
                    # Send completion
                    await websocket.send_json({
                        "type": "done",
                        "thread_id": current_thread_id,
                        "tool_calls": tool_calls_list
                    })
                    
                    # Log to database
                    log_user = ConversationLog(
                        user_id=current_user.id,
                        thread_id=current_thread_id,
                        role="user",
                        content=user_message,
                        mode=mode
                    )
                    session.add(log_user)
                    
                    log_ai = ConversationLog(
                        user_id=current_user.id,
                        thread_id=current_thread_id,
                        role="assistant",
                        content=answer_content,
                        mode=mode,
                        tool_calls=tool_calls_list
                    )
                    session.add(log_ai)
                    session.commit()
                    
                except Exception as e:
                    print(f"❌ Error during agent streaming: {e}")
                    import traceback
                    traceback.print_exc()
                    await websocket.send_json({
                        "type": "error",
                        "error": str(e)
                    })
                    
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "error": "Invalid JSON"})
            except Exception as e:
                print(f"Error processing message: {e}")
                await websocket.send_json({"type": "error", "error": str(e)})
                
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for user {current_user.email if 'current_user' in locals() else 'unknown'}")
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
    new_user = User(email=user_data.email, password_hash=hashed_pwd)
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
    return {"email": current_user.email, "id": current_user.id}

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
    return logs
    
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
        
        # Extract response
        final_message = result["messages"][-1]
        response_text = final_message.content
        
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
        final_message = result["messages"][-1]
        response_text = final_message.content
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
