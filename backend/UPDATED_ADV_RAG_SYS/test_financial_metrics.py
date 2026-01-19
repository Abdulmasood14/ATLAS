"""
Comprehensive Financial Metrics Test Suite
==========================================

Tests based on questions.txt for IND_001 and TINNA_111
Covers objective metrics, semi-objective data, and subjective insights.
"""

from query_engine import FinancialRAGV2
import time
import pandas as pd
from datetime import datetime
import os

# Database config
db_config = {
    'host': 'localhost',
    'database': 'financial_rag',
    'user': 'postgres',
    'password': 'Prasanna!@#2002'
}

print("="*80)
print("FINANCIAL METRICS TEST SUITE - BASED ON QUESTIONS.TXT")
print("="*80)
print("\nInitializing RAG system...")

rag = FinancialRAGV2(db_config=db_config)
print("System initialized!\n")

# Test suite organized by question categories from questions.txt
test_suite = {
    "OBJECTIVE - FINANCIAL PERFORMANCE": [
        {
            'query': "What is the revenue growth rate over the past 3 years?",
            'description': "Revenue growth rate (3 years)",
            'expected': "Revenue growth percentages YoY for 3 years",
            'category': 'objective-financial'
        },
        {
            'query': "How are the profit margins (gross, EBITDA, net) trending?",
            'description': "Profit margins trend",
            'expected': "Gross margin, EBITDA margin, Net margin with trends",
            'category': 'objective-financial'
        },
        {
            'query': "Is the company generating positive operating cash flows?",
            'description': "Operating cash flow status",
            'expected': "Cash flow from operations - positive/negative with amounts",
            'category': 'objective-financial'
        },
        {
            'query': "What is the Return on Equity (ROE) and Return on Assets (ROA)?",
            'description': "ROE and ROA",
            'expected': "ROE and ROA percentages",
            'category': 'objective-financial'
        },
        {
            'query': "What is the debt-to-equity ratio and interest coverage ratio?",
            'description': "Debt ratios",
            'expected': "D/E ratio and interest coverage ratio",
            'category': 'objective-financial'
        },
        {
            'query': "What is the dividend payout ratio and dividend yield?",
            'description': "Dividend metrics",
            'expected': "Payout ratio and dividend yield percentages",
            'category': 'objective-financial'
        }
    ],

    "SEMI-OBJECTIVE - BUSINESS METRICS": [
        {
            'query': "How much is the company spending on capital expenditure and R&D?",
            'description': "Capex and R&D spending",
            'expected': "Capex amount and R&D expenses",
            'category': 'semi-objective'
        },
        {
            'query': "What is the market share of the company in key product lines?",
            'description': "Market share by product",
            'expected': "Market share percentages for main products",
            'category': 'semi-objective'
        },
        {
            'query': "What is the revenue breakup by geography?",
            'description': "Geographic revenue distribution",
            'expected': "Revenue split by regions/countries",
            'category': 'semi-objective'
        },
        {
            'query': "What is the revenue breakup by product line?",
            'description': "Product line revenue distribution",
            'expected': "Revenue split by product categories",
            'category': 'semi-objective'
        },
        {
            'query': "What is the company's business vision, mission, or 5-year plan?",
            'description': "Business vision and strategy",
            'expected': "Vision statement, mission, strategic goals",
            'category': 'semi-objective'
        },
        {
            'query': "What are the company's financial targets for the coming years?",
            'description': "Financial targets",
            'expected': "Revenue targets, margin targets, growth objectives",
            'category': 'semi-objective'
        }
    ],

    "SEMI-OBJECTIVE - INDUSTRY-SPECIFIC METRICS": [
        {
            'query': "What are the key operational parameters like same store sales growth, number of outlets, or new units added?",
            'description': "Retail operational metrics",
            'expected': "SSG, store count, new store additions (for retail)",
            'category': 'industry-specific'
        },
        {
            'query': "What are the banking metrics like number of branches, NPAs, and NIMs?",
            'description': "Banking operational metrics",
            'expected': "Branch count, NPA ratios, Net Interest Margin (for banking)",
            'category': 'industry-specific'
        },
        {
            'query': "What are the pharma metrics like USFDA inspections, approvals, MDFs filings, or ANDAs filings?",
            'description': "Pharma regulatory metrics",
            'expected': "USFDA status, approvals, regulatory filings (for pharma)",
            'category': 'industry-specific'
        },
        {
            'query': "What is the status of new orders, total order book, and order book growth?",
            'description': "Order book metrics",
            'expected': "New orders, total order book, YoY growth, execution pipeline",
            'category': 'industry-specific'
        }
    ],

    "SUBJECTIVE - RISKS & GOVERNANCE": [
        {
            'query': "What are the major risk factors disclosed by the company?",
            'description': "Risk factors",
            'expected': "Key business, financial, operational, regulatory risks",
            'category': 'subjective'
        },
        {
            'query': "Are there any significant related party transactions disclosed in the financial statements?",
            'description': "Related party transactions",
            'expected': "Details of RPTs with amounts and parties",
            'category': 'subjective'
        },
        {
            'query': "Are there any pending legal cases or regulatory issues mentioned?",
            'description': "Legal and regulatory issues",
            'expected': "Pending litigations, regulatory matters",
            'category': 'subjective'
        }
    ],

    "SUBJECTIVE - STRATEGIC INITIATIVES": [
        {
            'query': "What is the status of Capex or updates on Greenfield and Brownfield projects or expansion plans?",
            'description': "Capex and expansion updates",
            'expected': "Project status, expansion plans, timeline",
            'category': 'strategic'
        },
        {
            'query': "What are the company's new initiatives to increase revenue?",
            'description': "Revenue growth initiatives",
            'expected': "New products, markets, strategies to boost revenue",
            'category': 'strategic'
        },
        {
            'query': "What initiatives has the company taken to improve margins (EBITDA/Operating Margin)?",
            'description': "Margin improvement initiatives",
            'expected': "Cost optimization, efficiency programs",
            'category': 'strategic'
        },
        {
            'query': "What measures are being taken to improve ROCE, ROE, or ROIC?",
            'description': "Return ratios improvement",
            'expected': "Capital efficiency initiatives, asset optimization",
            'category': 'strategic'
        }
    ]
}

