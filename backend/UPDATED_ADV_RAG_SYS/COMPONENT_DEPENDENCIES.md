# COMPONENT DEPENDENCIES

This document shows the complete dependency tree for the RAG system.

---

## 📊 **DEPENDENCY TREE**

```
master_ingest_annual_report.py (MAIN INGESTION)
├── annual_report_processor.py (Orientation correction)
│   ├── fitz (PyMuPDF) - external
│   ├── cv2 (OpenCV) - external
│   └── docling (Document converter) - external
│
└── ingest_pdf.py (Ingestion pipeline)
    ├── adaptive_chunker.py (Chunking)
    ├── universal_classifier.py (Classification)
    ├── embedding_pipeline.py (BGE-M3 embeddings)
    │   └── sentence-transformers - external
    ├── vision_ocr.py (OCR for scanned pages)
    │   └── Ollama qwen2.5vl - external
    ├── section_context_detector.py (Section detection)
    └── deduplication_utils.py (Deduplication)


interactive_rag.py (MAIN INTERFACE)
├── query_engine.py (Query orchestration)
│   ├── hybrid_retrieval.py (3-tier retrieval)
│   │   ├── embedding_pipeline.py (shared)
│   │   ├── retrieval_types.py (data structures)
│   │   ├── deduplication_utils.py (shared)
│   │   └── psycopg2 - external
│   │
│   ├── llm_integration.py (LLM wrapper)
│   │   ├── Ollama phi4:14b - external
│   │   └── Ollama qwen2.5vl - external
│   │
│   └── section_context_detector.py (shared)
│
└── ingest_pdf.py (For ingestion option - shared)


test_financial_metrics.py (MAIN TESTING)
├── query_engine.py (Uses full query pipeline)
│   └── (all query dependencies above)
├── pandas - external
└── openpyxl - external


comprehensive_test_suite.py (TESTING)
└── query_engine.py (Uses full query pipeline)


check_progress.py (UTILITY)
└── psycopg2 - external


analyze_db_content.py (UTILITY)
└── psycopg2 - external


verify_tables.py (UTILITY)
└── psycopg2 - external


setup_database.py (SETUP)
└── psycopg2 - external
```

---

## 🔗 **SHARED COMPONENTS**

These files are used by multiple components:

1. **embedding_pipeline.py**
   - Used by: ingest_pdf.py, hybrid_retrieval.py
   - Purpose: BGE-M3 embeddings generation

2. **section_context_detector.py**
   - Used by: ingest_pdf.py, query_engine.py
   - Purpose: Section detection and query parsing

3. **deduplication_utils.py**
   - Used by: ingest_pdf.py, hybrid_retrieval.py
   - Purpose: Smart deduplication

4. **retrieval_types.py**
   - Used by: query_engine.py, hybrid_retrieval.py
   - Purpose: Data structures for retrieval

5. **ingest_pdf.py**
   - Used by: master_ingest_annual_report.py, interactive_rag.py
   - Purpose: PDF ingestion orchestration

6. **query_engine.py**
   - Used by: interactive_rag.py, test_financial_metrics.py, comprehensive_test_suite.py
   - Purpose: Main query interface

---

## 📦 **EXTERNAL DEPENDENCIES**

### **Python Packages**:
```
pdfplumber           # PDF text extraction
psycopg2-binary      # PostgreSQL connection
sentence-transformers # BGE-M3 embeddings
torch                # PyTorch for embeddings
numpy                # Numerical operations
requests             # HTTP requests to LLM
pandas               # Data manipulation (testing)
openpyxl             # Excel export (testing)
fitz (PyMuPDF)       # PDF manipulation
cv2 (opencv-python)  # Image processing
docling              # Document conversion
```

### **External Services**:
```
PostgreSQL 14+       # Database with pgvector
Ollama phi4:14b      # Text LLM
Ollama qwen2.5vl     # Vision LLM for OCR
```

---

## 🎯 **IMPORT RELATIONSHIPS**

### **master_ingest_annual_report.py imports**:
- annual_report_processor (AnnualReportProcessor, OrientationCorrector, Logger)
- ingest_pdf (PDFIngestionPipeline)

### **ingest_pdf.py imports**:
- universal_classifier (UniversalClassifier)
- adaptive_chunker (AdaptiveChunker, Chunk)
- embedding_pipeline (BGE_M3_EmbeddingPipeline)
- vision_ocr (VisionOCR)
- section_context_detector (SectionContextDetector)

### **query_engine.py imports**:
- hybrid_retrieval (HybridRetrievalEngine)
- retrieval_types (RetrievalResult)
- llm_integration (DualLLMSystem, format_chunks_for_llm)
- section_context_detector (extract_statement_type_from_query, extract_note_number_from_query)

