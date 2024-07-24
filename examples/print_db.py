import os
import sqlite3

# Database file path
db_path = 'examples/text.db'

# Check database file size
print(f"Database file size: {os.path.getsize(db_path)} bytes")

# Connect to the SQLite database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Function to dump table schema
def dump_table_schema(cursor, table_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    print(f"\nSchema for table '{table_name}':")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")

# Function to dump sample data from a table
def dump_sample_data(cursor, table_name, limit=5):
    cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
    rows = cursor.fetchall()
    print(f"\nSample data from '{table_name}' (up to {limit} rows):")
    for row in rows:
        print(f"  {row}")

# Get list of all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

if not tables:
    print("No tables found in the database.")
else:
    # Dump schema and sample data for each table
    for table in tables:
        table_name = table[0]
        dump_table_schema(cursor, table_name)
        dump_sample_data(cursor, table_name)

    # Count total number of rows in each table
    print("\nRow counts for each table:")
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"  {table_name}: {count} rows")

# Close the connection
conn.close()