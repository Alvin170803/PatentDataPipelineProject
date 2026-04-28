"""
Step 3: I now load the Clean Data into an SQLite Database for storage and querying.
This script reads the cleaned CSV files and inserts them into a structured SQLite database.
"""
import sqlite3
import pandas as pd
import os

OUTPUT_DIR = "output"
DB_PATH = "patents.db"

print("=" * 60)
print("STEP 3: Loading Data to SQLite Database")
print("=" * 60)

# Connect to database (creates file if doesn't exist)
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# ------------------------------------------------------------
# Read and execute schema
# ------------------------------------------------------------
print("\n[1/5] Creating database schema...")

with open("sql/schema.sql", "r") as f:
    schema_sql = f.read()
    cursor.executescript(schema_sql)

conn.commit()
print("✅ Schema created")

# ------------------------------------------------------------
# Load Patents
# ------------------------------------------------------------
print("\n[2/5] Loading patents...")
patents_df = pd.read_csv(f"{OUTPUT_DIR}/clean_patents.csv")
patents_df.to_sql("patents", conn, if_exists="append", index=False)
print(f"✅ Loaded {len(patents_df):,} patents")

# ------------------------------------------------------------
# Load Inventors
# ------------------------------------------------------------
print("\n[3/5] Loading inventors...")
inventors_df = pd.read_csv(f"{OUTPUT_DIR}/clean_inventors.csv")
inventors_df.to_sql("inventors", conn, if_exists="append", index=False)
print(f"✅ Loaded {len(inventors_df):,} inventors")

# ------------------------------------------------------------
# Load Companies
# ------------------------------------------------------------
print("\n[4/5] Loading companies...")
companies_df = pd.read_csv(f"{OUTPUT_DIR}/clean_companies.csv")
companies_df.to_sql("companies", conn, if_exists="append", index=False)
print(f"✅ Loaded {len(companies_df):,} companies")

# ------------------------------------------------------------
# Load Relationships
# ------------------------------------------------------------
print("\n[5/5] Loading relationships...")
rel_path = f"{OUTPUT_DIR}/relationships.csv"
if os.path.exists(rel_path):
    rel_df = pd.read_csv(rel_path)
    rel_df.to_sql("patent_inventor_company", conn, if_exists="append", index=False)
    print(f"✅ Loaded {len(rel_df):,} relationships")
else:
    print("SORRY! No relationships file found")

# ------------------------------------------------------------
# Create indexes for performance
# ------------------------------------------------------------
print("\n[6/6] Creating indexes...")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_pic_patent ON patent_inventor_company(patent_id)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_pic_inventor ON patent_inventor_company(inventor_id)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_pic_company ON patent_inventor_company(company_id)")
conn.commit()
print("✅ Indexes created")

# Close connection
conn.close()

print("\n" + "=" * 60)
print("YAYY! Database Load Complete!")
print("=" * 60)
print(f"📁 Database saved to: {DB_PATH}")
print("=" * 60)