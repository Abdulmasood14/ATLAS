# SETUP AND TESTING GUIDE - Financial RAG Chatbot

## ✅ FRONTEND COMPONENTS COMPLETED (100%)

All frontend components have been implemented:
- ✅ globals.css - Professional dark theme styles
- ✅ layout.tsx - Root layout
- ✅ page.tsx - Main chat interface with state management
- ✅ ChatWindow.tsx - Message display with auto-scroll
- ✅ MessageBubble.tsx - Individual messages with sources
- ✅ InputBox.tsx - Auto-expanding input with keyboard shortcuts
- ✅ TypingIndicator.tsx - Animated loading dots
- ✅ FeedbackButtons.tsx - RLHF feedback system (Good/Medium/Bad)

## 🚀 COMPLETE SETUP INSTRUCTIONS

### STEP 1: Database Setup

Run these commands in PostgreSQL:

```sql
-- Connect to PostgreSQL
psql -U postgres

-- Ensure database exists
CREATE DATABASE financial_rag;

-- Connect to the database
\c financial_rag

-- Run migrations
\i 'D:/Objective and Subjective/Objective and Subjective/New folder/FINAL/chatbot_ui/backend/database/migrations.sql'

-- Verify tables were created
\dt

-- You should see:
-- chat_sessions
-- chat_messages
-- feedback_responses
-- query_exports
-- company_uploads
```

Or use this one-liner:
```bash
psql -U postgres -d financial_rag -f "D:\Objective and Subjective\Objective and Subjective\New folder\FINAL\chatbot_ui\backend\database\migrations.sql"
```

### STEP 2: Backend Dependencies

```bash
cd "D:\Objective and Subjective\Objective and Subjective\New folder\FINAL\chatbot_ui\backend"

# Install backend dependencies
py -3.11 -m pip install -r requirements.txt

# Also install RAG system dependencies
cd "..\..\UPDATED_ADV_RAG_SYS"
py -3.11 -m pip install -r requirements.txt

cd "..\chatbot_ui\backend"
```

### STEP 3: Start Backend Server

```bash
cd "D:\Objective and Subjective\Objective and Subjective\New folder\FINAL\chatbot_ui\backend"
py -3.11 main.py
```

**Backend will start at:** `http://localhost:8000`
**API Documentation:** `http://localhost:8000/docs`

### STEP 4: Frontend Dependencies

Open a **NEW terminal** window:

```bash
cd "D:\Objective and Subjective\Objective and Subjective\New folder\FINAL\chatbot_ui\frontend"

# Install Node dependencies
npm install

# Start development server
npm run dev
```

**Frontend will start at:** `http://localhost:3000`

---

## 🧪 TESTING INSTRUCTIONS

### TEST 1: Backend Health Check

Open browser or use curl:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-12-18T00:00:00Z"
}
```

### TEST 2: API Documentation (Swagger UI)

1. Open: `http://localhost:8000/docs`
2. You should see interactive API documentation
3. Try creating a session:
   - Click on `POST /api/chat/session`
   - Click "Try it out"
   - Enter:
     ```json
     {
       "company_id": "TEST_001",
       "company_name": "Test Company"
     }
     ```
   - Click "Execute"
   - Copy the `session_id` from the response

### TEST 3: Send a Test Query

In Swagger UI:
1. Click on `POST /api/chat/query`
2. Click "Try it out"
3. Enter (use the session_id from above):
   ```json
   {
     "query": "What is the fair value of investment properties?",
     "session_id": "YOUR_SESSION_ID_HERE",
     "company_id": "PHX_FXD",
     "top_k": 5
   }
   ```
4. Click "Execute"
5. Check the response - you should get an answer (or error if PDF not ingested yet)

### TEST 4: Frontend UI

1. Open: `http://localhost:3000`
2. You should see the chat interface
3. The session should auto-create (check browser console)
4. Try typing a message and sending it
5. Wait for the response
6. Click on feedback buttons (Good/Medium/Bad)

### TEST 5: Submit Feedback (RLHF)

After receiving a response in the UI:
1. Click one of the feedback buttons:
   - 👍 Good
   - ⚖️ Medium
   - 👎 Bad
2. You should see a toast notification "✓ Feedback recorded"
3. Verify in backend logs or database

### TEST 6: View Feedback in Database

