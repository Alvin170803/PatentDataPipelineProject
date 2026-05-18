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
    print("SORRY! No inventor data for chart")

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
    print("SORRY! No company data for chart")

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
    print("SORRY! No country data for chart")

# ------------------------------------------------------------
# Chart 4: Patents Per Year (Line Chart)
# ------------------------------------------------------------
print("\n[4/6] Patents Per Year Chart...")

q4 = """
SELECT 
    year,
    COUNT(*) as patent_count
FROM patents
WHERE year IS NOT NULL
GROUP BY year
ORDER BY year
"""
yearly_trends = pd.read_sql_query(q4, conn)

if not yearly_trends.empty:
    fig, ax = plt.subplots(figsize=(14, 6))  # Wider for all years
    
    # Line with markers
    ax.plot(yearly_trends['year'], yearly_trends['patent_count'], 
            marker='o', linewidth=2, markersize=5, color=COLORS[0], 
            markerfacecolor='white', markeredgewidth=1.5, markeredgecolor=COLORS[0])
    
    # Fill area under line
    ax.fill_between(yearly_trends['year'], yearly_trends['patent_count'], 
                    alpha=0.15, color=COLORS[0])
    
    # Add value labels (every 5th year only to avoid overlap)
    for i, (x, y) in enumerate(zip(yearly_trends['year'], yearly_trends['patent_count'])):
        if i % 5 == 0:
            ax.annotate(f'{y:,}', (x, y), textcoords="offset points", 
                        xytext=(0, 12), ha='center', fontsize=8, fontweight='bold')
    
    ax.set_xlabel('Year', fontsize=12, fontweight='bold')
    ax.set_ylabel('Number of Patents', fontsize=12, fontweight='bold')
    ax.set_title('Patent Grants by Year (1976-2025)', fontsize=14, fontweight='bold', pad=15)
    
    # Set all years as ticks, rotate vertically
    ax.set_xticks(yearly_trends['year'])
    ax.set_xticklabels(yearly_trends['year'], rotation=90, fontsize=6)
    
    ax.yaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}'))
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout(pad=2.0)
    plt.savefig(f"{OUTPUT_DIR}/patents_per_year.png", dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✅ Saved patents_per_year.png")
else:
    print("SORRY! No yearly data for chart")
    
# ------------------------------------------------------------
# Chart 5: Decade Trends (Bar Chart)
# ------------------------------------------------------------
print("\n[5/6] Decade Trends Chart...")

q5 = """
SELECT 
    (year / 10) * 10 as decade,
    COUNT(*) as patent_count
FROM patents
WHERE year IS NOT NULL
GROUP BY decade
ORDER BY decade
"""
decade_data = pd.read_sql_query(q5, conn)

if not decade_data.empty:
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Convert decade to label like "1970s"
    decade_data['label'] = decade_data['decade'].astype(int).astype(str) + 's'
    
    bars = ax.bar(decade_data['label'], decade_data['patent_count'], 
                  color=COLORS[:len(decade_data)], edgecolor='white', width=0.6)
    
    # Add value labels on top of bars
    for bar, count in zip(bars, decade_data['patent_count']):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(decade_data['patent_count'])*0.01,
                f'{count:,}', ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    ax.set_xlabel('Decade', fontsize=12, fontweight='bold')
    ax.set_ylabel('Number of Patents', fontsize=12, fontweight='bold')
    ax.set_title('Patent Grants by Decade (1976-2025)', fontsize=14, fontweight='bold', pad=15)
    ax.yaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}'))
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/decade_trends.png", dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✅ Saved decade_trends.png")
else:
    print("SORRY! No decade data for chart")

# ------------------------------------------------------------
# Chart 6: Top Collaborations (Horizontal Bar Chart)
# ------------------------------------------------------------
print("\n[6/6] Top Collaborations Chart...")

q6 = """
SELECT 
    i.name as inventor,
    c.name as company,
    COUNT(DISTINCT pic.patent_id) as joint_patents
FROM patent_inventor_company pic
JOIN inventors i ON pic.inventor_id = i.inventor_id
JOIN companies c ON pic.company_id = c.company_id
WHERE c.name IS NOT NULL AND c.name != ''
GROUP BY i.inventor_id, c.company_id
ORDER BY joint_patents DESC
LIMIT 8
"""
collaborations = pd.read_sql_query(q6, conn)

if not collaborations.empty and len(collaborations) > 0:
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Create label combining inventor and company
    collaborations['label'] = collaborations['inventor'].str[:20] + ' + ' + collaborations['company'].str[:20]
    collaborations = collaborations.iloc[::-1]  # Reverse for horizontal bar
    
    bars = ax.barh(collaborations['label'], collaborations['joint_patents'], 
                   color=COLORS[3], edgecolor='white', height=0.7)
    
    for bar, count in zip(bars, collaborations['joint_patents']):
        ax.text(bar.get_width() + max(collaborations['joint_patents'])*0.01, 
                bar.get_y() + bar.get_height()/2,
                f'{count:,}', va='center', fontsize=9, fontweight='bold')
    
    ax.set_xlabel('Joint Patents', fontsize=12, fontweight='bold')
    ax.set_title('Top Inventor-Company Collaborations', fontsize=14, fontweight='bold', pad=15)
    ax.xaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}'))
    
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/collaborations.png", dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✅ Saved collaborations.png")
else:
    print("SORRY! No collaboration data for chart (skipping)")    

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
print("   - decade_trends.png")        
print("   - collaborations.png") 
print("\n✅ Ready for reports or dashboard!")
print("=" * 60)