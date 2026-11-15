# Power BI implementation guide

The working deliverable is the browser dashboard. No native PBIX or Power BI Service deployment is included.

## Import-ready star model

Run `python export_powerbi.py --db ecommerce.db`. Load the CSVs from ignored `bi-export/` into Power BI Desktop:

| File | Grain |
| --- | --- |
| fact_items.csv | Delivered order item, keyed by order_id + order_item_id |
| dim_date.csv | One calendar date |
| dim_state.csv | One state |
| dim_category.csv | One normalized category, including Unknown |

Set `price`/`freight_value` as decimal numbers, `date` as Date and identifiers as text. Create single-direction 1:* relationships from each dimension to its fact column. Mark dim_date as the date table. Never join payment rows directly to fact_items.

```dax
Product Value = SUM(fact_items[price])
Freight Value = SUM(fact_items[freight_value])
Orders = DISTINCTCOUNT(fact_items[order_id])
Items = COUNTROWS(fact_items)
Product AOV = DIVIDE([Product Value], [Orders])
Category Share = DIVIDE([Product Value], CALCULATE([Product Value], REMOVEFILTERS(dim_category)))
```

## Three pages

1. Overview: value, orders, AOV, monthly trend; explicit period slicer.
2. Categories: ranked value and selected-category order count/AOV; keep Unknown visible.
3. Geography: state value/share; comparisons within the same period.

Validate the all-history totals against README and dashboard/quality.json. Check category/state/date selections against SQL. Show Jan–Jul 2017 and 2018 as separate comparable periods. Avoid a YoY card over partial years and do not label product value as profit.

The export stays local and includes pseudonymous source order IDs needed for distinct counts; no names, addresses, reviews or customer identifiers are exported. Do not publish raw exports by default.
