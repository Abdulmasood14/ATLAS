# ✅ Sector Detection & Question Fixes

## Issues Fixed:

### 1. Database Column Error ✅
**Error**: `column "section_types" does not exist`
**Cause**: Query was using wrong table name `document_chunks` instead of `document_chunks_v2`

**Fix Applied**:
```python
# BEFORE (Line 129):
FROM document_chunks

# AFTER (Line 130):
FROM document_chunks_v2
```

Also removed `section_types` from SELECT since it's not needed for sector detection.

---

### 2. Laurus Labs Misclassified ✅
**Issue**: Laurus Labs (Pharma company) detected as "General"
**Cause**: Not enough pharma-specific keywords

**Fix Applied**:
```python
# Enhanced Pharmaceuticals keywords (Lines 40-47):
"Pharmaceuticals": [
    "drug", "pharmaceutical", "clinical", "FDA", "medicine", "R&D",
    "trials", "therapy", "biotech", "patent", "prescription",
    "dosage", "treatment", "diagnosis", "regulatory approval",
    # NEW KEYWORDS:
    "USFDA", "API", "formulation", "generic", "molecule", "ANDA",
    "DCGI", "oncology", "diabetes", "cardiovascular", "antibiotic",
    "vaccine", "biologics", "clinical trial", "drug approval"
]
```

---

### 3. Sector Questions Not Specific Enough ✅
**Issue**: Pharma sector showing generic questions, not industry-specific

**Fix Applied**:

#### Pharmaceuticals (10 questions now):
**BEFORE** (Generic):
1. "What is the R&D spending on new drug development?"
2. "What is the current drug pipeline status?"
3. ...

**AFTER** (Industry-Specific):
1. "What USFDA and regulatory approvals were received this year?"
2. "What is the current drug pipeline and ANDA filing status?"
3. "What are the key therapeutic areas and API manufacturing capabilities?"
4. "What R&D investments and formulation development initiatives exist?"
5. "What clinical trial activities and regulatory compliance measures are ongoing?"
6. "What is the generic vs branded drug revenue mix?"
7. "What contract manufacturing (CDMO) partnerships and collaborations exist?"
8. "What quality certifications (WHO-GMP, USFDA, EMA) does the company hold?"
9. "What patent challenges or exclusivity opportunities exist?"
10. "What biosimilar and oncology drug development programs are underway?"

#### Healthcare (10 questions now):
**Enhanced with specific metrics**:
1. "What is the bed occupancy rate across all facilities?"
2. "What are the Average Revenue Per Occupied Bed (ARPOB) metrics?"
3. "What medical specialties and Centers of Excellence does the company operate?"
4. "What is the doctor-to-bed ratio and staffing metrics?"
5. "What diagnostic and medical equipment investments were made?"
6. "What telemedicine and digital health initiatives exist?"
7. "What hospital accreditations (NABH, JCI, NABL) are held?"
8. "What expansion plans for new hospitals or bed additions exist?"
9. "What is the insurance vs cash patient revenue mix?"
10. "What international patient programs and medical tourism initiatives exist?"

---

## All Sector Questions Enhanced:

Each sector now has 8-10 highly specific questions:

### Pharmaceuticals (10 questions)
- USFDA approvals, ANDA filings, API manufacturing
- Clinical trials, regulatory compliance
- CDMO partnerships, quality certifications
- Patent challenges, biosimilar programs

### Healthcare (10 questions)
- Bed occupancy rates, ARPOB metrics
- Doctor-to-bed ratio, staffing
- Accreditations (NABH, JCI, NABL)
- Medical tourism, Centers of Excellence

### Technology (8 questions)
- ARR, CAC, LTV metrics
- Cloud infrastructure, AI/ML
- Cybersecurity, R&D investments

### Manufacturing (8 questions)
- Capacity utilization, automation
- Supply chain, quality certifications
- Inventory turnover, capex

### FMCG (8 questions)
- Distribution network, product launches
- Market share, brand portfolio
- E-commerce, rural vs urban sales

### Finance (8 questions)
- NIM, NPA ratio, capital adequacy
- Digital banking, fintech partnerships
- Loan-to-deposit ratio, compliance

### Construction (8 questions)
- Project pipeline, order book
- Land bank, project financing
- Infrastructure projects, technologies

### Energy (8 questions)
- Installed capacity, PLF
- Renewable investments, coal/gas linkage
- Environmental compliance, expansion

### Food & Beverage (8 questions)
- Raw material sourcing, certifications
- Cold chain, packaging innovations
- Export markets, sustainability

### Telecommunications (8 questions)
- Subscriber growth, ARPU
- 5G rollout, spectrum holdings
- Churn rate, digital services

### Automotive (8 questions)
- Production volume, EV plans
- Market share, supplier partnerships
- R&D, autonomous driving

### Textiles (8 questions)
- Spinning/weaving capacity
- Export vs domestic sales
- Sustainability certifications

---

## Testing Instructions

### 1. Restart Backend (REQUIRED)
```bash
cd D:\Objective and Subjective\Objective and Subjective\New folder\FINAL\chatbot_ui\backend
py -3.11 main.py
```

### 2. Test Laurus Labs
1. Select "Laurus Labs Ltd" company
2. Click "Deep Dive" tab
3. **Expected**:
   - ✅ Detected Sector: **Pharmaceuticals** (not "General")
   - ✅ Sector-Specific Questions show pharma-focused questions:
     - "What USFDA and regulatory approvals..."
     - "What is the current drug pipeline and ANDA filing status..."
     - "What quality certifications (WHO-GMP, USFDA, EMA)..."
   - ✅ No errors in backend logs

### 3. Verify Backend Logs
**Should see**:
```
INFO - Generating questions for Laurus Labs Ltd (L_Lll_111ABS)
INFO - Detected sector for L_Lll_111ABS: Pharmaceuticals (score: XX)
INFO - Generated questions for Laurus Labs Ltd: Pharmaceuticals sector
INFO - Successfully generated questions for Laurus Labs Ltd
```

**Should NOT see**:
```
ERROR - Error fetching sample chunks: column "section_types" does not exist
WARNING - No chunks found for company L_Lll_111ABS
INFO - Generated questions for Laurus Labs Ltd: General sector
```

---

## Files Modified

| File | Lines | Change |
|------|-------|--------|
| `backend/services/question_generator.py` | 40-47 | Added pharma-specific keywords (USFDA, API, ANDA, etc.) |
| `backend/services/question_generator.py` | 129-134 | Fixed table name: `document_chunks_v2` |
| `backend/services/question_generator.py` | 171-182 | Enhanced Pharma questions (10 questions) |
| `backend/services/question_generator.py` | 233-244 | Enhanced Healthcare questions (10 questions) |

---

## Summary

✅ **Database error fixed** - Using correct table `document_chunks_v2`
✅ **Pharma detection improved** - Added USFDA, API, ANDA keywords
✅ **Pharma questions enhanced** - 10 industry-specific questions
✅ **Healthcare questions enhanced** - 10 questions with ARPOB, bed occupancy, NABH/JCI
✅ **All sectors have unique questions** - Each sector has 8-10 tailored questions

**Result**: Laurus Labs should now be correctly classified as "Pharmaceuticals" with relevant pharma-specific questions! 🎉
