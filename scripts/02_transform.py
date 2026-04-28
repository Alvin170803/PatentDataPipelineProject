"""
Step 2: I proceed to transform and clean the Sample Data(2020-2025) created in Step 1. This involves:
- Loading the sample TSV files for patents, abstracts, inventors, and assignees.
This creates clean CSV files ready for database loading.
"""

import pandas as pd
import os

SAMPLE_DIR = "data/sample"
OUTPUT_DIR = "output"
CHUNK_SIZE = 50000

os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 60)
print("STEP 2: Transforming and Cleaning Data")
print("=" * 60)

# ------------------------------------------------------------
# 1. Check if sample files exist
# ------------------------------------------------------------
print("\n[Checking] Looking for sample files...")
sample_files = os.listdir(SAMPLE_DIR) if os.path.exists(SAMPLE_DIR) else []
print(f"   Files found: {sample_files}")

patents_path = f"{SAMPLE_DIR}/patents_sample.tsv"
if not os.path.exists(patents_path):
    print(f"❌ ERROR: {patents_path} not found!")
    print("   Did Script 1 complete successfully?")
    exit(1)

# Check file size
file_size = os.path.getsize(patents_path) / (1024 * 1024)  # MB
print(f"   patents_sample.tsv size: {file_size:.2f} MB")

if file_size < 0.1:
    print(f"❌ ERROR: patents_sample.tsv is too small ({file_size:.2f} MB)")
    print("   Script 1 may not have extracted any data.")
    exit(1)

# ------------------------------------------------------------
# 2. Load and Clean Patents
# ------------------------------------------------------------
print("\n[1/5] Loading patents sample...")

# First, peek at the columns
peek = pd.read_csv(patents_path, sep="\t", nrows=0)
print(f"   Available columns: {peek.columns.tolist()}")

# Now read the actual data
patents_sample = pd.read_csv(patents_path, sep="\t", low_memory=False)
print(f"   Loaded {len(patents_sample):,} rows")

# Check what columns we actually have
print(f"   Shape: {patents_sample.shape}")

# Keep only needed columns (adjust based on what's available)
keep_cols = []
if 'patent_id' in patents_sample.columns:
    keep_cols.append('patent_id')
else:
    print("❌ ERROR: 'patent_id' column not found!")
    print(f"   Columns are: {patents_sample.columns.tolist()}")
    exit(1)

if 'patent_title' in patents_sample.columns:
    keep_cols.append('patent_title')
elif 'title' in patents_sample.columns:
    keep_cols.append('title')

if 'patent_date' in patents_sample.columns:
    keep_cols.append('patent_date')
elif 'date' in patents_sample.columns:
    keep_cols.append('date')

print(f"   Keeping columns: {keep_cols}")

patents_clean = patents_sample[keep_cols].copy()

# Rename columns to standard names
if 'title' in patents_clean.columns and 'patent_title' not in patents_clean.columns:
    patents_clean = patents_clean.rename(columns={'title': 'patent_title'})
if 'date' in patents_clean.columns and 'patent_date' not in patents_clean.columns:
    patents_clean = patents_clean.rename(columns={'date': 'patent_date'})

# Add year column
if 'patent_date' in patents_clean.columns:
    patents_clean['patent_date'] = pd.to_datetime(patents_clean['patent_date'], errors='coerce')
    patents_clean['year'] = patents_clean['patent_date'].dt.year

# Deduplicate
patents_clean = patents_clean.drop_duplicates(subset=['patent_id'])
print(f"   After deduplication: {len(patents_clean):,} unique patents")

# Add abstract placeholder (we'll merge real abstract later if available)
patents_clean['patent_abstract'] = 'No abstract available'

# Save
patents_clean.to_csv(f"{OUTPUT_DIR}/clean_patents.csv", index=False)
print(f"✅ Saved {len(patents_clean):,} clean patents to {OUTPUT_DIR}/clean_patents.csv")

# ------------------------------------------------------------
# 3. Process Abstracts (if available)
# ------------------------------------------------------------
print("\n[2/5] Processing abstracts...")

