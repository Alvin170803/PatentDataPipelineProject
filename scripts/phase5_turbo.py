import sqlite3, pandas as pd, time

start = time.time()
conn = sqlite3.connect('patents.db')
cur = conn.cursor()

print('Loading country lookup...')
loc = pd.read_csv('data/g_location_disambiguated.tsv', sep='\t', low_memory=False)
loc = loc[['location_id','disambig_country']].dropna(subset=['location_id']).drop_duplicates(subset=['location_id'])
loc.columns = ['location_id', 'country']
print(f'{len(loc):,} locations loaded')

print('Creating lookup table...')
loc.to_sql('_loc', conn, if_exists='replace', index=False)
cur.execute('CREATE INDEX IF NOT EXISTS _loc_idx ON _loc(location_id)')
conn.commit()

print('Building new inventors table with countries...')
cur.execute('''
    CREATE TABLE inventors_new AS
    SELECT 
        i.inventor_id,
        i.name,
        COALESCE(l.country, 'US') as country,
        i.location_id
    FROM inventors i
    LEFT JOIN _loc l ON i.location_id = l.location_id
''')
conn.commit()
print('New table created')

print('Swapping tables...')
cur.execute('DROP TABLE inventors')
cur.execute('ALTER TABLE inventors_new RENAME TO inventors')
conn.commit()
print('Table swapped')

print('Cleaning up...')
cur.execute('DROP TABLE IF EXISTS _loc')
cur.execute('DROP TABLE IF EXISTS _il_unique')
conn.commit()

# Show results
dist = pd.read_sql('SELECT country, COUNT(*) c FROM inventors GROUP BY country ORDER BY c DESC LIMIT 10', conn)
print('\nTop 10 Countries:')
for _, r in dist.iterrows():
    print(f'   {r["country"]:>5}: {r["c"]:>10,}')

conn.close()
print(f'\nDone in {(time.time()-start)/60:.1f} minutes!')