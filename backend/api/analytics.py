"""
Analytics API Routes

Extracts comprehensive financial metrics from annual reports and supplements with yfinance data.
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import asyncio
from datetime import datetime

from services.rag_service import get_rag_service, RAGService
from database.connection import get_db, DatabaseManager

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


# Financial metrics template: Expanded to 30 critical indicators
FINANCIAL_METRICS = [
    # --- Market & Valuation (yfinance priority) ---
    {"key": "current_price", "name": "Current Price", "source": "yfinance", "category": "market"},
    {"key": "pe_ratio", "name": "PE Ratio", "source": "yfinance", "category": "market"},
    {"key": "eps", "name": "EPS", "source": "yfinance", "category": "market"},
    {"key": "pb_ratio", "name": "P/BV Ratio", "source": "yfinance", "category": "market"},
    {"key": "peg_ratio", "name": "PEG Ratio", "source": "yfinance", "category": "market"},
    {"key": "price_sales", "name": "Price/Sales", "source": "yfinance", "category": "market"},
    {"key": "market_cap", "name": "Market Capitalization", "source": "yfinance", "category": "market"},
    {"key": "dividend_yield", "name": "Dividend Yield", "source": "yfinance", "category": "market"},
    {"key": "beta", "name": "Beta (Volatility)", "source": "yfinance", "category": "market"},
    {"key": "fifty_two_week_high", "name": "52 Week High", "source": "yfinance", "category": "market"},
    {"key": "fifty_two_week_low", "name": "52 Week Low", "source": "yfinance", "category": "market"},
    
    # --- Performance & Profitability (Mixed) ---
    {"key": "roic", "name": "ROIC (Return on Invested Capital)", "source": "annual_report", "category": "performance"},
    {"key": "revenue_growth", "name": "Revenue Growth (YoY)", "source": "annual_report", "category": "performance"},
    {"key": "ebitda_margin", "name": "EBITDA Margin", "source": "annual_report", "category": "performance"},
    {"key": "net_profit_margin", "name": "Net Profit Margin", "source": "annual_report", "category": "performance"},
    {"key": "roe", "name": "Return on Equity (ROE)", "source": "annual_report", "category": "performance"},
    {"key": "debt_to_equity", "name": "Debt to Equity Ratio", "source": "annual_report", "category": "performance"},
    {"key": "current_ratio", "name": "Current Ratio", "source": "annual_report", "category": "performance"},

    # --- Business Profile & Strategy (RAG) ---
    {"key": "business_model", "name": "Core Business Model", "source": "annual_report", "category": "business"},
    {"key": "key_competitive_advantages", "name": "Key Competitive Advantages (Moats)", "source": "annual_report", "category": "business"},
    {"key": "market_share", "name": "Market Share Position", "source": "annual_report", "category": "business"},
    {"key": "top_customers", "name": "Customer Concentration/Top Clients", "source": "annual_report", "category": "business"},
    {"key": "geographical_presence", "name": "Geographical Presence", "source": "annual_report", "category": "business"},
    
    # --- Valuation Strategy & Risks (RAG) ---
    {"key": "growth_prospects", "name": "Future Growth Prospects", "source": "annual_report", "category": "valuation"},
    {"key": "margin_of_safety", "name": "Margin of Safety Analysis", "source": "annual_report", "category": "valuation"},
    {"key": "investment_thesis", "name": "Analyst Investment Thesis", "source": "annual_report", "category": "valuation"},
    {"key": "business_risk", "name": "Top Strategic Risks", "source": "annual_report", "category": "risk"},
    {"key": "recent_alerts", "name": "Recent Alerts & Red Flags", "source": "annual_report", "category": "risk"},
    {"key": "legal_issues", "name": "Outstanding Legal Issues", "source": "annual_report", "category": "risk"},
    {"key": "governance_score", "name": "Governance & Management Quality", "source": "annual_report", "category": "risk"},
]


class MetricValue(BaseModel):
    """Single metric value"""
    key: str
    name: str
    value: Optional[Any]
    source: str  # 'annual_report', 'yfinance', or 'not_found'
    confidence: float  # 0.0 to 1.0
    extracted_at: datetime


class AnalyticsResponse(BaseModel):
    """Complete analytics response"""
    company_id: str
    company_name: str
    ticker_symbol: Optional[str]
    metrics: List[MetricValue]
    categories: Dict[str, List[MetricValue]]
    extraction_status: str
    generated_at: datetime


class AnalyticsRequest(BaseModel):
    """Request for analytics generation"""
    company_id: str
    company_name: str
    ticker_symbol: Optional[str] = None
    force_refresh: bool = False


# ============================================================================
# GENERATE ANALYTICS
# ============================================================================

@router.post("/generate", response_model=AnalyticsResponse)
async def generate_analytics(
    request: AnalyticsRequest,
    rag: RAGService = Depends(get_rag_service),
    db: DatabaseManager = Depends(get_db)
):
    """
    Generate comprehensive financial analytics for a company
    Parallelized for high performance extraction.
    """
    try:
        # Step 1: Detect Ticker
        ticker = request.ticker_symbol
        if not ticker:
            # Fallback map for common names
            ticker_map = {
                'laurus': 'LAURUSLABS.NS', 'phoenix': 'PHOENIXLTD.NS',
                'reliance': 'RELIANCE.NS', 'tcs': 'TCS.NS',
                'infosys': 'INFY.NS', 'hicp': 'HICP.NS', 'dr reddy': 'DRREDDY.NS',
            }
            company_lower = request.company_name.lower()
            for key, value in ticker_map.items():
                if key in company_lower:
                    ticker = value
                    break
            
            # If still not found, try yfinance SEARCH
            if not ticker:
                try:
                    import yfinance as yf
                    search = yf.Search(request.company_name, max_results=3)
                    if search.quotes:
                        # Prioritize NSE/BSE for Indian user context if any matched
                        indian_quote = next((q['symbol'] for q in search.quotes if q['symbol'].endswith('.NS') or q['symbol'].endswith('.BO')), None)
                        ticker = indian_quote or search.quotes[0]['symbol']
                        print(f"  [DISCOVERY] Found ticker {ticker} for {request.company_name}")
                except Exception as e:
                    print(f"Ticker discovery failed: {e}")

        # Step 2: Parallelize Report and Market Extraction
        # We wrap them in tasks to run concurrently
        report_task = extract_from_annual_report(request.company_id, request.company_name, rag)
        market_task = extract_from_yfinance(ticker, request.company_name) if ticker else None

        # Execute both tasks in parallel with error handling
        try:
            if market_task:
                # Use return_exceptions=True to prevent one task from killing the whole request
                results = await asyncio.gather(report_task, market_task, return_exceptions=True)
                
                # Check for exceptions in results
                if isinstance(results[0], Exception):
                    print(f"Report Task failed: {results[0]}")
                    report_metrics = []
                else:
                    report_metrics = results[0]
                    
                if isinstance(results[1], Exception):
                    print(f"Market Task failed: {results[1]}")
                    market_metrics = []
                else:
                    market_metrics = results[1]

                # --- NEW: PROGRESSIVE FALLBACK LOGIC ---
                # If RAG missed a metric that might be in yfinance, fill the gap
                final_metrics = []
                report_lookup = {o.key: o for o in report_metrics}
                market_lookup = {o.key: o for o in market_metrics}
                
                for m_def in FINANCIAL_METRICS:
                    m_val = report_lookup.get(m_def['key'])
                    
                    # If RAG failed or found nothing, check market data fallback
                    if (not m_val or m_val.source in ['not_found', 'timeout', 'error']) and m_def['key'] in market_lookup:
                        fallback_val = market_lookup[m_def['key']]
                        if fallback_val.value is not None:
                            print(f"  [FALLBACK] Replaced {m_def['name']} with yfinance data.")
                            final_metrics.append(fallback_val)
                        else:
                            final_metrics.append(m_val or fallback_val)
                    elif m_val:
                        final_metrics.append(m_val)
                
                report_metrics = final_metrics
            else:
                report_metrics = await report_task
                market_metrics = []
        except Exception as e:
            print(f"Critical error during parallel gather: {e}")
            report_metrics = []
            market_metrics = []

        # --- FIX: Ensure no duplicate keys in all_metrics ---
        # We prioritize the merged 'report_metrics' which already has fallbacks
        all_metrics_map = {m.key: m for m in report_metrics}
        
        # Add any remaining market-only metrics that weren't in FINANCIAL_METRICS report list
        for m in market_metrics:
            if m.key not in all_metrics_map:
                all_metrics_map[m.key] = m
        
        all_metrics = list(all_metrics_map.values())

        # Step 3: Categorize metrics
        categories = {}
        for metric in all_metrics:
            cat = next((m['category'] for m in FINANCIAL_METRICS if m['key'] == metric.key), 'other')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(metric)

        return AnalyticsResponse(
            company_id=request.company_id,
            company_name=request.company_name,
            ticker_symbol=ticker,
            metrics=all_metrics,
            categories=categories,
            extraction_status="completed",
            generated_at=datetime.now()
        )

    except Exception as e:
        import traceback
        print(f"Error generating analytics: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Analytics generation failed: {str(e)}")


async def extract_from_annual_report(
    company_id: str,
    company_name: str,
    rag: RAGService
) -> List[MetricValue]:
    """Extract metrics from annual report using PARALLEL RAG queries"""
    import asyncio

    report_based_metrics = [m for m in FINANCIAL_METRICS if m['source'] == 'annual_report']
    print(f"Parallelizing extraction of {len(report_based_metrics)} metrics...")

    async def _extract_single(metric_def):
        try:
            print(f"  [START] Extracting: {metric_def['name']}")

            # Customize query based on metric type for better retrieval
            metric_key = metric_def['key']
            metric_name = metric_def['name']

            # Define better queries for specific metrics
            if metric_key == 'roic':
                query = "What is the Return on Invested Capital (ROIC) or return on capital employed? Look for profitability ratios, capital efficiency metrics, or ROCE in the financial highlights."
            elif metric_key == 'revenue_growth':
                query = "What was the revenue growth year-over-year? Compare current year revenue with previous year revenue and calculate the growth percentage."
            elif metric_key == 'ebitda_margin':
                query = "What is the EBITDA margin? Look for EBITDA or operating profit margins in the financial performance section."
            elif metric_key == 'net_profit_margin':
                query = "What is the net profit margin? Calculate from net profit divided by total revenue."
            elif metric_key == 'roe':
                query = "What is the Return on Equity (ROE)? Look for ROE or calculate from net profit divided by shareholder's equity."
            elif metric_key == 'debt_to_equity':
                query = "What is the debt to equity ratio? Look for total debt and shareholder's equity in the balance sheet."
            elif metric_key == 'current_ratio':
                query = "What is the current ratio? Calculate from current assets divided by current liabilities from the balance sheet."
            elif 'risk' in metric_key or 'risk' in metric_name.lower():
                query = f"What are the {metric_name.lower()}? Look in the Risk Management, Risk Factors, or Management Discussion sections."
            elif 'growth' in metric_name.lower() or 'prospect' in metric_name.lower():
                query = f"What are the {metric_name.lower()}? Look in the Business Outlook, Future Plans, or Strategy sections."
            elif 'business model' in metric_name.lower():
                query = "Describe the company's core business model and revenue streams. What products or services does the company offer?"
            elif 'competitive advantage' in metric_name.lower() or 'moat' in metric_name.lower():
                query = "What are the company's key competitive advantages or economic moats? What makes the company unique or defensible?"
            elif 'market share' in metric_name.lower():
                query = "What is the company's market share position? How does it rank compared to competitors?"
            elif 'governance' in metric_name.lower():
                query = "Describe the company's governance structure and management quality. Include board composition, key management personnel, and corporate governance practices."
            else:
                # Generic query for other metrics
                query = (
                    f"Extract detailed information about: {metric_name}. "
                    "Search in sections like Management Discussion & Analysis (MD&A), Financial Statements, Notes, Auditor's Report, and Business Overview. "
                    "Provide a direct summary with specific data. Do not use conversational filler. "
                    "If numbers are found, lead with them."
                )

            # ADD TIMEOUT to avoid hanging
            try:
                response = await asyncio.wait_for(
                    rag.query(
                        query=query,
                        company_id=company_id,
                        top_k=10, # INCREASED from 3 for better coverage of qualitative themes
                        verbose=False
                    ),
                    timeout=60.0 # Higher timeout for broader context
                )
            except asyncio.TimeoutError:
                print(f"  [TIMEOUT] {metric_def['name']} failed after 60s")
                return MetricValue(
                    key=metric_def['key'],
                    name=metric_def['name'],
                    value=None,
                    source='timeout',
                    confidence=0.0,
                    extracted_at=datetime.now()
                )

            if response.success and response.answer:
                value = response.answer.strip()
                print(f"  [SUCCESS] {metric_def['name']} extracted.")
                
                # Professional cleaning for analysts
                prefixes_to_remove = [
                    "Information not found", "Based on the provided context",
                    "According to the document", "The document states",
                    "Not mentioned", "Not specified", "### ", "###", "**", "*",
                    "Upon reviewing the provided financial statements",
                    "Specific details regarding", "A synthesis of available information",
                    "There is no mention of", "I could not find", "Conclusion:"
                ]
                for prefix in prefixes_to_remove:
                    if value.lower().startswith(prefix.lower()):
                        value = value[len(prefix):].lstrip(':').strip()
                        # Recursively remove more prefixes if they appear after cleaning
                        for p2 in prefixes_to_remove:
                            if value.lower().startswith(p2.lower()):
                                value = value[len(p2):].lstrip(':').strip()
                
                # Strip ALL markdown hashtags and excessive bolding symbols from the middle of text too
                import re
                value = re.sub(r'#+\s*', '', value)  # Remove hashtags
                value = re.sub(r'\*+', '', value)   # Remove bolding/italics
                value = value.strip()

                not_found_indicators = [
                    "not found", "not available", "not mentioned",
                    "not specified", "does not include", "not disclosed",
                    "insufficient information"
                ]
                # Only mark as 'not found' if it's a very short response containing one of these
                is_not_found = len(value) < 100 and any(indicator in value.lower() for indicator in not_found_indicators)

                # Extended length for professional analysis (up to 3000 chars)
                if len(value) > 3000:
                    value = value[:2997] + "..."

                confidence = 0.0
                if response.sources and not is_not_found:
                    avg_score = sum(s.get('score', 0.0) for s in response.sources) / len(response.sources)
                    confidence = min(avg_score, 1.0)

                if not is_not_found and value and len(value) > 5:
                    return MetricValue(
                        key=metric_def['key'],
                        name=metric_def['name'],
                        value=value,
                        source='annual_report',
                        confidence=confidence,
                        extracted_at=datetime.now()
                    )

            print(f"  [EMPTY] {metric_def['name']} returned no data.")
            return MetricValue(
                key=metric_def['key'],
                name=metric_def['name'],
                value=None,
                source='not_found',
                confidence=0.0,
                extracted_at=datetime.now()
            )
        except Exception as e:
            print(f"  [ERROR] {metric_def['name']}: {e}")
            return MetricValue(
                key=metric_def['key'],
                name=metric_def['name'],
                value=None,
                source='error',
                confidence=0.0,
                extracted_at=datetime.now()
            )

    # SECURE PARALLEL EXECUTION (Throttle to 3 at a time to avoid slamming LLM/DB)
    semaphore = asyncio.Semaphore(3)
    async def throttled_extract(m):
        async with semaphore:
            return await _extract_single(m)

    tasks = [throttled_extract(m) for m in report_based_metrics]
    results = await asyncio.gather(*tasks)
    return list(results)


async def extract_from_yfinance(
    ticker_symbol: str,
    company_name: str
) -> List[MetricValue]:
    """Extract market metrics using yfinance"""
    import yfinance as yf

    metrics = []

    try:
        # Get ticker data
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info

        # Map yfinance fields to our metrics (including calculated ratios)
        yfinance_mapping = {
            'current_price': ('currentPrice', 'regularMarketPrice'),
            'pe_ratio': ('trailingPE', 'forwardPE'),
            'eps': ('trailingEps', 'forwardEps'),
            'pb_ratio': ('priceToBook',),
            'peg_ratio': ('pegRatio',),
            'price_sales': ('priceToSalesTrailing12Months',),
            'market_cap': ('marketCap',),
            'dividend_yield': ('dividendYield',),
            'beta': ('beta',),
            'fifty_two_week_high': ('fiftyTwoWeekHigh',),
            'fifty_two_week_low': ('fiftyTwoWeekLow',),
            'roe': ('returnOnEquity',),
            'roa': ('returnOnAssets',),
        }

        for metric_def in FINANCIAL_METRICS:
            # Check both yfinance source AND if it's available in yfinance as fallback
            if metric_def['source'] == 'yfinance' or metric_def['key'] in yfinance_mapping:
                value = None
                confidence = 0.0

                # Try to get value from yfinance
                if metric_def['key'] in yfinance_mapping:
                    for field in yfinance_mapping[metric_def['key']]:
                        if field in info and info[field] is not None:
                            value = info[field]
                            
                            # Professional formatting for analysts
                            if metric_def['key'] == 'market_cap':
                                if value >= 1_000_000_000_000:
                                    value = f"{value/1_000_000_000_000:.2f}T"
                                elif value >= 1_000_000_000:
                                    value = f"{value/1_000_000_000:.2f}B"
                                elif value >= 1_000_000:
                                    value = f"{value/1_000_000:.2f}M"
                            elif metric_def['key'] in ['roe', 'roa', 'dividend_yield']:
                                value = f"{value * 100:.2f}%"
                            elif metric_def['key'] in ['pe_ratio', 'pb_ratio', 'peg_ratio', 'price_sales', 'beta']:
                                value = round(float(value), 2)
                                
                            confidence = 1.0
                            break

                # Special calculations
                if metric_def['key'] == 'volatility' and value is None:
                    hist = ticker.history(period="1y")
                    if not hist.empty:
                        vol = float(hist['Close'].pct_change().std() * (252 ** 0.5))
                        value = f"{vol * 100:.2f}%"
                        confidence = 0.9

                # Only add if from yfinance source
                if metric_def['source'] == 'yfinance':
                    metrics.append(MetricValue(
                        key=metric_def['key'],
                        name=metric_def['name'],
                        value=value,
                        source='yfinance' if value is not None else 'not_found',
                        confidence=confidence,
                        extracted_at=datetime.now()
                    ))

    except Exception as e:
        print(f"Error fetching yfinance data for {ticker_symbol}: {str(e)}")
        # Return empty metrics with error status
        for metric_def in FINANCIAL_METRICS:
            if metric_def['source'] == 'yfinance':
                metrics.append(MetricValue(
                    key=metric_def['key'],
                    name=metric_def['name'],
                    value=None,
                    source='error',
                    confidence=0.0,
                    extracted_at=datetime.now()
                ))

    return metrics


# ============================================================================
# GET CACHED ANALYTICS
# ============================================================================

@router.get("/{company_id}", response_model=AnalyticsResponse)
async def get_analytics(
    company_id: str,
    ticker_symbol: Optional[str] = None,
    rag: RAGService = Depends(get_rag_service),
    db: DatabaseManager = Depends(get_db)
):
    """Get analytics for a company (cached or generate new)"""

    # Get company name from database
    async with db.get_cursor() as cursor:
        cursor.execute("""
            SELECT company_name
            FROM document_chunks_v2
            WHERE company_id = %s
            LIMIT 1
        """, (company_id,))

        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Company not found")

        company_name = row['company_name']

    # For now, always generate fresh (can add caching later)
    return await generate_analytics(
        AnalyticsRequest(
            company_id=company_id,
            company_name=company_name,
            ticker_symbol=ticker_symbol,
            force_refresh=False
        ),
        rag=rag,
        db=db
    )