abstract_path = f"{SAMPLE_DIR}/abstracts_sample.tsv"
if os.path.exists(abstract_path):
    file_size = os.path.getsize(abstract_path) / (1024 * 1024)
    print(f"   Found abstracts_sample.tsv ({file_size:.2f} MB)")
    
    abstracts_sample = pd.read_csv(abstract_path, sep="\t", low_memory=False, nrows=100000)
    print(f"   Loaded {len(abstracts_sample):,} abstract rows")
    
    if 'patent_id' in abstracts_sample.columns:
        abstract_col = None
        if 'patent_abstract' in abstracts_sample.columns:
            abstract_col = 'patent_abstract'
        elif 'abstract' in abstracts_sample.columns:
            abstract_col = 'abstract'
        
    
        if abstract_col:
            abstracts_clean = abstracts_sample[['patent_id', abstract_col]].copy()
            abstracts_clean = abstracts_clean.rename(columns={abstract_col: 'patent_abstract'})
            abstracts_clean = abstracts_clean.dropna(subset=['patent_id'])
            abstracts_clean = abstracts_clean.drop_duplicates(subset=['patent_id'])
            
            # FIX: Convert both patent_id columns to the same type (string)
            patents_clean['patent_id'] = patents_clean['patent_id'].astype(str)
            abstracts_clean['patent_id'] = abstracts_clean['patent_id'].astype(str)
            
            # Merge with patents
            patents_clean = patents_clean.drop(columns=['patent_abstract'], errors='ignore')
            patents_clean = patents_clean.merge(abstracts_clean, on='patent_id', how='left')
            patents_clean['patent_abstract'] = patents_clean['patent_abstract'].fillna('No abstract available')
            
            # Re-save
            patents_clean.to_csv(f"{OUTPUT_DIR}/clean_patents.csv", index=False)
            print(f"✅ Merged abstracts with patents")
        else:
            print("   SORRY! No abstract column found")
    else:
        print("   SORRY! No patent_id column in abstracts file")
else:
    print("   SORRY! abstracts_sample.tsv not found, using placeholder")

# ------------------------------------------------------------
# 4. Process Inventors
# ------------------------------------------------------------
print("\n[3/5] Processing inventors...")

inventor_path = f"{SAMPLE_DIR}/inventors_sample.tsv"
locations_path = f"{SAMPLE_DIR}/locations_sample.tsv"

inventors_clean = pd.DataFrame()
relationships_inventor = pd.DataFrame()

# Load location data if available
locations_df = None
if os.path.exists(locations_path):
    print("   Loading location data for countries...")
    locations_df = pd.read_csv(locations_path, sep="\t", low_memory=False)
    locations_df = locations_df[['location_id', 'disambig_country']].drop_duplicates(subset=['location_id'])
    print(f"   Loaded {len(locations_df):,} location records")

if os.path.exists(inventor_path):
    file_size = os.path.getsize(inventor_path) / (1024 * 1024)
    print(f"   Found inventors_sample.tsv ({file_size:.2f} MB)")
    
    inventors_sample = pd.read_csv(inventor_path, sep="\t", low_memory=False)
    print(f"   Loaded {len(inventors_sample):,} inventor rows")
    
    # FIXED: Use the correct column names for disambiguated data
    first_col = 'disambig_inventor_name_first'
    last_col = 'disambig_inventor_name_last'
    id_col = 'inventor_id'
    
    has_inventor_id = id_col in inventors_sample.columns
    has_patent_id = 'patent_id' in inventors_sample.columns
    has_location_id = 'location_id' in inventors_sample.columns
    
    print(f"   Using name columns: '{first_col}' and '{last_col}'")
    
    if has_inventor_id and first_col in inventors_sample.columns and last_col in inventors_sample.columns:
        inventors_sample['full_name'] = (
            inventors_sample[first_col].fillna('') + ' ' + 
            inventors_sample[last_col].fillna('')
        ).str.strip()
        
        # Start with basic inventor info
        inventors_clean = inventors_sample[[id_col, 'full_name']].copy()
        if has_location_id:
            inventors_clean['location_id'] = inventors_sample['location_id']
        
        # Merge with location data to get country
        if locations_df is not None and has_location_id:
            inventors_clean = inventors_clean.merge(
                locations_df, 
                on='location_id', 
                how='left'
            )
            inventors_clean['country'] = inventors_clean['disambig_country'].fillna('US')
            inventors_clean = inventors_clean.drop(columns=['location_id', 'disambig_country'], errors='ignore')
        else:
            inventors_clean['country'] = 'USA'  # Default if no location data
        
        # Clean up
        inventors_clean = inventors_clean.dropna(subset=[id_col])
        inventors_clean = inventors_clean[inventors_clean['full_name'] != '']
        inventors_clean = inventors_clean.drop_duplicates(subset=[id_col])
        inventors_clean = inventors_clean.rename(columns={id_col: 'inventor_id', 'full_name': 'name'})
        
        # Count countries for reporting
        country_counts = inventors_clean['country'].value_counts()
        print(f"   Country distribution: {dict(country_counts.head(5))}")
        print(f"   Created {len(inventors_clean):,} unique inventors")
        
        if has_patent_id:
            relationships_inventor = inventors_sample[['patent_id', id_col]].copy()
            relationships_inventor = relationships_inventor.dropna()
            relationships_inventor = relationships_inventor.drop_duplicates()
            relationships_inventor = relationships_inventor.rename(columns={id_col: 'inventor_id'})
            print(f"   Created {len(relationships_inventor):,} inventor relationships")
    else:
        print(f"   SORRY! Missing required columns for inventors")
