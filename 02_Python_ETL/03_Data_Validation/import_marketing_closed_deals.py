import pandas as pd
import mysql.connector
from getpass import getpass

file_path = r"01_Data\02_Cleaned\Olist_Marketing_Funnel\olist_closed_deals_dataset.csv"

print("Reading Marketing Closed Deals...")
df = pd.read_csv(file_path, dtype=str)
df = df.astype(object).where(pd.notna(df), None)

print("Total records:", len(df))

columns = [
    "mql_id",
    "seller_id",
    "sdr_id",
    "sr_id",
    "won_date",
    "business_segment",
    "lead_type",
    "lead_behaviour_profile",
    "has_company",
    "has_gtin",
    "average_stock",
    "business_type",
    "declared_product_catalog_size",
    "declared_monthly_revenue"
]

records = list(df[columns].itertuples(index=False, name=None))

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

    cursor.execute("SELECT COUNT(*) FROM marketing_closed_deals")
    existing = cursor.fetchone()[0]

    if existing > 0:
        raise Exception(
            f"Table already contains {existing} records. Import stopped."
        )

    sql = """
        INSERT INTO marketing_closed_deals (
            mql_id, seller_id, sdr_id, sr_id, won_date,
            business_segment, lead_type, lead_behaviour_profile,
            has_company, has_gtin, average_stock, business_type,
            declared_product_catalog_size, declared_monthly_revenue
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s
        )
    """

    batch_size = 500
    imported = 0

    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        cursor.executemany(sql, batch)
        conn.commit()

        imported += len(batch)
        print(f"Imported: {imported}/{len(records)}")

    print("\nMARKETING CLOSED DEALS IMPORT COMPLETED!")
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
