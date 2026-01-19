"""
Simple Query Script
===================
Direct command-line interface for querying the RAG system.

Usage:
    python simple_query.py "Your question here" COMPANY_ID

Example:
    python simple_query.py "What is the Trade Receivables?" IND_001
"""

import sys
from query_engine import FinancialRAGV2

def main():
    if len(sys.argv) < 3:
        print("="*80)
        print("SIMPLE QUERY - Financial RAG V2")
        print("="*80)
        print("\nUsage:")
        print('  python simple_query.py "Your question" COMPANY_ID')
        print("\nExample:")
        print('  python simple_query.py "What is the Trade Receivables?" IND_001')
        print('  python simple_query.py "What is Note 10 in Consolidated FS?" COMPANY_001')
        print("\nOptions:")
        print("  --verbose    Show detailed retrieval information")
        print("  --top_k N    Number of chunks to retrieve (default: 7)")
        print("\n" + "="*80)
        sys.exit(1)

    # Parse arguments
    query = sys.argv[1]
    company_id = sys.argv[2]

    # Optional arguments
    verbose = '--verbose' in sys.argv
    top_k = 7

    # Check for top_k
    if '--top_k' in sys.argv:
        try:
            idx = sys.argv.index('--top_k')
            top_k = int(sys.argv[idx + 1])
        except (IndexError, ValueError):
            print("Error: --top_k requires a number")
            sys.exit(1)

    print("="*80)
    print("FINANCIAL RAG V2 - QUERY")
    print("="*80)
    print(f"\nCompany: {company_id}")
    print(f"Query: {query}")
    print(f"Top-K: {top_k}")
    print(f"Verbose: {verbose}")
    print()

    # Initialize RAG system
    print("Initializing RAG system...")
    rag = FinancialRAGV2()
    print("System ready!")
    print()

    # Execute query
    try:
        response = rag.query(
            query=query,
            company_id=company_id,
            top_k=top_k,
            verbose=verbose
        )

        if response.success:
            print("="*80)
            print("ANSWER")
            print("="*80)
            print(response.answer)
            print()

            print("="*80)
            print(f"SOURCES ({len(response.sources)} chunks)")
            print("="*80)
            for i, source in enumerate(response.sources[:5], 1):
                print(f"\n[{i}] Pages: {source['pages']}")
                if source.get('note'):
                    print(f"    Note: {source['note']}")
                if source.get('sections'):
                    print(f"    Sections: {source['sections']}")
                print(f"    Score: {source['score']:.3f}")
                print(f"    Tier: {source['tier']}")
                print(f"    Preview: {source['text'][:100]}...")

            print()
            print("="*80)
            print(f"Model: {response.model_used}")
            print(f"Retrieval: {response.retrieval_tier_used}")
            print("="*80)

        else:
            print("="*80)
            print("QUERY FAILED")
            print("="*80)
            print(f"Error: {response.error}")
            print()

            if "No relevant information found" in str(response.error):
                print("Possible reasons:")
                print("  1. Company not ingested yet")
                print("  2. Company ID incorrect")
                print("  3. Database connection issue")
                print()
                print("Try:")
                print(f'  python check_progress.py  # Check if {company_id} is ingested')

    except Exception as e:
        print("="*80)
        print("EXCEPTION OCCURRED")
        print("="*80)
        print(f"Error: {e}")
        print()
        import traceback
        traceback.print_exc()

    finally:
        rag.close()
        print()
        print("RAG system closed.")

if __name__ == "__main__":
    main()
