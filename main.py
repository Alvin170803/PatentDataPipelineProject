# """
# Patent Data Pipeline - Main Orchestrator
# Complete ETL pipeline for USPTO patent data (1976-2025)
# """
# import subprocess
# import sys
# import os

# def run_script(script_name, optional=False):
#     """Run a Python script. If optional=True, warn but don't exit on failure."""
#     print(f"\n{'='*60}")
#     print(f"🚀 Running: {script_name}")
#     print('='*60)
#     result = subprocess.run([sys.executable, script_name])
#     if result.returncode != 0:
#         if optional:
#             print(f"\n⚠️  {script_name} encountered an issue (non-critical)")
#         else:
#             print(f"\n❌ Error running {script_name}")
#             sys.exit(1)
#     else:
#         print(f"\n✅ {script_name} completed")

# if __name__ == "__main__":
#     print("\n" + "="*60)
#     print("🔷 PATENT DATA PIPELINE - FULL DATASET (1976-2025) 🔷")
#     print("="*60)
    
#     # Step 1: Fix company relationships (if needed)
#     run_script("scripts/fix_companies.py", optional=True)
    
#     # Step 2: Analyze and generate reports
#     run_script("scripts/04_analysis.py")
    
#     # Step 3: Generate visualizations
#     run_script("scripts/05_visualizations.py")
    
#     print("\n" + "="*60)
#     print("🎉🎉🎉 PIPELINE COMPLETE! 🎉🎉🎉")
#     print("="*60)
#     print(f"\n📁 Output folder: {os.path.abspath('output')}/")
#     print("   📊 CSV reports: top_inventors, top_companies, country_trends, etc.")
#     print("   📄 JSON summary: summary.json")
#     print("   📈 Charts: top_inventors, top_companies, country_distribution, etc.")
#     print(f"\n📁 Database: {os.path.abspath('patents.db')}")
#     print(f"   Size: {os.path.getsize('patents.db')/1024/1024:.0f} MB")
#     print("\n🚀 Launch dashboard: streamlit run app.py")
#     print("="*60)

"""
Patent Data Pipeline - Main Orchestrator
Complete ETL pipeline for USPTO patent data (1976-2025)

Pipeline Overview:
  1. fix_companies.py  - Links assignees to patents (Phase 4 continuation)
  2. fix_countries.py  - Enriches inventors with country data (Phase 5)
  3. 04_analysis.py    - Runs SQL queries & generates CSV/JSON reports
  4. 05_visualizations.py - Creates PNG charts for dashboard
"""
import subprocess
import sys
import os

def run_script(script_name, optional=False):
    """Run a Python script. If optional=True, warn but don't exit on failure."""
    print(f"\n{'='*60}")
    print(f"🚀 Running: {script_name}")
    print('='*60)
    result = subprocess.run([sys.executable, script_name])
    if result.returncode != 0:
        if optional:
            print(f"\n⚠️  {script_name} encountered an issue (non-critical)")
        else:
            print(f"\n❌ Error running {script_name}")
            sys.exit(1)
    else:
        print(f"\n✅ {script_name} completed")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🔷 PATENT DATA PIPELINE - FULL DATASET (1976-2025) 🔷")
    print("="*60)
    
    # ----------------------------------------------------------------
    # Phase 4 & 5: Data Enrichment (optional - may already be done)
    # These scripts complete what extract_all.py started but couldn't
    # finish due to processing time constraints on large files.
    # They're marked optional=True so the pipeline continues even if
    # the tables/operations were already completed in a prior run.
    # ----------------------------------------------------------------
    
    # Step 1: Fix company relationships (links assignees to patents)
    run_script("scripts/fix_companies.py", optional=True)
    
    # Step 2: ADDED - Enrich inventors with real country data
    # Joins inventor location_ids with g_location_disambiguated.tsv
    run_script("scripts/fix_countries.py", optional=True)
    
    # Step 3: Analyze and generate reports (CSV + JSON + Console)
    run_script("scripts/04_analysis.py")
    
    # Step 4: Generate visualizations (PNG charts for dashboard)
    run_script("scripts/05_visualizations.py")
    
    print("\n" + "="*60)
    print("🎉🎉🎉 PIPELINE COMPLETE! 🎉🎉🎉")
    print("="*60)
    print(f"\n📁 Output folder: {os.path.abspath('output')}/")
    print("   📊 CSV reports: top_inventors, top_companies, country_trends, etc.")
    print("   📄 JSON summary: summary.json")
    print("   📈 Charts: top_inventors, top_companies, country_distribution, etc.")
    print(f"\n📁 Database: {os.path.abspath('patents.db')}")
    print(f"   Size: {os.path.getsize('patents.db')/1024/1024:.0f} MB")
    print("\n🚀 Launch dashboard: streamlit run app.py")
    print("="*60)