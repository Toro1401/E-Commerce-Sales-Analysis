-- ============================================================
-- E-Commerce Sales Analysis — SQL Queries
-- Dataset: Brazilian E-Commerce (Olist) — SQLite
-- Business Question: Which product categories drive the most
--   revenue, and how do sales patterns vary by season?
-- ============================================================

-- ============================================================
-- REVENUE BY CATEGORY
-- ============================================================

-- Q1: Top 15 categories by total revenue
-- Revenue = SUM(price) from delivered orders only
SELECT
    ct.product_category_name_english AS category,
    COUNT(DISTINCT o.order_id)       AS total_orders,
    ROUND(SUM(oi.price), 2)         AS total_revenue,
    ROUND(AVG(oi.price), 2)         AS avg_item_price
FROM order_items oi
JOIN orders o     ON oi.order_id = o.order_id
JOIN products p   ON oi.product_id = p.product_id
JOIN category_translation ct ON p.product_category_name = ct.product_category_name
WHERE o.order_status = 'delivered'
GROUP BY ct.product_category_name_english
ORDER BY total_revenue DESC
LIMIT 15;


-- Q2: Top 15 categories by order count
SELECT
    ct.product_category_name_english AS category,
    COUNT(DISTINCT o.order_id)       AS total_orders,
    COUNT(oi.order_item_id)          AS total_items_sold
FROM order_items oi
JOIN orders o     ON oi.order_id = o.order_id
JOIN products p   ON oi.product_id = p.product_id
JOIN category_translation ct ON p.product_category_name = ct.product_category_name
WHERE o.order_status = 'delivered'
GROUP BY ct.product_category_name_english
ORDER BY total_orders DESC
LIMIT 15;


-- Q3: Average order value by category (top 15 by AOV)
SELECT
    ct.product_category_name_english AS category,
    COUNT(DISTINCT o.order_id)       AS total_orders,
    ROUND(SUM(oi.price) / COUNT(DISTINCT o.order_id), 2) AS avg_order_value,
    ROUND(SUM(oi.price), 2)         AS total_revenue
FROM order_items oi
JOIN orders o     ON oi.order_id = o.order_id
JOIN products p   ON oi.product_id = p.product_id
JOIN category_translation ct ON p.product_category_name = ct.product_category_name
WHERE o.order_status = 'delivered'
GROUP BY ct.product_category_name_english
HAVING total_orders >= 50  -- filter low-volume noise
ORDER BY avg_order_value DESC
LIMIT 15;


-- Q4: Revenue share — top 10 categories vs rest
WITH category_revenue AS (
    SELECT
        ct.product_category_name_english AS category,
        SUM(oi.price) AS revenue
    FROM order_items oi
    JOIN orders o     ON oi.order_id = o.order_id
    JOIN products p   ON oi.product_id = p.product_id
    JOIN category_translation ct ON p.product_category_name = ct.product_category_name
    WHERE o.order_status = 'delivered'
    GROUP BY ct.product_category_name_english
),
ranked AS (
    SELECT category, revenue,
           ROW_NUMBER() OVER (ORDER BY revenue DESC) AS rn
    FROM category_revenue
),
total AS (
    SELECT SUM(revenue) AS grand_total FROM category_revenue
)
SELECT
    CASE WHEN rn <= 10 THEN category ELSE 'All Others' END AS category_group,
    ROUND(SUM(revenue), 2) AS total_revenue,
    ROUND(SUM(revenue) * 100.0 / (SELECT grand_total FROM total), 2) AS pct_share
FROM ranked
GROUP BY category_group
ORDER BY total_revenue DESC;


-- ============================================================
-- SEASONAL / TIME ANALYSIS
-- ============================================================

-- Q5: Monthly revenue trend (full timeline)
SELECT
    STRFTIME('%Y-%m', o.order_purchase_timestamp) AS month,
    COUNT(DISTINCT o.order_id)                    AS orders,
    ROUND(SUM(oi.price), 2)                       AS revenue
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
WHERE o.order_status = 'delivered'
  AND o.order_purchase_timestamp IS NOT NULL
GROUP BY month
ORDER BY month;


