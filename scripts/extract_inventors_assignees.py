"""
Extract Inventor and Assignee Samples (2020-2025 Only)
Uses the patent_ids from the existing sample to filter.
"""
import pandas as pd
import os

RAW_DATA_DIR = "data"
SAMPLE_DATA_DIR = "data/sample"
CHUNK_SIZE = 50000

os.makedirs(SAMPLE_DATA_DIR, exist_ok=True)

print("=" * 60)
print("Extracting Inventors and Assignees")
print("=" * 60)

# Load the patent IDs we already extracted
patent_ids_path = f"{SAMPLE_DATA_DIR}/patent_ids.txt"
if not os.path.exists(patent_ids_path):
    print("❌ patent_ids.txt not found! Run extract_sample1.py first.")
    exit(1)

with open(patent_ids_path, "r") as f:
    patent_ids_to_keep = set(line.strip() for line in f)

print(f"📋 Loaded {len(patent_ids_to_keep):,} patent IDs to filter by")

# ------------------------------------------------------------
# 1. Process Inventors
# ------------------------------------------------------------
print("\n[1/2] Processing g_inventor_disambiguated.tsv...")
inventor_file = f"{RAW_DATA_DIR}/g_inventor_disambiguated.tsv"

filtered_inventors = []
total_processed = 0

for chunk in pd.read_csv(inventor_file, sep="\t", chunksize=CHUNK_SIZE, low_memory=False):
    total_processed += len(chunk)
    
    if 'patent_id' in chunk.columns:
        chunk_filtered = chunk[chunk['patent_id'].isin(patent_ids_to_keep)]
        if not chunk_filtered.empty:
            filtered_inventors.append(chunk_filtered)
    
    if total_processed % 500000 == 0:
        print(f"   Processed {total_processed:,} rows, kept {sum(len(f) for f in filtered_inventors):,}...")

if filtered_inventors:
    inventors_sample = pd.concat(filtered_inventors, ignore_index=True)
    inventors_sample.to_csv(f"{SAMPLE_DATA_DIR}/inventors_sample.tsv", sep="\t", index=False)
    print(f"✅ Saved {len(inventors_sample):,} inventor records")
else:
    print("SORRY! No inventor records found for the sample patents")

# ------------------------------------------------------------
# 2. Process Assignees
# ------------------------------------------------------------
print("\n[2/2] Processing g_assignee_disambiguated.tsv...")
assignee_file = f"{RAW_DATA_DIR}/g_assignee_disambiguated.tsv"

filtered_assignees = []
total_processed = 0

for chunk in pd.read_csv(assignee_file, sep="\t", chunksize=CHUNK_SIZE, low_memory=False):
    total_processed += len(chunk)
    
    if 'patent_id' in chunk.columns:
        chunk_filtered = chunk[chunk['patent_id'].isin(patent_ids_to_keep)]
        if not chunk_filtered.empty:
            filtered_assignees.append(chunk_filtered)
    
    if total_processed % 500000 == 0:
        print(f"   Processed {total_processed:,} rows, kept {sum(len(f) for f in filtered_assignees):,}...")

if filtered_assignees:
    assignees_sample = pd.concat(filtered_assignees, ignore_index=True)
    assignees_sample.to_csv(f"{SAMPLE_DATA_DIR}/assignees_sample.tsv", sep="\t", index=False)
    print(f"✅ Saved {len(assignees_sample):,} assignee records")
else:
    print("SORRY! No assignee records found for the sample patents")

print("\n" + "=" * 60)
print("YAYY! Extraction Complete!")
print("=" * 60)