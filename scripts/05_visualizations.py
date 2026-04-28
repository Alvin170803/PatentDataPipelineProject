"""
Step 5: Generate Data Visualizations
Creates charts and graphs from the analysis results.
"""
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import os

DB_PATH = "patents.db"
OUTPUT_DIR = "output"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Set a clean, professional style
plt.style.use('seaborn-v0_8-whitegrid')

# Color palette
COLORS = ['#2196F3', '#4CAF50', '#FF9800', '#E91E63', '#9C27B0', 
          '#00BCD4', '#FF5722', '#795548', '#607D8B', '#F44336']

print("=" * 60)
print("STEP 5: Generating Visualizations")
print("=" * 60)

conn = sqlite3.connect(DB_PATH)

# ------------------------------------------------------------
# Chart 1: Top 10 Inventors (Horizontal Bar Chart)
# ------------------------------------------------------------
print("\n[1/4] Top Inventors Chart...")

q1 = """
SELECT 
    i.name,
    COUNT(DISTINCT pic.patent_id) as patent_count
FROM patent_inventor_company pic
JOIN inventors i ON pic.inventor_id = i.inventor_id
WHERE i.name IS NOT NULL AND i.name != ''
GROUP BY i.inventor_id, i.name
ORDER BY patent_count DESC
LIMIT 10
"""
top_inventors = pd.read_sql_query(q1, conn)

if not top_inventors.empty:
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Reverse order so highest is at top
    top_inventors = top_inventors.iloc[::-1]
    
    bars = ax.barh(top_inventors['name'].str[:25], top_inventors['patent_count'], 
                   color=COLORS[0], edgecolor='white', height=0.7)
    
    # Add value labels
    for bar, count in zip(bars, top_inventors['patent_count']):
        ax.text(bar.get_width() + max(top_inventors['patent_count'])*0.01, 
                bar.get_y() + bar.get_height()/2,
                f'{count:,}', va='center', fontsize=10, fontweight='bold')
    
    ax.set_xlabel('Number of Patents', fontsize=12, fontweight='bold')
    ax.set_title('Top 10 Inventors by Patent Count', fontsize=14, fontweight='bold', pad=15)
    ax.xaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}'))
    
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/top_inventors.png", dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✅ Saved top_inventors.png")
else:
    print("⚠️ No inventor data for chart")

# ------------------------------------------------------------
# Chart 2: Top 10 Companies (Horizontal Bar Chart)
# ------------------------------------------------------------
print("\n[2/4] Top Companies Chart...")

q2 = """
SELECT 
    c.name,
    COUNT(DISTINCT pic.patent_id) as patent_count
FROM patent_inventor_company pic
JOIN companies c ON pic.company_id = c.company_id
WHERE c.name IS NOT NULL AND c.name != ''
GROUP BY c.company_id, c.name
ORDER BY patent_count DESC
LIMIT 10
"""
top_companies = pd.read_sql_query(q2, conn)

if not top_companies.empty:
    fig, ax = plt.subplots(figsize=(10, 6))
    
    top_companies = top_companies.iloc[::-1]
    
    bars = ax.barh(top_companies['name'].str[:30], top_companies['patent_count'], 
                   color=COLORS[1], edgecolor='white', height=0.7)
    
    for bar, count in zip(bars, top_companies['patent_count']):
        ax.text(bar.get_width() + max(top_companies['patent_count'])*0.01, 
                bar.get_y() + bar.get_height()/2,
                f'{count:,}', va='center', fontsize=10, fontweight='bold')
    
    ax.set_xlabel('Number of Patents', fontsize=12, fontweight='bold')
    ax.set_title('Top 10 Companies by Patent Count', fontsize=14, fontweight='bold', pad=15)
    ax.xaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}'))
    
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/top_companies.png", dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✅ Saved top_companies.png")
else:
    print("⚠️ No company data for chart")

# ------------------------------------------------------------
# Chart 3: Country Distribution (Pie Chart)
# ------------------------------------------------------------
print("\n[3/4] Country Distribution Chart...")

