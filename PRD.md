# Product Requirements — Olist Commercial Performance

Updated 2026-11-15. Status: verified SQL pipeline and offline dashboard implemented; native Power BI report not yet authored.

## User and decision

A commercial analyst needs to identify category/state contributions and compare like-for-like periods without confusing payments, product value and profit.

## Delivered scope and acceptance

| Requirement | Acceptance evidence |
| --- | --- |
| Stable KPI contract | docs/DATA_MODEL.md defines grains, status filter, AOV, payment weights and period coverage |
| No join multiplication | Item/order/payment aggregates reconcile to source sums within R$0.01 |
| Keep unknown categories | Left joins retain missing category rows in total value |
| Period-aware exploration | Dashboard filters all history, 2017 and matched Jan–Jul windows; no unsupported recurring-seasonality assertion |
| Interactive dashboard | Offline embedded HTML, state/category filters, export of displayed table; category order/AOV disabled when unavailable |
| Reproducibility | Read-only source connection, strict new-database loader, fixture tests and generated quality diagnostics |
| Portfolio presentation | README, PRD, verified report, preview image and GitHub About |
| BI handoff | Item-grain CSV exporter, star relationships and DAX guide; no fabricated PBIX |

## Nonfunctional requirements

No raw dataset or local database publication. No rewriting the source database. Existing exploratory charts/code preserved; verified report supersedes legacy interpretations. Python standard library for the verified SQL/HTML pipeline. No external runtime dependencies in the dashboard.

## Evidence and limits

96,478 delivered orders; R$13,221,498.11 product value. Unknown-category items retained: 1,537. Historical observational data, not a revenue-growth experiment. Costs, margins and ad exposure unavailable; economic uplifts remain unmeasured hypotheses. Observed months do not prove source completeness.

## Next work

Author and visually validate the native Power BI report using the supplied export/guide; optionally validate operational recommendations using additional cost, stock and marketing data. The current HTML dashboard is complete and reproducible.
