"""Export item-grain star-model CSVs locally for Power BI Desktop."""
import argparse,csv,sqlite3,datetime
from contextlib import closing
from pathlib import Path

def export(db,output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    with closing(sqlite3.connect(Path(db).resolve().as_uri()+'?mode=ro',uri=True)) as con:
        cur=con.execute("""SELECT i.order_id,i.order_item_id,date(o.order_purchase_timestamp) date,
            COALESCE(c.customer_state,'Unknown') state,
            COALESCE(t.product_category_name_english,p.product_category_name,'Unknown') category,
            i.price,i.freight_value FROM order_items i JOIN orders o USING(order_id)
            LEFT JOIN customers c USING(customer_id) LEFT JOIN products p USING(product_id)
            LEFT JOIN category_translation t ON t.product_category_name=p.product_category_name
            WHERE o.order_status='delivered'""")
        rows=cur.fetchall()
        def save(name,headers,values):
            with (output/(name+'.csv')).open('w',encoding='utf-8',newline='') as f:
                w=csv.writer(f);w.writerow(headers);w.writerows(values)
        save('fact_items',[d[0] for d in cur.description],rows)
        save('dim_state',['state'],[(x,) for x in sorted({r[3] for r in rows})])
        save('dim_category',['category'],[(x,) for x in sorted({r[4] for r in rows})])
        first=datetime.date.fromisoformat(min(r[2] for r in rows));last=datetime.date.fromisoformat(max(r[2] for r in rows))
        dates=[]
        while first<=last:
            dates.append((first.isoformat(),first.year,first.month));first+=datetime.timedelta(days=1)
        save('dim_date',['date','year','month'],dates)
        return len(rows)

if __name__=='__main__':
    root=Path(__file__).resolve().parent;p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--db',default=str(root/'ecommerce.db'));p.add_argument('--output',default=str(root/'bi-export'))
    a=p.parse_args();print('Exported item rows:',export(a.db,a.output))
