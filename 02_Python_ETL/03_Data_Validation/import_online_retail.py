import pandas as pd
import mysql.connector
from getpass import getpass

files = [
    r"01_Data\02_Cleaned\Online_Retail_II\online_retail_2009_2010_cleaned.csv",
    r"01_Data\02_Cleaned\Online_Retail_II\online_retail_2010_2011_cleaned.csv"
]

columns = [
    "Invoice",
    "StockCode",
    "Description",
    "Quantity",
    "InvoiceDate",
    "Price",
    "Customer_ID",
    "Country",
    "is_return",
    "is_cancellation_invoice",
    "line_value_gbp",
    "source_period"
]

batch_size = 5000

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

    cursor.execute("SELECT COUNT(*) FROM online_retail_transactions")
    existing = cursor.fetchone()[0]

    if existing > 0:
        raise Exception(
            f"Table already contains {existing} records. Import stopped."
        )

    sql = """
        INSERT INTO online_retail_transactions (
            Invoice,
            StockCode,
            Description,
            Quantity,
            InvoiceDate,
            Price,
            Customer_ID,
            Country,
            is_return,
            is_cancellation_invoice,
            line_value_gbp,
            source_period
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    total_imported = 0

    for file in files:
        print("\nProcessing:", file.split("\\")[-1])

        file_imported = 0

        for chunk in pd.read_csv(
            file,
            dtype=str,
            chunksize=batch_size
        ):
            missing = set(columns) - set(chunk.columns)

            if missing:
                raise Exception(f"Missing CSV columns: {missing}")

            chunk = chunk[columns]
            chunk = chunk.astype(object).where(pd.notna(chunk), None)

            records = list(
                chunk.itertuples(index=False, name=None)
            )

            cursor.executemany(sql, records)
            conn.commit()

            file_imported += len(records)
            total_imported += len(records)

            print(
                f"File imported: {file_imported} | "
                f"Overall imported: {total_imported}"
            )

        print("File completed:", file_imported)

    print("\nONLINE RETAIL II IMPORT COMPLETED!")
    print("Total imported:", total_imported)

except Exception as e:
    print("\nIMPORT FAILED:", e)
    print("Previously committed batches may remain in the table.")

    if conn and conn.is_connected():
        conn.rollback()

finally:
    if cursor:
        cursor.close()

    if conn and conn.is_connected():
        conn.close()
