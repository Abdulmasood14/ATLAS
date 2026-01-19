"""
Comprehensive Test Suite for Section Context-Aware RAG System
==============================================================

Tests:
1. Objective Questions (Numbers, Facts, Tables)
2. Subjective Questions (Policies, Methodologies, Explanations)
3. Section-Aware Queries (Consolidated vs Standalone)
4. Note-Specific Queries
"""

from query_engine import FinancialRAGV2
import time

# Database config
db_config = {
    'host': 'localhost',
    'database': 'financial_rag',
    'user': 'postgres',
    'password': 'Prasanna!@#2002'
}

print("="*80)
print("COMPREHENSIVE TEST SUITE - SECTION CONTEXT-AWARE RAG")
print("="*80)
print("\nInitializing RAG system...")

rag = FinancialRAGV2(db_config=db_config)
print("System initialized!\n")

# Test queries organized by category
test_suite = {
    "OBJECTIVE QUESTIONS (Numbers, Facts, Tables)": [
        # {
        #     'query': "What is Note 10 about in Consolidated Financial Statement?",
        #     'description': "Trade Receivables from Consolidated FS",
        #     'expected': "Trade Receivables with exact amounts (should be different from standalone)",
        #     'category': 'objective'
        # },
        # {
        #     'query': "What is Note 9 about in Standalone Financial Statement?",
        #     'description': "Note 9 from Standalone FS",
        #     'expected': "Should return standalone data (different note number may have different content)",
        #     'category': 'objective'
        # },
        {
            'query': "What is the Trade Receivables?",
            'description': "",
            'expected': "",
            'category': 'objective'
        },
        # {
        #     'query': "What is the total revenue from operations in the Consolidated Statement of Profit and Loss?",
        #     'description': "Revenue from Consolidated P&L",
        #     'expected': "Revenue figures from consolidated P&L only",
        #     'category': 'objective'
        # },
        # {
        #     'query': "What is the depreciation rate for Property, Plant and Equipment?",
        #     'description': "Depreciation rate extraction",
        #     'expected': "Percentage rates for different asset categories",
        #     'category': 'objective'
        # }
    ],

    # "SUBJECTIVE QUESTIONS (Policies, Methodologies, Explanations)": [
    #     {
    #         'query': "How is the fair value of investment properties determined in the Consolidated Financial Statements?",
    #         'description': "Fair value methodology",
    #         'expected': "Explanation of valuation approach, assumptions, standards used",
    #         'category': 'subjective'
    #     },
    #     {
    #         'query': "What is the accounting policy for revenue recognition?",
    #         'description': "Revenue recognition policy",
    #         'expected': "Policy description with applicable accounting standards (Ind AS 115, etc.)",
    #         'category': 'subjective'
    #     },
    #     {
    #         'query': "What assumptions are used in the provision matrix for trade receivables?",
    #         'description': "ECL assumptions and methodology",
    #         'expected': "Expected Credit Loss model explanation, aging buckets, credit risk assessment",
    #         'category': 'subjective'
    #     },
    #     {
    #         'query': "What is the basis of preparation of financial statements?",
    #         'description': "Accounting basis and standards",
    #         'expected': "Ind AS compliance, accrual basis, going concern, etc.",
    #         'category': 'subjective'
    #     }
    # ],

    # "SECTION-AWARE QUERIES (Consolidated vs Standalone)": [
    #     {
    #         'query': "What are the current assets in the Consolidated Balance Sheet?",
    #         'description': "Current assets from consolidated only",
    #         'expected': "List of current assets from consolidated balance sheet",
    #         'category': 'section-aware'
    #     },
    #     {
    #         'query': "What are the current assets in the Standalone Balance Sheet?",
    #         'description': "Current assets from standalone only",
    #         'expected': "List of current assets from standalone (should differ from consolidated)",
    #         'category': 'section-aware'
    #     },
    #     {
    #         'query': "What is Note 3A about in Consolidated Financial Statement?",
    #         'description': "Note 3A from consolidated",
    #         'expected': "Property, Plant & Equipment or similar (consolidated version)",
    #         'category': 'section-aware'
    #     }
    # ],

    # "NOTE-SPECIFIC QUERIES": [
    #     {
    #         'query': "What does Note 12 explain in the financial statements?",
    #         'description': "Note 12 content",
    #         'expected': "Complete explanation of what Note 12 covers",
    #         'category': 'notes'
    #     },
    #     {
    #         'query': "List all information available in Note 1",
    #         'description': "Note 1 complete content",
    #         'expected': "Corporate information or accounting policies from Note 1",
    #         'category': 'notes'
    #     }
    # ]
}

