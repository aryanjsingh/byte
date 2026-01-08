# Gemini 2.5 Pro + FastAPI: Thinking + Streaming + Context Guide

**Last Updated:** January 2026  
**Models:** Gemini 2.5 Pro (primary), Gemini 2.5 Flash (alt)  
**Features:** Thinking mode, streaming, context history, error handling

---

## Quick Reference

| Aspect | Value |
|--------|-------|
| **Model** | `gemini-2.5-pro` |
| **Thinking Budget** | `8192` (default, range: 128-32768) |
| **Dynamic Thinking** | Set budget to `-1` |
| **Disable Thinking** | Cannot disable on Pro (use Flash if needed) |
| **Streaming** | Yes, via `generate_content_stream()` |
| **Context** | Full message history sent each request |
| **API Latency** | ~2-5s with thinking (vs 200ms without) |

---

## Architecture

```
FastAPI Backend
├── POST /api/chat              (streaming endpoint)
├── GET /api/chat/history       (fetch context)
└── POST /api/chat/clear        (reset conversation)
        ↓
    Gemini 2.5 Pro (with thinking)
        ↓
Client (Next.js / React Native)
├── SSE stream receiver
├── Thinking panel display
└── Incremental UI update
```

---

## Setup

### 1. Install Dependencies

```bash
pip install fastapi uvicorn google-generativeai python-dotenv pydantic
```

### 2. Environment Variables

Create `.env`:

```
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.5-pro
THINKING_BUDGET=8192
```

### 3. Core Configuration

Create `config.py`:

```python
import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")
THINKING_BUDGET = int(os.getenv("THINKING_BUDGET", "8192"))

# Thinking config options
THINKING_CONFIGS = {
    "max_reasoning": {
        "budget": 24576,  # Max allowed for 2.5 Pro
        "description": "Maximum reasoning (slowest, best quality)"
    },
    "balanced": {
        "budget": 8192,   # Default
        "description": "Balanced reasoning & speed"
    },
    "minimal": {
        "budget": 128,    # Minimum
        "description": "Minimal reasoning (fastest)"
    },
    "dynamic": {
        "budget": -1,     # Model decides
        "description": "Dynamic thinking (model chooses budget)"
    }
}
```

---

## Backend Implementation

### 1. Main FastAPI App

Create `main.py`:

