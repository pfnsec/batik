import pandas as pd
import sqlite3 as sql


class SQLiteAdapter:
    def __init__(self, table=None, db=None):
        self.db = db
        self.table = table
        print(f"Using table {table} from {db}")

    def data_in(self, x):
        print(x)
        x.to_sql(self.table, self.db, if_exists='append')

    def data_dump(self, page):
        x = pd.read_sql_table(self.table, self.db)
        print("dump: ")
        print(x)
        return x