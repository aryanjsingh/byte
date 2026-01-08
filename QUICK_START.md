# 🚀 BYTE - Quick Start Guide

## ⚡ 3-Step Setup

### 1️⃣ Test Everything is Working
```bash
cd backend
python3 test_setup.py
```

Expected output:
```
✅ PASS - Environment Variables
✅ PASS - Google GenAI SDK
✅ PASS - Thinking Wrapper
✅ PASS - LangChain Integration
✅ PASS - Agent Initialization

Result: 5/5 tests passed 🎉
```

### 2️⃣ Start Backend
```bash
cd backend
python3 run.py
```

You should see:
```
🚀 Starting BYTE Security Agent Backend
📍 Server will be available at:
   • Local:   http://localhost:8000
   • Network: http://0.0.0.0:8000
```

### 3️⃣ Start Frontend (new terminal)
```bash
cd frontend
npm run dev
```

You should see:
```
  ▲ Next.js 16.1.1
  - Local:        http://localhost:3000
```

## 🌐 Access the App

Open your browser to: **http://localhost:3000**

## 🧠 Test Gemini Thinking

Once the app is running, try asking:
- "What is quantum computing?"
- "Explain blockchain technology step by step"
- "How does encryption work?"

You'll see:
1. 💭 **Reasoning component opens** (showing thinking process)
2. 💬 **Answer streams in real-time**
3. ✨ **Both are displayed beautifully**

## 🐛 Troubleshooting

### Backend won't start
```bash
# Error: No module named 'backend'
# Fix: Make sure you're in the backend directory
cd backend
python3 run.py
```

### Missing dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Missing GOOGLE_API_KEY
```bash
# Create/edit .env file in project root
echo "GOOGLE_API_KEY=your_key_here" > ../.env
```

### Test fails
```bash
cd backend
python3 test_setup.py
# Read the output - it will tell you what's missing
```

### WebSocket connection fails
- Make sure backend is running on port 8000
- Check browser console for errors
- Verify JWT token exists (login again if needed)

## 📊 Verify Everything is Working

### Check Backend Console
You should see:
```
🔥 Starting Gemini thinking stream
💭 Thinking chunk 1, 2, 3...
💬 Answer chunk 1, 2, 3...
✅ Stream complete
```

### Check Browser Console (F12)
You should see:
```
🔌 WebSocket connected
📤 Send message
📨 Thinking received
📨 Answer received
✅ Complete
```

## 🔑 Environment Setup

Make sure `.env` exists in project root with:
```bash
GOOGLE_API_KEY=your_gemini_api_key_here
```

Get your API key from: https://aistudio.google.com/apikey

## 📚 Documentation

- **Quick Start**: `QUICK_START.md` (this file)
- **Full Details**: `IMPLEMENTATION_COMPLETE.md`
- **Architecture**: `ARCHITECTURE_DIAGRAM.md`
- **File Structure**: `PROJECT_STRUCTURE.md`
- **Reorganization**: `FILE_REORGANIZATION.md`

## 🎯 What You'll See

### Backend Startup
```
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║      🚀 BYTE Security Agent - Backend Startup           ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝

📍 Server will be available at:
   • Local:   http://localhost:8000
   • Network: http://0.0.0.0:8000

📡 WebSocket endpoint:
   • ws://localhost:8000/ws/chat?token=YOUR_TOKEN

✅ Gemini Thinking Wrapper initialized with gemini-2.5-pro
```

### Frontend Chat
- Beautiful dark mode interface
- Real-time typing indicator
- Voice input/output support
- Thinking process visualization
- Markdown rendering
- Tool call badges

## 💡 Tips

1. **Use Turbo Mode** for complex questions (toggle in UI)
2. **Watch the Reasoning** component to see how Gemini thinks
3. **Check console logs** for detailed debugging
4. **Ask follow-up questions** - conversations are threaded
5. **Try voice input** by clicking the microphone icon

## ⚙️ Default Configuration

- **Model**: Gemini 2.5 Pro
- **Thinking Budget**: -1 (dynamic - auto-adjusts)
- **Token Expiry**: 7 days
- **Streaming**: Enabled
- **Include Thoughts**: True

---

**Ready to go!** 🎉 Just follow the 3 steps above and start chatting!
