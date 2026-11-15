import importlib.util
from pathlib import Path
import sqlite3,tempfile,unittest
from unittest.mock import patch
from contextlib import closing
import build_portfolio as project

class MetricsTests(unittest.TestCase):
    def fixture(self,root):
        path=root/'fixture.db'
        with closing(sqlite3.connect(path)) as c, c:
            c.executescript("""
            CREATE TABLE orders(order_id TEXT,customer_id TEXT,order_status TEXT,order_purchase_timestamp TEXT);
            CREATE TABLE customers(customer_id TEXT,customer_state TEXT);
            CREATE TABLE products(product_id TEXT,product_category_name TEXT);
            CREATE TABLE category_translation(product_category_name TEXT,product_category_name_english TEXT);
            CREATE TABLE order_items(order_id TEXT,order_item_id INTEGER,product_id TEXT,price REAL,freight_value REAL);
            CREATE TABLE order_payments(order_id TEXT,payment_type TEXT,payment_value REAL);
            INSERT INTO orders VALUES ('a','c','delivered','2017-01-10'),('b','c','canceled','2017-01-10');
            INSERT INTO customers VALUES ('c','SP');
            INSERT INTO products VALUES ('p','known'),('q',NULL);
            INSERT INTO category_translation VALUES ('known','Known');
            INSERT INTO order_items VALUES ('a',1,'p',60,3),('a',2,'q',40,2),('b',1,'p',999,0);
            INSERT INTO order_payments VALUES ('a','credit',80),('a','voucher',25);
            """)
        return path

    def test_multicategory_multiple_payments_reconcile_and_unknown_survives(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);db=self.fixture(root)
            (root/'portfolio_queries.sql').write_text((project.ROOT/'portfolio_queries.sql').read_text())
            # Patch report root so fixtures never overwrite the real report.
            with patch.object(project,'ROOT',root):
                audit=project.export(db,root/'dashboard')
            self.assertEqual(audit['product_value'],100)
            self.assertEqual(audit['payments'],105)
            self.assertEqual(audit['total_orders'],1)
            self.assertEqual(audit['unknown_category_items'],1)
            self.assertEqual(audit['payment_allocation_delta'],0)

    def test_duplicate_item_key_blocks_export(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);db=self.fixture(root)
            with closing(sqlite3.connect(db)) as c,c:
                c.execute("INSERT INTO order_items VALUES ('a',1,'p',1,0)")
            with self.assertRaisesRegex(ValueError,'Blocking quality'):
                project.export(db,root/'dashboard')

if __name__=='__main__':unittest.main()
