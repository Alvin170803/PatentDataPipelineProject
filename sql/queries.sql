-- Patent Data Analysis Queries

-- Q1: Top Inventors (Who has the most patents?)
SELECT 
    i.name,
    COUNT(DISTINCT pic.patent_id) as patent_count
FROM patent_inventor_company pic
JOIN inventors i ON pic.inventor_id = i.inventor_id
WHERE i.name IS NOT NULL AND i.name != ''
GROUP BY i.inventor_id, i.name
ORDER BY patent_count DESC
LIMIT 10;

-- Q2: Top Companies (Which companies own the most patents?)
SELECT 
    c.name,
    COUNT(DISTINCT pic.patent_id) as patent_count
FROM patent_inventor_company pic
JOIN companies c ON pic.company_id = c.company_id
WHERE c.name IS NOT NULL AND c.name != ''
GROUP BY c.company_id, c.name
ORDER BY patent_count DESC
LIMIT 10;

-- Q3: Top Countries (Which countries produce the most patents?)
SELECT 
    i.country,
    COUNT(DISTINCT pic.patent_id) as patent_count
FROM patent_inventor_company pic
JOIN inventors i ON pic.inventor_id = i.inventor_id
WHERE i.country IS NOT NULL AND i.country != ''
GROUP BY i.country
ORDER BY patent_count DESC
LIMIT 10;

-- Q4: Trends Over Time (How many patents are created each year?)
SELECT 
    year,
    COUNT(*) as patent_count
FROM patents
WHERE year IS NOT NULL
GROUP BY year
ORDER BY year DESC;

-- Q5: JOIN Query (Combine patents with inventors and companies)
SELECT 
    p.patent_id,
    p.patent_title,
    p.year,
    i.name as inventor_name,
    c.name as company_name
FROM patents p
LEFT JOIN patent_inventor_company pic ON p.patent_id = pic.patent_id
LEFT JOIN inventors i ON pic.inventor_id = i.inventor_id
LEFT JOIN companies c ON pic.company_id = c.company_id
LIMIT 20;

-- Q6: CTE Query (WITH statement - Break complex query into steps)
WITH inventor_counts AS (
    SELECT 
        inventor_id,
        COUNT(DISTINCT patent_id) as num_patents
    FROM patent_inventor_company
    GROUP BY inventor_id
),
ranked_inventors AS (
    SELECT 
        i.name,
        ic.num_patents,
        RANK() OVER (ORDER BY ic.num_patents DESC) as rank
    FROM inventor_counts ic
    JOIN inventors i ON ic.inventor_id = i.inventor_id
)
SELECT * FROM ranked_inventors WHERE rank <= 5;

-- Q7: Ranking Query (Rank inventors using window functions)
SELECT 
    i.name,
    COUNT(DISTINCT pic.patent_id) as patent_count,
    RANK() OVER (ORDER BY COUNT(DISTINCT pic.patent_id) DESC) as rank,
    DENSE_RANK() OVER (ORDER BY COUNT(DISTINCT pic.patent_id) DESC) as dense_rank
FROM patent_inventor_company pic
JOIN inventors i ON pic.inventor_id = i.inventor_id
GROUP BY i.inventor_id, i.name
ORDER BY rank
LIMIT 20;