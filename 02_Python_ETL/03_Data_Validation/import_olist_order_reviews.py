
import pandas as pd
import mysql.connector
from getpass import getpass

file_path = (
    r"01_Data\02_Cleaned\Olist_Ecommerce"
    r"\olist_order_reviews_dataset.csv"
)

print("Reading Olist review data...")

df = pd.read_csv(
    file_path,
    dtype=str,
    keep_default_na=False
)

columns = [
    "review_id",
    "order_id",
    "review_score",
    "review_comment_title",
    "review_comment_message",
    "review_creation_date",
    "review_answer_timestamp"
]

df = df[columns]
df = df.where(df != "", None)

records = list(df.itertuples(index=False, name=None))

print("Total records:", len(records))

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

    query = """
        INSERT INTO olist_order_reviews (
            review_id,
            order_id,
            review_score,
            review_comment_title,
            review_comment_message,
            review_creation_date,
            review_answer_timestamp
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    batch_size = 2000

    for start in range(0, len(records), batch_size):
        batch = records[start:start + batch_size]

        cursor.executemany(query, batch)
        conn.commit()

        print(
            f"Imported: {min(start + batch_size, len(records))}"
            f"/{len(records)}"
        )

    print("\nORDER REVIEWS IMPORT COMPLETED!")

except Exception as e:
    if conn:
        conn.rollback()
    print("\nIMPORT FAILED:", e)

finally:
    if cursor:
        cursor.close()
    if conn and conn.is_connected():
        conn.close()
