# Patent Data Pipeline

A data engineering mini-project that builds an ETL(Extract, Transform and Load) pipeline for USPTO patent data.

## Project Structure
- `data/` - Raw data files (ignored by Git)
- `scripts/` - Python ETL scripts
- `sql/` - SQL schema and queries
- `output/` - Cleaned CSV files and reports

## Setup
1. Download USPTO patent data files
2. Run `python scripts/extract_all.py` ,'python scripts/finish_phases_4.py','python scripts/fix_countries.py','python scripts/phase5_turbo.py'
3. Run `python main.py`
4. Run streamlit run app.py to launch the dashboard.
