import sqlite3, pandas as pd, time

start = time.time()
conn = sqlite3.connect('patents.db')
cur = conn.cursor()

# Check if _il_unique still exists
exists = cur.execute("SELECT name FROM sqlite_master WHERE name='_il_unique'").fetchone()

if not exists:
    print('Re-extracting location mappings from inventors file...')
    cur.execute('CREATE TABLE _il_temp (inventor_id TEXT, location_id TEXT)')
    for chunk in pd.read_csv('data/g_inventor_disambiguated.tsv', sep='\t', chunksize=50000, low_memory=False):
        if 'inventor_id' in chunk.columns and 'location_id' in chunk.columns:
            tmp = chunk[['inventor_id','location_id']].dropna().drop_duplicates()
            if not tmp.empty:
                tmp.to_sql('_il_temp', conn, if_exists='append', index=False)
    cur.execute('CREATE TABLE _il_unique AS SELECT DISTINCT inventor_id, location_id FROM _il_temp')
    cur.execute('DROP TABLE _il_temp')
    conn.commit()
    print('Mappings extracted')
else:
    print('Using existing _il_unique table')

print('Loading country lookup...')
loc = pd.read_csv('data/g_location_disambiguated.tsv', sep='\t', low_memory=False)
loc = loc[['location_id','disambig_country']].dropna(subset=['location_id']).drop_duplicates(subset=['location_id'])

print('Joining mappings with countries...')
mappings = pd.read_sql('SELECT * FROM _il_unique', conn)
mappings = mappings.merge(loc, on='location_id', how='left')
mappings['country'] = mappings['disambig_country'].fillna('US')
mappings = mappings[['inventor_id','country']]
print(f'{len(mappings):,} inventors with real countries')

print('Writing updates...')
mappings.to_sql('_updates', conn, if_exists='replace', index=False)

print('Rebuilding inventors table with real countries...')
cur.execute('''
    CREATE TABLE inventors_new AS
    SELECT i.inventor_id, i.name, COALESCE(u.country, 'US') as country
    FROM inventors i
    LEFT JOIN _updates u ON i.inventor_id = u.inventor_id
''')
cur.execute('DROP TABLE inventors')
cur.execute('ALTER TABLE inventors_new RENAME TO inventors')
conn.commit()

# Results
dist = pd.read_sql('SELECT country, COUNT(*) c FROM inventors GROUP BY country ORDER BY c DESC LIMIT 10', conn)
print('\nTop 10 Countries:')
for _, r in dist.iterrows():
    print(f'   {r["country"]:>5}: {r["c"]:>10,}')

cur.execute('DROP TABLE IF EXISTS _updates')
cur.execute('DROP TABLE IF EXISTS _il_unique')
conn.commit()
conn.close()
print(f'\nDone in {(time.time()-start)/60:.1f} min!')