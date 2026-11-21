import pandas as pd
import mysql.connector
from getpass import getpass

file_path = r"01_Data\02_Cleaned\Olist_Ecommerce\olist_geolocation_dataset.csv"

print("Reading Olist geolocation data...")
print("Expected records: 1000163")

password = getpass("Enter your MySQL password: ")

conn = None
cursor = None

try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password=password,
        database="salessight360"
    )

    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM olist_geolocation")
    existing = cursor.fetchone()[0]

    if existing > 0:
        raise Exception(
            f"Table already contains {existing} records. Import stopped."
        )

    sql = """
        INSERT INTO olist_geolocation
        (
            geolocation_zip_code_prefix,
            geolocation_lat,
            geolocation_lng,
            geolocation_city,
            geolocation_state
        )
        VALUES (%s, %s, %s, %s, %s)
    """

    imported = 0
    batch_size = 10000

    for chunk in pd.read_csv(
        file_path,
        dtype=str,
        chunksize=batch_size
    ):
        chunk = chunk.where(pd.notna(chunk), None)

        records = list(
            chunk[
                [
                    "geolocation_zip_code_prefix",
                    "geolocation_lat",
                    "geolocation_lng",
                    "geolocation_city",
                    "geolocation_state"
                ]
            ].itertuples(index=False, name=None)
        )

        cursor.executemany(sql, records)
        conn.commit()

        imported += len(records)
        print(f"Imported: {imported}/1000163")

    print("\nGEOLOCATION IMPORT COMPLETED!")
    print("Total imported:", imported)

except Exception as e:
    print("\nIMPORT FAILED:", e)

    if conn and conn.is_connected():
        conn.rollback()

finally:
    if cursor:
        cursor.close()

    if conn and conn.is_connected():
        conn.close()