else:
    print("   SORRY! inventors_sample.tsv not found")

if not inventors_clean.empty:
    inventors_clean.to_csv(f"{OUTPUT_DIR}/clean_inventors.csv", index=False)
    print(f"✅ Saved {len(inventors_clean):,} unique inventors")
else:
    print("   SORRY! No inventor data extracted")

# ------------------------------------------------------------
# 5. Process Companies (Assignees)
# ------------------------------------------------------------
print("\n[4/5] Processing companies...")

assignee_path = f"{SAMPLE_DIR}/assignees_sample.tsv"
companies_clean = pd.DataFrame()
relationships_assignee = pd.DataFrame()

if os.path.exists(assignee_path):
    file_size = os.path.getsize(assignee_path) / (1024 * 1024)
    print(f"   Found assignees_sample.tsv ({file_size:.2f} MB)")
    
    assignees_sample = pd.read_csv(assignee_path, sep="\t", low_memory=False, nrows=100000)
    print(f"   Loaded {len(assignees_sample):,} assignee rows")
    
    #Use the correct column names
    org_col = 'disambig_assignee_organization'  # <-- As it is in the tsv file!
    id_col = 'assignee_id'
    
    # Also check for individual names (combine if organization is missing)
    first_col = 'disambig_assignee_individual_name_first'
    last_col = 'disambig_assignee_individual_name_last'
    
    has_assignee_id = id_col in assignees_sample.columns
    has_patent_id = 'patent_id' in assignees_sample.columns
    
    print(f"   Using organization column: '{org_col}'")
    
    if has_assignee_id:
        # Create a full name column (prioritize organization, fallback to individual name)
        assignees_sample['company_name'] = assignees_sample[org_col]
        
        # If organization is missing, use individual name
        if first_col in assignees_sample.columns and last_col in assignees_sample.columns:
            mask = assignees_sample['company_name'].isna() | (assignees_sample['company_name'] == '')
            assignees_sample.loc[mask, 'company_name'] = (
                assignees_sample.loc[mask, first_col].fillna('') + ' ' + 
                assignees_sample.loc[mask, last_col].fillna('')
            ).str.strip()
        
        # Remove rows with no name
        companies_clean = assignees_sample[[id_col, 'company_name']].copy()
        companies_clean = companies_clean.dropna(subset=[id_col, 'company_name'])
        companies_clean = companies_clean[companies_clean['company_name'] != '']
        companies_clean = companies_clean.drop_duplicates(subset=[id_col])
        companies_clean = companies_clean.rename(columns={id_col: 'company_id', 'company_name': 'name'})
        
        print(f"   Created {len(companies_clean):,} unique companies")
        
        if has_patent_id:
            relationships_assignee = assignees_sample[['patent_id', id_col]].copy()
            relationships_assignee = relationships_assignee.dropna()
            relationships_assignee = relationships_assignee.drop_duplicates()
            relationships_assignee = relationships_assignee.rename(columns={id_col: 'company_id'})
            print(f"   Created {len(relationships_assignee):,} assignee relationships")
    else:
        print(f"   SORRY! '{id_col}' column not found")
else:
    print("   SORRY! assignees_sample.tsv not found")

if not companies_clean.empty:
    companies_clean.to_csv(f"{OUTPUT_DIR}/clean_companies.csv", index=False)
    print(f"✅ Saved {len(companies_clean):,} unique companies")
else:
    print("   SORRY! No company data extracted")

# ------------------------------------------------------------
# 6. Create Combined Relationships Table
# ------------------------------------------------------------
print("\n[5/5] Creating relationships table...")

relationships = pd.DataFrame()

if not relationships_inventor.empty and not relationships_assignee.empty:
    relationships = relationships_inventor.merge(relationships_assignee, on='patent_id', how='outer')
elif not relationships_inventor.empty:
    relationships = relationships_inventor.copy()
    relationships['company_id'] = None
elif not relationships_assignee.empty:
    relationships = relationships_assignee.copy()
    relationships['inventor_id'] = None

if not relationships.empty:
    relationships = relationships.drop_duplicates()
    relationships.to_csv(f"{OUTPUT_DIR}/relationships.csv", index=False)
    print(f"✅ Saved {len(relationships):,} relationship records")
else:
    print("SORRY! No relationship data found")

# ------------------------------------------------------------
# Summary
# ------------------------------------------------------------
print("\n" + "=" * 60)
print("YAYY! Transformation Complete!")
print("=" * 60)
print(f"📁 Output files saved to: {OUTPUT_DIR}/")
print(f"   - clean_patents.csv: {len(patents_clean):,} rows")
print(f"   - clean_inventors.csv: {len(inventors_clean):,} rows")
print(f"   - clean_companies.csv: {len(companies_clean):,} rows")
if not relationships.empty:
    print(f"   - relationships.csv: {len(relationships):,} rows")
print("=" * 60)