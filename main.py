"""
Patent Data Pipeline - Main Orchestrator
Run this script to execute the complete pipeline.
Usage: python main.py
"""
import subprocess
import sys
import os

def run_script(script_name):
    """
    Run a Python script and exit if it fails.
    """
    print(f"\n{'='*60}")
    print(f" Running: {script_name}")
    print('='*60)
    
    result = subprocess.run([sys.executable, script_name])
    
    if result.returncode != 0:
        print(f"\n Error running {script_name}")
        print("   Check the error message above for details.")
        sys.exit(1)
    
    print(f"\n✅ {script_name} completed successfully")

def check_prerequisites():
    """
    Verify required files and folders exist.
    """
    required_folders = ['data', 'scripts', 'sql', 'output']
    required_files = [
        'sql/schema.sql',
        'sql/queries.sql'
    ]
    
    print("Checking prerequisites...")
    
    # Create output folder if missing
    os.makedirs('output', exist_ok=True)
    
    # Check required files
    for folder in required_folders:
        if not os.path.exists(folder):
            print(f"SORRY! Folder '{folder}' not found, creating...")
            os.makedirs(folder, exist_ok=True)
    
    for file in required_files:
        if not os.path.exists(file):
            print(f"Required file '{file}' not found!")
            print("   Please create this file before running the pipeline.")
            return False
    
    print("✅ Prerequisites check passed\n")
    return True

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🔷 PATENT DATA PIPELINE 🔷")
    print("="*60)
    
    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)
    
    # Step 1: Extract sample data (uncomment if needed)
    # print("\n  Skipping extraction (already completed)")
    # print("   To re-extract, uncomment the lines in main.py")
    # run_script("scripts/extract_sample1.py")
    # run_script("scripts/extract_inventors_assignees.py")
    # run_script("scripts/extract_locations.py")
    
    # Step 2: Transform and clean data
    run_script("scripts/02_transform.py")
    
    # Step 3: Load to SQLite database
    run_script("scripts/03_load.py")
    
    # Step 4: Analyze and generate reports
    run_script("scripts/04_analysis.py")
    
    # Step 5: Generate visualizations
    run_script("scripts/05_visualizations.py")
    
    # Done!
    print("\n" + "="*60)
    print("🎉🎉🎉 PIPELINE COMPLETE! 🎉🎉🎉")
    print("="*60)
    print("\n📁 Check the 'output/' folder for:")
    print("   📊 clean_patents.csv")
    print("   📊 clean_inventors.csv")
    print("   📊 clean_companies.csv")
    print("   📊 top_inventors.csv")
    print("   📊 top_companies.csv")
    print("   📊 country_trends.csv")
    print("   📄 summary.json")
    print("   📈 top_inventors.png")
    print("   📈 top_companies.png")
    print("   📈 country_distribution.png")
    print("   📈 patents_per_year.png")
    print("\n📁 Database: patents.db")
    print("\n✅ Ready for submission!")
    print("="*60)