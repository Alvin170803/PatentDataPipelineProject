"""
Patent Data Pipeline - Main Orchestrator
Complete ETL pipeline for USPTO patent data (1976-2025)
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
    
    # Step 1: Fix company relationships (if needed)
    run_script("scripts/fix_companies.py", optional=True)
    
    # Step 2: Analyze and generate reports
    run_script("scripts/04_analysis.py")
    
    # Step 3: Generate visualizations
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