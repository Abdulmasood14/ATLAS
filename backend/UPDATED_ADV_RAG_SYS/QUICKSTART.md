# QUICKSTART GUIDE

Get the RAG system up and running in 15 minutes!

---

## ⚡ **5-STEP SETUP**

### **STEP 1: Install Python Dependencies (2 minutes)**

```bash
cd UPDATED_ADV_RAG_SYS

# Install all requirements
pip install -r requirements.txt
```

---

### **STEP 2: Setup PostgreSQL Database (3 minutes)**

```bash
# Create database
psql -U postgres -c "CREATE DATABASE financial_rag;"

# Install pgvector extension
psql -U postgres -d financial_rag -c "CREATE EXTENSION vector;"

# Run schema
psql -U postgres -d financial_rag -f schema.sql

# OR use Python script
python setup_database.py
```

**Verify**:
```bash
python verify_tables.py
# Should show: "✓ All tables exist"
```

---

### **STEP 3: Setup Ollama Models (5 minutes)**

```bash
# Install Ollama (if not already installed)
# Visit: https://ollama.ai

# Pull phi4:14b model (for text extraction)
ollama pull phi4:14b

# Pull qwen2.5vl model (for vision OCR)
ollama pull qwen2.5vl:latest

# Verify
ollama list
# Should show both models
```

---

### **STEP 4: Ingest Your First PDF (5 minutes)**

```bash
# Example: Ingest annual report
python master_ingest_annual_report.py \
  "path/to/your/annual_report.pdf" \
  "COMPANY_001" \
  --company_name "Your Company Name" \
  --fiscal_year "2024-25"
```

**What you'll see**:
```
================================================================================
                    MASTER ANNUAL REPORT INGESTION PIPELINE
================================================================================

STAGE 1: ORIENTATION DETECTION & CORRECTION
✓ Detected 12 rotated pages
✓ Corrected and saved to corrected_pdfs/

STAGE 2: INGESTION INTO RAG SYSTEM
✓ Extracted 200 pages
✓ Created 280 chunks
✓ Classified 280 chunks
✓ Generated embeddings
✓ Stored in PostgreSQL

Status: SUCCESS
```

**Check progress**:
```bash
python check_progress.py
# Should show chunk counts and note numbers
```

---

### **STEP 5: Query the System (Now!)**

```bash
# Interactive mode
python interactive_rag.py
```

**Menu options**:
```
1. Ingest new PDF
2. Query existing company
3. List available companies
4. Exit

Select option (1-4): 2
```

**Or use Python directly**:
```python
from query_engine import FinancialRAGV2

rag = FinancialRAGV2()

# Ask a question
response = rag.query(
    "What is the Fair Value of Investment Properties?",
    company_id="COMPANY_001",
    top_k=7
)

print(response.answer)
# Output: The fair value of investment properties as at March 31, 2025...

rag.close()
```

---

## 🧪 **TEST THE SYSTEM**

### **Quick Test**:

```bash
# Run comprehensive test suite
python test_financial_metrics.py
```

This will:
- Test 23 questions per company
- Export results to Excel
- Show pass rates and performance metrics

**Expected output**:
```
================================================================================
FINANCIAL METRICS TEST SUITE - BASED ON QUESTIONS.TXT
================================================================================

TESTING: COMPANY_001
[1/6] Revenue growth rate... SUCCESS (2.3s)
[2/6] Profit margins trend... SUCCESS (2.1s)
...

FINAL SUMMARY
COMPANY_001: 20/23 passed (87.0%)
```

---

## 📋 **EXAMPLE QUERIES**

### **Objective Queries** (Numbers & Facts):

```python
# Fair Value
"What is the Fair Value of Investment Properties?"

# Financial Ratios
"What is the debt-to-equity ratio and interest coverage ratio?"

# Revenue
"What is the revenue growth rate over the past 3 years?"

# Note-Specific
"What is Note 10 about in Consolidated Financial Statement?"
```

### **Subjective Queries** (Policies & Explanations):