```python
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
from typing import List, Optional
import google.generativeai as genai
from pydantic import BaseModel

from config import GEMINI_API_KEY, GEMINI_MODEL, THINKING_BUDGET, THINKING_CONFIGS

# Configure API
genai.configure(api_key=GEMINI_API_KEY)

# FastAPI app
app = FastAPI(title="Gemini Thinking Chat API")

# CORS middleware (adjust origins for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Your domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Data Models
# ============================================================================

class Message(BaseModel):
    role: str  # "user" or "model"
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    thinking_level: Optional[str] = "balanced"  # "max_reasoning", "balanced", "minimal", "dynamic"
    system_prompt: Optional[str] = None

class ChatResponse(BaseModel):
    thinking: str
    answer: str
    stop_reason: str

# ============================================================================
# In-Memory Context Storage (use Redis/DB for production)
# ============================================================================

# Store conversation histories per client/session
conversation_histories = {}

def get_conversation_history(session_id: str) -> List[Message]:
    """Retrieve conversation history for a session."""
    return conversation_histories.get(session_id, [])

def save_conversation_history(session_id: str, messages: List[Message]):
    """Save conversation history for a session."""
    conversation_histories[session_id] = messages

def clear_conversation_history(session_id: str):
    """Clear conversation history for a session."""
    if session_id in conversation_histories:
        del conversation_histories[session_id]

# ============================================================================
# Streaming Endpoint
# ============================================================================

async def stream_chat_response(
    messages: List[Message],
    thinking_level: str = "balanced",
    system_prompt: Optional[str] = None
):
    """
    Stream chat response from Gemini 2.5 Pro with thinking.
    
    Yields JSON-formatted chunks:
    - {"type": "thinking", "content": "..."}
    - {"type": "answer", "content": "..."}
    - {"type": "done", "stop_reason": "..."}
    """
    
    # Get thinking budget config
    thinking_config = THINKING_CONFIGS.get(thinking_level, THINKING_CONFIGS["balanced"])
    budget = thinking_config["budget"]
    
    # Build message history for API
    api_messages = []
    for msg in messages:
        api_messages.append({
            "role": msg.role,
            "parts": [{"text": msg.content}]
        })
    
    # System prompt (optional context awareness)
    system_instruction = system_prompt or (
        "You are a helpful assistant. "
        "Think step-by-step before answering complex questions. "
        "Maintain context from the conversation history."
    )
    
    try:
        # Create model instance
        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            system_instruction=system_instruction,
        )
        
        # Stream with thinking enabled
        response_stream = model.generate_content(
            contents=api_messages,
            stream=True,
            generation_config={
                "temperature": 1,  # Required for thinking mode
                "top_p": 0.95,
                "top_k": 40,
            },
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            ],
            # CRITICAL: Thinking configuration
            thinking_config={
                "budget_tokens": budget,  # Tokens for thinking phase
                "include_thoughts": True,  # Expose thoughts in response
            }
        )
        
        # Variables to accumulate content
        current_thinking = ""
        current_answer = ""
        
        # Stream chunks
        async for chunk in response_stream:
            # Iterate through content parts
            if chunk.candidates and len(chunk.candidates) > 0:
                candidate = chunk.candidates[0]
                
                for part in candidate.content.parts:
                    # Check if this is a thinking part
                    if hasattr(part, 'thought') and part.thought:
                        # Thinking content
                        if hasattr(part, 'text'):
                            current_thinking += part.text
                            # Yield thinking chunk
                            yield json.dumps({
                                "type": "thinking",
                                "content": part.text,
                            }) + "\n"
                    else:
                        # Regular answer content
                        if hasattr(part, 'text') and part.text:
                            current_answer += part.text
                            # Yield answer chunk
                            yield json.dumps({
                                "type": "answer",
                                "content": part.text,
                            }) + "\n"
            
            # Allow async context switching
            await asyncio.sleep(0)
        
        # Yield completion signal
        yield json.dumps({
            "type": "done",
            "stop_reason": chunk.candidates[0].finish_reason if chunk.candidates else "STOP",
        }) + "\n"
        
    except Exception as e:
        # Error handling
        yield json.dumps({
            "type": "error",
            "error": str(e),
        }) + "\n"

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Stream chat response with thinking.
    
    Request body:
    {
        "messages": [
            {"role": "user", "content": "..."},
            {"role": "model", "content": "..."}
        ],
        "thinking_level": "balanced",
        "system_prompt": "Custom system instruction (optional)"
    }
    
    Response: Server-Sent Events (SSE) stream of JSON objects
    """
    
    # Validate
    if not request.messages:
        raise HTTPException(status_code=400, detail="Messages required")
    
    # Stream response
    return StreamingResponse(
        stream_chat_response(
            messages=request.messages,
            thinking_level=request.thinking_level or "balanced",
            system_prompt=request.system_prompt,
        ),
        media_type="application/x-ndjson",
    )

# ============================================================================
# Non-Streaming Endpoint (if needed)
# ============================================================================

@app.post("/api/chat/sync")
async def chat_sync(request: ChatRequest):
    """
    Non-streaming chat endpoint (returns full response at once).
    Use this for simple queries that don't need streaming.
    """
    
    if not request.messages:
        raise HTTPException(status_code=400, detail="Messages required")
    
    thinking_config = THINKING_CONFIGS.get(request.thinking_level or "balanced", THINKING_CONFIGS["balanced"])
    budget = thinking_config["budget"]
    
    # Build message history
    api_messages = []
    for msg in request.messages:
        api_messages.append({
            "role": msg.role,
            "parts": [{"text": msg.content}]
        })
    
    try:
        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            system_instruction=request.system_prompt or "You are a helpful assistant.",
        )
        
        response = model.generate_content(
            contents=api_messages,
            generation_config={"temperature": 1, "top_p": 0.95, "top_k": 40},
            thinking_config={"budget_tokens": budget, "include_thoughts": True},
        )
        
        # Parse thinking and answer from response
        thinking_text = ""
        answer_text = ""
        
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'thought') and part.thought:
                thinking_text += part.text
            else:
                answer_text += part.text
        
        return ChatResponse(
            thinking=thinking_text,
            answer=answer_text,
            stop_reason=str(response.candidates[0].finish_reason),
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Context Management Endpoints
# ============================================================================

@app.get("/api/chat/history/{session_id}")
async def get_history(session_id: str):
    """Fetch conversation history for a session."""
    history = get_conversation_history(session_id)
    return {"session_id": session_id, "messages": history}

@app.post("/api/chat/clear/{session_id}")
async def clear_history(session_id: str):
    """Clear conversation history for a session."""
    clear_conversation_history(session_id)
    return {"status": "cleared", "session_id": session_id}

@app.get("/api/thinking-configs")
async def get_thinking_configs():
    """Get available thinking level configurations."""
    return THINKING_CONFIGS

# ============================================================================
# Health Check
# ============================================================================

@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "model": GEMINI_MODEL,
        "thinking_budget_default": THINKING_BUDGET,
    }

# ============================================================================
# Run Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## Thinking Configuration Details

### Budget Tokens Explained

For **Gemini 2.5 Pro**:

```python
# Minimum reasoning
thinking_config={"budget_tokens": 128}
# → Fast, minimal thinking
# → ~1-2 seconds