def run_test_for_company(company_id, company_name):
    """Run all tests for a specific company"""
    print(f"\n{'='*80}")
    print(f"TESTING: {company_name} ({company_id})")
    print(f"{'='*80}")

    all_results = []

    for category, questions in test_suite.items():
        print(f"\n{'-'*80}")
        print(f"Category: {category}")
        print(f"{'-'*80}")

        for i, test in enumerate(questions, 1):
            print(f"\n[{i}/{len(questions)}] {test['description']}...", end=' ')

            start_time = time.time()

            try:
                response = rag.query(
                    query=test['query'],
                    company_id=company_id,
                    top_k=7,
                    verbose=False
                )

                elapsed = time.time() - start_time

                if response.success:
                    print(f"SUCCESS ({elapsed:.1f}s)")

                    result = {
                        'Company_ID': company_id,
                        'Company_Name': company_name,
                        'Category': category,
                        'Question': test['query'],
                        'Description': test['description'],
                        'Status': 'SUCCESS',
                        'Answer': response.answer,
                        'Answer_Length': len(response.answer),
                        'Source_Count': len(response.sources),
                        'Model': response.model_used,
                        'Retrieval_Method': response.retrieval_tier_used,
                        'Response_Time_Sec': round(elapsed, 2),
                        'Error': None,
                        'Top_Note': response.sources[0].get('note', 'N/A') if response.sources else 'N/A',
                        'Top_Pages': str(response.sources[0].get('pages', [])[:5]) if response.sources else 'N/A'
                    }
                else:
                    print(f"FAILED ({elapsed:.1f}s) - {response.error}")

                    result = {
                        'Company_ID': company_id,
                        'Company_Name': company_name,
                        'Category': category,
                        'Question': test['query'],
                        'Description': test['description'],
                        'Status': 'FAILED',
                        'Answer': None,
                        'Answer_Length': 0,
                        'Source_Count': 0,
                        'Model': None,
                        'Retrieval_Method': None,
                        'Response_Time_Sec': round(elapsed, 2),
                        'Error': response.error,
                        'Top_Note': None,
                        'Top_Pages': None
                    }

            except Exception as e:
                elapsed = time.time() - start_time
                print(f"EXCEPTION ({elapsed:.1f}s) - {str(e)[:50]}")

                result = {
                    'Company_ID': company_id,
                    'Company_Name': company_name,
                    'Category': category,
                    'Question': test['query'],
                    'Description': test['description'],
                    'Status': 'EXCEPTION',
                    'Answer': None,
                    'Answer_Length': 0,
                    'Source_Count': 0,
                    'Model': None,
                    'Retrieval_Method': None,
                    'Response_Time_Sec': round(elapsed, 2),
                    'Error': str(e),
                    'Top_Note': None,
                    'Top_Pages': None
                }

            all_results.append(result)

    return all_results

# Companies to test
companies = [
    {'id': 'IND_001', 'name': 'Company IND_001'},
    {'id': 'TINNA_111', 'name': 'Company TINNA_111'}
]

