"""
SKIP-AHEAD: Processes only Phases 4 & 5 (Assignees + Countries)
Uses the existing patents.db - doesn't touch Phases 1-3
"""
import pandas as pd
import sqlite3
import os
import time

RAW_DATA_DIR = "data"
DB_PATH = "patents.db"
CHUNK_SIZE = 50000
BATCH_SIZE = 50000

print("=" * 70)
print("FINISHING PHASES 4 & 5: Assignees + Countries")
print("=" * 70)

start = time.time()
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# ------------------------------------------------------------
# Phase 4: Assignees (BATCHED)
# ------------------------------------------------------------
print("\n[4/5] Assignees...")
f = f"{RAW_DATA_DIR}/g_assignee_disambiguated.tsv"
cur.execute("CREATE TABLE _at (patent_id TEXT, assignee_id TEXT, company_name TEXT)")

n, rows = 0, 0
for c in pd.read_csv(f, sep="\t", chunksize=CHUNK_SIZE, low_memory=False):
    n += 1
    if 'patent_id' in c.columns:
        org = 'disambig_assignee_organization'
        c['company_name'] = c.get(org, None)
        if 'disambig_assignee_individual_name_first' in c.columns:
            m = c['company_name'].isna() | (c['company_name'] == '')
            c.loc[m, 'company_name'] = (c.loc[m, 'disambig_assignee_individual_name_first'].fillna('') + ' ' + c.loc[m, 'disambig_assignee_individual_name_last'].fillna('')).str.strip()
        tmp = c[['patent_id','assignee_id','company_name']].dropna(subset=['assignee_id','company_name'])
        tmp = tmp[tmp['company_name'] != '']
        if not tmp.empty:
            tmp.to_sql('_at', conn, if_exists='append', index=False)
            rows += len(tmp)
    if n % 200 == 0: print(f"   Chunk {n}: {rows:,} rows ({time.time()-start:.0f}s)")

print(f"   {rows:,} rows loaded")
print("   Inserting companies...")

comp_tot = 0
while True:
    cur.execute("INSERT OR IGNORE INTO companies (company_id, name) SELECT DISTINCT assignee_id, company_name FROM _at WHERE assignee_id NOT IN (SELECT company_id FROM companies) LIMIT ?", (BATCH_SIZE,))
    conn.commit()
    r = cur.rowcount
    if r == 0: break
    comp_tot += r
    if comp_tot % 100000 == 0: print(f"   {comp_tot:,} companies")

print(f"   {comp_tot:,} unique companies")

print("   Updating relationships with company IDs...")
upd = 0
while True:
    cur.execute("UPDATE patent_inventor_company SET company_id = (SELECT a.assignee_id FROM _at a WHERE a.patent_id = patent_inventor_company.patent_id LIMIT 1) WHERE company_id IS NULL AND patent_id IN (SELECT patent_id FROM patent_inventor_company WHERE company_id IS NULL LIMIT ?)", (BATCH_SIZE,))
    conn.commit()
    r = cur.rowcount
    if r == 0: break
    upd += r
    if upd % 500000 == 0: print(f"   {upd:,} updated")
print(f"   {upd:,} relationships updated")

cur.execute("DROP TABLE _at")
conn.commit()
print(f"✅ Companies: {comp_tot:,}")

# ------------------------------------------------------------
# Phase 5: Countries
# ------------------------------------------------------------
print("\n[5/5] Countries...")

# Get location mapping from inventors file
f = f"{RAW_DATA_DIR}/g_inventor_disambiguated.tsv"
cur.execute("CREATE TABLE _il_temp (inventor_id TEXT, location_id TEXT)")

n, rows = 0, 0
print("   Extracting inventor location mappings...")
for c in pd.read_csv(f, sep="\t", chunksize=CHUNK_SIZE, low_memory=False):
    n += 1
    if 'inventor_id' in c.columns and 'location_id' in c.columns:
        tmp = c[['inventor_id','location_id']].dropna(subset=['inventor_id','location_id']).drop_duplicates()
        if not tmp.empty:
            tmp.to_sql('_il_temp', conn, if_exists='append', index=False)
            rows += len(tmp)
    if n % 200 == 0: print(f"   Chunk {n}: {rows:,} mappings ({time.time()-start:.0f}s)")

# Create the _il table needed by the script
cur.execute("CREATE TABLE _il AS SELECT DISTINCT inventor_id, location_id FROM _il_temp")
cur.execute("DROP TABLE _il_temp")
conn.commit()

try: cur.execute("ALTER TABLE inventors ADD COLUMN location_id TEXT")
except: pass

cur.execute("UPDATE inventors SET location_id = (SELECT location_id FROM _il WHERE _il.inventor_id = inventors.inventor_id) WHERE EXISTS (SELECT 1 FROM _il WHERE _il.inventor_id = inventors.inventor_id)")
cur.execute("DROP TABLE _il")
conn.commit()

f = f"{RAW_DATA_DIR}/g_location_disambiguated.tsv"
if os.path.exists(f):
    print("   Loading location data...")
    ldf = pd.read_csv(f, sep="\t", low_memory=False)
    ldf = ldf[['location_id','disambig_country']].drop_duplicates(subset=['location_id'])
    ldf.to_sql('_loc', conn, if_exists='replace', index=False)
    u = cur.execute("UPDATE inventors SET country = (SELECT disambig_country FROM _loc WHERE _loc.location_id = inventors.location_id) WHERE EXISTS (SELECT 1 FROM _loc WHERE _loc.location_id = inventors.location_id)").rowcount
    cur.execute("DROP TABLE _loc")
    print(f"   {u:,} updated with real countries")

cur.execute("UPDATE inventors SET country = 'US' WHERE country IS NULL OR country = ''")
conn.commit()

dist = pd.read_sql("SELECT country, COUNT(*) c FROM inventors GROUP BY country ORDER BY c DESC LIMIT 10", conn)
print("\n   🌍 Top 10:")
for _, r in dist.iterrows(): print(f"      {r['country']:>5}: {r['c']:>10,}")

# ------------------------------------------------------------
# Done
# ------------------------------------------------------------
t = time.time() - start
fp = cur.execute("SELECT COUNT(*) FROM patents").fetchone()[0]
fi = cur.execute("SELECT COUNT(*) FROM inventors").fetchone()[0]
fc = cur.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
fr = cur.execute("SELECT COUNT(*) FROM patent_inventor_company").fetchone()[0]
yr = cur.execute("SELECT MIN(year), MAX(year) FROM patents WHERE year IS NOT NULL").fetchone()

cur.execute("CREATE INDEX IF NOT EXISTS idx_y ON patents(year)")
cur.execute("CREATE INDEX IF NOT EXISTS idx_pp ON patent_inventor_company(patent_id)")
conn.commit()
conn.close()

print(f"\n{'='*70}")
print(f"🎉 PHASES 4-5 COMPLETE! ({t/60:.0f} min)")
print(f"{'='*70}")
print(f"   Patents:        {fp:>12,}")
print(f"   Inventors:      {fi:>12,}")
print(f"   Companies:      {fc:>12,}")
print(f"   Relationships:  {fr:>12,}")
print(f"   Years:          {yr[0]} - {yr[1]}")
print(f"   DB Size:        {os.path.getsize(DB_PATH)/1024/1024:.0f} MB")