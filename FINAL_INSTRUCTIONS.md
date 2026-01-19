# 🚀 FINAL SETUP INSTRUCTIONS - Financial RAG Chatbot

**✅ Status:** ALL CODE COMPLETE - READY TO RUN
**🔧 Fixed:** Import errors resolved

---

## 📋 PREREQUISITES

Before starting, ensure you have:

- ✅ Python 3.11 installed (`py -3.11 --version`)
- ✅ Node.js 18+ installed (`node --version`)
- ✅ PostgreSQL running and accessible
- ✅ Database `financial_rag` exists

---

## 🎯 QUICK START (3 STEPS)

### **STEP 1: Run Database Migrations (ONE TIME ONLY)**

Open PostgreSQL command line:

```sql
-- Connect to PostgreSQL
psql -U postgres

-- Run migrations
\i 'D:/Objective and Subjective/Objective and Subjective/New folder/FINAL/chatbot_ui/backend/database/migrations.sql'

-- Verify tables created
\dt

-- You should see 5 tables:
-- - chat_sessions
-- - chat_messages
-- - feedback_responses
-- - query_exports
-- - company_uploads
```

Or use command line:
```bash
psql -U postgres -d financial_rag -f "D:\Objective and Subjective\Objective and Subjective\New folder\FINAL\chatbot_ui\backend\database\migrations.sql"
```

---

### **STEP 2: Start Backend Server**

**Option A: Use the Batch File (Easy)**

Double-click: `RUN_THIS.bat`

**Option B: Manual (Recommended for first time)**

```bash
# Navigate to backend folder
cd "D:\Objective and Subjective\Objective and Subjective\New folder\FINAL\chatbot_ui\backend"

# Install dependencies (FIRST TIME ONLY)
py -3.11 -m pip install -r requirements.txt

# Also install RAG system dependencies (FIRST TIME ONLY)
cd "..\..\UPDATED_ADV_RAG_SYS"
py -3.11 -m pip install -r requirements.txt

# Go back to backend
cd "..\chatbot_ui\backend"

# Start the server
py -3.11 main.py
```

**Expected Output:**
```
================================================================================
FINANCIAL RAG CHATBOT - STARTING UP
================================================================================
✓ RAG service ready (will initialize on first use)
✓ Database connection pool ready
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**✅ Backend is running when you see:** `Uvicorn running on http://0.0.0.0:8000`

**Test it:** Open `http://localhost:8000/docs` in your browser

---

### **STEP 3: Start Frontend (NEW TERMINAL)**

Open a **NEW terminal window:**

```bash
# Navigate to frontend folder
cd "D:\Objective and Subjective\Objective and Subjective\New folder\FINAL\chatbot_ui\frontend"

# Install dependencies (FIRST TIME ONLY)
npm install

# Start development server
npm run dev
```

**Expected Output:**
```
  ▲ Next.js 15.1.6
  - Local:        http://localhost:3000
  - Environments: .env

 ✓ Ready in 2.5s
```

**✅ Frontend is running when you see:** `Ready in 2.5s`

**Open:** `http://localhost:3000` in your browser

---

## ✅ VERIFICATION

### Test 1: Backend Health

```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-18T..."
}
```

### Test 2: API Documentation

Open: `http://localhost:8000/docs`

You should see **Swagger UI** with all API endpoints.

### Test 3: Frontend UI

Open: `http://localhost:3000`

You should see:
- Professional dark navy interface
- "Welcome to Financial RAG Assistant" message
- Input box at the bottom
- "Connected" status indicator in header

### Test 4: Full Integration Test

Run the automated test script:

```bash
# Make sure backend is running first
cd "D:\Objective and Subjective\Objective and Subjective\New folder\FINAL\chatbot_ui"
py -3.11 TEST_BACKEND.py
```

This will test:
1. Health check
2. Session creation
3. Query processing
4. Feedback submission (RLHF)
5. Company listing

---

## 🧪 MANUAL TESTING

### Test the Chat Interface

1. **Open Frontend:** `http://localhost:3000`

2. **Wait for Session:**
   - You should see "Connected" in the header
   - Session auto-creates (check browser console for session_id)

3. **Send a Query:**
   - Type: "What is the fair value of investment properties?"
   - Press Enter or click Send

4. **Check Response:**
   - Wait for typing indicator (animated dots)
   - Response appears with sources (if data exists)
   - If no data: "No relevant information found"

5. **Submit Feedback:**
   - Click one of the feedback buttons:
     - 👍 **Good**
     - ⚖️ **Medium**
     - 👎 **Bad**
   - Toast notification should appear: "✓ Feedback recorded"

### Test API Directly (Swagger UI)

1. **Open:** `http://localhost:8000/docs`

2. **Test Create Session:**
   - Click `POST /api/chat/session`
   - Click "Try it out"
   - Enter:
     ```json
     {
       "company_id": "TEST_001",
       "company_name": "Test Company"
     }
     ```
   - Click "Execute"
   - Copy the `session_id` from response

3. **Test Send Query:**
   - Click `POST /api/chat/query`
   - Click "Try it out"
   - Enter (use your session_id):
     ```json
     {
       "query": "Test query",
       "session_id": "YOUR_SESSION_ID_HERE",
       "company_id": "PHX_FXD",
       "top_k": 5
     }
     ```
   - Click "Execute"
   - Check response

