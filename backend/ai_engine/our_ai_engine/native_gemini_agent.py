"""
Native Gemini Agent using Google GenAI SDK
Implements function calling, thinking, and streaming with native Gemini APIs
"""

import os
import json
from typing import AsyncIterator, Dict, Any, List, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

try:
    from google import genai
    from google.genai import types
    HAS_NATIVE_SDK = True
    print("✅ Google GenAI SDK loaded successfully")
except ImportError as e:
    HAS_NATIVE_SDK = False
    print(f"⚠️  WARNING: Native Google GenAI SDK not available: {e}")
    print("   Run: pip install google-genai")

# Database imports for profile fetching
from sqlmodel import Session, select
from backend.database import engine
from backend.models import User, UserSecurityProfile

# Import tools
from backend.ai_engine.our_ai_engine.tools import (
    virustotal_scan, 
    greynoise_ip_check, 
    update_user_security_profile
)

load_dotenv()


@dataclass
class Message:
    """Simple message structure"""
    role: str  # 'user', 'model', 'tool'
    content: str = ""  # Empty default for tool messages
    tool_calls: Optional[List[Dict]] = None
    tool_responses: Optional[List[Dict]] = None



class NativeGeminiAgent:
    """
    Native Gemini Agent using the official Google GenAI SDK.
    Supports:
    - Native function calling
    - Thinking/reasoning with thought signatures
    - Structured outputs
    - Streaming
    """
    
    def __init__(self, model_name: str = "gemini-2.5-pro"):
        """Initialize the native Gemini agent"""
        if not HAS_NATIVE_SDK:
            raise ImportError("google-genai package is required. Run: pip install google-genai")
        
        self.model_name = model_name
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        
        # Convert LangChain tools to native function declarations
        self.function_declarations = self._convert_tools_to_declarations()
        
        print(f"✅ Native Gemini Agent initialized with {model_name}")
        print(f"   Tools available: {len(self.function_declarations)}")
    
    def _convert_tools_to_declarations(self) -> List[Dict]:
        """
        Convert LangChain tools to native Gemini function declarations.
        Manually creates declarations since LangChain tools need special handling.
        """
        from google.genai.types import Type
        
        # Manual declarations for each tool
        return [
            {
                "name": "virustotal_scan",
                "description": "Scans a URL or File Hash (MD5, SHA-1, SHA-256) using VirusTotal API. IMPORTANT: Pass the EXACT URL as provided by the user, including the full 'https://' or 'http://' prefix. Do not modify or shorten the URL.",
                "parameters": {
                    "type": Type.OBJECT,
                    "properties": {
                        "target": {
                            "type": Type.STRING,
                            "description": "The EXACT URL (including https:// or http://) or file hash to scan. Pass the URL exactly as the user provided it."
                        }
                    },
                    "required": ["target"]
                }
            },
            {
                "name": "greynoise_ip_check",
                "description": "Checks if an IP address is known for malicious activity using GreyNoise API. Provides information about scanning behavior and threats.",
                "parameters": {
                    "type": Type.OBJECT,
                    "properties": {
                        "ip": {
                            "type": Type.STRING,
                            "description": "The IP address to check"
                        }
                    },
                    "required": ["ip"]
                }
            },
            {
                "name": "update_user_security_profile",
                "description": "Updates the user's security profile with information about their technical level, common threats, and preferences.",
                "parameters": {
                    "type": Type.OBJECT,
                    "properties": {
                        "user_id": {
                            "type": Type.STRING,
                            "description": "The user's ID"
                        },
                        "technical_level": {
                            "type": Type.STRING,
                            "description": "User's technical expertise level: beginner, intermediate, or advanced"
                        }
                    },
                    "required": ["user_id"]
                }
            }
        ]
    
    def get_system_prompt(self, user_id: str, mode: str = "simple") -> str:
        """
        Fetch user profile and generate system prompt.
        Replicates the logic from the original agent.
        """
        # Fetch Profile
        profile_text = "Standard User"
        if user_id:
            with Session(engine) as session:
                try:
                    if user_id.isdigit():
                        statement = select(User).where(User.id == int(user_id))
                        user = session.exec(statement).first()
                        if user and user.profile:
                            p = user.profile
                            profile_text = f"""
                            Technical Level: {p.technical_level}
                            Common Threats: {', '.join(p.common_threats) if p.common_threats else 'None'}
                            Explanation Preference: {p.explanation_preference}
                            """
                except:
                    pass

        # Select system prompt based on mode - HARD SPLIT
        if mode == "turbo":
            return f"""You are BYTE in TURBO MODE.
You are a technical cybersecurity expert, but you are also a capable general assistant.

USER ID: {user_id}
USER PROFILE: {profile_text}

### INSTRUCTIONS:
1. **Cybersecurity Topics**: Be technical, detailed, and precise. Use standard terminology.
2. **General Topics (History, Cooking, etc.)**: Answer them competently and professionally. 
   - **CRITICAL TWIST**: After answering a general question, ALWAYS try to add a specific "Cybersecurity Angle" or risk assessment related to that topic if possible.
   - Example: If asked about "Coffee", answer what it is, then add: "Security Note: Public coffeeshops often have insecure Wi-Fi. Use a VPN."

### FORMATTING:
- **LINK FORMATTING**: Never show raw long URLs. Use `[Input](url)` for the target of a scan and `[VirusTotal](url)` for reports.
- **Style**: Professional, concise, efficient.
- **FORBIDDEN**: Do not use "simple" analogies unless requested.
- **LINE BREAKS**: After every sentence ending with a period (.), start a new line.
- **SECURITY TIPS**: When providing security tips or warnings, format them as a blockquote using `> ` prefix. Example: `> Security Tip: Always use strong passwords.`

TOOLS: virustotal_scan, greynoise_ip_check, update_user_security_profile
"""
        else:  # Simple mode (default)
            return f"""You are BYTE in SIMPLE MODE.
You are a friendly helper for non-technical Indian users. You can talk about ANYTHING (Cybersecurity OR General Life).

USER ID: {user_id}
USER PROFILE: {profile_text}

### CRITICAL INSTRUCTIONS:
1. **General Topics**: You can answer questions about cooking, movies, history, etc.
   - **THE TWIST**: Whenever you answer a general question, try to end with a fun "Byte Security Tip" related to it.
   - Example: "To make tea, boil water... Tip: Just like you don't take tea from strangers, don't take file downloads from unknown emails!"

2. **Cybersecurity Topics**: Use real-life analogies (Lock and Key, Watchman).
   - **FORBIDDEN**: Do not use complex jargon like "TCP/IP" or "Gateway" without explaining it as a "road" or "postman".

### LINK FORMATTING:
- Use **[Input](url)** (with double stars) for the address you checked.
- Use **[VirusTotal](url)** for the report.

### RESPONSE STYLE:
- Keep it simple, friendly, and relatable to Indian context (WhatsApp, UPI, Mom/Dad metaphors).
- If it's a tool result, just say if it's safe or not in 2 sentences.
- **LINE BREAKS**: After every sentence ending with a period (.), start a new line.
- **SECURITY TIPS**: When providing "Byte Security Tip" or any security advice, format it as a blockquote using `> ` prefix. Example: `> Byte Security Tip: Just like you don't take tea from strangers, don't download files from unknown emails!`
"""
    
    def _convert_to_native_contents(self, messages: List[Message]) -> List[Dict]:
        """
        Convert our Message format to native Gemini contents format.
        Handles thought signatures properly.
        """
        contents = []
        
        for msg in messages:
            if msg.role == "system":
                # System messages go as user role with system context
                contents.append({
                    "role": "user",
                    "parts": [{"text": f"SYSTEM INSTRUCTIONS:\n{msg.content}"}]
                })
            elif msg.role == "user":
                contents.append({
                    "role": "user",
                    "parts": [{"text": msg.content}]
                })
            elif msg.role == "model":
                parts = []
                if msg.content:
                    parts.append({"text": msg.content})
                if msg.tool_calls:
                    for tc in msg.tool_calls:
                        parts.append({
                            "functionCall": {
                                "name": tc["name"],
                                "args": tc["args"]
                            }
                        })
                contents.append({
                    "role": "model",
                    "parts": parts
                })
            elif msg.role == "tool":
                # Tool responses
                if msg.tool_responses:
                    parts = []
                    for tr in msg.tool_responses:
                        parts.append({
                            "functionResponse": {
                                "name": tr["name"],
                                "response": {"result": tr["response"]}
                            }
                        })
                    contents.append({
                        "role": "user",
                        "parts": parts
                    })
        
        return contents
    
    async def generate_stream(
        self,
        messages: List[Message],
        thinking_budget: int = 1024,
        include_thoughts: bool = True
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream response with thinking support using native Gemini API.
        
        Yields:
            Dict with: {"type": "thinking" | "answer" | "done", "content": str, ...}
        """
        if not HAS_NATIVE_SDK:
            raise ImportError("google-genai required for native streaming")
        
        # Convert messages to native format
        contents = self._convert_to_native_contents(messages)
        
        # Build config with thinking and tools
        config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(
                thinking_budget=thinking_budget,
                include_thoughts=include_thoughts
            ),
            tools=[types.Tool(
                function_declarations=self.function_declarations
            )]
        )
        
        try:
            # Use native streaming
            stream = self.client.models.generate_content_stream(
                model=self.model_name,
                contents=contents,
                config=config
            )
            
            for chunk in stream:
                # Process each chunk
                for part in chunk.candidates[0].content.parts:
                    if not hasattr(part, 'text'):
                        continue
                    
                    # Check if it's a thought or answer
                    if hasattr(part, 'thought') and part.thought:
                        yield {
                            "type": "thinking",
                            "content": part.text
                        }
                    else:
                        yield {
                            "type": "answer",
                            "content": part.text
                        }
            
            yield {"type": "done"}
            
        except Exception as e:
            print(f"❌ Streaming error: {e}")
            yield {
                "type": "error",
                "error": str(e)
            }
    
    async def run_agent_loop(
        self,
        messages: List[Message],
        user_id: str,
        mode: str = "simple",
        thinking_budget: int = 1024,
        max_iterations: int = 10
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Run the full agent loop with:
        - Thinking
        - Function calling
        - Streaming responses
        
        Yields events: {"type": "thinking"|"answer"|"tool_call"|"done", ...}
        """
        # Add system message
        system_prompt = self.get_system_prompt(user_id, mode)
        full_messages = [Message(role="system", content=system_prompt)] + messages
        
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            # Convert to native format
            contents = self._convert_to_native_contents(full_messages)
            
            # Build config
            config = types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(
                    thinking_budget=thinking_budget,
                    include_thoughts=True
                ),
                tools=[types.Tool(
                    function_declarations=self.function_declarations
                )]
            )
            
            # Stream the response
            full_response_parts = []
            thoughts_text = ""
            answer_text = ""
            function_calls = []
            
            try:
                print(f"📡 STREAM: Starting Gemini stream...")
                stream = self.client.models.generate_content_stream(
                    model=self.model_name,
                    contents=contents,
                    config=config
                )
                
                chunk_count = 0
                for chunk in stream:
                    chunk_count += 1
                    print(f"📡 STREAM: Received chunk #{chunk_count}")
                    
                    for part in chunk.candidates[0].content.parts:
                        full_response_parts.append(part)
                        
                        # Handle thinking
                        if hasattr(part, 'thought') and part.thought and hasattr(part, 'text'):
                            thoughts_text += part.text
                            print(f"🧠 THINKING: Chunk length={len(part.text)}, total={len(thoughts_text)}")
                            yield {
                                "type": "thinking",
                                "content": part.text
                            }
                            print(f"🧠 THINKING: Yielded to WebSocket")
                        # Handle function calls
                        elif hasattr(part, 'function_call') and part.function_call:
                            fc = part.function_call
                            fc_name = fc.name if hasattr(fc, 'name') else str(fc.get('name', 'unknown'))
                            fc_args = dict(fc.args) if hasattr(fc, 'args') else fc.get('args', {})
                            
                            print(f"🔧 TOOL_CALL: {fc_name} with args {fc_args}")
                            function_calls.append({
                                "name": fc_name,
                                "args": fc_args
                            })
                            yield {
                                "type": "tool_call",
                                "tool_name": fc_name,
                                "tool_args": fc_args
                            }
                            print(f"🔧 TOOL_CALL: Yielded to WebSocket")
                        # Handle regular text
                        elif hasattr(part, 'text') and not (hasattr(part, 'thought') and part.thought):
                            answer_text += part.text
                            print(f"📝 ANSWER: Chunk length={len(part.text)}, total={len(answer_text)}")
                            yield {
                                "type": "answer",
                                "content": part.text
                            }
                            print(f"📝 ANSWER: Yielded to WebSocket")
                
                print(f"📡 STREAM: Completed. Total chunks={chunk_count}, thinking={len(thoughts_text)}, answer={len(answer_text)}")
                
                # If function calls were made, execute them
                if function_calls:
                    print(f"🔧 TOOLS: Executing {len(function_calls)} tool calls...")
                    # Execute tools
                    tool_responses = []
                    for fc in function_calls:
                        print(f"🔧 TOOLS: Executing {fc['name']}...")
                        result = await self._execute_tool(fc["name"], fc["args"])
                        print(f"🔧 TOOLS: Result from {fc['name']}: {str(result)[:100]}...")
                        tool_responses.append({
                            "name": fc["name"],
                            "response": result
                        })
                        
                        yield {
                            "type": "tool_result",
                            "tool_name": fc["name"],
                            "content": result
                        }
                        print(f"🔧 TOOLS: Yielded tool_result to WebSocket")
                    
                    # Add model response and tool responses to conversation
                    full_messages.append(Message(
                        role="model",
                        content=answer_text,
                        tool_calls=function_calls
                    ))
                    full_messages.append(Message(
                        role="tool",
                        tool_responses=tool_responses
                    ))
                    
                    # Continue loop to get final answer
                    continue
                else:
                    # No more function calls - we're done
                    yield {"type": "done"}
                    break
                    
            except Exception as e:
                print(f"❌ Agent loop error: {e}")
                import traceback
                traceback.print_exc()
                yield {
                    "type": "error",
                    "error": str(e)
                }
                break
        
        if iteration >= max_iterations:
            yield {
                "type": "error",
                "error": "Max iterations reached"
            }
    
    async def _execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        """Execute a tool by name with given arguments"""
        tools_map = {
            "virustotal_scan": virustotal_scan,
            "greynoise_ip_check": greynoise_ip_check,
            "update_user_security_profile": update_user_security_profile
        }
        
        if tool_name not in tools_map:
            return {"error": f"Unknown tool: {tool_name}"}
        
        try:
            tool = tools_map[tool_name]
            # LangChain @tool decorated functions can be invoked directly
            # They expect keyword arguments
            print(f"🔧 Executing tool: {tool_name} with args: {args}")
            result = tool.invoke(args)
            print(f"✅ Tool result: {result}")
            return result
        except Exception as e:
            print(f"❌ Tool execution error ({tool_name}): {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}


# Global instance
_native_agent = None


def get_native_agent(model_name: str = "gemini-2.5-pro") -> NativeGeminiAgent:
    """Get or create the global native agent instance"""
    global _native_agent
    if _native_agent is None:
        _native_agent = NativeGeminiAgent(model_name=model_name)
    return _native_agent
