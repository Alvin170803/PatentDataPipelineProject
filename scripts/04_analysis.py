"""
Step 4: Here, I analyze Patent Data and Generate Required Reports
"""
import sqlite3
import pandas as pd
import json
import os

DB_PATH = "patents.db"
OUTPUT_DIR = "output"

os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 60)
print("STEP 4: Running Analysis and Generating Reports")
print("=" * 60)

conn = sqlite3.connect(DB_PATH)

# ------------------------------------------------------------
# Helper function to run queries
# ------------------------------------------------------------
def run_query(query, description=""):
    """Execute SQL query and return DataFrame."""
    if description:
        print(f"\n{description}")
    return pd.read_sql_query(query, conn)

# ------------------------------------------------------------
# Q1: Top Inventors
# ------------------------------------------------------------
print("\n[Q1] Top Inventors...")
q1 = """
SELECT 
    i.name,
    COUNT(DISTINCT pic.patent_id) as patent_count
FROM patent_inventor_company pic
JOIN inventors i ON pic.inventor_id = i.inventor_id
WHERE i.name IS NOT NULL AND i.name != ''
GROUP BY i.inventor_id, i.name
ORDER BY patent_count DESC
LIMIT 10
"""
top_inventors = run_query(q1)
top_inventors.to_csv(f"{OUTPUT_DIR}/top_inventors.csv", index=False)
print(f"✅ Saved top_inventors.csv")

# ------------------------------------------------------------
# Q2: Top Companies
# ------------------------------------------------------------
print("\n[Q2] Top Companies...")
q2 = """
SELECT 
    c.name,
    COUNT(DISTINCT pic.patent_id) as patent_count
FROM patent_inventor_company pic
JOIN companies c ON pic.company_id = c.company_id
WHERE c.name IS NOT NULL AND c.name != ''
GROUP BY c.company_id, c.name
ORDER BY patent_count DESC
LIMIT 10
"""
top_companies = run_query(q2)
top_companies.to_csv(f"{OUTPUT_DIR}/top_companies.csv", index=False)
print(f"✅ Saved top_companies.csv")

# ------------------------------------------------------------
# Q3: Top Countries
# ------------------------------------------------------------
print("\n[Q3] Top Countries...")
q3 = """
SELECT 
    i.country,
    COUNT(DISTINCT pic.patent_id) as patent_count
FROM patent_inventor_company pic
JOIN inventors i ON pic.inventor_id = i.inventor_id
WHERE i.country IS NOT NULL AND i.country != ''
GROUP BY i.country
ORDER BY patent_count DESC
LIMIT 10
"""
top_countries = run_query(q3)
top_countries.to_csv(f"{OUTPUT_DIR}/country_trends.csv", index=False)
print(f"✅ Saved country_trends.csv")

# ------------------------------------------------------------
# Q4: Trends Over Time
# ------------------------------------------------------------
print("\n[Q4] Patents by Year...")
q4 = """
SELECT 
    year,
    COUNT(*) as patent_count
FROM patents
WHERE year IS NOT NULL
GROUP BY year
ORDER BY year DESC
"""
yearly_trends = run_query(q4)
yearly_trends.to_csv(f"{OUTPUT_DIR}/patents_by_year.csv", index=False)
print(f"✅ Saved patents_by_year.csv")

# Also print the trends to console
print("\n   Yearly Breakdown:")
for _, row in yearly_trends.iterrows():
    print(f"   {int(row['year'])}: {int(row['patent_count']):,} patents")

# ------------------------------------------------------------
# Get total counts for console report
# ------------------------------------------------------------
total_patents = pd.read_sql_query("SELECT COUNT(*) as total FROM patents", conn).iloc[0,0]
total_inventors = pd.read_sql_query("SELECT COUNT(*) as total FROM inventors", conn).iloc[0,0]
total_companies = pd.read_sql_query("SELECT COUNT(*) as total FROM companies", conn).iloc[0,0]

# ------------------------------------------------------------
# CONSOLE REPORT
# ------------------------------------------------------------
print("\n" + "=" * 60)
print("                    PATENT REPORT")
print("=" * 60)
print(f"\nTotal Patents: {total_patents:,}")
print(f"Total Inventors: {total_inventors:,}")
print(f"Total Companies: {total_companies:,}")

print("\nTop Inventors:")
for i, row in top_inventors.head(5).iterrows():
    print(f"   {i+1}. {row['name'][:30]} - {row['patent_count']}")

print("\nTop Companies:")
for i, row in top_companies.head(5).iterrows():
    name = row['name'] if pd.notna(row['name']) else "Unknown"
    print(f"   {i+1}. {name[:30]} - {row['patent_count']}")

print("\nTop Countries:")
for i, row in top_countries.head(5).iterrows():
    country = row['country'] if pd.notna(row['country']) else "Unknown"
    print(f"   {i+1}. {country} - {row['patent_count']}")

print("\n" + "=" * 60)

# ------------------------------------------------------------
# JSON REPORT
# ------------------------------------------------------------
print("\n[Export] Generating JSON report...")

json_report = {
    "total_patents": int(total_patents),
    "total_inventors": int(total_inventors),
    "total_companies": int(total_companies),
    "top_inventors": [
        {"name": row['name'], "patents": int(row['patent_count'])} 
        for _, row in top_inventors.head(5).iterrows()
    ],
    "top_companies": [
        {"name": row['name'] if pd.notna(row['name']) else "Unknown", 
         "patents": int(row['patent_count'])} 
        for _, row in top_companies.head(5).iterrows()
    ],
    "top_countries": [
        {"country": row['country'] if pd.notna(row['country']) else "Unknown", 
         "patents": int(row['patent_count'])} 
        for _, row in top_countries.head(5).iterrows()
    ]
}

with open(f"{OUTPUT_DIR}/summary.json", "w") as f:
    json.dump(json_report, f, indent=2)

print(f"✅ Saved summary.json")

# ------------------------------------------------------------
# Complete
# ------------------------------------------------------------
conn.close()

print("\n" + "=" * 60)
print("YAYY! ANALYSIS COMPLETE!")
print("=" * 60)
print(f"\n📁 All reports saved to: {OUTPUT_DIR}/")
print("\nFiles generated:")
print("   - top_inventors.csv")
print("   - top_companies.csv")
print("   - country_trends.csv")
print("   - summary.json")
print("\n✅ Pipeline finished successfully!")
print("=" * 60)