import pandas as pd
import mysql.connector
from getpass import getpass

file_path = r"01_Data\02_Cleaned\Olist_Marketing_Funnel\olist_marketing_qualified_leads_dataset.csv"

print("Reading Marketing Qualified Leads...")
df = pd.read_csv(file_path, dtype=str)
df = df.where(pd.notna(df), None)

print("Total records:", len(df))

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

    cursor.execute("SELECT COUNT(*) FROM marketing_qualified_leads")
    existing = cursor.fetchone()[0]

    if existing > 0:
        raise Exception(
            f"Table already contains {existing} records. Import stopped."
        )

    sql = """
        INSERT INTO marketing_qualified_leads
        (
            mql_id,
            first_contact_date,
            landing_page_id,
            origin
        )
        VALUES (%s, %s, %s, %s)
    """

    records = list(
        df[
            [
                "mql_id",
                "first_contact_date",
                "landing_page_id",
                "origin"
            ]
        ].itertuples(index=False, name=None)
    )

    batch_size = 2000
    imported = 0

    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        cursor.executemany(sql, batch)
        conn.commit()

        imported += len(batch)
        print(f"Imported: {imported}/{len(records)}")

    print("\nMARKETING QUALIFIED LEADS IMPORT COMPLETED!")
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
