#!/usr/bin/env python3
"""
BYTE Backend Runner
Simple script to start the backend server with one command.
"""

import sys
import os

# Add backend directory to path (current directory when run from backend/)
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import uvicorn

def main():
    """Start the BYTE backend server"""
    print("=" * 60)
    print("🚀 Starting BYTE Security Agent Backend")
    print("=" * 60)
    print()
    print("📍 Server will be available at:")
    print("   • Local:   http://localhost:8000")
    print("   • Network: http://0.0.0.0:8000")
    print()
    print("📡 WebSocket endpoint:")
    print("   • ws://localhost:8000/ws/chat?token=YOUR_TOKEN")
    print()
    print("📚 API Documentation:")
    print("   • Swagger UI: http://localhost:8000/docs")
    print("   • ReDoc:      http://localhost:8000/redoc")
    print()
    print("=" * 60)
    print()
    
    # Check for required environment variables
    required_vars = ["GOOGLE_API_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("⚠️  WARNING: Missing environment variables:")
        for var in missing_vars:
            print(f"   • {var}")
        print()
        print("💡 Make sure to set these in your .env file")
        print()
    
    # Start server
    uvicorn.run(
        "server:app",  # Use import string instead of app object for reload to work
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=True,  # Auto-reload on code changes
        access_log=True
    )

if __name__ == "__main__":
    main()