### **hybrid_retrieval.py imports**:
- embedding_pipeline (BGE_M3_EmbeddingPipeline)
- retrieval_types (RetrievalResult)
- deduplication_utils (smart_deduplicate)

### **interactive_rag.py imports**:
- query_engine (FinancialRAGV2)
- ingest_pdf (PDFIngestionPipeline)

### **test_financial_metrics.py imports**:
- query_engine (FinancialRAGV2)

---

## 🔄 **EXECUTION FLOWS**

### **INGESTION FLOW**:
```
User → master_ingest_annual_report.py
     → annual_report_processor.py (orientation correction)
     → ingest_pdf.py (orchestrator)
        → adaptive_chunker.py (chunking)
        → universal_classifier.py (classification)
        → section_context_detector.py (section detection)
        → embedding_pipeline.py (embeddings)
        → vision_ocr.py (OCR if needed)
        → deduplication_utils.py (dedup)
        → PostgreSQL (storage)
```

### **QUERY FLOW**:
```
User → interactive_rag.py
     → query_engine.py (orchestrator)
        → section_context_detector.py (parse query)
        → hybrid_retrieval.py (retrieval)
           → embedding_pipeline.py (query embedding)
           → retrieval_types.py (data structures)
           → deduplication_utils.py (dedup results)
           → PostgreSQL (search)
        → llm_integration.py (answer extraction)
           → Ollama phi4:14b (LLM)
     → User (answer + sources)
```

### **TESTING FLOW**:
```
User → test_financial_metrics.py
     → query_engine.py (for each question)
        → (full query pipeline)
     → pandas (aggregate results)
     → Excel export (results file)
```

---

## 📋 **FILE INTERDEPENDENCIES**

### **Self-Contained (No Internal Dependencies)**:
- retrieval_types.py
- deduplication_utils.py
- schema.sql

### **Low Dependencies (1-2 internal imports)**:
- annual_report_processor.py (standalone)
- vision_ocr.py (standalone)
- embedding_pipeline.py (standalone)
- adaptive_chunker.py (standalone)
- universal_classifier.py (standalone)
- section_context_detector.py (standalone)

### **Medium Dependencies (3-5 internal imports)**:
- llm_integration.py (2 imports)
- hybrid_retrieval.py (3 imports)

### **High Dependencies (5+ internal imports)**:
- ingest_pdf.py (6 imports)
- query_engine.py (4 imports)
- interactive_rag.py (2 imports)
- master_ingest_annual_report.py (2 imports)

---

## 🎯 **USAGE PATTERNS**

### **For Ingestion Only**:
Minimum required files:
```
master_ingest_annual_report.py
annual_report_processor.py
ingest_pdf.py
adaptive_chunker.py
universal_classifier.py
section_context_detector.py
embedding_pipeline.py
vision_ocr.py
deduplication_utils.py
schema.sql
setup_database.py
```

### **For Querying Only**:
Minimum required files:
```
interactive_rag.py (or direct use of query_engine.py)
query_engine.py
hybrid_retrieval.py
llm_integration.py
retrieval_types.py
embedding_pipeline.py
section_context_detector.py
deduplication_utils.py
```

### **For Complete System**:
All 21 files required for full functionality.

---

## 🔧 **CONFIGURATION POINTS**

### **Database Configuration**:
Files that need database config:
- ingest_pdf.py
- query_engine.py
- hybrid_retrieval.py
- interactive_rag.py
- master_ingest_annual_report.py
- setup_database.py
- All testing/utility files

**Default Config**:
```python
{
    'host': 'localhost',
    'database': 'financial_rag',
    'user': 'postgres',
    'password': 'Prasanna!@#2002'
}
```

### **LLM Configuration**:
Files that need LLM endpoints:
- llm_integration.py
- vision_ocr.py

**Default Endpoints**:
```python
text_llm_endpoint = "http://10.100.20.76:11434/v1/chat/completions"
text_llm_model = "phi4:14b"
vision_llm_endpoint = "http://10.100.20.76:11434/api/generate"
vision_llm_model = "qwen2.5vl:latest"
```

---

## ✅ **DEPENDENCY VERIFICATION**

To verify all dependencies are met:

```bash
# Python packages
pip list | grep pdfplumber
pip list | grep psycopg2
pip list | grep sentence-transformers
pip list | grep torch
pip list | grep opencv-python
pip list | grep pandas
pip list | grep openpyxl

# PostgreSQL
psql --version
psql -U postgres -c "SELECT * FROM pg_extension WHERE extname='vector';"

# Ollama models
ollama list | grep phi4
ollama list | grep qwen2.5vl
```

---

**Created**: December 2024
**Purpose**: Component dependency documentation
**Audience**: Developers, system administrators
