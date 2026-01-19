# 🎯 Deep Dive Tab Implementation Plan

## Overview
Create a new "Deep Dive" tab with AI-generated questions in 3 categories + Fix Analytics tab caching

---

## Issue 1: Analytics Tab Reloading ✅ TO FIX

### Problem:
```typescript
// Current behavior in AnalysisTab.tsx line 191-195:
useEffect(() => {
  if (companyId && companyName) {
    loadAnalytics();  // ❌ Reloads every time tab switches
  }
}, [companyId, companyName, tickerSymbol]);
```

**What happens**:
1. User clicks "Analysis" tab → Data loads
2. User switches to "Chat" tab
3. User clicks "Analysis" tab again → **Data reloads from scratch!**

### Solution:
**Move analytics data state UP to page.tsx** (parent component)

**Why this works**:
- `page.tsx` doesn't unmount when switching tabs
- Data persists across tab switches
- Only reloads when company actually changes

**Changes Required**:
1. **File**: `frontend/src/app/page.tsx`
   - Add state: `const [analyticsData, setAnalyticsData] = useState(null)`
   - Add state: `const [analyticsLoading, setAnalyticsLoading] = useState(false)`
   - Pass as props to `AnalysisTab`

2. **File**: `frontend/src/components/AnalysisTab.tsx`
   - Receive `analyticsData` and `analyticsLoading` as props
   - Only fetch if `analyticsData === null`
   - Lift state up to parent

---

## Issue 2: New "Deep Dive" Tab ✅ TO CREATE

### Tab Name: **"Deep Dive"** (suggested) or **"Insights"** or **"Q&A Hub"**

### Structure:
```
┌─────────────────────────────────────────┐
│ Deep Dive                               │
├─────────────────────────────────────────┤
│ 📋 General Questions                    │
│ ┌─────────────────────────────────────┐ │
│ │ • What is the company's revenue?   │ │ ← Click to get answer
│ │ • What are the main products?      │ │
│ │ • Financial performance summary?   │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ 🏭 Sector-Specific (Pharma)            │ ← Auto-detected
│ ┌─────────────────────────────────────┐ │
│ │ • R&D spending on new drugs?       │ │
│ │ • Drug pipeline status?            │ │
│ │ • Regulatory approvals?            │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ 💼 Business-Specific                   │
│ ┌─────────────────────────────────────┐ │
│ │ • Key competitive advantages?      │ │
│ │ • Market share analysis?           │ │
│ │ • Strategic partnerships?          │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

### Interaction Flow:
1. User selects company
2. User clicks "Deep Dive" tab
3. Backend generates 3 sets of questions (General, Sector, Business)
4. Questions displayed as clickable cards
5. User clicks question → Answer loads below with smooth animation
6. Answer is comprehensive (like normal RAG chat)

---

## Backend Implementation

### New Endpoint: `/api/deep-dive/generate-questions`

**Request**:
```json
{
  "company_id": "KEMP_111",
  "company_name": "KEMP & Company LTD"
}
```

**Response**:
```json
{
  "company_id": "KEMP_111",
  "company_name": "KEMP & Company LTD",
  "detected_sector": "Manufacturing",
  "questions": {
    "general": [
      "What is the company's total revenue for the fiscal year?",
      "What are the main products or services offered?",
      "What is the profit margin?",
      "What are the key financial highlights?",
      "What is the company's market position?"
    ],
    "sector_specific": [
      "What is the production capacity utilization?",
      "What are the raw material costs and trends?",
      "What is the supply chain efficiency?",
      "What automation initiatives are in place?",
      "What sustainability measures are implemented?"
    ],
    "business_specific": [
      "What are the key competitive advantages?",
      "What is the market share compared to competitors?",
      "What strategic partnerships exist?",
      "What are the expansion plans?",
      "What risks does the company face?"
    ]
  },
  "generated_at": "2025-12-26T10:30:00"
}
```

### Question Generation Logic:

**File**: `backend/api/deep_dive.py` (NEW)

```python
from fastapi import APIRouter, Depends
from services.question_generator import QuestionGenerator

router = APIRouter(prefix="/api/deep-dive", tags=["deep-dive"])