```sql
-- Connect to database
psql -U postgres -d financial_rag

-- View all feedback
SELECT * FROM feedback_responses ORDER BY feedback_timestamp DESC LIMIT 5;

-- View feedback summary
SELECT * FROM v_feedback_summary_by_company;

-- View bad responses
SELECT user_query, assistant_response, feedback_score
FROM feedback_responses
WHERE feedback_score = 0.0;
```

---

## 🎯 FULL INTEGRATION TEST

### Prerequisites
- Ensure you have a PDF ingested in the RAG system
- If not, ingest one first using the existing RAG system

### Test Flow

1. **Open Frontend:** `http://localhost:3000`

2. **Send Query:**
   - Type: "What is the fair value of investment properties?"
   - Press Enter or click Send
   - Wait for response

3. **View Response:**
   - Check the answer appears
   - Click to expand sources
   - Verify page numbers and relevance scores

4. **Submit Feedback:**
   - Click "Good" button
   - Verify toast notification appears

5. **Send Multiple Queries:**
   - Try different types of questions
   - Test error handling (ask nonsense questions)
   - Test with different companies

6. **Check Database:**
   ```sql
   -- Check session
   SELECT * FROM chat_sessions ORDER BY created_at DESC LIMIT 1;

   -- Check messages
   SELECT role, substring(content, 1, 50) as content_preview, created_at
   FROM chat_messages
   ORDER BY created_at DESC LIMIT 10;

   -- Check feedback
   SELECT user_query, feedback_score, model_used
   FROM feedback_responses
   ORDER BY feedback_timestamp DESC LIMIT 5;
   ```

---

## 🐛 TROUBLESHOOTING

### Backend Issues

**Issue:** `ModuleNotFoundError: No module named 'fastapi'`
```bash
cd backend
py -3.11 -m pip install -r requirements.txt
```

**Issue:** `ImportError: No module named 'query_engine'`
```bash
cd ../../UPDATED_ADV_RAG_SYS
py -3.11 -m pip install -r requirements.txt
```

**Issue:** Database connection error
```bash
# Check PostgreSQL is running
psql -U postgres -c "SELECT 1"

# Verify database exists
psql -U postgres -l | findstr financial_rag
```

**Issue:** Port 8000 already in use
```bash
# Windows: Find and kill process
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Frontend Issues

**Issue:** `Module not found: Can't resolve 'axios'`
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Issue:** TypeScript errors
```bash
# Clear Next.js cache
rm -rf .next
npm run dev
```

**Issue:** Port 3000 already in use
```bash
# Use different port
set PORT=3001
npm run dev
```

**Issue:** "Failed to create session"
- Check backend is running (`http://localhost:8000/health`)
- Check browser console for CORS errors
- Verify backend CORS allows `http://localhost:3000`

---

## ✅ VERIFICATION CHECKLIST

Before considering setup complete, verify:

- [ ] Database tables created (5 tables)
- [ ] Backend starts without errors
- [ ] Backend health endpoint works (`/health`)
- [ ] Swagger UI accessible (`/docs`)
- [ ] Can create session via API
- [ ] Frontend starts without errors
- [ ] Frontend loads in browser
- [ ] Session auto-creates on page load
- [ ] Can send query and receive response
- [ ] Feedback buttons work
- [ ] Feedback saved to database
- [ ] No console errors in browser
- [ ] No errors in backend logs

---

## 📊 PERFORMANCE TESTING

### Response Time Test

```python
import time
import requests

API_URL = "http://localhost:8000"

# Create session
session_resp = requests.post(f"{API_URL}/api/chat/session", json={
    "company_id": "TEST_001",
    "company_name": "Test Company"
})
session_id = session_resp.json()["session_id"]

# Send query and measure time
start = time.time()
query_resp = requests.post(f"{API_URL}/api/chat/query", json={
    "query": "What is the fair value?",
    "session_id": session_id,
    "company_id": "PHX_FXD",
    "top_k": 5
})
end = time.time()

print(f"Response time: {end - start:.2f} seconds")
print(f"Status: {query_resp.status_code}")
```

Expected response time: 2-5 seconds (depending on LLM)

### Load Testing

