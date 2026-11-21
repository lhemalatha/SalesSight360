
import pandas as pd
import mysql.connector
from pathlib import Path

csv_file = Path(
    r"C:\Users\S LAKSHMI NARAYANAN\Desktop\SalesSight360\01_Data\02_Cleaned\Olist_Ecommerce\olist_products_dataset.csv"
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

columns = [
    "product_id",
    "product_category_name",
    "product_name_lenght",
    "product_description_lenght",
    "product_photos_qty",
    "product_weight_g",
    "product_length_cm",
    "product_height_cm",
    "product_width_cm"
]

sql = """
INSERT INTO olist_products (
    product_id,
    product_category_name,
    product_name_lenght,
    product_description_lenght,
    product_photos_qty,
    product_weight_g,
    product_length_cm,
    product_height_cm,
    product_width_cm
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

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

    print("\nPRODUCTS IMPORT COMPLETED!")

except Exception as e:
    conn.rollback()
    print("Import failed:", e)

finally:
    cursor.close()
    conn.close()