-- Q6: Revenue by quarter
SELECT
    STRFTIME('%Y', o.order_purchase_timestamp) AS year,
    CASE
        WHEN CAST(STRFTIME('%m', o.order_purchase_timestamp) AS INTEGER) BETWEEN 1 AND 3 THEN 'Q1'
        WHEN CAST(STRFTIME('%m', o.order_purchase_timestamp) AS INTEGER) BETWEEN 4 AND 6 THEN 'Q2'
        WHEN CAST(STRFTIME('%m', o.order_purchase_timestamp) AS INTEGER) BETWEEN 7 AND 9 THEN 'Q3'
        ELSE 'Q4'
    END AS quarter,
    COUNT(DISTINCT o.order_id) AS orders,
    ROUND(SUM(oi.price), 2)   AS revenue
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
WHERE o.order_status = 'delivered'
  AND o.order_purchase_timestamp IS NOT NULL
GROUP BY year, quarter
ORDER BY year, quarter;


-- Q7: Revenue by day of week
SELECT
    CASE CAST(STRFTIME('%w', o.order_purchase_timestamp) AS INTEGER)
        WHEN 0 THEN 'Sunday'
        WHEN 1 THEN 'Monday'
        WHEN 2 THEN 'Tuesday'
        WHEN 3 THEN 'Wednesday'
        WHEN 4 THEN 'Thursday'
        WHEN 5 THEN 'Friday'
        WHEN 6 THEN 'Saturday'
    END AS day_of_week,
    CAST(STRFTIME('%w', o.order_purchase_timestamp) AS INTEGER) AS day_num,
    COUNT(DISTINCT o.order_id) AS orders,
    ROUND(SUM(oi.price), 2)   AS revenue
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
WHERE o.order_status = 'delivered'
  AND o.order_purchase_timestamp IS NOT NULL
GROUP BY day_of_week, day_num
ORDER BY day_num;


-- Q8: Seasonal index — top 10 categories by quarter
-- Shows how each category's quarterly revenue compares to its annual average
WITH quarterly AS (
    SELECT
        ct.product_category_name_english AS category,
        CASE
            WHEN CAST(STRFTIME('%m', o.order_purchase_timestamp) AS INTEGER) BETWEEN 1 AND 3 THEN 'Q1'
            WHEN CAST(STRFTIME('%m', o.order_purchase_timestamp) AS INTEGER) BETWEEN 4 AND 6 THEN 'Q2'
            WHEN CAST(STRFTIME('%m', o.order_purchase_timestamp) AS INTEGER) BETWEEN 7 AND 9 THEN 'Q3'
            ELSE 'Q4'
        END AS quarter,
        SUM(oi.price) AS q_revenue
    FROM order_items oi
    JOIN orders o     ON oi.order_id = o.order_id
    JOIN products p   ON oi.product_id = p.product_id
    JOIN category_translation ct ON p.product_category_name = ct.product_category_name
    WHERE o.order_status = 'delivered'
      AND o.order_purchase_timestamp IS NOT NULL
    GROUP BY category, quarter
),
cat_total AS (
    SELECT category, SUM(q_revenue) AS annual_revenue
    FROM quarterly
    GROUP BY category
),
top_cats AS (
    SELECT category FROM cat_total ORDER BY annual_revenue DESC LIMIT 10
)
SELECT
    q.category,
    q.quarter,
    ROUND(q.q_revenue, 2) AS quarterly_revenue,
    ROUND(q.q_revenue / (ct.annual_revenue / 4.0) * 100, 1) AS seasonal_index
FROM quarterly q
JOIN cat_total ct ON q.category = ct.category
WHERE q.category IN (SELECT category FROM top_cats)
ORDER BY ct.annual_revenue DESC, q.quarter;


-- ============================================================
-- REGIONAL ANALYSIS
-- ============================================================

-- Q9: Revenue by customer state (top 10)
SELECT
    c.customer_state                  AS state,
    COUNT(DISTINCT o.order_id)        AS total_orders,
    ROUND(SUM(oi.price), 2)          AS total_revenue,
    ROUND(SUM(oi.price) / COUNT(DISTINCT o.order_id), 2) AS avg_order_value
FROM order_items oi
JOIN orders o    ON oi.order_id = o.order_id
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_status = 'delivered'
GROUP BY c.customer_state
ORDER BY total_revenue DESC
LIMIT 10;