# Run tests for all companies
all_company_results = []

for company in companies:
    company_results = run_test_for_company(company['id'], company['name'])
    all_company_results.extend(company_results)
    time.sleep(1)  # Brief pause between companies

# Create DataFrame
df = pd.DataFrame(all_company_results)

# Generate filename with timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
excel_filename = f"Financial_Metrics_Test_Results_{timestamp}.xlsx"
excel_path = os.path.join(os.getcwd(), excel_filename)

# Save to Excel with multiple sheets
print(f"\n{'='*80}")
print("SAVING RESULTS TO EXCEL")
print(f"{'='*80}")

with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
    # Sheet 1: All results
    df.to_excel(writer, sheet_name='All Results', index=False)

    # Sheet 2: IND_001 only
    df_ind = df[df['Company_ID'] == 'IND_001']
    df_ind.to_excel(writer, sheet_name='IND_001', index=False)

    # Sheet 3: TINNA_111 only
    df_tinna = df[df['Company_ID'] == 'TINNA_111']
    df_tinna.to_excel(writer, sheet_name='TINNA_111', index=False)

    # Sheet 4: Summary statistics
    summary_data = []
    for company in companies:
        company_df = df[df['Company_ID'] == company['id']]

        total_tests = len(company_df)
        passed = len(company_df[company_df['Status'] == 'SUCCESS'])
        failed = len(company_df[company_df['Status'] == 'FAILED'])
        exceptions = len(company_df[company_df['Status'] == 'EXCEPTION'])

        avg_response_time = company_df[company_df['Status'] == 'SUCCESS']['Response_Time_Sec'].mean()
        avg_answer_length = company_df[company_df['Status'] == 'SUCCESS']['Answer_Length'].mean()
        avg_sources = company_df[company_df['Status'] == 'SUCCESS']['Source_Count'].mean()

        summary_data.append({
            'Company_ID': company['id'],
            'Company_Name': company['name'],
            'Total_Tests': total_tests,
            'Passed': passed,
            'Failed': failed,
            'Exceptions': exceptions,
            'Pass_Rate_%': round(passed/total_tests*100, 1) if total_tests > 0 else 0,
            'Avg_Response_Time_Sec': round(avg_response_time, 2) if pd.notna(avg_response_time) else 0,
            'Avg_Answer_Length': round(avg_answer_length, 0) if pd.notna(avg_answer_length) else 0,
            'Avg_Source_Count': round(avg_sources, 1) if pd.notna(avg_sources) else 0
        })

    df_summary = pd.DataFrame(summary_data)
    df_summary.to_excel(writer, sheet_name='Summary', index=False)

    # Sheet 5: Category-wise breakdown
    category_data = []
    for company in companies:
        company_df = df[df['Company_ID'] == company['id']]
        for category in df['Category'].unique():
            cat_df = company_df[company_df['Category'] == category]
            total = len(cat_df)
            passed = len(cat_df[cat_df['Status'] == 'SUCCESS'])

            category_data.append({
                'Company_ID': company['id'],
                'Category': category,
                'Total': total,
                'Passed': passed,
                'Failed': total - passed,
                'Pass_Rate_%': round(passed/total*100, 1) if total > 0 else 0
            })

    df_category = pd.DataFrame(category_data)
    df_category.to_excel(writer, sheet_name='Category Breakdown', index=False)

print(f"\n[OK] Results saved to: {excel_filename}")
print(f"  Location: {excel_path}")

# Print summary to console
print(f"\n{'='*80}")
print("FINAL SUMMARY")
print(f"{'='*80}")

for company in companies:
    company_df = df[df['Company_ID'] == company['id']]
    total = len(company_df)
    passed = len(company_df[company_df['Status'] == 'SUCCESS'])

    print(f"\n{company['name']} ({company['id']}):")
    print(f"  Total Tests: {total}")
    print(f"  Passed: {passed}/{total} ({passed/total*100:.1f}%)")
    print(f"  Failed: {total - passed}")

    # Category breakdown
    for category in test_suite.keys():
        cat_df = company_df[company_df['Category'] == category]
        if len(cat_df) > 0:
            cat_passed = len(cat_df[cat_df['Status'] == 'SUCCESS'])
            print(f"    {category}: {cat_passed}/{len(cat_df)} passed")

print(f"\n{'='*80}")
print("TEST SUITE COMPLETE")
print(f"{'='*80}")

# Close RAG system
rag.close()

print(f"\n[OK] Excel file created: {excel_filename}")
print(f"[OK] Total questions per company: {len(all_company_results) // len(companies)}")
print(f"[OK] Total responses captured: {len(all_company_results)}")
