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
    whoisxml_lookup,
    cybersecurity_knowledge_search,
    fake_news_analyze,
    detoxify_analyze,
    image_search,
    image_gen,
)

load_dotenv()


@dataclass
class Message:
    """Simple message structure with optional image support"""
    role: str  # 'user', 'model', 'tool'
    content: str = ""  # Empty default for tool messages
    tool_calls: Optional[List[Dict]] = None
    tool_responses: Optional[List[Dict]] = None
    image_data: Optional[str] = None  # Base64 encoded image
    image_mime_type: Optional[str] = None  # e.g., 'image/jpeg', 'image/png'



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
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
             # Fallback to secondary env var if primary is missing
             self.api_key = os.getenv("GEMINI_API_KEY")
             
        self.client = genai.Client(api_key=self.api_key)
        
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
                "name": "whoisxml_lookup",
                "description": "Looks up WHOIS information for a domain using WhoisXML API. Provides registrar, creation date, expiration date, and registrant information.",
                "parameters": {
                    "type": Type.OBJECT,
                    "properties": {
                        "domain": {
                            "type": Type.STRING,
                            "description": "The domain name to lookup (e.g., example.com)"
                        }
                    },
                    "required": ["domain"]
                }
            },
            {
                "name": "cybersecurity_knowledge_search",
                "description": """Search the cybersecurity knowledge base for information about:
- Phishing, scams, and fraud detection
- Indian cyber laws (IT Act sections 43, 66, 66C, 66D)
- Cybercrime reporting in India (1930 helpline, cybercrime.gov.in, CERT-In)
- UPI/payment fraud prevention and recovery
- Incident response procedures
- Cyber hygiene best practices
- Mental health support for cybercrime victims
- OWASP Top 10, NIST framework, CERT guidelines

ALWAYS use this tool when users ask about:
- How to report cybercrime in India
- What to do if hacked, scammed, or account compromised
- Indian cyber laws and penalties
- Security best practices and cyber hygiene
- Recognizing phishing, scams, or fraudulent messages
- UPI fraud, fake apps, or payment scams
- Helpline numbers and support resources""",
                "parameters": {
                    "type": Type.OBJECT,
                    "properties": {
                        "query": {
                            "type": Type.STRING,
                            "description": "The search query to find relevant cybersecurity information"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "fake_news_analyze",
                "description": """Analyze NEWS ARTICLES or HEADLINES for fake news indicators. Use this tool ONLY when users:
- Explicitly share a NEWS article or headline to verify
- Ask "is this news true?" or "is this fake?"
- Share content that is clearly NEWS-related (not regular requests)
- Ask to fact-check a specific news story

DO NOT use this tool for:
- Image generation requests
- General questions
- Cybersecurity queries
- Any request ending with "-gen"

Returns veracity (Fake/Real/Uncertain), confidence score, and analysis.""",
                "parameters": {
                    "type": Type.OBJECT,
                    "properties": {
                        "text": {
                            "type": Type.STRING,
                            "description": "The news text, article, headline, or social media post to analyze"
                        }
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "detoxify_analyze",
                "description": """Analyze text content for toxicity, threats, obscenity, insults, and identity-based hate speech. Use this tool when users:
- Want to check if content is toxic or offensive
- Ask if a comment violates community guidelines
- Share text that might contain hate speech
- Want to moderate or review user-generated content
- Ask about cyberbullying or harassment
- Need to assess online safety of content

Detects: toxicity, severe toxicity, obscene content, threats, insults, and identity-based attacks (hate speech).
Returns toxicity scores (0-100%) for each category and overall risk assessment.""",
                "parameters": {
                    "type": Type.OBJECT,
                    "properties": {
                        "text": {
                            "type": Type.STRING,
                            "description": "The text content to analyze for toxicity (comments, messages, posts, etc.)"
                        }
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "image_search",
                "description": """Search for relevant images to illustrate ANY concept or term. Use this tool AUTOMATICALLY when users ask definitional questions like:
- "What is phishing?"
- "What is iOS?"
- "Explain machine learning"
- "What is an iPhone?"
- "Define cloud computing"
- "What is Python programming?"
- "Explain blockchain"

Returns image URLs with thumbnails to display alongside your explanation. This helps users visualize concepts.

IMPORTANT: Call this tool automatically for ANY definitional question (what is X, explain X, define X) to enhance the response with visual aids. This works for ALL topics, not just cybersecurity.""",
                "parameters": {
                    "type": Type.OBJECT,
                    "properties": {
                        "query": {
                            "type": Type.STRING,
                            "description": "The term or concept to search images for (e.g., 'phishing', 'iOS device', 'machine learning')"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "image_gen",
                "description": """Generate an image using AI based on a text prompt. Use this tool when users end their message with '-gen' suffix.

Examples:
- "a cute cat -gen" → Generate image of a cute cat
- "cybersecurity shield logo -gen" → Generate a cybersecurity logo
- "sunset over mountains -gen" → Generate landscape image
- "phishing attack illustration -gen" → Generate educational image

IMPORTANT: Only use this tool when the user explicitly includes '-gen' at the end of their message.
The generated image will be displayed automatically by the frontend.""",
                "parameters": {
                    "type": Type.OBJECT,
                    "properties": {
                        "prompt": {
                            "type": Type.STRING,
                            "description": "The description of the image to generate (without -gen suffix)"
                        }
                    },
                    "required": ["prompt"]
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

### FORMATTING (VERY IMPORTANT):
- **BULLET POINTS**: ALWAYS use bullet points (- or •) for listing information. Never write long paragraphs.
- **STRUCTURE**: Break your response into clear sections with bullet points under each.
- **LINK FORMATTING**: Never show raw long URLs. Use `[Input](url)` for the target of a scan and `[VirusTotal](url)` for reports.
- **Style**: Professional, concise, efficient.
- **FORBIDDEN**: Do not use "simple" analogies unless requested.
- **LINE BREAKS**: After every sentence ending with a period (.), start a new line.
- **SECURITY TIPS**: When providing security tips or warnings, format them as a blockquote using `> ` prefix.
- **NO HTML**: NEVER output raw HTML tags like <img>, <br>, <center>, etc. Use Markdown only. For images, use the image_search tool - the frontend will display them automatically.

### RESPONSE STRUCTURE EXAMPLE:
**Summary**: One line summary

**Key Points**:
- Point 1
- Point 2
- Point 3

**Action Steps**:
- Step 1
- Step 2

> Security Tip: Your tip here

TOOLS: virustotal_scan, whoisxml_lookup, cybersecurity_knowledge_search, image_search

### MANDATORY IMAGE SEARCH:
**You MUST call the `image_search` tool for ANY definitional question**:
- "What is X?" → call image_search with X
- "Define X" → call image_search with X  
- "Explain X" → call image_search with X
- Examples: "What is phishing?", "Define proxy", "What is iOS?", "Explain VPN"
- The frontend will display the images automatically. DO NOT try to embed images yourself.

### KNOWLEDGE BASE USAGE:
- Use `cybersecurity_knowledge_search` tool for questions about Indian cyber laws, reporting procedures, helplines, or best practices.
- The knowledge base contains India-specific information about IT Act, 1930 helpline, cybercrime.gov.in, UPI fraud, etc.
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

### RESPONSE FORMATTING (VERY IMPORTANT):
- **BULLET POINTS**: ALWAYS use bullet points (- or •) for listing information. NEVER write long paragraphs.
- **STRUCTURE**: Break your response into clear sections with bullet points.
- **SHORT SENTENCES**: Keep each point short and easy to read.
- Keep it simple, friendly, and relatable to Indian context (WhatsApp, UPI, Mom/Dad metaphors).
- If it's a tool result, just say if it's safe or not in 2 sentences.
- **LINE BREAKS**: After every sentence ending with a period (.), start a new line.
- **SECURITY TIPS**: Format as blockquote using `> ` prefix.
- **NO HTML**: NEVER output raw HTML tags like <img>, <br>, <center>, etc. Use Markdown only. For images, use the image_search tool - the frontend will display them automatically.

### RESPONSE STRUCTURE EXAMPLE:
I understand you're facing [issue]. Here's what you can do:

**Immediate Steps**:
- Step 1: Do this first
- Step 2: Then do this
- Step 3: Finally do this

**Helpful Resources**:
- Resource 1: Description
- Resource 2: Description

> Byte Security Tip: Your friendly tip here

### TOOLS AVAILABLE:
- `virustotal_scan`: Check if a URL or file is safe
- `whoisxml_lookup`: Look up domain information
- `cybersecurity_knowledge_search`: Search knowledge base for Indian cyber laws, helplines (1930), reporting procedures, best practices
- `image_search`: Search for images to illustrate concepts (MANDATORY for "What is X", "Define X", "Explain X" questions)

### MANDATORY IMAGE SEARCH:
**You MUST call the `image_search` tool for ANY definitional question**:
- "What is X?" → call image_search with X
- "Define X" → call image_search with X  
- "Explain X" → call image_search with X
- Examples: "What is phishing?", "Define proxy", "What is iOS?", "Explain VPN"
- The frontend will display the images automatically. DO NOT try to embed images yourself.

### KNOWLEDGE BASE USAGE:
- Use `cybersecurity_knowledge_search` when users ask about:
  - How to report cybercrime in India
  - What to do if scammed or hacked
  - Indian cyber laws and IT Act
  - UPI fraud, fake apps, payment scams
  - Helpline numbers and support
"""
    
    def _convert_to_native_contents(self, messages: List[Message]) -> List[Dict]:
        """
        Convert our Message format to native Gemini contents format.
        Handles thought signatures properly.
        Truncates large content to prevent token overflow.
        """
        contents = []
        MAX_CONTENT_LENGTH = 4000  # Max chars per message to prevent token overflow
        
        for msg in messages:
            if msg.role == "system":
                # System messages go as user role with system context
                content = msg.content[:MAX_CONTENT_LENGTH] if msg.content and len(msg.content) > MAX_CONTENT_LENGTH else msg.content
                contents.append({
                    "role": "user",
                    "parts": [{"text": f"SYSTEM INSTRUCTIONS:\n{content}"}]
                })
            elif msg.role == "user":
                parts = []
                # Add text if present (truncate if too long)
                if msg.content:
                    text = msg.content[:MAX_CONTENT_LENGTH] if len(msg.content) > MAX_CONTENT_LENGTH else msg.content
                    parts.append({"text": text})
                # Add image if present (skip images in history to save tokens)
                if msg.image_data and msg.image_mime_type and len(contents) < 3:
                    # Only include images for recent messages (first 3)
                    parts.append({
                        "inline_data": {
                            "mime_type": msg.image_mime_type,
                            "data": msg.image_data
                        }
                    })
                contents.append({
                    "role": "user",
                    "parts": parts if parts else [{"text": ""}]
                })
            elif msg.role == "model":
                parts = []
                if msg.content:
                    # Truncate model responses
                    text = msg.content[:MAX_CONTENT_LENGTH] if len(msg.content) > MAX_CONTENT_LENGTH else msg.content
                    parts.append({"text": text})
                if msg.tool_calls and isinstance(msg.tool_calls, list):
                    for tc in msg.tool_calls:
                        parts.append({
                            "functionCall": {
                                "name": tc["name"],
                                "args": tc.get("args", {}) or {}
                            }
                        })
                # Only add if we have parts
                if parts:
                    contents.append({
                        "role": "model",
                        "parts": parts
                    })
            elif msg.role == "tool":
                # Tool responses - truncate large responses
                if msg.tool_responses and isinstance(msg.tool_responses, list):
                    parts = []
                    for tr in msg.tool_responses:
                        response_str = str(tr["response"])
                        # Truncate very large tool responses (like base64 images)
                        if len(response_str) > 5000:
                            response_str = response_str[:5000] + "...[truncated]"
                        parts.append({
                            "functionResponse": {
                                "name": tr["name"],
                                "response": {"content": response_str}
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
            stream = await self.client.aio.models.generate_content_stream(
                model=self.model_name,
                contents=contents,
                config=config
            )
            
            async for chunk in stream:
                # Process each chunk
                if not chunk.candidates:
                    continue
                for part in chunk.candidates[0].content.parts:
                    # Check if it's a thought or answer
                    is_thought = getattr(part, 'thought', False) or (hasattr(part, 'thought') and part.thought)
                    
                    if is_thought and hasattr(part, 'text') and part.text:
                        yield {
                            "type": "thinking",
                            "content": part.text
                        }
                    elif hasattr(part, 'text') and part.text:
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
        thinking_budget: int = -1,
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
                print(f"📡 STREAM: Starting Gemini stream (async)...")
                stream = await self.client.aio.models.generate_content_stream(
                    model=self.model_name,
                    contents=contents,
                    config=config
                )
                
                chunk_count = 0
                async for chunk in stream:
                    chunk_count += 1
                    # print(f"📡 STREAM: Received chunk #{chunk_count}") -- Reducing noise
                    
                    if not chunk.candidates:
                        continue
                    
                    # Safe access to content.parts - may be None
                    candidate = chunk.candidates[0]
                    if not candidate.content or not candidate.content.parts:
                        continue
                        
                    for part in candidate.content.parts:
                        full_response_parts.append(part)
                        
                        # Handle thinking
                        # Robust check for thought attribute
                        is_thought = getattr(part, 'thought', False) or (hasattr(part, 'thought') and part.thought)
                        
                        if is_thought and hasattr(part, 'text') and part.text:
                            thoughts_text += part.text
                            # print(f"🧠 THINKING: Chunk length={len(part.text)}, total={len(thoughts_text)}")
                            yield {
                                "type": "thinking",
                                "content": part.text
                            }
                        # Handle function calls
                        elif hasattr(part, 'function_call') and part.function_call:
                            fc = part.function_call
                            fc_name = fc.name if hasattr(fc, 'name') else str(getattr(fc, 'name', 'unknown'))
                            
                            # Safe argument parsing to avoid NoneType iteration error
                            raw_args = getattr(fc, 'args', None)
                            if raw_args is not None:
                                try:
                                    fc_args = dict(raw_args)
                                except (TypeError, ValueError):
                                    fc_args = {}
                            else:
                                fc_args = {}
                            
                            print(f"🔧 TOOL_CALL detected: {fc_name}")
                            function_calls.append({
                                "name": fc_name,
                                "args": fc_args
                            })
                            yield {
                                "type": "tool_call",
                                "tool_name": fc_name,
                                "tool_args": fc_args
                            }
                        # Handle regular text
                        elif hasattr(part, 'text') and part.text:
                            # Verify NOT a thought (some SDK versions might have both)
                            if not is_thought:
                                answer_text += part.text
                                yield {
                                    "type": "answer",
                                    "content": part.text
                                }
                
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
            "whoisxml_lookup": whoisxml_lookup,
            "cybersecurity_knowledge_search": cybersecurity_knowledge_search,
            "fake_news_analyze": fake_news_analyze,
            "detoxify_analyze": detoxify_analyze,
            "image_search": image_search,
            "image_gen": image_gen,
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
