"""Quick rebuild of core tables from raw files"""
import sqlite3, pandas as pd, os, time

start = time.time()
conn = sqlite3.connect('patents.db')
cur = conn.cursor()

# Read schema
with open('sql/schema.sql', 'r') as f:
    cur.executescript(f.read())
conn.commit()

print("Rebuilding core tables...")

# 1. Patents (fast - just load them)
print("[1/3] Patents...")
for chunk in pd.read_csv('data/g_patent.tsv', sep='\t', chunksize=50000, low_memory=False):
    if 'patent_date' in chunk.columns:
        chunk['year'] = pd.to_datetime(chunk['patent_date'], errors='coerce').dt.year
    cols = [c for c in ['patent_id','patent_title','patent_date'] if c in chunk.columns]
    pc = chunk[cols].copy()
    if 'year' in chunk.columns: pc['year'] = chunk['year']
    pc['patent_abstract'] = ''
    pc = pc.drop_duplicates(subset=['patent_id'])
    pc.to_sql('patents', conn, if_exists='append', index=False)
print(f'   Patents loaded')

# 2. Inventors (dump all to temp table, then deduplicate with SQL)
print("[2/3] Inventors...")
cur.execute('CREATE TABLE _inv (inventor_id TEXT, name TEXT)')

for chunk in pd.read_csv('data/g_inventor_disambiguated.tsv', sep='\t', chunksize=100000, low_memory=False):
    if 'inventor_id' in chunk.columns:
        chunk['name'] = (chunk.get('disambig_inventor_name_first','').fillna('') + ' ' + 
                         chunk.get('disambig_inventor_name_last','').fillna('')).str.strip()
        tmp = chunk[['inventor_id','name']].dropna(subset=['inventor_id'])
        tmp = tmp[tmp['name'] != '']
        tmp.to_sql('_inv', conn, if_exists='append', index=False)
print('   Deduplicating with SQL...')
cur.execute('INSERT OR IGNORE INTO inventors (inventor_id, name, country) SELECT DISTINCT inventor_id, name, \'US\' FROM _inv')
cur.execute('DROP TABLE _inv')
conn.commit()
cnt = cur.execute('SELECT COUNT(*) FROM inventors').fetchone()[0]
print(f'   {cnt:,} inventors')

# 3. Companies (same approach)
print("[3/3] Companies...")
cur.execute('CREATE TABLE _comp (company_id TEXT, name TEXT)')

for chunk in pd.read_csv('data/g_assignee_disambiguated.tsv', sep='\t', chunksize=100000, low_memory=False):
    if 'assignee_id' in chunk.columns:
        org = 'disambig_assignee_organization'
        chunk['cname'] = chunk.get(org, None)
        if 'disambig_assignee_individual_name_first' in chunk.columns:
            m = chunk['cname'].isna() | (chunk['cname'] == '')
            chunk.loc[m, 'cname'] = (chunk.loc[m, 'disambig_assignee_individual_name_first'].fillna('') + 
                                     ' ' + chunk.loc[m, 'disambig_assignee_individual_name_last'].fillna('')).str.strip()
        tmp = chunk[['assignee_id','cname']].dropna(subset=['assignee_id','cname'])
        tmp = tmp[tmp['cname'] != '']
        tmp.columns = ['company_id','name']
        tmp.to_sql('_comp', conn, if_exists='append', index=False)
print('   Deduplicating with SQL...')
cur.execute('INSERT OR IGNORE INTO companies (company_id, name) SELECT DISTINCT company_id, name FROM _comp')
cur.execute('DROP TABLE _comp')
conn.commit()
cnt = cur.execute('SELECT COUNT(*) FROM companies').fetchone()[0]
print(f'   {cnt:,} companies')

conn.close()
print(f'\n✅ Done in {(time.time()-start)/60:.1f} min!')
print('Next, Now run python main.py')