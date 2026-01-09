"""
Gemini Thinking Support Module
This module provides wrappers to enable thinking/reasoning capabilities for Gemini 2.5 Pro
using the native Google GenAI SDK alongside LangChain.
"""

import os
from typing import AsyncIterator, Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

try:
    from google import genai
    from google.genai.types import GenerateContentConfig, ThinkingConfig, Part, Content
    HAS_NATIVE_SDK = True
    print("✅ Google GenAI SDK loaded successfully")
except ImportError as e:
    HAS_NATIVE_SDK = False
    print(f"⚠️  WARNING: Native Google GenAI SDK not available: {e}")
    print("   Run: pip install google-genai")


class GeminiThinkingWrapper:
    """
    Wrapper for Gemini API with thinking support.
    Falls back to standard behavior if native SDK is unavailable.
    """
    
    def __init__(self, model_name: str = "gemini-2.5-pro"):
        self.model_name = model_name
        self.api_key = os.getenv("GOOGLE_API_KEY")
        
        if not self.api_key:
            print("⚠️  WARNING: GOOGLE_API_KEY not found in environment")
            self.client = None
            self.thinking_enabled = False
            return
        
        if HAS_NATIVE_SDK:
            try:
                self.client = genai.Client(api_key=self.api_key)
                self.thinking_enabled = True
                print(f"✅ Gemini Thinking Wrapper initialized with {model_name}")
            except Exception as e:
                print(f"❌ Failed to initialize Gemini client: {e}")
                self.client = None
                self.thinking_enabled = False
        else:
            self.client = None
            self.thinking_enabled = False
    
    async def generate_with_thinking_stream(
        self,
        messages: list,
        thinking_budget: int = -1,  # -1 for dynamic thinking
        include_thoughts: bool = True
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Generate streaming response with thinking support.
        
        Args:
            messages: List of LangChain messages
            thinking_budget: Token budget for thinking (-1 = dynamic, 128-32768 for Gemini 2.5 Pro)
            include_thoughts: Whether to include thought summaries
        
        Yields:
            Dict with 'type' ('thinking' or 'answer') and 'content'
        """
        if not self.thinking_enabled or not self.client:
            print("⚠️  Thinking not available, falling back")
            yield {
                "type": "error",
                "content": "Thinking not available with current configuration"
            }
            return
        
        # Convert messages to Gemini format
        gemini_contents = self._convert_messages(messages)
        
        print(f"🧠 Starting Gemini stream with thinking (budget={thinking_budget})")
        print(f"   Messages count: {len(gemini_contents)}")
        
        try:
            # Configure thinking
            config = GenerateContentConfig(
                thinking_config=ThinkingConfig(
                    include_thoughts=include_thoughts,
                    thinking_budget=thinking_budget
                )
            )
            
            chunk_count = 0
            thinking_chunks = 0
            answer_chunks = 0
            
            # Stream response
            response = await self.client.aio.models.generate_content_stream(
                model=self.model_name,
                contents=gemini_contents,
                config=config
            )
            
            async for chunk in response:
                chunk_count += 1
                
                # Check if chunk has candidates
                if not chunk.candidates or len(chunk.candidates) == 0:
                    print(f"⚠️  Chunk {chunk_count} has no candidates")
                    continue
                
                candidate = chunk.candidates[0]
                
                # Check if candidate has content
                if not hasattr(candidate, 'content') or not candidate.content:
                    print(f"⚠️  Chunk {chunk_count} has no content")
                    continue
                
                # Extract parts from content
                if not hasattr(candidate.content, 'parts') or not candidate.content.parts:
                    print(f"⚠️  Chunk {chunk_count} has no parts")
                    continue
                
                # Iterate through parts
                for part in candidate.content.parts:
                    # Check for text attribute
                    if not hasattr(part, 'text') or not part.text:
                        continue
                    
                    # Check if this is thinking or answer
                    if hasattr(part, 'thought') and part.thought:
                        # This is thinking content
                        thinking_chunks += 1
                        print(f"💭 Thinking chunk {thinking_chunks}: {part.text[:50]}...")
                        yield {
                            "type": "thinking",
                            "content": part.text
                        }
                    else:
                        # This is regular answer content
                        answer_chunks += 1
                        print(f"💬 Answer chunk {answer_chunks}: {part.text[:50]}...")
                        yield {
                            "type": "answer",
                            "content": part.text
                        }
            
            print(f"✅ Stream complete: {chunk_count} total chunks, {thinking_chunks} thinking, {answer_chunks} answer")
                        
        except Exception as e:
            print(f"❌ Error in thinking stream: {e}")
            import traceback
            traceback.print_exc()
            yield {
                "type": "error",
                "content": f"Thinking generation failed: {str(e)}"
            }
    
    async def run_native_agent_loop(
        self,
        messages: list,
        tools: list = None,
        thinking_budget: int = 1024,
        include_thoughts: bool = True
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Run the agent loop using native Gemini SDK.
        Handles thinking, streaming, and tool execution manually.
        """
        if not self.thinking_enabled or not self.client:
            yield {"type": "error", "content": "Native SDK not initialized"}
            return

        # 1. Convert Tools to Gemini Format
        gemini_tools = []
        genai_tools_config = None
        tool_map = {}
        
        if tools:
            # Native Tool Conversion
            from google.genai import types
            
            declarations = []
            
            for tool in tools:
                tool_map[tool.name] = tool
                
                # Try to convert using native SDK's from_callable if possible
                # This works if the tool has a valid underlying function with type hints
                try:
                    # Check for underlying function in LangChain tool
                    func = getattr(tool, "func", None)
                    if not func:
                        # Some tools wrap helpers, might be in 'function' or '_func'
                        func = getattr(tool, "function", None)
                    
                    if func and self.client:
                        # Use native conversion
                        # Note: we must ensure unique naming if multiple tools have same func name?
                        # LangChain tools have 'name' attr. from_callable uses func.__name__.
                        # We might need to rename declaration.
                        decl = types.FunctionDeclaration.from_callable(client=self.client, callable=func)
                        # Override name/description from Tool if set
                        decl.name = tool.name
                        decl.description = tool.description
                        declarations.append(decl)
                    else:
                        raise ValueError("No callable found")
                        
                except Exception as e:
                    print(f"⚠️ Native conversion failed for {tool.name}: {e}. Falling back to manual.")
                    # Fallback: Manual construction from LangChain args_schema
                    try:
                        # Get JSON schema from Pydantic
                        schema = tool.args_schema.schema() if tool.args_schema else {}
                        
                        # Convert JSON schema types to GenAI types
                        # Ideally we map 'title', 'type', 'properties' etc.
                        # For simplicity, if native SDK accepts dict schema, we pass it? 
                        # Docs say 'parameters' is an object.
                        # Let's hope types.FunctionDeclaration accepts simple dict or we need to map types.
                        # Since we want to be "native", let's assume we can pass the dict or rely on a helper.
                        
                        # Actually, let's just use the manual construction I wrote before but cleaner
                        declarations.append(types.FunctionDeclaration(
                             name=tool.name,
                             description=tool.description,
                             parameters=schema # Pass the JSON schema dict directly? SDK might handle it.
                        ))
                    except Exception as e2:
                        print(f"❌ Failed to convert tool {tool.name}: {e2}")

            if declarations:
                gemini_tools = [types.Tool(function_declarations=declarations)]

        # 2. Prepare Config
        config = GenerateContentConfig(
            thinking_config=ThinkingConfig(
                include_thoughts=include_thoughts,
                thinking_budget=thinking_budget
            ),
            tools=gemini_tools,
            temperature=0.7
        )

        # 3. Message Conversion
        gemini_contents = self._convert_messages(messages)
        
        # 4. Agent Loop
        MAX_TURNS = 10
        turn = 0
        
        while turn < MAX_TURNS:
            turn += 1
            print(f"🔄 Native Loop Turn {turn}")
            
            chunk_stream = await self.client.aio.models.generate_content_stream(
                model=self.model_name,
                contents=gemini_contents,
                config=config
            )
            
            tool_calls_to_make = []
            final_content = ""
            
            async for chunk in chunk_stream:
                if not chunk.candidates: continue
                
                # We might get text, thought, or function call
                for part in chunk.candidates[0].content.parts:
                    # check thought
                    if hasattr(part, 'thought') and part.thought:
                        # Stream thought
                        yield {"type": "thinking", "content": part.text}
                    
                    # check function call
                    elif hasattr(part, 'function_call') and part.function_call:
                        fc = part.function_call
                        print(f"   🛠️ Native Tool Call: {fc.name}")
                        yield {
                            "type": "tool_call",
                            "tool_call_id": "gen_id_" + fc.name, # GenAI doesn't give persistent ID like OpenAI
                            "tool_name": fc.name,
                            "tool_args": fc.args
                        }
                        tool_calls_to_make.append(fc)
                        
                    # check text (answer)
                    elif hasattr(part, 'text') and part.text:
                        final_content += part.text
                        yield {"type": "answer", "content": part.text}
            
            # If no tools, we are done
            if not tool_calls_to_make:
                print("   ✅ Turn complete - No tools")
                break
                
            # Execute Tools
            # Create a new "Turn" in history with the model's response (tool calls)
            # We must reconstruct the Model's message including tool calls for history consistency
            model_parts = []
            if final_content:
                model_parts.append(Part(text=final_content))
            for fc in tool_calls_to_make:
                model_parts.append(Part(function_call=fc))
            
            gemini_contents.append(Content(role="model", parts=model_parts))
            
            # Execute and Append Results
            for fc in tool_calls_to_make:
                tool_name = fc.name
                tool_args = fc.args
                
                tool_result_str = "Error: Tool not found"
                if tool_name in tool_map:
                    try:
                        # LangChain tool invoke
                        result = tool_map[tool_name].invoke(tool_args)
                        tool_result_str = str(result)
                    except Exception as e:
                        tool_result_str = f"Error executing tool: {e}"
                
                print(f"   ✅ Tool Result: {tool_name} -> {tool_result_str[:20]}...")
                yield {
                    "type": "tool_result",
                    "tool_call_id": "gen_id_" + tool_name,
                    "tool_name": tool_name,
                    "content": tool_result_str
                }
                
                # Append Function Response to history
                gemini_contents.append(Content(
                    role="function", # Or user? Gemini distinguishes 'function' role usually or part type?
                    # SDK v1 usually uses part with function_response inside 'user' or dedicated role?
                    # Docs say: role='tool' or 'function'? 
                    # Actually google-genai SDK v1 types:
                    # Content(role='tool', parts=[Part(function_response=FunctionResponse(...))])
                    parts=[Part(
                        function_response=types.FunctionResponse(
                            name=tool_name,
                            response={"result": tool_result_str} # Must be dict usually
                        )
                    )]
                ))
            
            # Loop continues to next turn
            
    def _convert_messages(self, langchain_messages) -> List[Content]:
        """Convert LangChain messages to Gemini Content format."""
        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
        
        gemini_contents = []
        system_prompt = None
        
        for msg in langchain_messages:
            # Handle system messages specially
            if isinstance(msg, SystemMessage):
                system_prompt = msg.content if isinstance(msg.content, str) else str(msg.content)
                continue
            
            role = self._get_gemini_role(msg)
            content_text = self._extract_content(msg)
            
            if content_text:
                # If we have a system prompt and this is the first user message, prepend it
                if system_prompt and role == "user" and len(gemini_contents) == 0:
                    content_text = f"{system_prompt}\n\n{content_text}"
                    system_prompt = None  # Only use once
                
                gemini_contents.append(
                    Content(
                        role=role,
                        parts=[Part(text=content_text)]
                    )
                )
        
        return gemini_contents
    
    def _get_gemini_role(self, msg) -> str:
        """Map LangChain message types to Gemini roles."""
        from langchain_core.messages import HumanMessage, AIMessage
        
        if isinstance(msg, HumanMessage):
            return "user"
        elif isinstance(msg, AIMessage):
            return "model"
        else:
            return "user"
    
    def _extract_content(self, msg) -> str:
        """Extract text content from message."""
        if isinstance(msg.content, str):
            return msg.content
        elif isinstance(msg.content, list):
            # Handle multi-part content
            texts = []
            for part in msg.content:
                if isinstance(part, dict) and 'text' in part:
                    texts.append(part['text'])
                elif hasattr(part, 'text'):
                    texts.append(part.text)
                elif isinstance(part, str):
                    texts.append(part)
            return "".join(texts)
        return str(msg.content)


# Global instance
_thinking_wrapper = None

def get_thinking_wrapper() -> GeminiThinkingWrapper:
    """Get or create the global thinking wrapper instance."""
    global _thinking_wrapper
    if _thinking_wrapper is None:
        _thinking_wrapper = GeminiThinkingWrapper()
    return _thinking_wrapper

