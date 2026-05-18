
"""
Patent Data Dashboard
Run with: streamlit run app.py
"""

import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# Page config
st.set_page_config(
    page_title="Patent Data Pipeline",
    page_icon="📊",
    layout="wide"
)

# Color palette
COLORS = ['#2196F3', '#4CAF50', '#FF9800', '#E91E63', '#9C27B0',
          '#00BCD4', '#FF5722', '#795548', '#607D8B', '#F44336']

# ------------------------------------------------------------
# Database Connection
# ------------------------------------------------------------
@st.cache_data(ttl=60)
def load_data():
    """Load all data from SQLite database."""
    conn = sqlite3.connect('patents.db', timeout=30)
    
    # Total counts
    total_patents = pd.read_sql("SELECT COUNT(*) as count FROM patents", conn).iloc[0,0]
    total_inventors = pd.read_sql("SELECT COUNT(*) as count FROM inventors", conn).iloc[0,0]
    total_companies = pd.read_sql("SELECT COUNT(*) as count FROM companies", conn).iloc[0,0]
    
    # Top inventors
    top_inventors = pd.read_sql("""
        SELECT i.name, COUNT(DISTINCT pic.patent_id) as patent_count
        FROM patent_inventor_company pic
        JOIN inventors i ON pic.inventor_id = i.inventor_id
        WHERE i.name IS NOT NULL AND i.name != ''
        GROUP BY i.inventor_id, i.name
        ORDER BY patent_count DESC LIMIT 10
    """, conn)
    
    # Top companies
    top_companies = pd.read_sql("""
        SELECT c.name, COUNT(DISTINCT pic.patent_id) as patent_count
        FROM patent_inventor_company pic
        JOIN companies c ON pic.company_id = c.company_id
        WHERE c.name IS NOT NULL AND c.name != ''
        GROUP BY c.company_id, c.name
        ORDER BY patent_count DESC LIMIT 10
    """, conn)
    
    # Top countries
    top_countries = pd.read_sql("""
        SELECT i.country, COUNT(DISTINCT pic.patent_id) as patent_count
        FROM patent_inventor_company pic
        JOIN inventors i ON pic.inventor_id = i.inventor_id
        WHERE i.country IS NOT NULL AND i.country != ''
        GROUP BY i.country
        ORDER BY patent_count DESC LIMIT 10
    """, conn)
    
    # Yearly trends
    yearly_trends = pd.read_sql("""
        SELECT year, COUNT(*) as patent_count
        FROM patents WHERE year IS NOT NULL
        GROUP BY year ORDER BY year
    """, conn)
    
    # Decade trends (BONUS)
    decade_trends = pd.read_sql("""
        SELECT (year / 10) * 10 as decade, COUNT(*) as patent_count
        FROM patents WHERE year IS NOT NULL
        GROUP BY decade ORDER BY decade
    """, conn)
    
    # Diverse companies (BONUS)
    diverse_companies = pd.read_sql("""
        SELECT 
            c.name, 
            COUNT(DISTINCT pic.patent_id) as total_patents
        FROM patent_inventor_company pic
        JOIN companies c ON pic.company_id = c.company_id
        WHERE c.name IS NOT NULL AND c.name != ''
        GROUP BY c.company_id, c.name
        ORDER BY total_patents DESC 
        LIMIT 10
    """, conn)
    
    conn.close()
    
    return (total_patents, total_inventors, total_companies, 
            top_inventors, top_companies, top_countries, 
            yearly_trends, decade_trends, diverse_companies)

# ------------------------------------------------------------
# Load Data
# ------------------------------------------------------------
(total_patents, total_inventors, total_companies, 
 top_inventors, top_companies, top_countries, 
 yearly_trends, decade_trends, diverse_companies) = load_data()

# ------------------------------------------------------------
# Dashboard UI
# ------------------------------------------------------------

st.title("📊 Patent Data Pipeline Dashboard (1976-2025)")
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()
st.markdown("---")

# KPI Metrics Row
st.subheader("📈 Key Metrics")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Patents", f"{total_patents:,}", delta="1976-2025")
with col2:
    st.metric("Total Inventors", f"{total_inventors:,}")
with col3:
    st.metric("Total Companies", f"{total_companies:,}")

st.markdown("---")

# Charts Row 1: Top Inventors + Top Companies
st.subheader("📊 Top Performers")
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Top 10 Inventors")
    if not top_inventors.empty:
        fig, ax = plt.subplots(figsize=(10, 5))
        data = top_inventors.iloc[::-1]
        bars = ax.barh(data['name'].str[:25], data['patent_count'], color=COLORS[0], edgecolor='white', height=0.7)
        max_val = max(data['patent_count'])
        ax.set_xlim(0, max_val * 1.25)
        for bar, count in zip(bars, data['patent_count']):
            ax.text(bar.get_width() + max_val * 0.02, bar.get_y() + bar.get_height()/2,
                    f'{count:,}', va='center', fontsize=9, fontweight='bold')
        ax.set_xlabel('Number of Patents', fontsize=11, fontweight='bold')
        ax.xaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}'))
        ax.grid(True, alpha=0.2, axis='x')
        plt.tight_layout(pad=1.5)
        st.pyplot(fig)
    else:
        st.info("No inventor data available")

