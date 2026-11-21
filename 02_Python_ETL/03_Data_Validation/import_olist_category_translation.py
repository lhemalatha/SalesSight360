import pandas as pd
import mysql.connector
from getpass import getpass

file_path = r"01_Data\02_Cleaned\Olist_Ecommerce\product_category_name_translation.csv"

print("Reading category translation data...")
df = pd.read_csv(file_path, dtype=str)
df = df.fillna("")

print("Total records:", len(df))

password = getpass("Enter your MySQL password: ")

try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password=password,
        database="salessight360"
    )

    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM olist_category_translation")
    existing = cursor.fetchone()[0]

    if existing > 0:
        raise Exception(
            f"Table already contains {existing} records. Import stopped."
        )

    sql = """
        INSERT INTO olist_category_translation
        (product_category_name, product_category_name_english)
        VALUES (%s, %s)
    """

    records = list(
        df[[
            "product_category_name",
            "product_category_name_english"
        ]].itertuples(index=False, name=None)
    )

    cursor.executemany(sql, records)
    conn.commit()

    print("Imported records:", cursor.rowcount)
    print("CATEGORY TRANSLATION IMPORT COMPLETED!")

except Exception as e:
    print("IMPORT FAILED:", e)
    if "conn" in locals() and conn.is_connected():
        conn.rollback()

finally:
    if "cursor" in locals():
        cursor.close()
    if "conn" in locals() and conn.is_connected():
        conn.close()
