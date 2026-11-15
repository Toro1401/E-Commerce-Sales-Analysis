"""Strict Olist CSV import into a NEW SQLite database; existing files are never overwritten."""
import argparse,csv,sqlite3
from contextlib import closing
from pathlib import Path

TABLES={
 'olist_customers_dataset.csv':'customers','olist_orders_dataset.csv':'orders',
 'olist_order_items_dataset.csv':'order_items','olist_order_payments_dataset.csv':'order_payments',
 'olist_order_reviews_dataset.csv':'order_reviews','olist_products_dataset.csv':'products',
 'olist_sellers_dataset.csv':'sellers','olist_geolocation_dataset.csv':'geolocation',
 'product_category_name_translation.csv':'category_translation'}

def ingest(source,output):
    source=Path(source);output=Path(output)
    if output.exists():raise FileExistsError('Refusing overwrite: '+str(output))
    for name in TABLES:
        if not (source/name).is_file():raise FileNotFoundError(source/name)
    stage=output.with_name(output.stem+'.building.db')
    if stage.exists():raise FileExistsError('Staging file exists: '+str(stage))
    quote=lambda s:'"'+s.replace('"','""')+'"'
    with closing(sqlite3.connect(stage)) as con,con:
        con.execute('CREATE TABLE ingestion_manifest(filename TEXT PRIMARY KEY,table_name TEXT,imported_rows INTEGER)')
        for filename,table in TABLES.items():
            with (source/filename).open(encoding='utf-8-sig',newline='') as f:
                reader=csv.reader(f,strict=True);header=next(reader)
                if len(set(header))!=len(header):raise ValueError('Duplicate columns: '+filename)
                schema=','.join(quote(c)+(' REAL' if c in ('price','freight_value','payment_value') else ' TEXT') for c in header)
                con.execute('CREATE TABLE '+quote(table)+' ('+schema+')')
                insert='INSERT INTO '+quote(table)+' VALUES ('+','.join('?' for _ in header)+')'
                batch=[];count=0
                for row in reader:
                    if len(row)!=len(header):raise ValueError(f'{filename}: malformed row {reader.line_num}')
                    batch.append([v if v!='' else None for v in row]);count+=1
                    if len(batch)>=2000:con.executemany(insert,batch);batch=[]
                if batch:con.executemany(insert,batch)
                con.execute('INSERT INTO ingestion_manifest VALUES (?,?,?)',(filename,table,count))
                print(filename,count)
        for table,key in [('orders','order_id'),('order_items','order_id'),('order_payments','order_id'),('products','product_id'),('customers','customer_id')]:
            con.execute(f'CREATE INDEX idx_{table}_{key} ON {table}({key})')
    stage.rename(output)

if __name__=='__main__':
    root=Path(__file__).resolve().parent;p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',default=str(root/'dataset'));p.add_argument('--output',default=str(root/'ecommerce_rebuilt.db'))
    a=p.parse_args();ingest(a.source,a.output)