```python
import concurrent.futures
import requests

def send_query(query_num):
    # Create session
    session_resp = requests.post(f"{API_URL}/api/chat/session", json={
        "company_id": "TEST_001",
        "company_name": "Test Company"
    })
    session_id = session_resp.json()["session_id"]

    # Send query
    query_resp = requests.post(f"{API_URL}/api/chat/query", json={
        "query": f"Test query {query_num}",
        "session_id": session_id,
        "company_id": "PHX_FXD"
    })

    return query_resp.status_code

# Send 10 concurrent requests
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(send_query, range(10)))

print(f"Success rate: {results.count(200)}/10")
```

---

## 🎨 UI TESTING

### Visual Checks

1. **Color Theme:**
   - Background should be deep navy (#0F1729)
   - Primary accent should be cyan/teal (#06B6D4)
   - No purple/violet colors

2. **Typography:**
   - Text should be readable
   - Font should be Inter
   - Proper hierarchy (headers, body text)

3. **Feedback Buttons:**
   - Good: Green when selected
   - Medium: Amber when selected
   - Bad: Red when selected
   - Hover states visible

4. **Animations:**
   - Messages slide in smoothly
   - Typing indicator dots bounce
   - Toast notifications slide in from right

5. **Responsiveness:**
   - Try resizing browser window
   - Should work on different screen sizes

---

## 📝 MANUAL TEST SCENARIOS

### Scenario 1: Happy Path
1. Open frontend
2. Wait for session creation
3. Type: "What is the fair value of investment properties?"
4. Press Enter
5. Wait for response
6. Verify answer is relevant
7. Click "Good" feedback button
8. Verify toast appears

**Expected:** ✅ All steps work smoothly

### Scenario 2: Error Handling
1. Send query with company that doesn't exist
2. Verify error message appears
3. Try sending empty message
4. Verify Send button is disabled

**Expected:** ✅ Graceful error handling

### Scenario 3: Multiple Messages
1. Send 5 different queries in sequence
2. Verify all messages appear
3. Verify auto-scroll to bottom works
4. Verify can scroll up to see old messages

**Expected:** ✅ Chat history preserved and scrollable

### Scenario 4: Feedback on Multiple Messages
1. Send 3 queries
2. Give different feedback on each (Good, Medium, Bad)
3. Check database for all 3 feedback entries

**Expected:** ✅ All feedback saved correctly

---

## 🔍 DEBUGGING TIPS

### Enable Debug Logging

**Backend:**
```python
# In main.py, add:
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Frontend:**
```typescript
// In page.tsx, add console logs:
console.log('Sending query:', query);
console.log('Response:', response);
```

### Check Network Requests

1. Open browser DevTools (F12)
2. Go to Network tab
3. Send a message
4. Look for API calls to `localhost:8000`
5. Check request/response payloads

### Monitor Database

```sql
-- Watch for new messages in real-time
-- Run this in psql:
SELECT * FROM chat_messages ORDER BY created_at DESC LIMIT 1;
-- Refresh frequently
```

---

## 🎉 SUCCESS CRITERIA

Your setup is **COMPLETE** and **WORKING** if:

✅ Backend starts without errors
✅ Frontend starts without errors
✅ Can create chat session
✅ Can send query and get response
✅ Feedback buttons work
✅ Feedback saved to database
✅ No console errors
✅ UI looks professional (dark theme, teal accents)
✅ Animations work smoothly
✅ Auto-scroll works

---

## 📞 NEXT STEPS AFTER TESTING

Once everything works:

1. **Upload Real PDF:**
   ```bash
   cd ../../UPDATED_ADV_RAG_SYS
   py -3.11 master_ingest_annual_report.py "path/to/pdf.pdf" COMPANY_ID
   ```

2. **Test with Real Data:**
   - Ask questions about the PDF
   - Verify accurate answers
   - Check source citations

3. **Collect Feedback:**
   - Use the system with real queries
   - Rate responses
   - Build RLHF dataset

4. **Review Feedback:**
   ```sql
   -- Get all bad/medium feedback for review
   SELECT * FROM v_feedback_needs_review;
   ```

5. **Improve Prompts:**
   - Analyze bad responses
   - Update prompts in `UPDATED_ADV_RAG_SYS/llm_integration.py`
   - Test improvements

---

**🎊 Congratulations! You now have a fully functional Financial RAG Chatbot with RLHF!**
