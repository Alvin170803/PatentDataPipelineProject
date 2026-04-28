-- Patent Pipeline Database Schema

-- Drop tables if they exist (for clean rebuilds)
DROP TABLE IF EXISTS patent_inventor_company;
DROP TABLE IF EXISTS patents;
DROP TABLE IF EXISTS inventors;
DROP TABLE IF EXISTS companies;

-- Patents table
CREATE TABLE patents (
    patent_id TEXT PRIMARY KEY,
    patent_title TEXT,
    patent_abstract TEXT,
    patent_date TEXT,
    year INTEGER
);

-- Inventors table
CREATE TABLE inventors (
    inventor_id TEXT PRIMARY KEY,
    name TEXT,
    country TEXT
);

-- Companies (assignees) table
CREATE TABLE companies (
    company_id TEXT PRIMARY KEY,
    name TEXT
);

-- Bridge table (relationships)
CREATE TABLE patent_inventor_company (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patent_id TEXT,
    inventor_id TEXT,
    company_id TEXT,
    FOREIGN KEY (patent_id) REFERENCES patents(patent_id),
    FOREIGN KEY (inventor_id) REFERENCES inventors(inventor_id),
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
);

-- Indexes for faster queries
CREATE INDEX idx_patent_year ON patents(year);
CREATE INDEX idx_bridge_patent ON patent_inventor_company(patent_id);
CREATE INDEX idx_bridge_inventor ON patent_inventor_company(inventor_id);
CREATE INDEX idx_bridge_company ON patent_inventor_company(company_id);