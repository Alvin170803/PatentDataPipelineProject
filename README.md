# Patent Data Pipeline

A data engineering mini-project that builds an ETL pipeline for USPTO patent data.

## Project Structure
- `data/` - Raw data files (ignored by Git)
- `scripts/` - Python ETL scripts
- `sql/` - SQL schema and queries
- `output/` - Cleaned CSV files and reports

## Setup
1. Download USPTO patent data files
2. Run `python scripts/01_extract_sample.py`
3. Run `python main.py`