q3 = """
SELECT 
    i.country,
    COUNT(DISTINCT pic.patent_id) as patent_count
FROM patent_inventor_company pic
JOIN inventors i ON pic.inventor_id = i.inventor_id
WHERE i.country IS NOT NULL AND i.country != ''
GROUP BY i.country
ORDER BY patent_count DESC
LIMIT 8
"""
top_countries = pd.read_sql_query(q3, conn)

if not top_countries.empty:
    # Group remaining countries as "Other"
    total_patents = top_countries['patent_count'].sum()
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Pie Chart
    wedges, texts, autotexts = ax1.pie(
        top_countries['patent_count'], 
        labels=top_countries['country'], 
        autopct='%1.1f%%',
        colors=COLORS[:len(top_countries)],
        startangle=140,
        pctdistance=0.85
    )
    for autotext in autotexts:
        autotext.set_fontsize(9)
        autotext.set_fontweight('bold')
    ax1.set_title('Patent Distribution by Country', fontsize=14, fontweight='bold', pad=15)
    
    # Bar Chart (same data)
    top_countries_sorted = top_countries.sort_values('patent_count', ascending=True)
    bars = ax2.barh(top_countries_sorted['country'], top_countries_sorted['patent_count'], 
                    color=COLORS[:len(top_countries)], edgecolor='white')
    
    for bar, count in zip(bars, top_countries_sorted['patent_count']):
        ax2.text(bar.get_width() + max(top_countries_sorted['patent_count'])*0.02, 
                bar.get_y() + bar.get_height()/2,
                f'{count:,}', va='center', fontsize=10, fontweight='bold')
    
    ax2.set_xlabel('Number of Patents', fontsize=12, fontweight='bold')
    ax2.set_title('Top Countries by Patent Count', fontsize=14, fontweight='bold', pad=15)
    ax2.xaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}'))
    
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/country_distribution.png", dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✅ Saved country_distribution.png")
else:
    print("⚠️ No country data for chart")

# ------------------------------------------------------------
# Chart 4: Patents Per Year (Line Chart)
# ------------------------------------------------------------
print("\n[4/4] Patents Per Year Chart...")

q4 = """
SELECT 
    year,
    COUNT(*) as patent_count
FROM patents
WHERE year IS NOT NULL AND year >= 2020 AND year <= 2025
GROUP BY year
ORDER BY year
"""
yearly_trends = pd.read_sql_query(q4, conn)

if not yearly_trends.empty:
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Line with markers
    ax.plot(yearly_trends['year'], yearly_trends['patent_count'], 
            marker='o', linewidth=3, markersize=12, color=COLORS[0], 
            markerfacecolor='white', markeredgewidth=2, markeredgecolor=COLORS[0])
    
    # Fill area under line
    ax.fill_between(yearly_trends['year'], yearly_trends['patent_count'], 
                    alpha=0.2, color=COLORS[0])
    
    # Add value labels
    for x, y in zip(yearly_trends['year'], yearly_trends['patent_count']):
        ax.annotate(f'{y:,}', (x, y), textcoords="offset points", 
                    xytext=(0, 15), ha='center', fontsize=11, fontweight='bold')
    
    ax.set_xlabel('Year', fontsize=12, fontweight='bold')
    ax.set_ylabel('Number of Patents', fontsize=12, fontweight='bold')
    ax.set_title('Patent Grants by Year (2020-2025)', fontsize=14, fontweight='bold', pad=15)
    ax.set_xticks(yearly_trends['year'])
    ax.yaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}'))
    
    # Add grid
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/patents_per_year.png", dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✅ Saved patents_per_year.png")
else:
    print("⚠️ No yearly data for chart")

# ------------------------------------------------------------
# Summary
# ------------------------------------------------------------
conn.close()

print("\n" + "=" * 60)
print("YAYY! Visualizations Complete!")
print("=" * 60)
print(f"\n📁 All charts saved to: {OUTPUT_DIR}/")
print("   - top_inventors.png")
print("   - top_companies.png")
print("   - country_distribution.png")
print("   - patents_per_year.png")
print("\n✅ Ready for reports or dashboard!")
print("=" * 60)