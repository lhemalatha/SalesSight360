
import pandas as pd
import mysql.connector
from pathlib import Path

csv_file = Path(
    r"C:\Users\S LAKSHMI NARAYANAN\Desktop\SalesSight360\01_Data\02_Cleaned\Olist_Ecommerce\olist_sellers_dataset.csv"
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
INSERT INTO olist_sellers (
    seller_id,
    seller_zip_code_prefix,
    seller_city,
    seller_state
)
VALUES (%s, %s, %s, %s)
"""

columns = [
    "seller_id",
    "seller_zip_code_prefix",
    "seller_city",
    "seller_state"
]

batch_size = 1000
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

    print("\nSELLERS IMPORT COMPLETED!")

except Exception as e:
    conn.rollback()
    print("Import failed:", e)

finally:
    cursor.close()
    conn.close()
