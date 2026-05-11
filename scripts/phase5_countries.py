"""
Phase 5 ONLY: Enrich Inventors with Country Data
Runs independently using existing patents.db
"""
import pandas as pd
import sqlite3
import os
import time

RAW_DATA_DIR = "data"
DB_PATH = "patents.db"
CHUNK_SIZE = 50000

print("=" * 70)
print("PHASE 5: Country Enrichment")
print("=" * 70)

start = time.time()
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Check current state
inv_count = cur.execute("SELECT COUNT(*) FROM inventors").fetchone()[0]
print(f"   Inventors in database: {inv_count:,}")

# ------------------------------------------------------------
# Step 1: Extract inventor-location mappings from the raw file
# ------------------------------------------------------------
print("\n[1/3] Extracting inventor → location mappings...")

inventor_file = f"{RAW_DATA_DIR}/g_inventor_disambiguated.tsv"

# Check if we already have location data
try:
    cur.execute("SELECT location_id FROM inventors LIMIT 1")
    has_location = True
except:
    has_location = False

if not has_location:
    cur.execute("ALTER TABLE inventors ADD COLUMN location_id TEXT")
    conn.commit()

# Create temp table for location mappings
cur.execute("CREATE TABLE IF NOT EXISTS _il_temp (inventor_id TEXT, location_id TEXT)")
cur.execute("DELETE FROM _il_temp")
conn.commit()

n, rows = 0, 0
print("   Reading g_inventor_disambiguated.tsv...")

for chunk in pd.read_csv(inventor_file, sep="\t", chunksize=CHUNK_SIZE, low_memory=False):
    n += 1
    if 'inventor_id' in chunk.columns and 'location_id' in chunk.columns:
        tmp = chunk[['inventor_id', 'location_id']].copy()
        tmp = tmp.dropna(subset=['inventor_id', 'location_id'])
        tmp = tmp.drop_duplicates()
        if not tmp.empty:
            tmp.to_sql('_il_temp', conn, if_exists='append', index=False)
            rows += len(tmp)
    if n % 200 == 0:
        print(f"   Chunk {n}: {rows:,} mappings ({time.time()-start:.0f}s)")

print(f"   Total mappings extracted: {rows:,}")

# ------------------------------------------------------------
# Step 2: Update inventors with location_ids
# ------------------------------------------------------------
print("\n[2/3] Updating inventor location_ids...")

# Create unique mapping table
cur.execute("CREATE TABLE IF NOT EXISTS _il_unique AS SELECT DISTINCT inventor_id, location_id FROM _il_temp")
cur.execute("DROP TABLE _il_temp")
conn.commit()

# Update inventors
updated_loc = cur.execute("""
    UPDATE inventors 
    SET location_id = (
        SELECT location_id FROM _il_unique 
        WHERE _il_unique.inventor_id = inventors.inventor_id
        LIMIT 1
    )
    WHERE EXISTS (
        SELECT 1 FROM _il_unique 
        WHERE _il_unique.inventor_id = inventors.inventor_id
    )
""").rowcount
conn.commit()
print(f"   {updated_loc:,} inventors assigned location_ids")

# ------------------------------------------------------------
# Step 3: Enrich with country names
# ------------------------------------------------------------
print("\n[3/3] Enriching with country names...")

location_file = f"{RAW_DATA_DIR}/g_location_disambiguated.tsv"

if os.path.exists(location_file):
    print("   Loading g_location_disambiguated.tsv...")
    ldf = pd.read_csv(location_file, sep="\t", low_memory=False)
    ldf = ldf[['location_id', 'disambig_country']].copy()
    ldf = ldf.dropna(subset=['location_id'])
    ldf = ldf.drop_duplicates(subset=['location_id'])
    print(f"   Loaded {len(ldf):,} unique locations")
    
    # Create lookup table
    ldf.to_sql('_loc_lookup', conn, if_exists='replace', index=False)
    
    # Update countries
    updated_country = cur.execute("""
        UPDATE inventors 
        SET country = (
            SELECT disambig_country FROM _loc_lookup 
            WHERE _loc_lookup.location_id = inventors.location_id
        )
        WHERE EXISTS (
            SELECT 1 FROM _loc_lookup 
            WHERE _loc_lookup.location_id = inventors.location_id
        )
    """).rowcount
    
    cur.execute("DROP TABLE _loc_lookup")
    conn.commit()
    print(f"   ✅ {updated_country:,} inventors updated with real countries")
else:
    print("   ⚠️ g_location_disambiguated.tsv not found!")
    updated_country = 0

# Default remaining to 'US'
remaining = cur.execute("""
    UPDATE inventors SET country = 'US' 
    WHERE country IS NULL OR country = ''
""").rowcount
conn.commit()
print(f"   ✅ {remaining:,} inventors defaulted to 'US'")

# Clean up
cur.execute("DROP TABLE IF EXISTS _il_unique")
conn.commit()

# ------------------------------------------------------------
# Show Results
# ------------------------------------------------------------
print("\n" + "=" * 70)
print("🌍 Country Distribution (Top 10)")
print("=" * 70)

dist = pd.read_sql("""
    SELECT country, COUNT(*) as inventor_count 
    FROM inventors 
    GROUP BY country 
    ORDER BY inventor_count DESC 
    LIMIT 10
""", conn)

for i, row in dist.iterrows():
    print(f"   {i+1:>2}. {row['country']:>5}: {row['inventor_count']:>12,}")

# ------------------------------------------------------------
# Final Stats
# ------------------------------------------------------------
t = time.time() - start
total_inv = cur.execute("SELECT COUNT(*) FROM inventors").fetchone()[0]
with_country = cur.execute("SELECT COUNT(*) FROM inventors WHERE country IS NOT NULL AND country != ''").fetchone()[0]
countries = cur.execute("SELECT COUNT(DISTINCT country) FROM inventors WHERE country IS NOT NULL AND country != ''").fetchone()[0]

conn.close()

print(f"\n{'='*70}")
print(f"✅ PHASE 5 COMPLETE! ({t/60:.1f} min)")
print(f"{'='*70}")
print(f"   Total inventors:     {total_inv:,}")
print(f"   With country data:   {with_country:,}")
print(f"   Unique countries:    {countries:,}")
print(f"{'='*70}")