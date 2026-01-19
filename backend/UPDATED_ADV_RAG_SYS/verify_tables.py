"""
Verify that database tables were created successfully
"""
import psycopg2

def verify_tables():
    """Check if required tables exist"""

    db_config = {
        'host': 'localhost',
        'database': 'financial_rag',
        'user': 'postgres',
        'password': 'Prasanna!@#2002'
    }

    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        # Check if document_chunks_v2 exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'document_chunks_v2'
            );
        """)
        chunks_exists = cursor.fetchone()[0]

        # Check if financial_metrics_v2 exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'financial_metrics_v2'
            );
        """)
        metrics_exists = cursor.fetchone()[0]

        print("=" * 80)
        print("DATABASE VERIFICATION")
        print("=" * 80)
        print()
        print(f"document_chunks_v2: {'EXISTS' if chunks_exists else 'MISSING'}")
        print(f"financial_metrics_v2: {'EXISTS' if metrics_exists else 'MISSING'}")
        print()

        if chunks_exists and metrics_exists:
            print("SUCCESS: All required tables exist!")
            print()
            print("You can now run your PDF ingestion pipeline.")
        else:
            print("ERROR: Some tables are missing!")

        cursor.close()
        conn.close()

        return chunks_exists and metrics_exists

    except Exception as e:
        print("=" * 80)
        print("ERROR")
        print("=" * 80)
        print(f"\nError: {e}")
        return False


if __name__ == "__main__":
    verify_tables()
