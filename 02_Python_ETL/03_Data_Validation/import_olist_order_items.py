
import pandas as pd
import mysql.connector
from pathlib import Path

csv_file = Path(
    r"C:\Users\S LAKSHMI NARAYANAN\Desktop\SalesSight360\01_Data\02_Cleaned\Olist_Ecommerce\olist_order_items_dataset.csv"
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
INSERT INTO olist_order_items (
    order_id,
    order_item_id,
    product_id,
    seller_id,
    shipping_limit_date,
    price,
    freight_value
)
VALUES (%s, %s, %s, %s, %s, %s, %s)
"""

columns = [
    "order_id",
    "order_item_id",
    "product_id",
    "seller_id",
    "shipping_limit_date",
    "price",
    "freight_value"
]

batch_size = 2000
inserted = 0

try:
    for start in range(0, len(df), batch_size):
        batch = df.iloc[start:start + batch_size]

        values = [
            (
                row[0],
                int(row[1]),
                None if row[2] == "" else row[2],
                None if row[3] == "" else row[3],
                None if row[4] == "" else row[4],
                None if row[5] == "" else row[5],
                None if row[6] == "" else row[6]
            )
            for row in batch[columns].values
        ]

        cursor.executemany(sql, values)
        conn.commit()

        inserted += len(values)
        print(f"Imported: {inserted}/{len(df)}")

    print("\nORDER ITEMS IMPORT COMPLETED!")

except Exception as e:
    conn.rollback()
    print("Import failed:", e)

finally:
    cursor.close()
    conn.close()
