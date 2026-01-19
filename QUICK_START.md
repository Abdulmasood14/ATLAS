# ⚡ QUICK START - Financial RAG Chatbot UI

**Get the chatbot running in 5 minutes!**

---

## 🚀 **ONE-TIME SETUP**

### **1. Database Setup** (2 minutes)

```bash
# Run migrations to create chat tables
cd backend
psql -U postgres -d financial_rag -f database/migrations.sql
```

Expected output: 5 tables created (chat_sessions, chat_messages, feedback_responses, query_exports, company_uploads)

### **2. Backend Setup** (2 minutes)

```bash
# Install dependencies
pip install -r requirements.txt

# Also install RAG system dependencies
cd ../../UPDATED_ADV_RAG_SYS
pip install -r requirements.txt
cd ../chatbot_ui
```

### **3. Frontend Setup** (1 minute)

```bash
# Install Node dependencies
cd frontend
npm install
cd ..
```

---

## ▶️ **RUNNING THE APP**

### **Option A: Both Services (Recommended)**

Open **TWO terminals**:

**Terminal 1 - Backend:**
```bash
cd backend
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

Then open: **http://localhost:3000**

### **Option B: Backend Only (For API Testing)**

```bash
cd backend
python main.py
```

Then open: **http://localhost:8000/docs** (Swagger UI)

---

## ✅ **VERIFY IT'S WORKING**

### **Backend Health Check**

```bash
curl http://localhost:8000/health
```

Expected: `{"status": "healthy"}`

### **Test Creating a Session**

```bash
curl -X POST http://localhost:8000/api/chat/session \
  -H "Content-Type: application/json" \
  -d '{"company_id": "TEST", "company_name": "Test Company"}'
```

Expected: JSON with session_id

### **Test Sending a Query**

```bash
# Replace {session_id} with the session_id from above
curl -X POST http://localhost:8000/api/chat/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the fair value?",
    "session_id": "{session_id}",
    "company_id": "PHX_FXD",
    "top_k": 5
  }'
```

---

## 🎯 **WHAT'S READY TO USE**

### ✅ **Backend (100% Functional)**

| Feature | Endpoint | Status |
|---------|----------|--------|
| Create Session | `POST /api/chat/session` | ✅ Working |
| Send Query | `POST /api/chat/query` | ✅ Working |
| Chat History | `GET /api/chat/history/{id}` | ✅ Working |
| Submit Feedback | `POST /api/feedback/submit` | ✅ Working |
| Get Bad Feedback | `GET /api/feedback/bad` | ✅ Working |
| Upload PDF | `POST /api/upload/pdf` | ✅ Working |
| Get Companies | `GET /api/upload/companies` | ✅ Working |
| Export Session | `POST /api/export/session` | ✅ Working |
| WebSocket Chat | `WS /ws/chat/{id}` | ✅ Working |

### 🔨 **Frontend (40% Complete)**

| Component | Status |
|-----------|--------|
| API Client | ✅ Ready |
| TypeScript Types | ✅ Ready |
| FeedbackButtons | ✅ Ready |
| TailwindCSS Config | ✅ Ready |
| ChatWindow | ⏳ TODO |
| MessageBubble | ⏳ TODO |
| InputBox | ⏳ TODO |
| Main Page | ⏳ TODO |

**To complete frontend:** Follow `IMPLEMENTATION_GUIDE.md`

---

## 🧪 **INTERACTIVE API TESTING**

The backend includes **Swagger UI** for easy API testing:

1. Start backend: `python backend/main.py`
2. Open: **http://localhost:8000/docs**
3. Try the endpoints:
   - Click "Try it out"
   - Fill in parameters
   - Click "Execute"
   - View response

---

## 📊 **TEST WITH SAMPLE DATA**

### **1. Upload a PDF**

```bash
curl -X POST http://localhost:8000/api/upload/pdf \
  -F "file=@/path/to/your/financial_report.pdf" \
  -F "company_id=SAMPLE_001" \
  -F "company_name=Sample Company" \
  -F "fiscal_year=2024-25"
```

### **2. Check Upload Status**

```bash
# Replace {upload_id} with the ID from upload response
curl http://localhost:8000/api/upload/status/{upload_id}
```

### **3. Query the Document**

```bash
# First create a session
curl -X POST http://localhost:8000/api/chat/session \
  -H "Content-Type: application/json" \
  -d '{"company_id": "SAMPLE_001", "company_name": "Sample Company"}'

# Then send query (replace {session_id})
curl -X POST http://localhost:8000/api/chat/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the total revenue?",
    "session_id": "{session_id}",
    "company_id": "SAMPLE_001",
    "top_k": 5
  }'
```

### **4. Submit Feedback**

```bash
# Replace {message_id} and {session_id}
curl -X POST http://localhost:8000/api/feedback/submit \
  -H "Content-Type: application/json" \
  -d '{
    "message_id": {message_id},
    "session_id": "{session_id}",
    "feedback_score": 1.0
  }'
```

---

## 🔍 **TROUBLESHOOTING**

### **Backend won't start**

❌ **Problem:** `ModuleNotFoundError: No module named 'fastapi'`
✅ **Solution:**
```bash
cd backend
pip install -r requirements.txt
```

❌ **Problem:** `psycopg2.OperationalError: connection refused`
✅ **Solution:**
```bash
# Check PostgreSQL is running
psql -U postgres -c "SELECT 1"

# Check database exists
psql -U postgres -l | grep financial_rag
```

❌ **Problem:** `ImportError: No module named 'query_engine'`
✅ **Solution:**
```bash
# Make sure UPDATED_ADV_RAG_SYS path is correct
cd UPDATED_ADV_RAG_SYS
pip install -r requirements.txt
cd ../chatbot_ui/backend
```

### **Frontend won't start**

❌ **Problem:** `Module not found: Can't resolve 'axios'`
✅ **Solution:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

❌ **Problem:** `Port 3000 is already in use`
✅ **Solution:**
```bash
# Use different port
PORT=3001 npm run dev

# Or kill process on port 3000
# Windows: netstat -ano | findstr :3000
# Linux/Mac: lsof -ti:3000 | xargs kill
```

---

## 📚 **NEXT STEPS**

1. ✅ Backend is ready - test it using Swagger UI
2. 🔨 Implement remaining frontend components (see `IMPLEMENTATION_GUIDE.md`)
3. 🎨 Customize the UI colors/theme
4. 🚀 Deploy to production

---

## 📖 **DOCUMENTATION**

- **README.md** - Complete setup guide
- **IMPLEMENTATION_GUIDE.md** - Frontend component templates
- **PROJECT_STATUS.md** - Progress tracking
- **API Docs** - http://localhost:8000/docs (when running)

---

## ⚡ **QUICK COMMANDS**

```bash
# Backend
cd backend && python main.py

# Frontend
cd frontend && npm run dev

# Database
psql -U postgres -d financial_rag

# Run migrations
psql -U postgres -d financial_rag -f backend/database/migrations.sql

# Check API health
curl http://localhost:8000/health

# View Swagger docs
open http://localhost:8000/docs  # Mac
start http://localhost:8000/docs  # Windows
xdg-open http://localhost:8000/docs  # Linux
```

---

**🎉 You're all set! The backend is fully functional and ready to use. Complete the frontend following the implementation guide to get the full chatbot UI!**
