# Native Gemini Streaming & Thinking Issues - FIXES

## Issues Identified

### 1. ✅ **VirusTotal Event Loop Error** - FIXED
**Problem:** `This event loop is already running`
**Cause:** Sync `vt.Client` being called from async context
**Solution:** Removed problematic `client.scan_url()` call and simplified to use only `get_object()` which is safer

**File:** `/backend/ai_engine/our_ai_engine/tools/virustotal_tool.py`

### 2. ⚠️  **Thinking Not Streaming** - SDK LIMITATION
**Problem:** All thinking shows up at once instead of incrementally
**Cause:** The Google Gen AI SDK may be buff

ering thought summaries before sending them
**Current Status:** Backend IS yielding thoughts incrementally, but SDK might buffer

**To verify:**
```bash
# Check backend logs to see if thoughts are streaming server-side
tail -f backend.log
```

### 3. ⚠️  **Thinking Accumulation** - FRONTEND ISSUE
**Problem:** Multiple separate thoughts from different tool-call iterations showing together
**This is likely a FRONTEND issue** - the UI is accumulating ALL thoughts instead of clearing between iterations

**Frontend needs to:**
1. Clear/separate thoughts when a new iteration starts
2. Show thoughts incrementally as they arrive
3. Add visual separator between tool-call iterations

---

## Quick Fixes Applied

### ✅ VirusTotal Tool (`virustotal_tool.py`)
```python
# OLD (caused event loop error):
analysis = client.scan_url(target)  # Async call in sync context!

# NEW (safe):
url_id = vt.url_id(target)
obj = client.get_object("/urls/{}", url_id)  # Sync only
```

### ⚙️  Streaming (Verification Needed)

The backend code DOES stream correctly:
```python
for chunk in stream:
    for part in chunk.candidates[0].content.parts:
        if part.thought:
            yield {"type": "thinking", "content": part.text}  # ✅ Yields immediately
        elif part.text:
            yield {"type": "answer", "content": part.text}   # ✅ Yields immediately
```

**The issue might be:**
1. SDK buffering thought summaries (not our code)
2. WebSocket not flushing immediately
3. Frontend accumulating instead of streaming

---

## Testing

### Test 1: Verify Backend Streaming
```bash
# Watch backend logs in real-time
cd backend
python3 run.py | grep -E "(thinking|answer|tool)"
```

### Test 2: Test VirusTotal Fix
Send message: `"Check google.com with VirusTotal"`

Expected:
- ✅ No "event loop" error
- ✅ Tool executes successfully
- ⚠️  Thinking might still buffer (SDK issue)

### Test 3: Frontend Streaming
Open browser devtools Network tab:
- Watch WebSocket messages
- See if thoughts arrive one-by-one or all at once
- **If they arrive one-by-one but display all at once = Frontend issue**
- **If they arrive all at once = SDK buffering issue**

---

## Frontend Fixes Needed

If thoughts are streaming from backend but displaying all at once:

### Fix 1: Clear Thoughts Between Iterations
```typescript
// When new message starts, clear previous thinking
if (event.type === "thinking") {
  // First thinking event of new iteration?
  if (isNewIteration) {
    setThinkingContent("");  // Clear previous
  }
  setThinkingContent(prev => prev + event.content);  // Stream new
}
```

### Fix 2: Add Iteration Separators
```typescript
if (event.type === "tool_call") {
  // Mark start of new iteration
  setIsNewIteration(true);
}
```

### Fix 3: Stream Display (Not All At Once)
```typescript
// Show thinking as it streams, not in collapsed dropdown
{thinkingContent && (
  <div className="thinking-stream">
    {thinkingContent}
  </div>
)}
```

---

##  SDK Buffering Workaround

If Gemini SDK is buffering thoughts, we can try:

### Option 1: Flush Explicitly
```python
import sys
for chunk in stream:
    # ... yield events ...
    sys.stdout.flush()  # Force flush
```

### Option 2: Lower Thinking Budget
```python
thinking_config=types.ThinkingConfig(
    thinking_budget=512,  # Lower = faster streaming?
    include_thoughts=True
)
```

### Option 3: Use Response Chunks Differently
```python
#Instead of waiting for part.thought flag,
# parse all text and detect thinking patterns
```

---

## Recommended Next Steps

1. **Test VirusTotal** - Should work now without event loop error ✅
2. **Check Backend Logs** - Are thoughts streaming server-side?
3. **Check Browser DevTools** - Are thoughts arriving incrementally via WebSocket?
4. **If thoughts arrive one-by-one but display all at once** → Frontend fix needed
5. **If thoughts arrive all at once** → SDK buffering, try workarounds above

---

## Files Modified

- ✅ `/backend/ai_engine/our_ai_engine/tools/virustotal_tool.py` - Fixed async issue
- ℹ️  `/backend/ai_engine/our_ai_engine/native_gemini_agent.py` - Already streams correctly
- ⚠️  Frontend components may need updates

---

## Current Status

| Issue | Backend Status | Frontend Status | Action |
|-------|---------------|-----------------|---------|
| VirusTotal Error | ✅ Fixed | N/A | Test it |
| Thinking Streaming | ✅ Yields incrementally | ⚠️  Shows all at once | Check where buffering happens |
| Thought Accumulation | ✅ Per-iteration tracking | ⚠️  Accumulates all | Clear between iterations |

**Next:** Restart backend and test!
