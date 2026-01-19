"""Check ingestion progress"""
import psycopg2

conn = psycopg2.connect(
    host='localhost',
    database='financial_rag',
    user='postgres',
    password='Prasanna!@#2002'
)

cursor = conn.cursor()

# Count chunks for DEN_999
cursor.execute("SELECT COUNT(*) FROM document_chunks_v2 WHERE company_id = 'DEN_999';")
count = cursor.fetchone()[0]

print(f"Chunks ingested so far: {count}")

if count > 0:
    # Check statement_type distribution
    cursor.execute("""
        SELECT statement_type, COUNT(*)
        FROM document_chunks_v2
        WHERE company_id = 'DEN_999'
        GROUP BY statement_type;
    """)

    print("\nStatement type distribution:")
    for row in cursor.fetchall():
        stmt_type = row[0] or 'NULL'
        count = row[1]
        print(f"  {stmt_type}: {count}")

    # Sample a few note numbers
    cursor.execute("""
        SELECT DISTINCT note_number
        FROM document_chunks_v2
        WHERE company_id = 'DEN_999'
          AND note_number IS NOT NULL
        LIMIT 10;
    """)

    notes = [row[0] for row in cursor.fetchall()]
    if notes:
        print(f"\nSample note numbers: {notes[:5]}")

cursor.close()
conn.close()
