"""Build a reconciled, aggregate-only portfolio from a read-only Olist SQLite database."""
import argparse
from contextlib import closing
import csv
import json
from pathlib import Path
import sqlite3
from dashboard_template import render

ROOT=Path(__file__).resolve().parent

def queries():
    text=(ROOT/'portfolio_queries.sql').read_text(encoding='utf-8')
    return {part.splitlines()[0].strip(): '\n'.join(part.splitlines()[1:]).strip() for part in text.split('-- name: ')[1:]}

def export(db,output):
    with closing(sqlite3.connect(Path(db).resolve().as_uri()+'?mode=ro',uri=True)) as con:
        con.row_factory=sqlite3.Row
        checks={}
        for table,key in [('orders','order_id'),('customers','customer_id'),('products','product_id'),('category_translation','product_category_name')]:
            checks[table+'_duplicate_keys']=con.execute(f'SELECT COUNT(*)-COUNT(DISTINCT {key}) FROM {table}').fetchone()[0]
        checks['item_duplicate_keys']=con.execute('SELECT COUNT(*) FROM (SELECT order_id,order_item_id FROM order_items GROUP BY 1,2 HAVING COUNT(*)>1)').fetchone()[0]
        checks['orphan_items']=con.execute('SELECT COUNT(*) FROM order_items i LEFT JOIN orders o USING(order_id) WHERE o.order_id IS NULL').fetchone()[0]
        checks['delivered_without_items']=con.execute("SELECT COUNT(*) FROM orders o LEFT JOIN order_items i USING(order_id) WHERE order_status='delivered' AND i.order_id IS NULL").fetchone()[0]
        checks['invalid_item_values']=con.execute('SELECT COUNT(*) FROM order_items WHERE price IS NULL OR price<0 OR freight_value IS NULL OR freight_value<0').fetchone()[0]
        if any(checks.values()):
            raise ValueError('Blocking quality checks: '+str(checks))
        data={name:[dict(row) for row in con.execute(sql)] for name,sql in queries().items()}
        raw_revenue=con.execute("SELECT SUM(price) FROM order_items JOIN orders USING(order_id) WHERE order_status='delivered'").fetchone()[0]
        raw_paid=con.execute("SELECT SUM(payment_value) FROM order_payments JOIN orders USING(order_id) WHERE order_status='delivered'").fetchone()[0]
        checks['revenue_reconciliation_delta']=round(sum(r['revenue'] for r in data['items'])-raw_revenue,6)
        checks['payment_allocation_delta']=round(sum(r['allocated_payment'] for r in data['payment_allocation'])-raw_paid,6)
        checks['order_grain_revenue_delta']=round(sum(r['revenue'] for r in data['orders'])-raw_revenue,6)
        if any(abs(checks[k])>.01 for k in checks if k.endswith('delta')):
            raise ValueError('Reconciliation failed')
        checks['unknown_category_items']=sum(r['items'] for r in data['items'] if r['category']=='Unknown')
        checks['total_orders']=sum(r['orders'] for r in data['orders'])
        checks['product_value']=round(raw_revenue,2)
        checks['payments']=round(raw_paid,2)
        checks['status_counts']=[dict(r) for r in con.execute('SELECT order_status,COUNT(*) records FROM orders GROUP BY 1')]
        checks['coverage']=[dict(r) for r in con.execute("SELECT substr(order_purchase_timestamp,1,4) year,COUNT(DISTINCT substr(order_purchase_timestamp,1,7)) observed_months,MIN(order_purchase_timestamp) first_observed,MAX(order_purchase_timestamp) last_observed FROM orders WHERE order_status='delivered' GROUP BY 1")]
        checks['note']='Observed transactions do not prove source completeness. 2017 is the only calendar year with 12 observed months; restrict cross-year comparisons to Jan-Jul 2017/2018.'
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    for name,rows in data.items():
        with (output/(name+'.csv')).open('w',encoding='utf-8',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    data['audit']=checks
    (output/'portfolio.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
    (output/'quality.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
    render('ecommerce',data,output/'index.html')
    cats={}
    for r in data['items']:cats[r['category']]=cats.get(r['category'],0)+r['revenue']
    top=sorted(cats,key=cats.get,reverse=True)
    matched={yr:sum(r['revenue'] for r in data['items'] if r['month'][:4]==yr and '01'<=r['month'][5:]<='07') for yr in ['2017','2018']}
    report=f"""# E-Commerce analysis — verified edition

## Scope and definitions
{checks['total_orders']:,} delivered orders; R${raw_revenue:,.2f} product value. Excludes freight from product value and excludes all non-delivered orders. Payment totals include freight and other adjustments; they are not interchangeable with product value. AOV is product value divided by DISTINCT order count. Category values are additive; category order counts would not be additive for multi-category orders.

## Findings
1. Leading category: **{top[0]}**, R${cats[top[0]]:,.2f}. Top ten account for {sum(cats[k] for k in top[:10])/raw_revenue:.1%} of product value, including Unknown in the denominator.
2. Matched January–July product value: R${matched['2017']:,.2f} in 2017 and R${matched['2018']:,.2f} in 2018 ({matched['2018']/matched['2017']-1:+.1%}). This is observed marketplace growth, not causal proof of a marketing effect.
3. September/October totals from pooled years are unsuitable for a seasonal-dip claim: month coverage is unequal. The dashboard offers 2017 alone and matched Jan–Jul periods. A single complete observed year is insufficient to establish recurring seasonality.

## Decisions to investigate
- Prioritize category-level commercial review of the highest-value segments; validate margins, acquisition costs and stock constraints before reallocating budget.
- Compare like-for-like periods and separate growth from seasonal effects before planning campaigns.
- Investigate regional delivery economics before proposing geographic expansion; transaction concentration alone does not establish untapped demand.

## Quality and reproducibility
Revenue reconciliation delta: {checks['revenue_reconciliation_delta']}; allocated-payment delta: {checks['payment_allocation_delta']}. Unknown category items retained: {checks['unknown_category_items']}. All blocking key/orphan/value checks passed. See `dashboard/quality.json`, `portfolio_queries.sql` and the README.

## Limits
Historical observational dataset; no cost/margin, marketing exposure or counterfactual data. No claimed uplift or profit estimate. Legacy PNG charts and `analysis.py` remain historical exploratory work; the verified dashboard and this report supersede their seasonal interpretations.
"""
    (ROOT/'analysis_report.md').write_text(report,encoding='utf-8')
    return checks

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--db',default=str(ROOT/'ecommerce.db'));p.add_argument('--output',default=str(ROOT/'dashboard'))
    args=p.parse_args();print(json.dumps(export(args.db,args.output),indent=2))
