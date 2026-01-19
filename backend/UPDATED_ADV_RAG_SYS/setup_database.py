"""
Setup Database - Execute schema.sql to create tables
"""
import psycopg2

def setup_database():
    """Execute schema.sql to create all required tables"""

    db_config = {
        'host': 'localhost',
        'database': 'financial_rag',
        'user': 'postgres',
        'password': 'Prasanna!@#2002'
    }

    print("Connecting to database...")
    try:
        conn = psycopg2.connect(**db_config)
        conn.autocommit = True
        cursor = conn.cursor()

        print("Reading schema.sql...")
        with open('schema.sql', 'r', encoding='utf-8') as f:
            schema_sql = f.read()

        print("Executing schema.sql...")
        cursor.execute(schema_sql)

        print("\n" + "=" * 80)
        print("DATABASE SETUP SUCCESSFUL")
        print("=" * 80)
        print("\nTables created:")
        print("  ✓ document_chunks_v2")
        print("  ✓ financial_metrics_v2")
        print("\nIndexes created:")
        print("  ✓ HNSW index for vector search")
        print("  ✓ GIN index for full-text search")
        print("  ✓ B-tree indexes for filtering")
        print("\nViews created:")
        print("  ✓ fair_value_chunks")
        print("  ✓ notes_chunks")

        cursor.close()
        conn.close()

        print("\nYou can now run your ingestion pipeline!")

    except Exception as e:
        print("\n" + "=" * 80)
        print("ERROR DURING DATABASE SETUP")
        print("=" * 80)
        print(f"\nError: {e}")
        print("\nPlease check:")
        print("  1. PostgreSQL is running")
        print("  2. Database 'financial_rag' exists")
        print("  3. pgvector extension is available")
        print("  4. Credentials are correct")
        return False

    return True


if __name__ == "__main__":
    setup_database()
