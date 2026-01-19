"""
Interactive Financial RAG - Complete Workflow

This script handles:
1. PDF ingestion (optional)
2. Interactive querying
3. Company management

User can either:
- Ingest a new PDF and query it
- Query existing PDFs
- Switch between companies

Usage:
    python interactive_rag.py
"""
from query_engine import FinancialRAGV2
from ingest_pdf import PDFIngestionPipeline
import os
import sys
import psycopg2


def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header():
    """Print header"""
    print("=" * 80)
    print("FINANCIAL RAG V2 - INTERACTIVE SYSTEM")
    print("=" * 80)
    print()


def get_existing_companies():
    """Get list of companies already in the database"""
    try:
        db_config = {
            'host': 'localhost',
            'database': 'financial_rag',
            'user': 'postgres',
            'password': 'Prasanna!@#2002'
        }

        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT company_id, company_name, COUNT(*) as chunk_count
            FROM document_chunks_v2
            GROUP BY company_id, company_name
            ORDER BY company_id
        """)

        companies = cursor.fetchall()
        cursor.close()
        conn.close()

        return companies
    except Exception as e:
        print(f"Warning: Could not fetch companies: {e}")
        return []


def ingest_new_pdf():
    """Handle PDF ingestion workflow"""
    print()
    print("-" * 80)
    print("PDF INGESTION")
    print("-" * 80)
    print()

    # Get PDF path
    pdf_path = input("Enter PDF file path: ").strip().strip('"')

    if not os.path.exists(pdf_path):
        print(f"\nError: File not found: {pdf_path}")
        return None

    # Get company details
    print()
    company_id = input("Enter Company ID (e.g., REL_001, INFY_001): ").strip()
    company_name = input("Enter Company Name (e.g., Reliance Industries): ").strip()
    fiscal_year = input("Enter Fiscal Year (e.g., 2024-25): ").strip()

    if not company_id or not company_name:
        print("\nError: Company ID and Name are required!")
        return None

    # Confirm
    print()
    print("=" * 80)
    print("INGESTION SUMMARY")
    print("=" * 80)
    print(f"PDF Path: {pdf_path}")
    print(f"Company ID: {company_id}")
    print(f"Company Name: {company_name}")
    print(f"Fiscal Year: {fiscal_year or 'Not specified'}")
    print("=" * 80)

    confirm = input("\nProceed with ingestion? (yes/no): ").strip().lower()

    if confirm not in ['yes', 'y']:
        print("Ingestion cancelled.")
        return None

    # Ingest PDF
    print()
    print("=" * 80)
    print("STARTING INGESTION...")
    print("=" * 80)
    print()

    try:
        # Initialize ingestor
        db_config = {
            'host': 'localhost',
            'database': 'financial_rag',
            'user': 'postgres',
            'password': 'Prasanna!@#2002'
        }

        ingestor = PDFIngestionPipeline(db_config)

        # Ingest
        result = ingestor.ingest_pdf(
            pdf_path=pdf_path,
            company_id=company_id,
            company_name=company_name,
            fiscal_year=fiscal_year
        )

        ingestor.close()

        if result['status'] == 'success':
            print()
            print("=" * 80)
            print("INGESTION SUCCESSFUL!")
            print("=" * 80)
            print(f"Total chunks created: {result['chunks_created']}")
            print(f"Chunks stored: {result['chunks_stored']}")
            print()
            print(f"You can now query company: {company_id}")
            print("=" * 80)
            return company_id
        else:
            print()
            print("=" * 80)
            print("INGESTION FAILED")
            print("=" * 80)
            print(f"Error: {result.get('error', 'Unknown error')}")
            print("=" * 80)
            return None

    except Exception as e:
        print()
        print("=" * 80)
        print("INGESTION ERROR")
        print("=" * 80)
        print(f"Error: {str(e)}")
        print("=" * 80)
        import traceback
        traceback.print_exc()
        return None


def query_company(rag, company_id):
    """Interactive query loop for a company"""
    print()
    print("=" * 80)
    print(f"QUERYING: {company_id}")
    print("=" * 80)
    print()
    print("Ask questions about the financial document.")
    print("Type 'back' to return to main menu, 'exit' to quit.")
    print("-" * 80)
    print()

    while True:
        query = input("Your question: ").strip()

        if not query:
            continue

        if query.lower() in ['exit', 'quit', 'q']:
            return 'exit'

        if query.lower() in ['back', 'b', 'menu']:
            return 'back'

        print()
        print("-" * 80)
        print("Processing...")
        print("-" * 80)

        try:
            response = rag.query(query, company_id, verbose=False)

            if response.success:
                print()
                print("=" * 80)
                print("ANSWER")
                print("=" * 80)
                print(response.answer)
                print()
                print("-" * 80)
                print(f"Model: {response.model_used}")
                print(f"Sources: {len(response.sources)} chunks")
                print(f"Retrieval: {response.retrieval_tier_used}")

                # Show source pages (only from top 5 sources, with limited page range)
                pages = set()
                for source in response.sources[:5]:  # Top 5 sources only
                    source_pages = source.get('pages', [])
                    # If a chunk spans many pages (like a large note), only show first and last
                    if len(source_pages) > 5:
                        # Show first 3 and last 2 pages to indicate range
                        pages.add(source_pages[0])
                        pages.add(source_pages[1])
                        pages.add(source_pages[2])
                        pages.add(source_pages[-2])
                        pages.add(source_pages[-1])
                    else:
                        pages.update(source_pages)

                if pages:
                    sorted_pages = sorted(pages)
                    # Format nicely if there are gaps
                    if len(sorted_pages) > 10:
                        print(f"Pages: {sorted_pages[0]}-{sorted_pages[-1]} (spanning {len(sorted_pages)} pages)")
                    else:
                        print(f"Pages: {sorted_pages}")
                print("-" * 80)
            else:
                print()
                print("=" * 80)
                print("ERROR")
                print("=" * 80)
                print(response.answer)
                if response.error:
                    print(f"\nDetails: {response.error}")
                print("=" * 80)

        except Exception as e:
            print()
            print("=" * 80)
            print("ERROR")
            print("=" * 80)
            print(f"Failed to process query: {e}")
            print("=" * 80)

        print()


def main():
    """Main interactive loop"""
    clear_screen()
    print_header()

    print("Initializing Financial RAG V2...")
    try:
        rag = FinancialRAGV2()
        print("System initialized successfully!")
    except Exception as e:
        print(f"ERROR: Failed to initialize system: {e}")
        print("\nPlease check:")
        print("1. PostgreSQL is running")
        print("2. Database 'financial_rag' exists")
        print("3. BGE-M3 embedding model is available")
        print("4. LLM endpoint is accessible")
        return

    current_company = None

    while True:
        print()
        print("=" * 80)
        print("MAIN MENU")
        print("=" * 80)
        print()
        print("1. Ingest new PDF")
        print("2. Query existing company")
        print("3. List available companies")
        print("4. Exit")
        print()

        choice = input("Select option (1-4): ").strip()

        if choice == '1':
            # Ingest new PDF
            company_id = ingest_new_pdf()
            if company_id:
                current_company = company_id
                # Offer to query immediately
                query_now = input("\nQuery this company now? (yes/no): ").strip().lower()
                if query_now in ['yes', 'y']:
                    result = query_company(rag, current_company)
                    if result == 'exit':
                        break

        elif choice == '2':
            # Query existing company
            companies = get_existing_companies()

            if not companies:
                print("\nNo companies found in database.")
                print("Please ingest a PDF first (option 1).")
                continue

            print()
            print("-" * 80)
            print("AVAILABLE COMPANIES")
            print("-" * 80)
            for i, (comp_id, comp_name, chunk_count) in enumerate(companies, 1):
                print(f"{i}. {comp_id} - {comp_name} ({chunk_count} chunks)")
            print("-" * 80)
            print()

            company_input = input("Enter company ID or number: ").strip()

            # Check if input is a number (index)
            if company_input.isdigit():
                idx = int(company_input) - 1
                if 0 <= idx < len(companies):
                    current_company = companies[idx][0]
                else:
                    print(f"\nInvalid selection: {company_input}")
                    continue
            else:
                # Check if company exists
                company_ids = [c[0] for c in companies]
                if company_input in company_ids:
                    current_company = company_input
                else:
                    print(f"\nCompany not found: {company_input}")
                    continue

            result = query_company(rag, current_company)
            if result == 'exit':
                break

        elif choice == '3':
            # List companies
            companies = get_existing_companies()

            print()
            print("=" * 80)
            print("AVAILABLE COMPANIES")
            print("=" * 80)

            if companies:
                print()
                for comp_id, comp_name, chunk_count in companies:
                    print(f"  {comp_id:20s} - {comp_name:30s} ({chunk_count:4d} chunks)")
                print()
            else:
                print("\nNo companies found in database.")
                print("Please ingest a PDF first (option 1).")

            print("=" * 80)

        elif choice == '4':
            # Exit
            break

        else:
            print("\nInvalid option. Please select 1-4.")

    print()
    print("Closing system...")
    rag.close()
    print("Goodbye!")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        print("Goodbye!")
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