```python
# Accounting Policy
"How is fair value of investment properties determined?"

# Revenue Recognition
"What is the accounting policy for revenue recognition?"

# Risk Factors
"What are the major risk factors disclosed by the company?"

# Assumptions
"What assumptions are used in the provision matrix for trade receivables?"
```

### **Section-Aware Queries**:

```python
# Consolidated vs Standalone
"What is Note 9 about in Standalone Financial Statement?"
"What is Note 10 about in Consolidated Financial Statement?"

# Specific Sections
"What is the total revenue from operations in Consolidated Profit & Loss?"
```

---

## 🔧 **CONFIGURATION**

### **Update Database Password**:

Edit these files if your PostgreSQL password is different:
- `master_ingest_annual_report.py` (line 76)
- `query_engine.py` (line 58)
- `interactive_rag.py` (line ~30)
- All test files

Change:
```python
'password': 'Prasanna!@#2002'  # ← Update this
```

### **Update LLM Endpoint**:

If your Ollama is running on a different host, edit:
- `llm_integration.py` (line 41-42)
- `vision_ocr.py` (line ~30)

Change:
```python
text_llm_endpoint = "http://YOUR_HOST:11434/v1/chat/completions"
```

---

## 📊 **VERIFY INSTALLATION**

### **1. Check Database**:
```bash
python verify_tables.py
# Expected: ✓ All tables exist
```

### **2. Check Ingestion**:
```bash
python check_progress.py
# Expected: Shows chunk count, statement types, note numbers
```

### **3. Check Models**:
```bash
ollama list
# Expected: Shows phi4:14b and qwen2.5vl
```

### **4. Test Query**:
```python
from query_engine import FinancialRAGV2
rag = FinancialRAGV2()
print("✓ System ready!")
rag.close()
```

---

## 🚨 **TROUBLESHOOTING**

### **Problem: Database connection error**

```bash
# Check PostgreSQL is running
pg_ctl status

# Start if needed
pg_ctl start

# Check password
psql -U postgres -d financial_rag
```

### **Problem: LLM endpoint not accessible**

```bash
# Check Ollama is running
ollama list

# Start Ollama server
ollama serve
```

### **Problem: Import errors**

```bash
# Reinstall requirements
pip install -r requirements.txt --force-reinstall
```

### **Problem: No results for queries**

```bash
# Check if data is ingested
python check_progress.py

# Re-ingest if needed
python master_ingest_annual_report.py <pdf> <company_id>
```

---

## 📈 **EXPECTED PERFORMANCE**

After successful setup:

| Metric | Expected Value |
|--------|---------------|
| Ingestion Time | 5-10 minutes per 200-page PDF |
| Query Response Time | 2-5 seconds |
| Note Detection | 15-30 notes per annual report |
| Consolidated Chunks | 35-45% of total chunks |
| Test Pass Rate | 85-100% |

---

## 🎯 **NEXT STEPS**

1. ✅ **Ingest More PDFs**: Add more companies to the database
2. ✅ **Run Tests**: Use `test_financial_metrics.py` for comprehensive testing
3. ✅ **Customize Queries**: Add your own questions to test suite
4. ✅ **Export Data**: Use trade receivables extractors for Excel export
5. ✅ **Monitor Performance**: Use `analyze_db_content.py` for diagnostics

---

## 📚 **DOCUMENTATION**

For more details:
- `README.md` - Complete system overview
- `COMPONENT_DEPENDENCIES.md` - Dependency tree
- Parent FINAL folder - Detailed technical documentation

---

## 💡 **TIPS**

1. **Start Small**: Test with 1-2 PDFs first
2. **Check Progress**: Use `check_progress.py` after each ingestion
3. **Verify Results**: Run test suite to ensure accuracy
4. **Use Verbose Mode**: Add `verbose=True` to queries for debugging
5. **Monitor Logs**: Watch terminal output during ingestion

---

**You're all set! 🎉**

Your RAG system is now ready to process financial documents and answer questions with high accuracy.

---

**Questions?**
- Check `README.md` for detailed documentation
- Run diagnostic tools: `check_progress.py`, `analyze_db_content.py`
- Review test results from `test_financial_metrics.py`
