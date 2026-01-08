#!/usr/bin/env python3
"""
Quick test script to verify Gemini thinking setup
"""

import os
import sys
# Add backend directory and parent directory to path when run from backend/
backend_dir = os.path.abspath(os.path.dirname(__file__))
parent_dir = os.path.abspath(os.path.join(backend_dir, '..'))
sys.path.insert(0, backend_dir)
sys.path.insert(0, parent_dir)

from dotenv import load_dotenv
# Load .env from parent directory (project root) if it exists
env_path = os.path.join(parent_dir, '.env')
load_dotenv(env_path)

def test_environment():
    """Test environment variables"""
    print("=" * 60)
    print("🧪 Testing Environment Setup")
    print("=" * 60)
    print()
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        print(f"✅ GOOGLE_API_KEY found (length: {len(api_key)})")
    else:
        print("❌ GOOGLE_API_KEY not found")
        print("   Please set it in your .env file")
        return False
    print()
    return True

def test_google_genai_sdk():
    """Test Google GenAI SDK installation"""
    print("=" * 60)
    print("🧪 Testing Google GenAI SDK")
    print("=" * 60)
    print()
    
    try:
        from google import genai
        from google.genai.types import GenerateContentConfig, ThinkingConfig
        print("✅ google-genai package imported successfully")
        print(f"   Version: {genai.__version__ if hasattr(genai, '__version__') else 'unknown'}")
    except ImportError as e:
        print(f"❌ Failed to import google-genai: {e}")
        print("   Run: pip install google-genai")
        return False
    print()
    return True

def test_thinking_wrapper():
    """Test Gemini thinking wrapper"""
    print("=" * 60)
    print("🧪 Testing Gemini Thinking Wrapper")
    print("=" * 60)
    print()
    
    try:
        from backend.ai_engine.our_ai_engine.gemini_thinking import get_thinking_wrapper
        
        wrapper = get_thinking_wrapper()
        print(f"✅ Thinking wrapper initialized")
        print(f"   Thinking enabled: {wrapper.thinking_enabled}")
        print(f"   Model: {wrapper.model_name}")
        print(f"   Has client: {wrapper.client is not None}")
        
        if not wrapper.thinking_enabled:
            print("⚠️  Warning: Thinking is not enabled")
            print("   Check GOOGLE_API_KEY and SDK installation")
            return False
            
    except Exception as e:
        print(f"❌ Failed to initialize thinking wrapper: {e}")
        import traceback
        traceback.print_exc()
        return False
    print()
    return True

def test_langchain_integration():
    """Test LangChain Google GenAI integration"""
    print("=" * 60)
    print("🧪 Testing LangChain Integration")
    print("=" * 60)
    print()
    
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro",
            temperature=0.7,
            streaming=True
        )
        print("✅ LangChain ChatGoogleGenerativeAI initialized")
        print(f"   Model: gemini-2.5-pro")
        print(f"   Streaming: enabled")
    except Exception as e:
        print(f"❌ Failed to initialize LangChain LLM: {e}")
        return False
    print()
    return True

def test_agent():
    """Test agent initialization"""
    print("=" * 60)
    print("🧪 Testing Agent")
    print("=" * 60)
    print()
    
    try:
        from backend.ai_engine.our_ai_engine.agent import app, llm
        print("✅ Agent initialized successfully")
        print(f"   LLM model: {llm.model_name if hasattr(llm, 'model_name') else 'gemini-2.5-pro'}")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        import traceback
        traceback.print_exc()
        return False
    print()
    return True

def main():
    print()
    print("🔬 BYTE Gemini Thinking Setup Verification")
    print()
    
    tests = [
        ("Environment Variables", test_environment),
        ("Google GenAI SDK", test_google_genai_sdk),
        ("Thinking Wrapper", test_thinking_wrapper),
        ("LangChain Integration", test_langchain_integration),
        ("Agent Initialization", test_agent),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Test '{name}' crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    print()
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print()
    print(f"Result: {passed}/{total} tests passed")
    print()
    
    if passed == total:
        print("🎉 All tests passed! Your setup is ready.")
        print()
        print("Next steps:")
        print("  1. Start the backend: python run.py")
        print("  2. Start the frontend: cd frontend && npm run dev")
        print("  3. Open http://localhost:3000 in your browser")
    else:
        print("⚠️  Some tests failed. Please fix the issues above.")
        print()
        print("Common fixes:")
        print("  • Set GOOGLE_API_KEY in .env file")
        print("  • Run: pip install -r requirements.txt")
        print("  • Run: pip install google-genai")
    
    print()
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
