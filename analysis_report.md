# E-Commerce analysis — verified edition

## Scope and definitions
96,478 delivered orders; R$13,221,498.11 product value. Excludes freight from product value and excludes all non-delivered orders. Payment totals include freight and other adjustments; they are not interchangeable with product value. AOV is product value divided by DISTINCT order count. Category values are additive; category order counts would not be additive for multi-category orders.

## Findings
1. Leading category: **health_beauty**, R$1,233,131.72. Top ten account for 62.4% of product value, including Unknown in the denominator.
2. Matched January–July product value: R$2,438,756.43 in 2017 and R$6,379,548.48 in 2018 (+161.6%). This is observed marketplace growth, not causal proof of a marketing effect.
3. September/October totals from pooled years are unsuitable for a seasonal-dip claim: month coverage is unequal. The dashboard offers 2017 alone and matched Jan–Jul periods. A single complete observed year is insufficient to establish recurring seasonality.

## Decisions to investigate
- Prioritize category-level commercial review of the highest-value segments; validate margins, acquisition costs and stock constraints before reallocating budget.
- Compare like-for-like periods and separate growth from seasonal effects before planning campaigns.
- Investigate regional delivery economics before proposing geographic expansion; transaction concentration alone does not establish untapped demand.

## Quality and reproducibility
Revenue reconciliation delta: 0.0; allocated-payment delta: 0.0. Unknown category items retained: 1537. All blocking key/orphan/value checks passed. See `dashboard/quality.json`, `portfolio_queries.sql` and the README.

## Limits
Historical observational dataset; no cost/margin, marketing exposure or counterfactual data. No claimed uplift or profit estimate. Legacy PNG charts and `analysis.py` remain historical exploratory work; the verified dashboard and this report supersede their seasonal interpretations.