def run_test_category(category_name, questions, company_id='BAR_999'):
    """Run tests for a specific category"""
    print("\n" + "="*80)
    print(f"{category_name}")
    print("="*80)

    results = []

    for i, test in enumerate(questions, 1):
        print(f"\n{'─'*80}")
        print(f"Test {i}/{len(questions)}: {test['description']}")
        print(f"{'─'*80}")
        print(f"Category: {test['category'].upper()}")
        print(f"Query: \"{test['query']}\"")
        print(f"Expected: {test['expected']}")
        print()

        start_time = time.time()

        try:
            # Execute query
            response = rag.query(
                query=test['query'],
                company_id=company_id,
                top_k=7,
                verbose=False  # Set to True for debugging
            )

            elapsed = time.time() - start_time

            if response.success:
                print(f"✓ SUCCESS ({elapsed:.2f}s)")
                print(f"\n{'─'*80}")
                print("ANSWER:")
                print(f"{'─'*80}")
                print(response.answer)
                print(f"\n{'─'*80}")
                print(f"Model: {response.model_used}")
                print(f"Retrieval: {response.retrieval_tier_used}")
                print(f"Sources: {len(response.sources)} chunks")

                # Show top 3 sources
                if response.sources:
                    print(f"\nTop 3 Source Chunks:")
                    for j, source in enumerate(response.sources[:3], 1):
                        pages = source.get('pages', [])
                        note = source.get('note', 'N/A')
                        score = source.get('score', 0)
                        sections = source.get('sections', [])
                        print(f"  [{j}] Pages: {pages}, Note: {note}, Score: {score:.3f}, Sections: {sections[:2]}")

                results.append({
                    'test': test['description'],
                    'query': test['query'],
                    'category': test['category'],
                    'success': True,
                    'answer_length': len(response.answer),
                    'source_count': len(response.sources),
                    'elapsed': elapsed
                })
            else:
                print(f"✗ FAILED ({elapsed:.2f}s)")
                print(f"Error: {response.error}")
                results.append({
                    'test': test['description'],
                    'query': test['query'],
                    'category': test['category'],
                    'success': False,
                    'error': response.error,
                    'elapsed': elapsed
                })

        except Exception as e:
            elapsed = time.time() - start_time
            print(f"✗ EXCEPTION ({elapsed:.2f}s)")
            print(f"Error: {e}")
            results.append({
                'test': test['description'],
                'query': test['query'],
                'category': test['category'],
                'success': False,
                'error': str(e),
                'elapsed': elapsed
            })

        print()

    return results

# Run all test categories
all_results = {}
total_tests = 0
total_passed = 0

for category, questions in test_suite.items():
    results = run_test_category(category, questions)
    all_results[category] = results

    passed = sum(1 for r in results if r['success'])
    total = len(results)
    total_tests += total
    total_passed += passed

# Final Summary
print("\n" + "="*80)
print("FINAL TEST SUMMARY")
print("="*80)

for category, results in all_results.items():
    passed = sum(1 for r in results if r['success'])
    total = len(results)
    percentage = (passed/total*100) if total > 0 else 0
    print(f"\n{category}:")
    print(f"  Passed: {passed}/{total} ({percentage:.1f}%)")

    # Show failed tests
    failed = [r for r in results if not r['success']]
    if failed:
        print(f"  Failed tests:")
        for r in failed:
            print(f"    - {r['test']}")
            print(f"      Error: {r.get('error', 'Unknown')}")

print(f"\n{'─'*80}")
print(f"OVERALL: {total_passed}/{total_tests} tests passed ({(total_passed/total_tests*100):.1f}%)")
print(f"{'─'*80}")

# Performance stats
all_results_flat = [r for results in all_results.values() for r in results]
successful_results = [r for r in all_results_flat if r['success']]

if successful_results:
    avg_time = sum(r['elapsed'] for r in successful_results) / len(successful_results)
    avg_sources = sum(r['source_count'] for r in successful_results) / len(successful_results)
    avg_answer_length = sum(r['answer_length'] for r in successful_results) / len(successful_results)

    print(f"\nPerformance Metrics:")
    print(f"  Average response time: {avg_time:.2f}s")
    print(f"  Average sources per query: {avg_sources:.1f}")
    print(f"  Average answer length: {avg_answer_length:.0f} chars")

print("\n" + "="*80)
print("TEST SUITE COMPLETE")
print("="*80)

# Close RAG system
rag.close()

print("\nRAG system closed. Test results saved above.")
