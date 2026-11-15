# Olist Commercial Performance Analysis

**Business question:** which product categories and customer states drive delivered-order value, and how does performance change over comparable periods?

A SQL-first analytical case using the Brazilian Olist dataset. Includes reconciled metrics, an offline interactive dashboard and a Power BI import guide. No profit, recurring seasonality or causal marketing uplift is claimed.

## Explore the results

- **[Interactive dashboard](dashboard/index.html)** — download/open the HTML locally; all data is embedded and no server is required.
- **[Verified findings](analysis_report.md)** and **[quality checks](dashboard/quality.json)**.
- [Authoritative SQL](portfolio_queries.sql), [data model / KPI definitions](docs/DATA_MODEL.md), [Power BI guide](docs/POWER_BI.md), [PRD](PRD.md).

![Dashboard preview](docs/dashboard-preview.svg)

## Verified snapshot

| Metric | Value |
| --- | --- |
| Delivered orders | 96,478 |
| Product value, excluding freight | R$13,221,498.11 |
| Payment value, including freight/adjustments | R$15,422,461.77 |
| Items without a known category | 1,537 — retained in totals |
| Top-ten category share of product value | 62.4% |

The earlier 63.3% category-share claim used a narrower category denominator. The verified version retains unknown categories and reconciles to all delivered product value. September/October totals pooled across partial years cannot establish a seasonal dip. Jan–Jul 2017 versus Jan–Jul 2018 is available as an explicit matched-window comparison; source completeness is not proven by observed transactions.

## Reproduce

Python 3.10+; the verified exporter uses only the standard library.

1. Download the [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) and place its CSV files in `dataset/`. Follow the source dataset's license/terms; no raw data is redistributed here.
2. Use the existing `ecommerce.db`, or build a new one with `python ingest_dataset.py`.
3. Run `python build_portfolio.py --db ecommerce.db` (or `--db ecommerce_rebuilt.db`).
4. Open `dashboard/index.html` directly. Choose a period, state and category. Export the displayed table if needed.
5. Run `python -m unittest discover -s tests -v` for fixture-based regression checks without the real dataset.

The exporter opens the database read-only, checks primary-key uniqueness, orphan items, invalid prices, delivered orders without items and reconciliations. It writes aggregate CSV/JSON, HTML and a generated report. No customer/order identifiers are published by the dashboard.

## Decisions supported

- Identify high-value categories for commercial review, then obtain costs/margins before reallocating budget.
- Separate observed marketplace growth from seasonality before planning promotions.
- Investigate delivery economics and customer acquisition before proposing regional expansion.

## Structure and boundaries

`portfolio_queries.sql` and `build_portfolio.py` are authoritative. `queries.sql` retains corrected exploratory examples. Existing `analysis.py` and PNG charts are legacy exploratory assets; their pooled-month/causal captions are not validated findings and are not used by the verified dashboard. A native `.pbix` is not shipped: [the guide](docs/POWER_BI.md) includes a CSV exporter, relationships, DAX and validation steps. The browser dashboard is the working interactive deliverable.

Only delivered orders are analyzed. Product value is not marketplace commission or profit; payments are different from product value. Costs, acquisition spend and experimental treatment data are unavailable. Category filters disable order/AOV cards because published category aggregates cannot produce a cross-category distinct order count. The Power BI item-grain export supports that distinct count correctly.
