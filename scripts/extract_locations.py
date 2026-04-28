"""
Extract Location Sample Based on location_ids from Inventors
"""
import pandas as pd
import os

RAW_DATA_DIR = "data"
SAMPLE_DATA_DIR = "data/sample"
CHUNK_SIZE = 50000

os.makedirs(SAMPLE_DATA_DIR, exist_ok=True)

print("=" * 60)
print("Extracting Location Data")
print("=" * 60)

# Load the inventor sample to get location_ids
inventors_path = f"{SAMPLE_DATA_DIR}/inventors_sample.tsv"
if not os.path.exists(inventors_path):
    print("OH NOO! inventors_sample.tsv not found! Run extract_inventors_assignees.py first.")
    exit(1)

print("Loading inventor sample to get location IDs...")
inventors_sample = pd.read_csv(inventors_path, sep="\t", low_memory=False)

# Get unique location_ids from inventors
if 'location_id' in inventors_sample.columns:
    location_ids_to_keep = set(inventors_sample['location_id'].dropna().unique())
    print(f"📋 Found {len(location_ids_to_keep):,} unique location IDs")
else:
    print("OH NOO! No location_id column in inventors sample!")
    exit(1)

# Process location file
print("\nProcessing g_location_disambiguated.tsv...")
location_file = f"{RAW_DATA_DIR}/g_location_disambiguated.tsv"

if not os.path.exists(location_file):
    print(f"OH NOO! {location_file} not found!")
    exit(1)

filtered_locations = []
total_processed = 0

for chunk in pd.read_csv(location_file, sep="\t", chunksize=CHUNK_SIZE, low_memory=False):
    total_processed += len(chunk)
    
    if 'location_id' in chunk.columns:
        chunk_filtered = chunk[chunk['location_id'].isin(location_ids_to_keep)]
        if not chunk_filtered.empty:
            filtered_locations.append(chunk_filtered)
    
    if total_processed % 100000 == 0:
        print(f"   Processed {total_processed:,} rows, kept {sum(len(f) for f in filtered_locations):,}...")

if filtered_locations:
    locations_sample = pd.concat(filtered_locations, ignore_index=True)
    locations_sample.to_csv(f"{SAMPLE_DATA_DIR}/locations_sample.tsv", sep="\t", index=False)
    print(f"\n✅ Saved {len(locations_sample):,} location records")
else:
    print("\SORRY! No matching location records found")

print("\n" + "=" * 60)
print("YAYY! Location Extraction Complete!")
print("=" * 60)