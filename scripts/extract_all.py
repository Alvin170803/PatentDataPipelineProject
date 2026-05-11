"""
FULL DATA EXTRACTION - All column names match DataFrames
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
print("BATCHED ETL - Full Dataset (1976-2025)")
print("=" * 70)

start = time.time()
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Schema
with open("sql/schema.sql", "r") as f:
    cur.executescript(f.read())
conn.commit()

# ------------------------------------------------------------
# Phase 1: Patents
# ------------------------------------------------------------
print("\n[1/5] Patents...")
f = f"{RAW_DATA_DIR}/g_patent.tsv"
t, n = 0, 0
for c in pd.read_csv(f, sep="\t", chunksize=CHUNK_SIZE, low_memory=False):
    n += 1
    if 'patent_date' in c.columns:
        c['year'] = pd.to_datetime(c['patent_date'], errors='coerce').dt.year
    cols = ['patent_id', 'patent_title', 'patent_date']
    avail = [x for x in cols if x in c.columns]
    pc = c[avail].copy()
    if 'year' in c.columns: pc['year'] = c['year']
    pc['patent_abstract'] = ''
    pc = pc.drop_duplicates(subset=['patent_id'])
    pc.to_sql('patents', conn, if_exists='append', index=False)
    t += len(pc)
    if n % 100 == 0: print(f"   {t:,} patents")
print(f"✅ {t:,}")

# ------------------------------------------------------------
# Phase 2: Abstracts
# ------------------------------------------------------------
print("\n[2/5] Abstracts...")
f = f"{RAW_DATA_DIR}/g_patent_abstract.tsv"
# FIXED: Column names match the DataFrame
cur.execute("CREATE TABLE _a (patent_id TEXT PRIMARY KEY, patent_abstract TEXT)")
n = 0
for c in pd.read_csv(f, sep="\t", chunksize=CHUNK_SIZE, low_memory=False):
    n += 1
    if 'patent_id' in c.columns and 'patent_abstract' in c.columns:
        ab = c[['patent_id', 'patent_abstract']].dropna(subset=['patent_id']).drop_duplicates(subset=['patent_id'])
        if not ab.empty: ab.to_sql('_a', conn, if_exists='append', index=False)
    if n % 200 == 0: print(f"   Chunk {n} ({time.time()-start:.0f}s)")

print("   Updating...")
tot = 0
while True:
    cur.execute("UPDATE patents SET patent_abstract = (SELECT patent_abstract FROM _a WHERE _a.patent_id = patents.patent_id) WHERE patent_id IN (SELECT patent_id FROM patents WHERE patent_abstract = '' LIMIT ?)", (BATCH_SIZE,))
    conn.commit()
    r = cur.rowcount
    if r == 0: break
    tot += r
    if tot % 500000 == 0: print(f"   {tot:,} updated")
cur.execute("DROP TABLE _a")
print(f"✅ {tot:,}")

# ------------------------------------------------------------
# Phase 3: Inventors
# ------------------------------------------------------------
print("\n[3/5] Inventors...")
f = f"{RAW_DATA_DIR}/g_inventor_disambiguated.tsv"
# FIXED: Column names match the DataFrame exactly
cur.execute("CREATE TABLE _it (patent_id TEXT, inventor_id TEXT, name TEXT, location_id TEXT)")
n, rows = 0, 0
for c in pd.read_csv(f, sep="\t", chunksize=CHUNK_SIZE, low_memory=False):
    n += 1
    if 'patent_id' in c.columns:
        c['name'] = (c.get('disambig_inventor_name_first','').fillna('') + ' ' + c.get('disambig_inventor_name_last','').fillna('')).str.strip()
        tmp = c[['patent_id','inventor_id','name']].copy()
        if 'location_id' in c.columns: tmp['location_id'] = c['location_id']
        tmp = tmp.dropna(subset=['inventor_id'])
        tmp = tmp[tmp['name'] != '']
        if not tmp.empty:
            tmp.to_sql('_it', conn, if_exists='append', index=False)
            rows += len(tmp)
    if n % 200 == 0: print(f"   Chunk {n}: {rows:,} rows ({time.time()-start:.0f}s)")

print(f"   {rows:,} rows loaded")

print("   Inserting inventors in batches...")
inv_tot = 0
while True:
    cur.execute("INSERT OR IGNORE INTO inventors (inventor_id, name, country) SELECT DISTINCT inventor_id, name, 'US' FROM _it WHERE inventor_id NOT IN (SELECT inventor_id FROM inventors) LIMIT ?", (BATCH_SIZE,))
    conn.commit()
    r = cur.rowcount
    if r == 0: break
    inv_tot += r
    if inv_tot % 500000 == 0: print(f"   {inv_tot:,} inventors")
print(f"   {inv_tot:,} unique inventors")

print("   Creating relationships in batches...")
rel_tot = 0
offset = 0
while True:
    cur.execute("INSERT OR IGNORE INTO patent_inventor_company (patent_id, inventor_id) SELECT DISTINCT patent_id, inventor_id FROM _it WHERE EXISTS (SELECT 1 FROM patents p WHERE _it.patent_id = p.patent_id) LIMIT ? OFFSET ?", (BATCH_SIZE, offset))
    conn.commit()
    r = cur.rowcount
    if r == 0: break
    rel_tot += r
    offset += BATCH_SIZE
    if rel_tot % 500000 == 0: print(f"   {rel_tot:,} relationships")
print(f"   {rel_tot:,} relationships")

cur.execute("CREATE TABLE _il AS SELECT DISTINCT inventor_id, location_id FROM _it WHERE location_id IS NOT NULL")
cur.execute("DROP TABLE _it")
conn.commit()
print(f"✅ Inventors: {inv_tot:,} | Relationships: {rel_tot:,}")

# ------------------------------------------------------------
# Phase 4: Assignees
# ------------------------------------------------------------
print("\n[4/5] Assignees...")
f = f"{RAW_DATA_DIR}/g_assignee_disambiguated.tsv"
# FIXED: Column names match the DataFrame exactly
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

comp_tot = 0
while True:
    cur.execute("INSERT OR IGNORE INTO companies (company_id, name) SELECT DISTINCT assignee_id, company_name FROM _at WHERE assignee_id NOT IN (SELECT company_id FROM companies) LIMIT ?", (BATCH_SIZE,))
    conn.commit()
    r = cur.rowcount
    if r == 0: break
    comp_tot += r
    if comp_tot % 100000 == 0: print(f"   {comp_tot:,} companies")

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
print(f"✅ Companies: {comp_tot:,}")

# ------------------------------------------------------------
# Phase 5: Countries
# ------------------------------------------------------------
print("\n[5/5] Countries...")
try: cur.execute("ALTER TABLE inventors ADD COLUMN location_id TEXT")
except: pass

cur.execute("UPDATE inventors SET location_id = (SELECT location_id FROM _il WHERE _il.inventor_id = inventors.inventor_id) WHERE EXISTS (SELECT 1 FROM _il WHERE _il.inventor_id = inventors.inventor_id)")
cur.execute("DROP TABLE _il")
conn.commit()

f = f"{RAW_DATA_DIR}/g_location_disambiguated.tsv"
if os.path.exists(f):
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
print(f"🎉 COMPLETE! ({t/60:.0f} min)")
print(f"{'='*70}")
print(f"   Patents:        {fp:>12,}")
print(f"   Inventors:      {fi:>12,}")
print(f"   Companies:      {fc:>12,}")
print(f"   Relationships:  {fr:>12,}")
print(f"   Years:          {yr[0]} - {yr[1]}")
print(f"   DB Size:        {os.path.getsize(DB_PATH)/1024/1024:.0f} MB")