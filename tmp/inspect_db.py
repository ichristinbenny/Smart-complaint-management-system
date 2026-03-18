import sqlite3
import pandas as pd

def inspect_db(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    key_tables = ['accounts_user', 'complaints_complaint', 'complaints_department']
    
    for table in key_tables:
        print(f"\n{'='*20} {table} {'='*20}")
        # Schema
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        print("\nSchema:")
        print(pd.DataFrame(columns, columns=['id', 'name', 'type', 'notnull', 'default_value', 'pk']).to_string(index=False))
        
        # Sample Data
        print("\nSample Data (Last 5 records):")
        try:
            df = pd.read_sql_query(f"SELECT * FROM {table} ORDER BY id DESC LIMIT 5", conn)
            print(df.to_string(index=False))
        except Exception as e:
            print(f"Error reading {table}: {e}")
                
    conn.close()

if __name__ == "__main__":
    inspect_db("db.sqlite3")