with col2:
    st.markdown("#### Top 10 Companies")
    if not top_companies.empty:
        fig, ax = plt.subplots(figsize=(10, 5))
        data = top_companies.iloc[::-1]
        bars = ax.barh(data['name'].str[:30], data['patent_count'], color=COLORS[1], edgecolor='white', height=0.7)
        max_val = max(data['patent_count'])
        ax.set_xlim(0, max_val * 1.25)
        for bar, count in zip(bars, data['patent_count']):
            ax.text(bar.get_width() + max_val * 0.02, bar.get_y() + bar.get_height()/2,
                    f'{count:,}', va='center', fontsize=9, fontweight='bold')
        ax.set_xlabel('Number of Patents', fontsize=11, fontweight='bold')
        ax.xaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}'))
        ax.grid(True, alpha=0.2, axis='x')
        plt.tight_layout(pad=1.5)
        st.pyplot(fig)
    else:
        st.info("No company data available")

st.markdown("---")

# Charts Row 2: Countries + Yearly Trends
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Patents by Country")
    if not top_countries.empty:
        fig, ax = plt.subplots(figsize=(7, 7))
        wedges, texts, autotexts = ax.pie(
            top_countries['patent_count'].head(8),
            labels=top_countries['country'].head(8),
            autopct='%1.1f%%',
            colors=COLORS[:8],
            startangle=140
        )
        for autotext in autotexts:
            autotext.set_fontsize(8)
            autotext.set_fontweight('bold')
        st.pyplot(fig)
    else:
        st.info("No country data available")

with col2:
    st.markdown("#### Patents by Year")
    if not yearly_trends.empty:
        fig, ax = plt.subplots(figsize=(12, 6))  # Wider figure
        
        # Only show every 5th year label to reduce clutter
        ax.plot(yearly_trends['year'], yearly_trends['patent_count'],
                marker='o', linewidth=2, markersize=6, color=COLORS[0],
                markerfacecolor='white', markeredgewidth=2, markeredgecolor=COLORS[0])
        ax.fill_between(yearly_trends['year'], yearly_trends['patent_count'], alpha=0.15, color=COLORS[0])
        
        # Only label every 5th year to avoid overlap
        for i, (x, y) in enumerate(zip(yearly_trends['year'], yearly_trends['patent_count'])):
            if i % 5 == 0:  # Label every 5th year
                ax.annotate(f'{y:,}', (x, y), textcoords="offset points",
                            xytext=(0, 14), ha='center', fontsize=8, fontweight='bold')
        
        ax.set_xlabel('Year', fontsize=11, fontweight='bold')
        ax.set_ylabel('Number of Patents', fontsize=11, fontweight='bold')
        
        # Set all years as ticks but rotate them vertically
        ax.set_xticks(yearly_trends['year'])
        ax.set_xticklabels(yearly_trends['year'], rotation=90, fontsize=7)  # Vertical labels!
        
        ax.yaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}'))
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout(pad=2.0)
        st.pyplot(fig)
    else:
        st.info("No yearly data available")

st.markdown("---")

# Charts Row 3: Decade Trends + Diverse Companies (BONUS)
st.subheader("📊 Bonus Analytics")
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Patents by Decade")
    if not decade_trends.empty:
        fig, ax = plt.subplots(figsize=(7, 5))
        decade_trends['label'] = decade_trends['decade'].astype(int).astype(str) + 's'
        bars = ax.bar(decade_trends['label'], decade_trends['patent_count'], 
                      color=COLORS[:len(decade_trends)], edgecolor='white', width=0.6)
        for bar, count in zip(bars, decade_trends['patent_count']):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(decade_trends['patent_count'])*0.01,
                    f'{count:,}', ha='center', va='bottom', fontsize=9, fontweight='bold')
        ax.set_xlabel('Decade')
        ax.set_ylabel('Patents')
        ax.yaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}'))
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig)
    else:
        st.info("No decade data available")

with col2:
    st.markdown("#### Top Companies by Patent Volume)")
    if not diverse_companies.empty:
        fig, ax = plt.subplots(figsize=(7, 5))
        data = diverse_companies.iloc[::-1]
        bars = ax.barh(data['name'].str[:25], data['total_patents'], color=COLORS[3], edgecolor='white', height=0.7)
        max_val = max(data['total_patents'])
        ax.set_xlim(0, max_val * 1.25)
        for bar, count in zip(bars, data['total_patents']):
            ax.text(bar.get_width() + max_val * 0.02, bar.get_y() + bar.get_height()/2,
                    f'{count:,}', va='center', fontsize=9, fontweight='bold')
        ax.set_xlabel('Total Patents', fontsize=11, fontweight='bold')
        ax.xaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}'))
        ax.grid(True, alpha=0.2, axis='x')
        plt.tight_layout(pad=1.5)
        st.pyplot(fig)
    else:
        st.info("No diverse company data available")

st.markdown("---")

# Data Tables (Expandable)
st.subheader("📋 Detailed Tabular Data")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Top Inventors", "Top Companies", "Yearly Trends", "Decade Trends", "Diverse Companies"])

with tab1:
    st.dataframe(top_inventors, use_container_width=True, hide_index=True)
with tab2:
    st.dataframe(top_companies, use_container_width=True, hide_index=True)
with tab3:
    st.dataframe(yearly_trends, use_container_width=True, hide_index=True)
with tab4:
    st.dataframe(decade_trends[['decade', 'patent_count']], use_container_width=True, hide_index=True)
with tab5:
    st.dataframe(diverse_companies, use_container_width=True, hide_index=True)

# Footer
st.markdown("---")
st.markdown("💡 **Data Source:** USPTO PatentsView (1976-2025) | Built with Streamlit & SQLite")