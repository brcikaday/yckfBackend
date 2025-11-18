from sqlalchemy import create_engine, inspect
import pandas as pd
import os

basedir = os.path.abspath(os.path.dirname(__file__))


# Connect to the SQLite database
sqlite_engine = create_engine(f"sqlite:///{os.path.join(basedir, 'app.db')}")

# Connect to the PostgreSQL database
pg_engine = create_engine(os.environ.get('DATABASE_URL'))

# Read data from SQLite
inspector = inspect(sqlite_engine)
tables = inspector.get_table_names()

for table in tables:
    df = pd.read_sql_table(table, sqlite_engine)
    df.to_sql(table, pg_engine, if_exists='replace', index=False)
    print(f"Migrated table: {table}")