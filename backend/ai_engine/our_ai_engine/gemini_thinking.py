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

