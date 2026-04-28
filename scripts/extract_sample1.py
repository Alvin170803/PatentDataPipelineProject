"""
Step 1: Extract Sample Data (2020-2025 Only)
Creates smaller, filtered TSV files from the massive raw data.
"""
import pandas as pd
import os

# Configuration
RAW_DATA_DIR = "data"
SAMPLE_DATA_DIR = "data/sample"
START_YEAR = 2020
END_YEAR = 2025
CHUNK_SIZE = 50000

# Create sample directory
os.makedirs(SAMPLE_DATA_DIR, exist_ok=True)

print("=" * 50)
print("STEP 1: Creating Sample Data (2020-2025)")
print("=" * 50)

# 1. Process g_patent.tsv (contains patent_date)
print("\n[1/4] Processing g_patent.tsv...")
patent_ids_to_keep = set()
filtered_patents = []

# Try different possible filenames
patent_file = None
for possible_name in ["g_patent.tsv", "g_patent_disambiguated.tsv", "patent.tsv"]:
    if os.path.exists(f"{RAW_DATA_DIR}/{possible_name}"):
        patent_file = f"{RAW_DATA_DIR}/{possible_name}"
        break

if not patent_file:
    print(" ERROR: Could not find patent TSV file in data/")
    print("   Files found:", os.listdir(RAW_DATA_DIR))
    exit(1)

for chunk in pd.read_csv(patent_file, sep="\t", chunksize=CHUNK_SIZE, low_memory=False):
    # Convert date and extract year
    if 'patent_date' in chunk.columns:
        chunk['patent_date'] = pd.to_datetime(chunk['patent_date'], errors='coerce')
        chunk['year'] = chunk['patent_date'].dt.year
        
        # Filter by year range
        chunk_filtered = chunk[
            (chunk['year'] >= START_YEAR) & 
            (chunk['year'] <= END_YEAR)
        ]
        
        if not chunk_filtered.empty:
            filtered_patents.append(chunk_filtered)
            patent_ids_to_keep.update(chunk_filtered['patent_id'].unique())
    
    print(f"   Processed {len(chunk):,} rows, kept {len(chunk_filtered) if 'chunk_filtered' in locals() else 0:,}...")
    
    # Safety: Stop after processing enough data (REMOVED to get all years)
    # if len(patent_ids_to_keep) > 100000:
    #     print("   Collected 100,000+ patent IDs, moving to next step...")
    #     break

if filtered_patents:
    patents_sample = pd.concat(filtered_patents, ignore_index=True)
    patents_sample.to_csv(f"{SAMPLE_DATA_DIR}/patents_sample.tsv", sep="\t", index=False)
    print(f" SAVED {len(patents_sample):,} patents from {START_YEAR}-{END_YEAR}")
else:
    print(" NO patents found in date range!")
    exit(1)

# Save patent IDs for filtering other files
with open(f"{SAMPLE_DATA_DIR}/patent_ids.txt", "w") as f:
    for pid in patent_ids_to_keep:
        f.write(f"{pid}\n")
print(f" SAVED {len(patent_ids_to_keep):,} patent IDs")

# 2. Filter g_patent_abstract.tsv
print("\n[2/4] Processing g_patent_abstract.tsv...")
abstract_file = None
for possible_name in ["g_patent_abstract.tsv", "patent_abstract.tsv", "abstract.tsv"]:
    if os.path.exists(f"{RAW_DATA_DIR}/{possible_name}"):
        abstract_file = f"{RAW_DATA_DIR}/{possible_name}"
        break

if abstract_file:
    filtered_abstracts = []
    for chunk in pd.read_csv(abstract_file, sep="\t", chunksize=CHUNK_SIZE, low_memory=False):
        if 'patent_id' in chunk.columns:
            chunk_filtered = chunk[chunk['patent_id'].isin(patent_ids_to_keep)]
            if not chunk_filtered.empty:
                filtered_abstracts.append(chunk_filtered)
    
    if filtered_abstracts:
        abstracts_sample = pd.concat(filtered_abstracts, ignore_index=True)
        abstracts_sample.to_csv(f"{SAMPLE_DATA_DIR}/abstracts_sample.tsv", sep="\t", index=False)
        print(f" SAVED {len(abstracts_sample):,} abstracts")
else:
    print("SORRY, Abstract file not found, skipping...")

# 3. Filter inventor file
print("\n[3/4] Processing inventor file...")
inventor_file = None
for possible_name in ["g_inventor_disambiguated.tsv", "g_inventor.tsv", "inventor.tsv"]:
    if os.path.exists(f"{RAW_DATA_DIR}/{possible_name}"):
        inventor_file = f"{RAW_DATA_DIR}/{possible_name}"
        break

if inventor_file:
    filtered_inventors = []
    for chunk in pd.read_csv(inventor_file, sep="\t", chunksize=CHUNK_SIZE, low_memory=False):
        if 'patent_id' in chunk.columns:
            chunk_filtered = chunk[chunk['patent_id'].isin(patent_ids_to_keep)]
            if not chunk_filtered.empty:
                filtered_inventors.append(chunk_filtered)
    
    if filtered_inventors:
        inventors_sample = pd.concat(filtered_inventors, ignore_index=True)
        inventors_sample.to_csv(f"{SAMPLE_DATA_DIR}/inventors_sample.tsv", sep="\t", index=False)
        print(f" SAVED {len(inventors_sample):,} inventor records")
else:
    print("SORRY, Inventor file not found, skipping...")

# 4. Filter assignee file
print("\n[4/4] Processing assignee file...")
assignee_file = None
for possible_name in ["g_assignee_disambiguated.tsv", "g_assignee.tsv", "assignee.tsv"]:
    if os.path.exists(f"{RAW_DATA_DIR}/{possible_name}"):
        assignee_file = f"{RAW_DATA_DIR}/{possible_name}"
        break

if assignee_file:
    filtered_assignees = []
    for chunk in pd.read_csv(assignee_file, sep="\t", chunksize=CHUNK_SIZE, low_memory=False):
        if 'patent_id' in chunk.columns:
            chunk_filtered = chunk[chunk['patent_id'].isin(patent_ids_to_keep)]
            if not chunk_filtered.empty:
                filtered_assignees.append(chunk_filtered)
    
    if filtered_assignees:
        assignees_sample = pd.concat(filtered_assignees, ignore_index=True)
        assignees_sample.to_csv(f"{SAMPLE_DATA_DIR}/assignees_sample.tsv", sep="\t", index=False)
        print(f" SAVED {len(assignees_sample):,} assignee records")
else:
    print(" Assignee file not found, skipping...")

print("\n" + "=" * 50)
print("YAYY! Sample data creation complete!")
print(f"📁 Sample files saved to: {SAMPLE_DATA_DIR}/")
print("=" * 50)