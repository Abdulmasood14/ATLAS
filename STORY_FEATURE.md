# 📖 Story Feature - Investment Narrative

**Date**: January 6, 2026

---

## 🎯 Overview

The **Story** tab provides a comprehensive, long-form investment narrative for investors and financial analysts. It automatically generates a detailed analysis covering all aspects of the company, extracted from the annual report using advanced RAG queries.

---

## ✨ Features

### 1. **Automatic Story Generation**
- Loads automatically when company is selected
- 6 parallel RAG queries for comprehensive coverage
- Long-form narrative (1000+ words)
- Processing time: 30-60 seconds

### 2. **Investment Sections Covered**

#### Business Overview
- Core business model and revenue streams
- Target markets and customer segments
- Products and services offered
- Strategic positioning

#### Financial Performance
- Revenue trends and growth metrics
- Profitability analysis (EBITDA, net profit)
- Margin analysis and cash flow
- Year-over-year comparisons
- Key financial ratios

#### Competitive Position
- Market share and competitive advantages
- Economic moats and differentiators
- Patents, brands, strategic assets
- Competitive landscape analysis

#### Risk Factors
- Operational risks
- Market and regulatory risks
- Competitive threats
- Challenges and concerns

#### Growth Strategy
- Expansion initiatives
- New product launches
- R&D focus areas
- Capital expenditure plans
- Market expansion roadmap

#### Corporate Governance
- Board composition
- Management quality and experience
- Governance practices
- Awards and recognition

### 3. **Investment Recommendation (BUY/SELL/HOLD)**
- Clear verdict with color coding:
  - 🟢 **BUY**: Green (emerald-50)
  - 🔴 **SELL**: Red (red-50)
  - 🟡 **HOLD**: Amber (amber-50)
- Detailed 2-3 paragraph justification
- Based on comprehensive analysis of all sections

### 4. **Strategic Milestones & Roadmap**
- Timeline visualization with connectors
- Up to 6 key milestones extracted from growth strategy
- Each milestone includes:
  - Title (short summary)
  - Description (detailed information)
- Visual timeline with gradient connectors

---

## 🏗️ Technical Implementation

### Backend: `/api/story/{company_id}`

**File**: `backend/api/story.py`

**Process**:
1. Execute 6 parallel RAG queries:
   - Business overview
   - Financial performance
   - Competitive position
   - Risk factors
   - Growth strategy
   - Governance quality

2. Generate investment recommendation using comprehensive context

3. Extract milestones from growth strategy text

4. Return structured JSON response

**Response Format**:
```json
{
  "company_id": "COMPANY_ID",
  "story": {
    "business_overview": "...",
    "financial_performance": "...",
    "competitive_position": "...",
    "risk_factors": "...",
    "growth_strategy": "...",
    "governance_quality": "...",
    "recommendation": "..."
  },
  "milestones": [
    {
      "title": "Milestone Title",
      "description": "Detailed description..."
    }
  ],
  "success": true
}
```

### Frontend: `StoryTab` Component

**File**: `frontend/src/components/StoryTab.tsx`

**Key Features**:
- Loading state with spinner (30-60s wait time)
- Error handling with retry button
- Verdict badge extraction and color coding
- Markdown rendering with ReactMarkdown
- Responsive grid layout (2-column on large screens)
- Timeline visualization for milestones

**Sections Layout**:
1. **Header Card** (full width):
   - Title with BookOpen icon
   - Verdict badge (BUY/SELL/HOLD)
   - Investment recommendation (prominent position)

2. **Story Sections** (2-column grid):
   - Business Overview
   - Financial Performance
   - Competitive Position
   - Risk Factors

3. **Growth Strategy** (full width card)

4. **Milestones/Roadmap** (full width with timeline):
   - Visual timeline with connectors
   - Up to 6 key milestones
   - Gradient vertical line between items

5. **Governance** (full width card)

---

## 🎨 Design Specifications

### Color Palette
- Primary Blue: `#1762C7`
- Teal Gradient: `rgb(31, 168, 166)`
- Background: White cards with blue borders
- Verdict Colors:
  - BUY: `emerald-50` / `emerald-700`
  - SELL: `red-50` / `red-700`
  - HOLD: `amber-50` / `amber-700`

### Typography
- Section Headers: `text-lg font-bold`
- Body Text: `text-gray-700 leading-relaxed`
- Icons: `w-5 h-5` (Lucide icons)

### Layout
- Cards: `rounded-xl border shadow-md hover:shadow-lg`
- Padding: `p-6` for sections
- Grid: `grid-cols-1 lg:grid-cols-2 gap-6`

### Icons Used
- BookOpen: Story header
- Target: Investment recommendation & growth strategy
- TrendingUp: Financial performance
- Award: Competitive position & governance
- Shield: Risk factors
- CheckCircle2: Milestones header
- Loader2: Loading state

---

## 🚀 Usage

### For Users:
1. Select a company from the sidebar
2. Click the **Story** tab in the navigation
3. Wait 30-60 seconds for generation
4. Read comprehensive investment narrative
5. Review BUY/SELL/HOLD recommendation
6. Check strategic milestones and roadmap