---

## 🎨 WHAT YOU SHOULD SEE

### Frontend UI

```
┌─────────────────────────────────────────────┐
│ 📊 Financial RAG Assistant      Connected   │  ← Header (Dark Navy)
├─────────────────────────────────────────────┤
│                                             │
│    Welcome to Financial RAG Assistant       │  ← Welcome Message
│    Ask questions about your financial...    │
│                                             │
│    💡 Example queries:                      │
│    • What is the fair value...              │
│                                             │
├─────────────────────────────────────────────┤
│ 💬 Type your question...      [Send]       │  ← Input (Teal accent)
│    Press Enter to send, Shift+Enter...     │
└─────────────────────────────────────────────┘
```

**Colors:**
- Background: Deep Navy (#0F1729) with gradient
- Primary: Bright Cyan/Teal (#06B6D4)
- Accent: Gold (#F59E0B)
- Text: White/Light Gray

---

## 🐛 TROUBLESHOOTING

### Error: "ImportError: cannot import name 'ingest_annual_report'"

**FIXED!** The import has been corrected to use `MasterAnnualReportPipeline`.

If you still see this:
```bash
# Make sure you're using the latest code
cd backend/services
# Check that rag_service.py imports MasterAnnualReportPipeline
```

### Error: "Module 'fastapi' not found"

```bash
cd backend
py -3.11 -m pip install -r requirements.txt
```

### Error: "Module 'query_engine' not found"

```bash
cd ../../UPDATED_ADV_RAG_SYS
py -3.11 -m pip install -r requirements.txt
```

### Error: "Port 8000 already in use"

**Windows:**
```bash
netstat -ano | findstr :8000
taskkill /PID <PID_NUMBER> /F
```

### Error: "Database connection refused"

```bash
# Check PostgreSQL is running
psql -U postgres -c "SELECT 1"

# Verify database exists
psql -U postgres -l | findstr financial_rag
```

### Frontend shows "Failed to create session"

**Causes:**
1. Backend not running → Start backend first
2. CORS error → Check backend logs
3. Wrong URL → Frontend should connect to `http://localhost:8000`

**Fix:**
- Ensure backend is running: `http://localhost:8000/health`
- Check browser console (F12) for errors
- Verify backend shows no errors

---

## 📊 EXPECTED BEHAVIOR

### First Query (No Data)

If you haven't ingested any PDFs yet:

**Query:** "What is the fair value?"

**Response:** "No relevant information found in the database. Please check if the PDF has been ingested for this company."

**This is NORMAL!** You need to ingest a PDF first.

### After Ingesting PDF

**Query:** "What is the fair value of investment properties?"

**Response:** Actual answer with sources, page numbers, and note citations.

---

## 📥 INGESTING YOUR FIRST PDF

To get real data, ingest a PDF using the RAG system:

```bash
cd "D:\Objective and Subjective\Objective and Subjective\New folder\FINAL\UPDATED_ADV_RAG_SYS"

py -3.11 master_ingest_annual_report.py "path/to/your/financial_report.pdf" YOUR_COMPANY_ID --company_name "Company Name" --fiscal_year "2024-25"
```

**Example:**
```bash
py -3.11 master_ingest_annual_report.py "D:\PDFs\phoenix_mills.pdf" PHX_FXD --company_name "Phoenix Mills" --fiscal_year "2024-25"
```

Then refresh the chatbot and ask questions!

---

## 🎯 SUCCESS CHECKLIST

- [ ] Database migrations ran successfully (5 tables created)
- [ ] Backend starts without errors
- [ ] Backend health check works: `http://localhost:8000/health`
- [ ] Swagger UI accessible: `http://localhost:8000/docs`
- [ ] Frontend starts without errors
- [ ] Frontend loads in browser: `http://localhost:3000`
- [ ] Session auto-creates (check browser console)
- [ ] Can send a message (even if no data)
- [ ] Feedback buttons appear on responses
- [ ] No console errors in browser (F12)
- [ ] No errors in backend terminal

**ALL CHECKED?** ✅ **YOU'RE READY!**

---

## 🎉 NEXT STEPS

1. **Ingest PDF:** Use the RAG system to ingest financial documents
2. **Test Queries:** Ask questions about the documents
3. **Collect Feedback:** Rate responses using feedback buttons
4. **Review Data:** Check `feedback_responses` table in database
5. **Improve Prompts:** Analyze bad responses and refine prompts

---

## 📚 DOCUMENTATION

- **This File** - Setup and testing
- **START_HERE.txt** - Quick command reference
- **README.md** - Complete feature documentation
- **SETUP_AND_TEST.md** - Detailed testing guide
- **IMPLEMENTATION_COMPLETE.md** - Project status

---

## 📞 SUPPORT

If you encounter issues:

1. Check this troubleshooting section
2. Review browser console (F12)
3. Check backend terminal for errors
4. Test API directly: `http://localhost:8000/docs`
5. Verify database connection

---

**✨ You're all set! Start the backend and frontend, then open http://localhost:3000**

**🎊 Enjoy your Financial RAG Chatbot with RLHF!**
