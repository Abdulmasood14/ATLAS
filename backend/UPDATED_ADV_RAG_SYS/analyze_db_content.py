"""Analyze database content for DEN_999"""
import psycopg2

conn = psycopg2.connect(
    host='localhost',
    database='financial_rag',
    user='postgres',
    password='Prasanna!@#2002'
)

cursor = conn.cursor()

print("="*80)
print("DATABASE CONTENT ANALYSIS - DEN_999")
print("="*80)

# 1. Total chunks
cursor.execute("SELECT COUNT(*) FROM document_chunks_v2 WHERE company_id = 'DEN_999';")
total_chunks = cursor.fetchone()[0]
print(f"\nTotal chunks: {total_chunks}")

# 2. Statement type distribution
cursor.execute("""
    SELECT statement_type, COUNT(*)
    FROM document_chunks_v2
    WHERE company_id = 'DEN_999'
    GROUP BY statement_type
    ORDER BY COUNT(*) DESC;
""")
print("\nStatement Type Distribution:")
for row in cursor.fetchall():
    stmt_type = row[0] or 'NULL'
    count = row[1]
    percentage = (count / total_chunks * 100) if total_chunks > 0 else 0
    print(f"  {stmt_type:15} {count:4} ({percentage:.1f}%)")

# 3. All note numbers
cursor.execute("""
    SELECT DISTINCT note_number
    FROM document_chunks_v2
    WHERE company_id = 'DEN_999' AND note_number IS NOT NULL
    ORDER BY note_number;
""")
notes = [row[0] for row in cursor.fetchall()]
print(f"\nAll Note Numbers ({len(notes)}):")
print(f"  {notes}")

# 4. Note number distribution by statement type
cursor.execute("""
    SELECT statement_type, note_number, COUNT(*)
    FROM document_chunks_v2
    WHERE company_id = 'DEN_999' AND note_number IS NOT NULL
    GROUP BY statement_type, note_number
    ORDER BY statement_type, note_number
    LIMIT 20;
""")
print("\nNote Numbers by Statement Type (top 20):")
print(f"  {'Statement Type':<15} {'Note Number':<12} Count")
print(f"  {'-'*15} {'-'*12} -----")
for row in cursor.fetchall():
    stmt = row[0] or 'NULL'
    note = row[1]
    count = row[2]
    print(f"  {stmt:<15} {note:<12} {count}")

# 5. Sample chunks with note numbers
cursor.execute("""
    SELECT statement_type, note_number, LEFT(chunk_text, 150)
    FROM document_chunks_v2
    WHERE company_id = 'DEN_999' AND note_number IS NOT NULL
    LIMIT 5;
""")
print("\nSample Chunks with Note Numbers:")
for i, row in enumerate(cursor.fetchall(), 1):
    stmt = row[0] or 'NULL'
    note = row[1]
    text = row[2].replace('\n', ' ')[:100]
    print(f"\n  [{i}] Type: {stmt}, Note: {note}")
    print(f"      Text: {text}...")

# 6. Chunks WITHOUT note numbers
cursor.execute("""
    SELECT statement_type, LEFT(chunk_text, 100)
    FROM document_chunks_v2
    WHERE company_id = 'DEN_999' AND note_number IS NULL
    LIMIT 3;
""")
print("\nSample Chunks WITHOUT Note Numbers:")
for i, row in enumerate(cursor.fetchall(), 1):
    stmt = row[0] or 'NULL'
    text = row[1].replace('\n', ' ')[:80]
    print(f"\n  [{i}] Type: {stmt}")
    print(f"      Text: {text}...")

# 7. Section types distribution
cursor.execute("""
    SELECT section_types[1] as first_section, COUNT(*)
    FROM document_chunks_v2
    WHERE company_id = 'DEN_999' AND array_length(section_types, 1) > 0
    GROUP BY first_section
    ORDER BY COUNT(*) DESC
    LIMIT 10;
""")
print("\nTop Section Types (first section tag):")
for row in cursor.fetchall():
    section = row[0]
    count = row[1]
    print(f"  {section:<30} {count:4}")

cursor.close()
conn.close()

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)