### For Developers:

#### Test the API:
```bash
curl http://localhost:8000/api/story/PHOENIX_MILLS_2025
```

#### Integration:
```tsx
import StoryTab from '../components/StoryTab';

<StoryTab
  companyId="PHOENIX_MILLS_2025"
  companyName="Phoenix Mills Limited"
/>
```

---

## 📊 RAG Query Strategy

### Query Optimization
Each section uses tailored prompts for better extraction:

**Business Overview**:
> "Provide a comprehensive overview of the company's business model, core products/services, target markets, and revenue streams..."

**Financial Performance**:
> "Analyze the company's financial performance including revenue trends, profitability metrics, margins, cash flow, and YoY growth..."

**Competitive Position**:
> "Describe the company's competitive position, advantages, moats, market share, and differentiators..."

**Risk Factors**:
> "What are the key risk factors and challenges? Include operational, market, regulatory risks..."

**Growth Strategy**:
> "What is the company's growth strategy? Include expansion, R&D, new products, capex plans, milestones..."

**Governance**:
> "Assess management quality and corporate governance. Include board composition, experience, practices..."

**Recommendation Query**:
Uses summaries from all sections (first 500 chars each) to generate holistic BUY/SELL/HOLD verdict.

---

## 🔧 Configuration

### Backend Settings
- **Top-K chunks**: 10 (more context for comprehensive story)
- **Parallel execution**: 6 concurrent queries
- **Timeout**: Default RAG timeout (180s)
- **Model**: phi4:14b via Ollama

### Frontend Settings
- **Auto-load**: Yes (on company selection)
- **Cache**: No (regenerates each time)
- **Retry**: Manual retry button on error

---

## 📝 Example Output

### Sample Investment Recommendation:
> "Phoenix Mills Limited presents a compelling investment opportunity in the premium retail real estate sector. The company has demonstrated strong financial performance with revenues of ₹5,554 crores and robust EBITDA margins. With a market capitalization of ₹330 billion and strategic expansion plans across multiple cities, the company is well-positioned for sustained growth.
>
> Key strengths include premium mall positioning, high occupancy rates, and diversified tenant mix. However, investors should note regulatory risks and market competition. The company's strong governance framework and experienced management team add confidence.
>
> **Verdict: BUY** - Strong fundamentals, healthy growth trajectory, and attractive valuation make this a compelling long-term investment."

### Sample Milestone:
**Title**: "Expansion into Tier 2 Cities"
**Description**: "The company plans to expand its retail footprint into tier 2 cities with three new mall developments scheduled for FY2027. Total capex estimated at ₹800 crores with expected ROI of 18%."

---

## 🐛 Known Limitations

1. **Generation Time**: 30-60 seconds (6 parallel RAG queries)
   - Can be improved with caching
   - Currently regenerates on each tab switch

2. **Milestone Extraction**: Heuristic-based
   - Uses keyword matching
   - May miss some milestones if phrasing is unusual
   - Can be improved with fine-tuned NER model

3. **Recommendation Accuracy**: Depends on data quality
   - Based on annual report content
   - May not reflect real-time market conditions
   - Should be combined with other analysis

4. **No Caching**: Story regenerates each time
   - Future: Add caching similar to Analytics tab
   - Reduce load times for repeated views

---

## 🔮 Future Enhancements

### Short Term:
- [ ] Add caching mechanism to avoid regeneration
- [ ] Add "Regenerate Story" button
- [ ] Add export to PDF functionality
- [ ] Add share link feature

### Medium Term:
- [ ] Sentiment analysis of narrative tone
- [ ] Comparison with industry peers
- [ ] Historical trend charts inline
- [ ] Interactive milestone timeline

### Long Term:
- [ ] Multi-company comparison stories
- [ ] AI-generated executive summary (TL;DR)
- [ ] Voice narration of the story
- [ ] Custom section selection by user

---

## 📚 Related Files

### Backend:
- `backend/api/story.py` - Main API endpoint
- `backend/main.py` - Router registration
- `backend/services/rag_service.py` - RAG integration

### Frontend:
- `frontend/src/components/StoryTab.tsx` - Main component
- `frontend/src/app/page.tsx` - Tab integration
- `frontend/src/types/index.ts` - Type definitions

---

## ✅ Testing Checklist

- [x] Backend API returns valid JSON
- [x] Frontend component renders without errors
- [x] Tab navigation works correctly
- [x] Loading state displays during generation
- [x] Error handling works with retry
- [x] Verdict badge extracts and colors correctly
- [x] Milestones display in timeline format
- [x] Markdown rendering works properly
- [x] Responsive design on mobile/tablet
- [ ] **Performance testing with multiple companies**
- [ ] **User acceptance testing**

---

## 🎉 Summary

The Story feature successfully provides investors with a comprehensive, AI-generated investment narrative that synthesizes information from annual reports into a coherent, actionable analysis. With BUY/SELL/HOLD recommendations and strategic milestone tracking, it serves as a powerful tool for informed investment decisions.

**Key Achievement**: Transforms 200+ page annual reports into digestible 1000+ word investment stories in under 60 seconds.
