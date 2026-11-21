
import pandas as pd
import mysql.connector
from pathlib import Path

csv_file = Path(
    r"C:\Users\S LAKSHMI NARAYANAN\Desktop\SalesSight360\01_Data\02_Cleaned\Olist_Ecommerce\olist_orders_dataset.csv"
)

df = pd.read_csv(csv_file, dtype=str).fillna("")

print("Total CSV records:", len(df))

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password=input("Enter MySQL root password: "),
    database="salessight360"
)

cursor = conn.cursor()

sql = """
INSERT INTO olist_orders (
    order_id,
    customer_id,
    order_status,
    order_purchase_timestamp,
    order_approved_at,
    order_delivered_carrier_date,
    order_delivered_customer_date,
    order_estimated_delivery_date
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
"""

columns = [
    "order_id",
    "customer_id",
    "order_status",
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date"
]

batch_size = 2000
inserted = 0

try:
    for start in range(0, len(df), batch_size):
        batch = df.iloc[start:start + batch_size]
        values = [
            tuple(None if value == "" else value for value in row)
            for row in batch[columns].values
        ]

        cursor.executemany(sql, values)
        conn.commit()

        inserted += len(values)
        print(f"Imported: {inserted}/{len(df)}")

    print("\nORDERS IMPORT COMPLETED!")

except Exception as e:
    conn.rollback()
    print("Import failed:", e)

finally:
    cursor.close()
    conn.close()
