"""
Test script for native Gemini agent
Tests basic functionality without WebSocket
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.ai_engine.our_ai_engine.native_gemini_agent import get_native_agent, Message

async def test_basic_conversation():
    """Test basic conversation without tools"""
    print("=" * 60)
    print("TEST 1: Basic Conversation")
    print("=" * 60)
    
    agent = get_native_agent()
    
    messages = [
        Message(role="user", content="What is cybersecurity in simple terms?")
    ]
    
    print("\n💬 User: What is cybersecurity in simple terms?")
    print("\n🤖 Assistant:")
    
    async for event in agent.run_agent_loop(
        messages=messages,
        user_id="1",
        mode="simple",
        thinking_budget=512
    ):
        if event["type"] == "thinking":
            print(f"💭 [Thinking]: {event['content']}", end="", flush=True)
        elif event["type"] == "answer":
            print(event["content"], end="", flush=True)
        elif event["type"] == "done":
            print("\n\n✅ Conversation complete")
        elif event["type"] == "error":
            print(f"\n❌ Error: {event['error']}")

async def test_tool_call():
    """Test conversation with tool calling"""
    print("\n" + "=" * 60)
    print("TEST 2: Tool Calling (VirusTotal)")
    print("="  * 60)
    
    agent = get_native_agent()
    
    messages = [
        Message(role="user", content="Can you check if google.com is safe using VirusTotal?")
    ]
    
    print("\n💬 User: Can you check if google.com is safe using VirusTotal?")
    print("\n🤖 Assistant:")
    
    async for event in agent.run_agent_loop(
        messages=messages,
        user_id="1",
        mode="simple",
        thinking_budget=512
    ):
        if event["type"] == "thinking":
            print(f"\n💭 [Thinking]: {event['content']}")
        elif event["type"] == "tool_call":
            print(f"\n🔧 [Tool Call]: {event['tool_name']}({event['tool_args']})")
        elif event["type"] == "tool_result":
            print(f"✅ [Tool Result]: {event['result'][:100]}...")
        elif event["type"] == "answer":
            print(event["content"], end="", flush=True)
        elif event["type"] == "done":
            print("\n\n✅ Conversation complete")
        elif event["type"] == "error":
            print(f"\n❌ Error: {event['error']}")

async def main():
    """Run all tests"""
    try:
        await test_basic_conversation()
        await test_tool_call()
        
        print("\n" + "=" * 60)
        print("✅ All tests completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