@router.post("/generate-questions")
async def generate_questions(request: QuestionRequest):
    """
    Generate 3 categories of questions based on uploaded report
    """
    generator = QuestionGenerator()

    # 1. Detect sector from document chunks
    sector = await generator.detect_sector(request.company_id)

    # 2. Generate general questions (universal for all companies)
    general_questions = generator.get_general_questions()

    # 3. Generate sector-specific questions (pharma, tech, food, etc.)
    sector_questions = generator.get_sector_questions(sector)

    # 4. Generate business-specific questions (from document context)
    business_questions = await generator.generate_business_questions(
        company_id=request.company_id,
        company_name=request.company_name
    )

    return {
        "company_id": request.company_id,
        "company_name": request.company_name,
        "detected_sector": sector,
        "questions": {
            "general": general_questions,
            "sector_specific": sector_questions,
            "business_specific": business_questions
        },
        "generated_at": datetime.now().isoformat()
    }
```

### Sector Detection Logic:

**File**: `backend/services/question_generator.py` (NEW)

```python
class QuestionGenerator:
    def __init__(self):
        self.db = DatabasePool()
        self.llm_client = LLMClient()

    async def detect_sector(self, company_id: str) -> str:
        """
        Detect sector from document chunks using keywords
        """
        # Fetch sample chunks from database
        chunks = await self.get_sample_chunks(company_id, limit=10)

        # Define sector keywords
        sector_keywords = {
            "Pharmaceuticals": ["drug", "pharmaceutical", "clinical", "FDA", "medicine", "R&D"],
            "Technology": ["software", "technology", "AI", "cloud", "SaaS", "platform"],
            "Manufacturing": ["production", "manufacturing", "factory", "capacity utilization"],
            "FMCG": ["consumer goods", "retail", "distribution", "FMCG"],
            "Finance": ["banking", "financial services", "loans", "deposits"],
            "Construction": ["construction", "infrastructure", "real estate", "projects"],
            "Healthcare": ["hospital", "healthcare", "medical services", "patients"],
            "Energy": ["energy", "power", "renewable", "oil", "gas"],
            "Food & Beverage": ["food", "beverage", "restaurant", "agriculture"]
        }

        # Count keyword matches
        sector_scores = {}
        combined_text = " ".join([c['text'].lower() for c in chunks])

        for sector, keywords in sector_keywords.items():
            score = sum(1 for kw in keywords if kw in combined_text)
            sector_scores[sector] = score

        # Return sector with highest score
        detected_sector = max(sector_scores, key=sector_scores.get)
        return detected_sector if sector_scores[detected_sector] > 0 else "General"

    def get_general_questions(self) -> List[str]:
        """Universal questions for all companies"""
        return [
            "What is the company's total revenue for the fiscal year?",
            "What are the main products or services offered by the company?",
            "What is the company's net profit margin?",
            "What are the key financial highlights from the annual report?",
            "What is the company's current market position?",
            "What are the company's future growth plans?",
            "What is the debt-to-equity ratio?",
            "What are the major sources of revenue?",
            "How many employees does the company have?",
            "What is the dividend payout ratio?"
        ]

    def get_sector_questions(self, sector: str) -> List[str]:
        """Sector-specific pre-defined questions"""
        sector_questions = {
            "Pharmaceuticals": [
                "What is the R&D spending on new drug development?",
                "What is the current drug pipeline status?",
                "What regulatory approvals were received this year?",
                "What are the key therapeutic areas of focus?",
                "What is the patent expiry timeline for major drugs?",
                "What clinical trials are currently ongoing?",
                "What is the generic competition landscape?",
                "What are the biosimilar development initiatives?"
            ],
            "Technology": [
                "What is the annual recurring revenue (ARR)?",
                "What is the customer acquisition cost (CAC)?",
                "What is the customer lifetime value (LTV)?",
                "What cloud infrastructure investments were made?",
                "What AI/ML initiatives are underway?",
                "What is the cybersecurity posture?",
                "What strategic tech acquisitions were completed?",
                "What is the R&D investment as % of revenue?"
            ],
            "Manufacturing": [
                "What is the production capacity utilization rate?",
                "What are the raw material cost trends?",
                "What automation initiatives are in place?",
                "What is the supply chain efficiency?",
                "What sustainability measures are implemented?",
                "What quality certifications does the company hold?",
                "What is the inventory turnover ratio?",
                "What are the major capital expenditures?"
            ],
            "FMCG": [
                "What is the distribution network coverage?",
                "What new product launches occurred this year?",
                "What is the market share in key categories?",
                "What brand portfolio does the company own?",
                "What advertising and marketing spend was allocated?",
                "What e-commerce revenue contribution exists?",
                "What sustainability initiatives in packaging?",
                "What are the rural vs urban sales split?"
            ],
            "Finance": [
                "What is the net interest margin (NIM)?",
                "What is the non-performing asset (NPA) ratio?",
                "What is the capital adequacy ratio?",
                "What digital banking initiatives were launched?",
                "What is the loan-to-deposit ratio?",
                "What fintech partnerships were established?",
                "What is the cost-to-income ratio?",
                "What regulatory compliance measures are in place?"
            ],
            # Add more sectors as needed...
        }

        return sector_questions.get(sector, self.get_general_questions()[:8])

    async def generate_business_questions(self, company_id: str, company_name: str) -> List[str]:
        """
        Use LLM to generate company-specific questions from document
        """
        # Get representative chunks
        chunks = await self.get_sample_chunks(company_id, limit=20)

        # Create prompt for LLM
        prompt = f"""
        Based on the following excerpts from {company_name}'s annual report, generate 8 specific business-related questions that would be valuable to ask:

        Excerpts:
        {self._format_chunks(chunks)}

        Generate 8 questions focusing on:
        - Competitive advantages
        - Market positioning
        - Strategic initiatives
        - Risk factors
        - Growth opportunities
        - Partnerships and collaborations
        - Innovation and R&D
        - Operational challenges

        Return ONLY the questions, one per line, numbered 1-8.
        """

        # Call LLM
        response = await self.llm_client.generate(prompt)

        # Parse questions from response
        questions = self._parse_questions(response)

        return questions[:8]  # Ensure exactly 8 questions
