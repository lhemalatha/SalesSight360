
import pandas as pd
import mysql.connector
from pathlib import Path

# CSV file
csv_file = Path(
    r"C:\Users\S LAKSHMI NARAYANAN\Desktop\SalesSight360\01_Data\02_Cleaned\Olist_Ecommerce\olist_customers_dataset.csv"
)

# Read CSV
df = pd.read_csv(csv_file, dtype=str).fillna("")
df = df.where(pd.notna(df), "")

print("Total CSV records:", len(df))

# MySQL connection
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password=input("Enter MySQL root password: "),
    database="salessight360"
)

cursor = conn.cursor()

sql = """
INSERT INTO olist_customers
(customer_id, customer_unique_id, customer_zip_code_prefix,
 customer_city, customer_state)
VALUES (%s, %s, %s, %s, %s)
"""

batch_size = 2000
inserted = 0

try:
    for start in range(0, len(df), batch_size):
        batch = df.iloc[start:start + batch_size]

        values = [
            tuple(row)
            for row in batch[
                [
                    "customer_id",
                    "customer_unique_id",
                    "customer_zip_code_prefix",
                    "customer_city",
                    "customer_state"
                ]
            ].values
        ]

        cursor.executemany(sql, values)
        conn.commit()

        inserted += len(values)
        print(f"Imported: {inserted}/{len(df)}")

    print("\nCUSTOMER IMPORT COMPLETED!")

except Exception as e:
    conn.rollback()
    print("Import failed:", e)

finally:
    cursor.close()
    conn.close()