# Default (recommended)
thinking_config={"budget_tokens": 8192}
# → Balanced speed/quality
# → ~3-5 seconds

# Maximum reasoning
thinking_config={"budget_tokens": 24576}
# → Deep reasoning on complex tasks
# → ~8-15 seconds

# Dynamic (model decides)
thinking_config={"budget_tokens": -1}
# → Model auto-selects budget
# → Caps at 8,192 tokens
# → Good for general use
```

### When to Use Each

```python
# Simple questions (factual answers)
thinking_budget = 128
# "What's the capital of France?"

# Balanced (default for most cases)
thinking_budget = 8192
# "Explain how RLHF works"
# "Debug this code error"

# Complex reasoning (math, strategy)
thinking_budget = 16384 or 24576
# "Solve this complex optimization problem"
# "Design a multi-step system architecture"

# Let model decide
thinking_budget = -1
# General assistant (handles varied questions)
```

---

## Frontend Integration (Next.js Example)

### 1. Hook for Streaming Chat

Create `hooks/useGeminiChat.ts`:

```typescript
import { useEffect, useRef, useState } from "react";

interface StreamChunk {
  type: "thinking" | "answer" | "done" | "error";
  content?: string;
  stop_reason?: string;
  error?: string;
}

export function useGeminiChat() {
  const [messages, setMessages] = useState<any[]>([]);
  const [thinking, setThinking] = useState("");
  const [answer, setAnswer] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const sendMessage = async (
    userMessage: string,
    thinkingLevel: string = "balanced"
  ) => {
    setIsLoading(true);
    setThinking("");
    setAnswer("");
    setError("");

    try {
      // Build message history
      const chatMessages = [
        ...messages,
        { role: "user", content: userMessage },
      ];

      // Call streaming endpoint
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: chatMessages,
          thinking_level: thinkingLevel,
        }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
      }

      // Read streaming response
      const reader = response.body?.getReader();
      if (!reader) throw new Error("No response body");

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");

        // Process complete lines
        for (let i = 0; i < lines.length - 1; i++) {
          const line = lines[i].trim();
          if (!line) continue;

          try {
            const chunk: StreamChunk = JSON.parse(line);

            if (chunk.type === "thinking") {
              setThinking((prev) => prev + (chunk.content || ""));
            } else if (chunk.type === "answer") {
              setAnswer((prev) => prev + (chunk.content || ""));
            } else if (chunk.type === "done") {
              // Update message history
              setMessages((prev) => [
                ...prev,
                { role: "user", content: userMessage },
                {
                  role: "model",
                  content: answer + chunk.content || "",
                },
              ]);
            } else if (chunk.type === "error") {
              setError(chunk.error || "Unknown error");
            }
          } catch (e) {
            console.error("Parse error:", e);
          }
        }

        // Keep incomplete line in buffer
        buffer = lines[lines.length - 1];
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setIsLoading(false);
    }
  };

  return {
    messages,
    thinking,
    answer,
    isLoading,
    error,
    sendMessage,
  };
}
```

### 2. Chat Component

```typescript
"use client";

import { useGeminiChat } from "@/hooks/useGeminiChat";
import { useState } from "react";