```

---

## Frontend Implementation

### New Component: `DeepDiveTab.tsx`

**File**: `frontend/src/components/DeepDiveTab.tsx` (NEW)

```typescript
'use client';

import React, { useState, useEffect } from 'react';
import { apiClient } from '../services/api';
import { Layers, Building2, Briefcase, ChevronRight, Loader2, Sparkles } from 'lucide-react';

interface DeepDiveData {
  company_id: string;
  company_name: string;
  detected_sector: string;
  questions: {
    general: string[];
    sector_specific: string[];
    business_specific: string[];
  };
  generated_at: string;
}

interface QuestionAnswer {
  question: string;
  answer: string | null;
  loading: boolean;
}

interface DeepDiveTabProps {
  companyId: string;
  companyName: string;
}

export default function DeepDiveTab({ companyId, companyName }: DeepDiveTabProps) {
  const [deepDiveData, setDeepDiveData] = useState<DeepDiveData | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedQuestion, setExpandedQuestion] = useState<string | null>(null);
  const [questionAnswers, setQuestionAnswers] = useState<Record<string, QuestionAnswer>>({});

  useEffect(() => {
    loadQuestions();
  }, [companyId]);

  const loadQuestions = async () => {
    setLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/api/deep-dive/generate-questions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ company_id: companyId, company_name: companyName })
      });
      const data = await response.json();
      setDeepDiveData(data);
    } catch (error) {
      console.error('Failed to load questions:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleQuestionClick = async (question: string, category: string) => {
    // Toggle expand
    if (expandedQuestion === question) {
      setExpandedQuestion(null);
      return;
    }

    setExpandedQuestion(question);

    // Check if already answered
    if (questionAnswers[question]?.answer) {
      return;
    }

    // Mark as loading
    setQuestionAnswers(prev => ({
      ...prev,
      [question]: { question, answer: null, loading: true }
    }));

    // Fetch answer from RAG
    try {
      const response = await apiClient.sendQuery(question, 'deep-dive-session', companyId);
      setQuestionAnswers(prev => ({
        ...prev,
        [question]: { question, answer: response.answer, loading: false }
      }));
    } catch (error) {
      console.error('Failed to get answer:', error);
      setQuestionAnswers(prev => ({
        ...prev,
        [question]: { question, answer: 'Failed to load answer', loading: false }
      }));
    }
  };

  const renderQuestionSection = (title: string, icon: React.ReactNode, questions: string[], category: string) => (
    <div className="space-y-3">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500/20 to-blue-500/20 border border-cyan-500/30 flex items-center justify-center">
          {icon}
        </div>
        <div>
          <h3 className="text-lg font-bold text-white">{title}</h3>
          {category === 'sector' && deepDiveData && (
            <p className="text-xs text-cyan-400">Sector: {deepDiveData.detected_sector}</p>
          )}
        </div>
      </div>

      <div className="space-y-2">
        {questions.map((question, idx) => {
          const isExpanded = expandedQuestion === question;
          const answerData = questionAnswers[question];

          return (
            <div key={idx} className="border border-cyan-500/20 rounded-xl overflow-hidden bg-gradient-to-r from-cyan-500/5 to-transparent hover:border-cyan-500/40 transition-all">
              <button
                onClick={() => handleQuestionClick(question, category)}
                className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-cyan-500/10 transition-all"
              >
                <span className="text-sm text-gray-200 flex-1">{question}</span>
                <ChevronRight className={`w-4 h-4 text-cyan-400 transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
              </button>

              {isExpanded && (
                <div className="px-4 py-4 bg-[#0a0e1a]/50 border-t border-cyan-500/20 animate-in slide-in-from-top-2 duration-300">
                  {answerData?.loading ? (
                    <div className="flex items-center gap-3 text-cyan-400">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span className="text-sm">Generating answer...</span>
                    </div>
                  ) : answerData?.answer ? (
                    <div className="text-sm text-gray-300 leading-relaxed whitespace-pre-line">
                      {answerData.answer}
                    </div>
                  ) : null}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center space-y-4">
          <Loader2 className="w-12 h-12 text-cyan-400 animate-spin mx-auto" />
          <p className="text-gray-400">Generating intelligent questions...</p>
        </div>
      </div>
    );
  }

  if (!deepDiveData) return null;

  return (
    <div className="flex-1 overflow-y-auto custom-scrollbar p-8 space-y-8">
      <div className="max-w-5xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
            <Sparkles className="w-8 h-8 text-cyan-400" />
            Deep Dive Analysis
          </h1>
          <p className="text-gray-400">Explore key insights through curated questions about {companyName}</p>
        </div>

        {/* General Questions */}
        {renderQuestionSection(
          'General Questions',
          <Layers className="w-5 h-5 text-cyan-400" />,
          deepDiveData.questions.general,
          'general'
        )}

        {/* Sector-Specific Questions */}
        {renderQuestionSection(
          'Sector-Specific Questions',
          <Building2 className="w-5 h-5 text-purple-400" />,
          deepDiveData.questions.sector_specific,
          'sector'
        )}

        {/* Business-Specific Questions */}
        {renderQuestionSection(
          'Business-Specific Questions',
          <Briefcase className="w-5 h-5 text-emerald-400" />,
          deepDiveData.questions.business_specific,
          'business'
        )}
      </div>
    </div>
  );
}
```

### Update `page.tsx` to Add Deep Dive Tab

**Changes in**: `frontend/src/app/page.tsx`

1. Add new tab state:
```typescript
const [activeTab, setActiveTab] = useState<'chat' | 'analysis' | 'deepdive'>('chat');
```

2. Add Deep Dive tab button (line ~221):
```typescript
<button
  onClick={() => setActiveTab('deepdive')}
  className={`flex items-center gap-2 px-4 py-1.5 rounded-md text-sm font-medium transition-all ${
    activeTab === 'deepdive'
      ? 'bg-cyan-500/20 text-cyan-400 shadow-lg shadow-cyan-500/20'
      : 'text-gray-400 hover:text-gray-300'
  }`}
>
  <Sparkles className="w-4 h-4" />
  Deep Dive
</button>
```

3. Add Deep Dive content rendering (line ~296):
```typescript
{activeTab === 'deepdive' && (
  <DeepDiveTab
    companyId={selectedCompany.company_id}
    companyName={selectedCompany.company_name}
  />
)}
```

---

## Summary of Changes

### Backend Files to Create:
1. ✅ `backend/api/deep_dive.py` - Deep dive API endpoints
2. ✅ `backend/services/question_generator.py` - Question generation logic

### Frontend Files to Create:
1. ✅ `frontend/src/components/DeepDiveTab.tsx` - New Deep Dive tab component

### Files to Modify:
1. ✅ `frontend/src/app/page.tsx` - Add analytics caching + Deep Dive tab
2. ✅ `frontend/src/components/AnalysisTab.tsx` - Accept cached data from parent
3. ✅ `backend/main.py` - Register deep_dive router

---

## Testing Plan

### Test 1: Analytics Caching
1. Select company → Click "Analysis" tab
2. Wait for data to load
3. Switch to "Chat" tab
4. Click "Analysis" tab again
5. **Expected**: Data appears instantly (no reload)

### Test 2: Deep Dive Questions
1. Select company → Click "Deep Dive" tab
2. **Expected**: See 3 sections with questions
3. **Expected**: Sector auto-detected (e.g., "Pharmaceuticals")
4. Click a question
5. **Expected**: Answer loads below with animation
6. Click same question again
7. **Expected**: Answer collapses (toggle behavior)
8. Click different question
9. **Expected**: New answer loads (previous answer cached)

---

## Implementation Order

1. ✅ Fix Analytics caching (Move state to page.tsx)
2. ✅ Create backend question generation service
3. ✅ Create backend API endpoint
4. ✅ Create frontend DeepDiveTab component
5. ✅ Integrate Deep Dive tab into page.tsx
6. ✅ Test complete flow

---

**Ready to implement! 🚀**
