# 🚀 ATLAS - Advanced Financial RAG Analysis System

**Version**: 2.0
**Last Updated**: January 7, 2026
**Built with**: Next.js 15, FastAPI, PostgreSQL, Ollama

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Key Features](#key-features)
4. [Technology Stack](#technology-stack)
5. [Prerequisites](#prerequisites)
6. [Installation Guide](#installation-guide)
7. [Configuration](#configuration)
8. [Usage Guide](#usage-guide)
9. [API Documentation](#api-documentation)
10. [Troubleshooting](#troubleshooting)
11. [Project Structure](#project-structure)

---

## 🎯 Overview

**ATLAS** (Advanced Technology for Learning and Analysis System) is a comprehensive financial document analysis platform powered by Retrieval-Augmented Generation (RAG) technology. It enables intelligent querying of annual reports, financial statements, and corporate documents using natural language processing.

### What ATLAS Does:

- 📄 **Document Processing**: Upload and process annual reports (PDF format)
- 💬 **Intelligent Chat**: Ask questions about financial documents in natural language
- 📊 **Analytics Dashboard**: Visual insights including sector detection, fiscal year analysis, and document statistics
- 🔍 **Deep Dive Analysis**: Multi-perspective financial analysis with 6 parallel queries
- 📖 **Story Generation**: Comprehensive investment narratives with milestones and recommendations
- 🎨 **Modern UI**: Clean, professional interface with custom color palette (#1762C7, #1FA8A6)

### Key Differentiators:

- ✅ **Adaptive Chunking**: Smart document chunking based on content structure
- ✅ **Vector Search**: pgvector-powered semantic search
- ✅ **Parallel Processing**: Multiple concurrent RAG queries for comprehensive analysis
- ✅ **Caching System**: Fast tab switching with intelligent data caching
- ✅ **Collapsible UI**: User-friendly expandable sections
- ✅ **Real-time Streaming**: WebSocket-based response streaming

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js 15)                │
│  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐  │
│  │  Chat   │  │ Analysis │  │ Deep Dive│  │   Story    │  │
│  └─────────┘  └──────────┘  └──────────┘  └────────────┘  │
│         React Components + TailwindCSS                      │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP/WebSocket
┌──────────────────────────┴──────────────────────────────────┐
│                    BACKEND (FastAPI)                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  API Routers:                                        │  │
│  │  • chat.py      - Chat interface & streaming        │  │
│  │  • upload.py    - Document upload & processing      │  │
│  │  • analytics.py - Statistics & sector detection     │  │
│  │  • deep_dive.py - Multi-perspective analysis        │  │
│  │  • story.py     - Investment story generation       │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  RAG Engine (UPDATED_ADV_RAG_SYS):                  │  │
│  │  • adaptive_chunker.py - Smart chunking             │  │
│  │  • llm_integration.py  - LLM interface              │  │
│  │  • rag_system.py       - Vector search              │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────┐
│                    DATA LAYER                               │
│  ┌─────────────────┐    ┌─────────────────┐               │
│  │  PostgreSQL     │    │  Ollama         │               │
│  │  + pgvector     │    │  (phi4:14b)     │               │
│  │                 │    │                 │               │
│  │  • Companies    │    │  LLM Inference  │               │
│  │  • Documents    │    │  Text Generation│               │
│  │  • Chunks       │    │                 │               │
│  │  • Embeddings   │    │                 │               │
│  └─────────────────┘    └─────────────────┘               │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow:

1. **Document Upload**: PDF → Text Extraction → Adaptive Chunking → Embeddings → PostgreSQL
2. **Query Processing**: User Query → Embedding → Vector Search → Context Retrieval → LLM → Response
3. **Story Generation**: 6 Parallel Queries → Milestone Extraction → Investment Recommendation
4. **Caching**: API Response → Frontend Cache → Instant Retrieval on Tab Switch

---

## ✨ Key Features

### 1. 💬 **Intelligent Chat Interface**
- Natural language querying of financial documents
- Conversational responses with context awareness
- Real-time streaming with WebSocket support
- Source attribution with page numbers
- Session-based conversation history

### 2. 📊 **Analytics Dashboard**
- **Sector Detection**: Automatic industry classification
- **Fiscal Year Detection**: Smart date range extraction
- **Document Statistics**: Page count, chunk count, upload date
- **Visual Insights**: Clean, professional data visualization

### 3. 🔍 **Deep Dive Analysis**
- **6 Parallel Queries**: Comprehensive multi-perspective analysis
  1. Financial Performance & KPIs
  2. Business Model & Revenue Streams
  3. Market Position & Competitive Advantages
  4. Risk Analysis & Challenges
  5. Growth Strategy & Future Plans
  6. Management Quality & Governance
- **Streaming Results**: Real-time updates as queries complete
- **Export Functionality**: Download analysis as formatted document

### 4. 📖 **Story Tab** (Investment Narrative)
- **7 Collapsible Sections**:
  1. Investment Recommendation (BUY/SELL/HOLD)
  2. Business Overview
  3. Financial Performance
  4. Competitive Position
  5. Risk Factors
  6. Growth Strategy
  7. Corporate Governance & Management
- **Strategic Milestones**: Visual roadmap with timeline
- **Smart Caching**: No reloading when switching tabs
- **Expandable Cards**: Collapsible sections for better UX

### 5. 📁 **Document Management**
- **PDF Upload**: Drag-and-drop or click to upload
- **Progress Tracking**: Real-time upload and processing status
- **Multi-Company Support**: Manage multiple companies
- **Document Versioning**: Track fiscal years

### 6. 🎨 **Modern UI/UX**
- **Custom Color Palette**: #1762C7 (primary blue), #1FA8A6 (accent teal)
- **Responsive Design**: Works on desktop, tablet, mobile
- **Professional Gradients**: Clean gradient backgrounds
- **Smooth Animations**: Tailwind CSS transitions
- **Icon Integration**: Lucide React icons

---

## 🛠️ Technology Stack

### Frontend
- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript
- **UI Library**: React 18
- **Styling**: TailwindCSS
- **Markdown**: react-markdown + remark-gfm
- **Icons**: Lucide React
- **HTTP Client**: Fetch API
- **WebSocket**: Native WebSocket API

### Backend
- **Framework**: FastAPI (Python 3.11)
- **ASGI Server**: Uvicorn
- **Database**: PostgreSQL 16+
- **Vector Extension**: pgvector
- **ORM**: psycopg2
- **PDF Processing**: PyMuPDF (fitz)
- **Embeddings**: Ollama embeddings (nomic-embed-text)
- **LLM**: Ollama (phi4:14b)

### Infrastructure
- **Database**: PostgreSQL with pgvector extension
- **LLM Server**: Ollama (local inference)
- **Environment**: Python venv + Node.js

---

## 📋 Prerequisites

Before installing ATLAS, ensure you have the following installed:

### Required Software:

1. **Python 3.11+**
   - Download: https://www.python.org/downloads/
   - Verify: `python --version` or `py -3.11 --version`

2. **Node.js 18+**
   - Download: https://nodejs.org/
   - Verify: `node --version`

3. **PostgreSQL 16+**
   - Download: https://www.postgresql.org/download/
   - Install pgvector extension
   - Verify: `psql --version`

4. **Ollama**
   - Download: https://ollama.ai/
   - Install models:
     ```bash
     ollama pull phi4:14b
     ollama pull nomic-embed-text
     ```
   - Verify: `ollama list`

### System Requirements:

- **RAM**: 16GB minimum (32GB recommended for LLM inference)
- **Storage**: 20GB free space
- **GPU**: Optional (CUDA-compatible GPU accelerates Ollama)
- **OS**: Windows 10/11, macOS, Linux

---

## 🚀 Installation Guide

### Step 1: Extract ATLAS

```bash
# Extract the ATLAS.zip file
unzip ATLAS.zip
cd ATLAS
```

### Step 2: Database Setup

```bash
# 1. Start PostgreSQL service
# Windows: Services → PostgreSQL → Start
# macOS: brew services start postgresql
# Linux: sudo systemctl start postgresql

# 2. Create database and user
psql -U postgres

CREATE DATABASE financial_rag;
CREATE USER rag_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE financial_rag TO rag_user;

# 3. Enable pgvector extension
\c financial_rag
CREATE EXTENSION vector;
\q

# 4. Run database initialization script
cd backend
python setup_database.py
```

### Step 3: Backend Setup

```bash
cd backend

# 1. Create virtual environment
python -m venv venv

# 2. Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
# Edit .env file with your database credentials
DATABASE_URL=postgresql://rag_user:your_secure_password@localhost:5432/financial_rag
OLLAMA_BASE_URL=http://localhost:11434

# 5. Verify database connection
python verify_tables.py
```

### Step 4: Frontend Setup

```bash
cd frontend

# 1. Install dependencies
npm install

# 2. Configure environment (optional)
# Create .env.local if you need custom API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# 3. Build frontend (optional, for production)
npm run build
```

### Step 5: Start Ollama

```bash
# Start Ollama server (in a separate terminal)
ollama serve

# Verify models are available
ollama list
# Should show: phi4:14b, nomic-embed-text
```

### Step 6: Start ATLAS

```bash
# Terminal 1: Start Backend
cd backend
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux
python main.py
# Backend runs at: http://localhost:8000

# Terminal 2: Start Frontend
cd frontend
npm run dev
# Frontend runs at: http://localhost:3000
```

### Step 7: Access ATLAS

Open your browser and navigate to:
```
http://localhost:3000
```

---

## ⚙️ Configuration

### Backend Configuration (`backend/.env`)

```env
# Database Configuration
DATABASE_URL=postgresql://rag_user:password@localhost:5432/financial_rag

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
EMBEDDING_MODEL=nomic-embed-text
LLM_MODEL=phi4:14b

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=["http://localhost:3000"]

# RAG Configuration
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K_RESULTS=10
TEMPERATURE=0.7
```

### Frontend Configuration (`frontend/.env.local`)

```env
# API Base URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# WebSocket URL
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

---

## 📖 Usage Guide

### 1. Upload a Document

1. Click **"Upload Document"** button in sidebar
2. **Drag and drop** a PDF or click to browse
3. Enter **Company Name** and **Fiscal Year**
4. Click **"Upload and Process"**
5. Wait for processing (progress bar shows status)
6. Document appears in company list when complete

### 2. Start Chatting

1. **Select a company** from the sidebar
2. Type your question in the input box
3. Press **Enter** or click **Send**
4. View the AI response with sources
5. Continue conversational follow-ups

**Example Questions**:
- "What was the revenue growth in FY2025?"
- "Summarize the key risks mentioned in the annual report"
- "What are the company's expansion plans?"
- "Compare this year's performance with last year"

### 3. View Analytics

1. Select a company
2. Click **"Analysis"** tab
3. View:
   - **Sector**: Auto-detected industry classification
   - **Fiscal Year**: Extracted date range
   - **Document Stats**: Pages, chunks, upload date
4. Explore visual insights

### 4. Generate Deep Dive Analysis

1. Select a company
2. Click **"Deep Dive"** tab
3. Click **"Generate Deep Dive Analysis"**
4. Watch as 6 parallel queries stream results
5. Click **"Export Analysis"** to download

### 5. Create Investment Story

1. Select a company
2. Click **"Story"** tab
3. Wait for comprehensive analysis
4. View **BUY/SELL/HOLD** verdict
5. **Expand/collapse sections** using chevron icons
6. Explore **Strategic Milestones** roadmap
7. Click **"Read more"** on long milestone descriptions

### 6. Smart Caching

- Story data is **cached** after first load
- Switch to **Chat** or **Analysis** tab
- Return to **Story** tab → **Instant load** (no waiting!)
- Cache persists per company

---

## 📁 Project Structure

```
ATLAS/
├── README.md                          # This file
├── backend/                          # FastAPI Backend
│   ├── main.py                       # Main application entry
│   ├── requirements.txt              # Python dependencies
│   ├── setup_database.py             # Database initialization
│   ├── api/                          # API Routers
│   │   ├── chat.py                   # Chat interface
│   │   ├── upload.py                 # Document upload
│   │   ├── analytics.py              # Analytics endpoints
│   │   ├── deep_dive.py              # Deep dive analysis
│   │   └── story.py                  # Story generation
│   └── UPDATED_ADV_RAG_SYS/          # RAG Engine
│       ├── rag_system.py             # Main RAG class
│       ├── llm_integration.py        # LLM interface
│       └── adaptive_chunker.py       # Smart chunking
│
├── frontend/                         # Next.js Frontend
│   ├── package.json                  # Node dependencies
│   ├── src/
│   │   ├── app/
│   │   │   └── page.tsx              # Main page component
│   │   ├── components/               # React Components
│   │   │   ├── ChatWindow.tsx        # Chat interface
│   │   │   ├── AnalysisTab.tsx       # Analytics view
│   │   │   ├── DeepDiveTab.tsx       # Deep dive view
│   │   │   └── StoryTab.tsx          # Story view
│   │   └── services/
│   │       └── api.ts                # API client
│   └── public/                       # Static assets
│
└── documentation/                    # Additional docs
    ├── STORY_CACHING_AND_COLLAPSIBLE.md
    ├── STORY_FINAL_FIXES.md
    └── CHANGES_SUMMARY.md
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. **Database Connection Failed**
```bash
# Check if PostgreSQL is running
# Verify credentials in backend/.env
psql -U rag_user -d financial_rag
```

#### 2. **Ollama Not Found**
```bash
# Start Ollama server
ollama serve

# Verify models
ollama list
```

#### 3. **Frontend Can't Connect to Backend**
```bash
# Verify backend is running
curl http://localhost:8000/health

# Check CORS settings in backend/main.py
```

#### 4. **Story Tab Shows Error**
```bash
# Check backend logs for failed sections
# Try the Retry button
# Verify Ollama is responding
```

---

## 🎓 Quick Start Checklist

- [ ] Install Python 3.11+
- [ ] Install Node.js 18+
- [ ] Install PostgreSQL 16+
- [ ] Install Ollama + models
- [ ] Extract ATLAS.zip
- [ ] Setup database
- [ ] Configure backend (.env)
- [ ] Install backend dependencies
- [ ] Install frontend dependencies
- [ ] Start Ollama server
- [ ] Start backend (python main.py)
- [ ] Start frontend (npm run dev)
- [ ] Access http://localhost:3000
- [ ] Upload first document
- [ ] Start chatting!

---

**Built with ❤️ by the ATLAS Team**

*Version 2.0 - January 2026*