export default function ChatPage() {
  const { messages, thinking, answer, isLoading, sendMessage } =
    useGeminiChat();
  const [input, setInput] = useState("");
  const [thinkingLevel, setThinkingLevel] = useState("balanced");
  const [showThinking, setShowThinking] = useState(false);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const message = input;
    setInput("");
    await sendMessage(message, thinkingLevel);
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <div className="bg-white border-b shadow-sm p-4">
        <h1 className="text-2xl font-bold text-slate-800">
          Gemini 2.5 Pro Chat
        </h1>
        <p className="text-sm text-slate-600">Thinking mode enabled</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-2xl px-4 py-3 rounded-lg ${
                msg.role === "user"
                  ? "bg-blue-600 text-white"
                  : "bg-white text-slate-800 border border-slate-200 shadow"
              }`}
            >
              <p className="text-sm">{msg.content}</p>
            </div>
          </div>
        ))}

        {/* Current thinking */}
        {thinking && (
          <div className="flex justify-start">
            <div className="max-w-2xl px-4 py-3 rounded-lg bg-amber-50 border border-amber-200">
              <button
                onClick={() => setShowThinking(!showThinking)}
                className="text-sm font-medium text-amber-900 hover:text-amber-700"
              >
                {showThinking ? "▼" : "▶"} Thinking ({thinking.length} chars)
              </button>
              {showThinking && (
                <pre className="mt-2 text-xs text-amber-700 max-h-48 overflow-y-auto whitespace-pre-wrap">
                  {thinking}
                </pre>
              )}
            </div>
          </div>
        )}

        {/* Current answer */}
        {answer && (
          <div className="flex justify-start">
            <div className="max-w-2xl px-4 py-3 rounded-lg bg-green-50 border border-green-200">
              <p className="text-sm text-slate-800">{answer}</p>
            </div>
          </div>
        )}

        {isLoading && (
          <div className="flex justify-start">
            <div className="text-sm text-slate-500">Generating response...</div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="bg-white border-t p-4 shadow-lg">
        <form onSubmit={handleSend} className="space-y-3">
          {/* Thinking level selector */}
          <div className="flex gap-2">
            {["minimal", "balanced", "max_reasoning", "dynamic"].map(
              (level) => (
                <button
                  key={level}
                  type="button"
                  onClick={() => setThinkingLevel(level)}
                  className={`px-3 py-1 text-xs rounded-full font-medium transition ${
                    thinkingLevel === level
                      ? "bg-blue-600 text-white"
                      : "bg-slate-200 text-slate-700 hover:bg-slate-300"
                  }`}
                >
                  {level}
                </button>
              )
            )}
          </div>

          {/* Input field */}
          <div className="flex gap-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask anything..."
              disabled={isLoading}
              className="flex-1 px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              type="submit"
              disabled={isLoading}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-400 text-white rounded-lg font-medium transition"
            >
              Send
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
```

---

## Production Checklist

### Backend

- [ ] Use PostgreSQL/Redis for context persistence (not in-memory)
- [ ] Add authentication (JWT, API keys)
- [ ] Implement rate limiting (per user/session)
- [ ] Add request validation (sanitize inputs)
- [ ] Use proper error logging (Sentry, LogRocket)
- [ ] Set `max_tokens` to prevent runaway costs
- [ ] Monitor API usage/costs
- [ ] Add retry logic with exponential backoff
- [ ] Use environment-specific configs

### Frontend

- [ ] Add session/user ID to identify conversations
- [ ] Implement message persistence
- [ ] Add UI feedback for streaming states
- [ ] Handle network disconnections gracefully
- [ ] Show thinking time estimates
- [ ] Add analytics for thinking level usage
- [ ] Implement dark mode
- [ ] Test on real devices (mobile)

---

## Troubleshooting

### Issue: Thinking not appearing

```python
# ❌ Wrong - thinking disabled
thinking_config={"budget_tokens": 0}  # Only for Flash

# ✅ Correct - 2.5 Pro always thinks
thinking_config={"budget_tokens": 8192, "include_thoughts": True}
```

### Issue: Slow responses

```python
# Use minimal thinking for simple queries
if is_simple_query:
    budget = 128  # ~1-2 seconds
else:
    budget = 8192  # ~3-5 seconds
```

### Issue: Streaming stops midway

```python
# Add timeout and error handling
import asyncio
try:
    async for chunk in response_stream:
        # Process chunk
        await asyncio.sleep(0)  # Prevent blocking
except asyncio.TimeoutError:
    yield json.dumps({"type": "error", "error": "Request timeout"}) + "\n"
```

### Issue: Cost too high

```python
# Option 1: Use Flash instead
model_name = "gemini-2.5-flash"  # ~30% cheaper

# Option 2: Disable thinking for simple queries
thinking_config={"budget_tokens": 0}  # Flash only

# Option 3: Use dynamic thinking
thinking_config={"budget_tokens": -1}  # Auto-selects
```

---

## Cost Estimation (as of Jan 2026)

| Model | Thinking | Cost (per 1M tokens) |
|-------|----------|----------------------|
| 2.5 Pro | Disabled | $3.50 |
| 2.5 Pro | 8K tokens | ~$7 |
| 2.5 Pro | 24K tokens | ~$14 |
| 2.5 Flash | Disabled | $0.075 |
| 2.5 Flash | 8K tokens | ~$0.15 |

**Optimization:** Use Flash (with thinking) for 80% of queries, Pro for complex tasks only.

---

## Quick Start Command

```bash
# 1. Install
pip install fastapi uvicorn google-generativeai python-dotenv

# 2. Create .env
echo "GEMINI_API_KEY=your_key" > .env

# 3. Run
python main.py

# 4. Test
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Explain thinking mode"}], "thinking_level": "balanced"}'
```

---

## References

- [Gemini Thinking API Docs](https://ai.google.dev/gemini-api/docs/thinking)
- [FastAPI Streaming](https://fastapi.tiangolo.com/advanced/response-streaming/)
- [Google Generative AI Python SDK](https://github.com/google/generative-ai-python)

---

**This guide covers everything you need for production-ready Gemini 2.5 Pro chat with thinking + streaming in FastAPI. Adjust thinking budgets based on your use case and cost constraints.**