-- Q10: Top 3 categories per top 5 states
WITH state_cat AS (
    SELECT
        c.customer_state AS state,
        ct.product_category_name_english AS category,
        SUM(oi.price) AS revenue,
        ROW_NUMBER() OVER (PARTITION BY c.customer_state ORDER BY SUM(oi.price) DESC) AS rn
    FROM order_items oi
    JOIN orders o     ON oi.order_id = o.order_id
    JOIN customers c  ON o.customer_id = c.customer_id
    JOIN products p   ON oi.product_id = p.product_id
    JOIN category_translation ct ON p.product_category_name = ct.product_category_name
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_state, ct.product_category_name_english
),
top_states AS (
    SELECT state FROM state_cat GROUP BY state ORDER BY SUM(revenue) DESC LIMIT 5
)
SELECT
    sc.state,
    sc.rn AS rank,
    sc.category,
    ROUND(sc.revenue, 2) AS revenue
FROM state_cat sc
WHERE sc.state IN (SELECT state FROM top_states)
  AND sc.rn <= 3
ORDER BY sc.state, sc.rn;


-- ============================================================
-- CROSS-DIMENSIONAL
-- ============================================================

-- Q11: Category × Month heatmap data (top 10 categories × 12 months)
WITH top_cats AS (
    SELECT ct.product_category_name_english AS category
    FROM order_items oi
    JOIN orders o   ON oi.order_id = o.order_id
    JOIN products p ON oi.product_id = p.product_id
    JOIN category_translation ct ON p.product_category_name = ct.product_category_name
    WHERE o.order_status = 'delivered'
    GROUP BY category
    ORDER BY SUM(oi.price) DESC
    LIMIT 10
)
SELECT
    ct.product_category_name_english AS category,
    CAST(STRFTIME('%m', o.order_purchase_timestamp) AS INTEGER) AS month_num,
    CASE CAST(STRFTIME('%m', o.order_purchase_timestamp) AS INTEGER)
        WHEN 1 THEN 'Jan' WHEN 2 THEN 'Feb' WHEN 3 THEN 'Mar'
        WHEN 4 THEN 'Apr' WHEN 5 THEN 'May' WHEN 6 THEN 'Jun'
        WHEN 7 THEN 'Jul' WHEN 8 THEN 'Aug' WHEN 9 THEN 'Sep'
        WHEN 10 THEN 'Oct' WHEN 11 THEN 'Nov' WHEN 12 THEN 'Dec'
    END AS month_name,
    ROUND(SUM(oi.price), 2) AS revenue
FROM order_items oi
JOIN orders o     ON oi.order_id = o.order_id
JOIN products p   ON oi.product_id = p.product_id
JOIN category_translation ct ON p.product_category_name = ct.product_category_name
WHERE o.order_status = 'delivered'
  AND o.order_purchase_timestamp IS NOT NULL
  AND ct.product_category_name_english IN (SELECT category FROM top_cats)
GROUP BY ct.product_category_name_english, month_num
ORDER BY ct.product_category_name_english, month_num;


-- Q12: Payment method distribution by category tier
WITH cat_tiers AS (
    SELECT
        ct.product_category_name_english AS category,
        SUM(oi.price) AS revenue,
        NTILE(3) OVER (ORDER BY SUM(oi.price) DESC) AS tier
    FROM order_items oi
    JOIN orders o   ON oi.order_id = o.order_id
    JOIN products p ON oi.product_id = p.product_id
    JOIN category_translation ct ON p.product_category_name = ct.product_category_name
    WHERE o.order_status = 'delivered'
    GROUP BY category
)
SELECT
    CASE ct_tier.tier
        WHEN 1 THEN 'Top Tier'
        WHEN 2 THEN 'Mid Tier'
        WHEN 3 THEN 'Low Tier'
    END AS category_tier,
    op.payment_type,
    COUNT(*) AS payment_count,
    ROUND(SUM(op.payment_value), 2) AS total_payment_value,
    ROUND(AVG(op.payment_installments), 1) AS avg_installments
FROM order_items oi
JOIN orders o     ON oi.order_id = o.order_id
JOIN products p   ON oi.product_id = p.product_id
JOIN category_translation ct_name ON p.product_category_name = ct_name.product_category_name
JOIN cat_tiers ct_tier ON ct_name.product_category_name_english = ct_tier.category
JOIN order_payments op ON o.order_id = op.order_id
WHERE o.order_status = 'delivered'
GROUP BY category_tier, op.payment_type
ORDER BY category_tier, total_payment_value DESC;
