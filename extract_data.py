"""Quick data extraction for report."""
import sqlite3, pandas as pd
conn = sqlite3.connect("ecommerce.db")

# Total revenue
r = pd.read_sql("SELECT ROUND(SUM(price),2) as total FROM order_items oi JOIN orders o ON oi.order_id=o.order_id WHERE o.order_status='delivered'", conn)
print("TOTAL REVENUE:", r["total"].values[0])

# Top 10 categories
print("\n--- TOP 10 CATEGORIES ---")
df = pd.read_sql("""SELECT ct.product_category_name_english AS cat, ROUND(SUM(oi.price),2) AS rev, COUNT(DISTINCT o.order_id) AS orders
FROM order_items oi JOIN orders o ON oi.order_id=o.order_id JOIN products p ON oi.product_id=p.product_id
JOIN category_translation ct ON p.product_category_name=ct.product_category_name
WHERE o.order_status='delivered' GROUP BY cat ORDER BY rev DESC LIMIT 10""", conn)
print(df.to_string(index=False))

# Revenue share top 10
total_rev = pd.read_sql("""SELECT SUM(oi.price) as total FROM order_items oi JOIN orders o ON oi.order_id=o.order_id
JOIN products p ON oi.product_id=p.product_id JOIN category_translation ct ON p.product_category_name=ct.product_category_name
WHERE o.order_status='delivered'""", conn)["total"].values[0]
top10_rev = df["rev"].sum()
print(f"\nTop 10 share: {top10_rev/total_rev*100:.1f}%")

# Quarterly
print("\n--- QUARTERLY ---")
df = pd.read_sql("""SELECT STRFTIME('%Y',o.order_purchase_timestamp) AS yr,
CASE WHEN CAST(STRFTIME('%m',o.order_purchase_timestamp) AS INT) BETWEEN 1 AND 3 THEN 'Q1'
WHEN CAST(STRFTIME('%m',o.order_purchase_timestamp) AS INT) BETWEEN 4 AND 6 THEN 'Q2'
WHEN CAST(STRFTIME('%m',o.order_purchase_timestamp) AS INT) BETWEEN 7 AND 9 THEN 'Q3' ELSE 'Q4' END AS q,
COUNT(DISTINCT o.order_id) AS orders, ROUND(SUM(oi.price),2) AS rev
FROM order_items oi JOIN orders o ON oi.order_id=o.order_id
WHERE o.order_status='delivered' AND o.order_purchase_timestamp IS NOT NULL
GROUP BY yr,q ORDER BY yr,q""", conn)
print(df.to_string(index=False))

# Top states
print("\n--- TOP STATES ---")
df = pd.read_sql("""SELECT c.customer_state AS state, COUNT(DISTINCT o.order_id) AS orders, ROUND(SUM(oi.price),2) AS rev
FROM order_items oi JOIN orders o ON oi.order_id=o.order_id JOIN customers c ON o.customer_id=c.customer_id
WHERE o.order_status='delivered' GROUP BY state ORDER BY rev DESC LIMIT 10""", conn)
print(df.to_string(index=False))

# Day of week
print("\n--- DAY OF WEEK ---")
df = pd.read_sql("""SELECT CASE CAST(STRFTIME('%w',o.order_purchase_timestamp) AS INT)
WHEN 0 THEN 'Sun' WHEN 1 THEN 'Mon' WHEN 2 THEN 'Tue' WHEN 3 THEN 'Wed'
WHEN 4 THEN 'Thu' WHEN 5 THEN 'Fri' WHEN 6 THEN 'Sat' END AS day,
COUNT(DISTINCT o.order_id) AS orders, ROUND(SUM(oi.price),2) AS rev
FROM order_items oi JOIN orders o ON oi.order_id=o.order_id
WHERE o.order_status='delivered' AND o.order_purchase_timestamp IS NOT NULL
GROUP BY day, CAST(STRFTIME('%w',o.order_purchase_timestamp) AS INT)
ORDER BY CAST(STRFTIME('%w',o.order_purchase_timestamp) AS INT)""", conn)
print(df.to_string(index=False))

# AOV by top categories
print("\n--- AVG ORDER VALUE (TOP 15, min 50 orders) ---")
df = pd.read_sql("""SELECT ct.product_category_name_english AS cat,
COUNT(DISTINCT o.order_id) AS orders,
ROUND(SUM(oi.price)/COUNT(DISTINCT o.order_id),2) AS aov
FROM order_items oi JOIN orders o ON oi.order_id=o.order_id JOIN products p ON oi.product_id=p.product_id
JOIN category_translation ct ON p.product_category_name=ct.product_category_name
WHERE o.order_status='delivered' GROUP BY cat HAVING orders>=50 ORDER BY aov DESC LIMIT 15""", conn)
print(df.to_string(index=False))

conn.close()
