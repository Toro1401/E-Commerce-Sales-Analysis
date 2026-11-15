-- Authoritative metrics: delivered orders; product value excludes freight and is not profit.
-- name: items
SELECT substr(o.order_purchase_timestamp,1,7) AS month,
       COALESCE(c.customer_state,'Unknown') AS state,
       COALESCE(ct.product_category_name_english,p.product_category_name,'Unknown') AS category,
       SUM(i.price) AS revenue, SUM(i.freight_value) AS freight, COUNT(*) AS items
FROM order_items i JOIN orders o USING(order_id)
LEFT JOIN customers c USING(customer_id)
LEFT JOIN products p USING(product_id)
LEFT JOIN category_translation ct ON ct.product_category_name=p.product_category_name
WHERE o.order_status='delivered'
GROUP BY 1,2,3;

-- name: orders
-- Order-grain facts: aggregate items/payments independently, then join 1:1.
WITH item_totals AS (SELECT order_id,SUM(price) revenue,SUM(freight_value) freight FROM order_items GROUP BY order_id),
payment_totals AS (SELECT order_id,SUM(payment_value) paid FROM order_payments GROUP BY order_id)
SELECT substr(o.order_purchase_timestamp,1,7) month,COALESCE(c.customer_state,'Unknown') state,
       COUNT(*) orders,SUM(i.revenue) revenue,SUM(i.freight) freight,SUM(p.paid) paid
FROM orders o JOIN item_totals i USING(order_id)
LEFT JOIN payment_totals p USING(order_id) LEFT JOIN customers c USING(customer_id)
WHERE o.order_status='delivered' GROUP BY 1,2;

-- name: payment_allocation
-- Allocate payment rows proportionally by product value; never count payments once per item.
-- Fractional payment_count is an allocation weight, NOT a distinct count.
WITH category_values AS (
 SELECT i.order_id,COALESCE(ct.product_category_name_english,p.product_category_name,'Unknown') category,SUM(i.price) value
 FROM order_items i LEFT JOIN products p USING(product_id)
 LEFT JOIN category_translation ct ON ct.product_category_name=p.product_category_name
 GROUP BY 1,2
), weights AS (
 SELECT *,CASE WHEN SUM(value) OVER(PARTITION BY order_id)>0
 THEN value/SUM(value) OVER(PARTITION BY order_id)
 ELSE 1.0/COUNT(*) OVER(PARTITION BY order_id) END weight FROM category_values
)
SELECT w.category,p.payment_type,SUM(p.payment_value*w.weight) allocated_payment,
       SUM(w.weight) allocated_payment_rows
FROM weights w JOIN order_payments p USING(order_id) JOIN orders o USING(order_id)
WHERE o.order_status='delivered' GROUP BY 1,2;
