import sqlite3, pandas as pd, time

start = time.time()
conn = sqlite3.connect('patents.db', timeout=30)
cur = conn.cursor()

print('Loading assignee data from raw file...')
cur.execute('CREATE TABLE _a (patent_id TEXT, assignee_id TEXT)')

for chunk in pd.read_csv('data/g_assignee_disambiguated.tsv', sep='\t', chunksize=100000, low_memory=False):
    if 'patent_id' in chunk.columns and 'assignee_id' in chunk.columns:
        tmp = chunk[['patent_id','assignee_id']].dropna()
        tmp.to_sql('_a', conn, if_exists='append', index=False)

print('Creating company relationships...')
cur.execute('''
    INSERT OR IGNORE INTO patent_inventor_company (patent_id, inventor_id, company_id)
    SELECT DISTINCT a.patent_id, NULL, a.assignee_id
    FROM _a a
    WHERE EXISTS (SELECT 1 FROM patents p WHERE a.patent_id = p.patent_id)
''')
conn.commit()
added = cur.rowcount
print(f'Added {added:,} company relationships')

cur.execute('DROP TABLE _a')
conn.commit()

total = cur.execute('SELECT COUNT(DISTINCT company_id) FROM patent_inventor_company WHERE company_id IS NOT NULL').fetchone()[0]
print(f'Companies with relationships: {total:,}')
conn.close()
print(f'\nDone in {(time.time()-start)/60:.1f} min!')