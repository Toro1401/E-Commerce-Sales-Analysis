# Product Requirement Document (PRD)
## Project: E-Commerce Sales Analysis (Brazilian Olist Dataset)

---

## 1. Project Overview & Objective

### 1.1 Background
This project analyzes the public Brazilian E-Commerce dataset by Olist (containing 100K+ orders from 2016 to 2018). The analysis aims to help department store managers, marketing executives, and logistics leads understand their sales performance.

### 1.2 Core Objective
Answering two main business questions:
1. **Revenue Drivers**: Which product categories generate the most revenue and have the highest average order value (AOV)?
2. **Seasonality & Trends**: How do sales volume and revenue fluctuate by month, quarter, day of the week, and specific shopping events (e.g., Black Friday)?

---

## 2. Target Audience & Personas

- **Chief Marketing Officer (CMO)**: Needs to identify low-performing months to target promotions and high-AOV categories to scale marketing spend.
- **Logistics Lead**: Needs state-by-state demand distribution (regional patterns) to optimize warehouse placement and shipping lanes.
- **Data Portfolio Reviewer**: Evaluates SQL capabilities, database design, visual design principles, and business interpretation.

---

## 3. Data Architecture & Schema

The system uses an SQLite database (`ecommerce.db`) loaded from 9 raw CSV datasets:

1. **orders**: Order metadata, order status, purchase/delivery timestamps.
2. **order_items**: Item price, freight values, product links.
3. **products**: Product dimensions and Portuguese category names.
4. **category_translation**: Portuguese to English translation mapping.
5. **customers**: Customer geographic location (states, ZIP codes).
6. **order_payments**: Installments, payment methods (credit card, boleto, voucher).
7. **order_reviews**: Review scores (1 to 5 stars).
8. **sellers**: Seller geographic locations.
9. **geolocation**: Brazilian ZIP code coordinates (lat/lng).

---

## 4. Functional Requirements

### 4.1 Data Pipeline (`setup_database.py`)
- Import 9 raw CSV files cleanly into SQLite.
- Standardize Portuguese characters and handle date-time formatting.
- Create indexes on key JOIN columns (`order_id`, `product_id`, `customer_id`) to ensure fast queries.

### 4.2 SQL Analysis Metrics (`queries.sql`)
- Run 12 business-oriented SQL queries:
  - Revenue and order count by category.
  - Average Order Value (AOV) and category revenue share.
  - Monthly/quarterly revenue trends.
  - Day-of-week patterns and category seasonality indexes.
  - Customer state revenue breakdowns and top categories per state.
  - Category payment methods and installment usage.

### 4.3 Minimalist Data Visualizations (`analysis.py`)
- Generate 5 highly polished, print-ready minimalist charts (light theme, Indigo base `#4F46E5`):
  1. **Top 15 Categories by Revenue**: Clean horizontal bar chart, no grids, value labels directly on bars.
  2. **Monthly Revenue Trend**: Line chart (revenue) + background bar chart (orders) on a dual axis.
  3. **Category × Month Heatmap**: Muted color grid, labels on peak cells only to reduce clutter.
  4. **Quarterly Revenue Trends**: Clean line chart showing time trends for top 5 categories, borderless legend.
  5. **Regional Revenue Breakdown**: Stacked horizontal bar chart of top 8 states by category, borderless legend.

### 4.4 Report Delivery (`analysis_report.md`)
- Provide a summary of executive findings.
- Offer actionable business recommendations based on findings.
- Embed all 5 minimalist charts with their corresponding SQL queries.

---

## 5. Non-Functional & Design Requirements

- **Visual Aesthetics**: Clean, minimal, light-background design system. Avoid rainbow colors; use a unified, professional Indigo/Slate/Teal palette.
- **Performance**: Queries must execute under 5 seconds utilizing database indexes.
- **Robustness**: Handled gracefully under non-interactive environments (matplotlib `Agg` backend).
- **Encoding**: Proper UTF-8 support for Portuguese character mappings.

---

## 6. Deliverables & Outputs

- `setup_database.py` (Database construction script)
- `queries.sql` (Comprehensive query catalog)
- `analysis.py` (Visual analysis script)
- `analysis_report.md` (Executive report with findings)
- `charts/` (5 clean PNG charts)
