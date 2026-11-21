
from pathlib import Path
import pandas as pd

# --------------------------------------------------
# SALESSIGHT 360
# Phase 1 - Olist E-commerce Data Cleaning
# --------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = ROOT / "01_Data" / "01_Raw" / "Olist_Ecommerce"
OUTPUT_DIR = ROOT / "01_Data" / "02_Cleaned" / "Olist_Ecommerce"
VALIDATION_DIR = ROOT / "02_Python_ETL" / "03_Data_Validation"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
VALIDATION_DIR.mkdir(parents=True, exist_ok=True)

FILES = [
    "olist_customers_dataset.csv",
    "olist_geolocation_dataset.csv",
    "olist_orders_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_order_reviews_dataset.csv",
    "olist_products_dataset.csv",
    "olist_sellers_dataset.csv",
    "product_category_name_translation.csv",
]

DATE_COLUMNS = {
    "olist_orders_dataset.csv": [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
    "olist_order_items_dataset.csv": [
        "shipping_limit_date",
    ],
    "olist_order_reviews_dataset.csv": [
        "review_creation_date",
        "review_answer_timestamp",
    ],
}

NUMERIC_COLUMNS = {
    "olist_order_items_dataset.csv": [
        "order_item_id", "price", "freight_value"
    ],
    "olist_order_payments_dataset.csv": [
        "payment_sequential", "payment_installments", "payment_value"
    ],
    "olist_order_reviews_dataset.csv": [
        "review_score"
    ],
    "olist_products_dataset.csv": [
        "product_name_lenght",
        "product_description_lenght",
        "product_photos_qty",
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm",
    ],
}


def clean_text_columns(df):
    """Trim whitespace and convert empty strings to missing values."""
    for column in df.select_dtypes(include="object").columns:
        df[column] = df[column].str.strip()
        df[column] = df[column].replace("", pd.NA)
    return df


def main():
    print("\nSALESSIGHT 360 - OLIST DATA CLEANING")
    print("-" * 50)

    validation_rows = []

    # Load and clean each source file without changing raw files.
    for filename in FILES:
        source_path = RAW_DIR / filename

        if not source_path.exists():
            raise FileNotFoundError(
                f"Required source file not found: {source_path}"
            )

        df = pd.read_csv(source_path, low_memory=False)
        original_rows = len(df)

        df = clean_text_columns(df)

        for column in DATE_COLUMNS.get(filename, []):
            if column in df.columns:
                df[column] = pd.to_datetime(
                    df[column], errors="coerce"
                )

        for column in NUMERIC_COLUMNS.get(filename, []):
            if column in df.columns:
                df[column] = pd.to_numeric(
                    df[column], errors="coerce"
                )

        exact_duplicate_rows = int(df.duplicated().sum())

        # Keep all records. Duplicate rows are reported, not deleted.
        output_path = OUTPUT_DIR / filename
        df.to_csv(output_path, index=False, encoding="utf-8-sig")

        validation_rows.append({
            "file_name": filename,
            "original_rows": original_rows,
            "cleaned_rows": len(df),
            "exact_duplicate_rows_retained": exact_duplicate_rows,
            "missing_cells_after_cleaning": int(df.isna().sum().sum()),
            "status": "SUCCESS",
        })

        print(
            f"Cleaned: {filename} | "
            f"Rows: {len(df):,} | "
            f"Duplicates retained: {exact_duplicate_rows:,}"
        )

    # --------------------------------------------------
    # ORDER-LEVEL PAYMENT RECONCILIATION
    # --------------------------------------------------

    orders = pd.read_csv(
        OUTPUT_DIR / "olist_orders_dataset.csv",
        low_memory=False
    )

    items = pd.read_csv(
        OUTPUT_DIR / "olist_order_items_dataset.csv",
        low_memory=False
    )

    payments = pd.read_csv(
        OUTPUT_DIR / "olist_order_payments_dataset.csv",
        low_memory=False
    )

    item_totals = (
        items.groupby("order_id", as_index=False)
        .agg(
            item_value=("price", "sum"),
            freight_value=("freight_value", "sum"),
        )
    )

    payment_totals = (
        payments.groupby("order_id", as_index=False)
        .agg(payment_value=("payment_value", "sum"))
    )

    reconciliation = orders[
        ["order_id", "order_status"]
    ].merge(
        item_totals,
        on="order_id",
        how="outer",
        indicator="item_match"
    )

    reconciliation = reconciliation.merge(
        payment_totals,
        on="order_id",
        how="outer",
        indicator="payment_match"
    )

    reconciliation["difference"] = (
        reconciliation["payment_value"]
        - reconciliation["item_value"]
        - reconciliation["freight_value"]
    )

    reconciliation["reconciliation_status"] = "MATCHED"

    reconciliation.loc[
        reconciliation["item_match"] == "left_only",
        "reconciliation_status"
    ] = "NO_ITEM_RECORD"

    reconciliation.loc[
        reconciliation["payment_match"] == "left_only",
        "reconciliation_status"
    ] = "NO_PAYMENT_RECORD"

    reconciliation.loc[
        reconciliation["item_match"] == "right_only",
        "reconciliation_status"
    ] = "ITEM_WITHOUT_ORDER"

    reconciliation.loc[
        reconciliation["payment_match"] == "right_only",
        "reconciliation_status"
    ] = "PAYMENT_WITHOUT_ORDER"

    # --------------------------------------------------
    # APPLY 0.01 BRL ROUNDING TOLERANCE
    # --------------------------------------------------

    rounded_difference = reconciliation["difference"].round(2)

    rounding_tolerance = (
        reconciliation["reconciliation_status"].eq("MATCHED")
        & rounded_difference.abs().eq(0.01)
    )

    amount_mismatch = (
        reconciliation["reconciliation_status"].eq("MATCHED")
        & rounded_difference.abs().gt(0.01)
    )

    reconciliation.loc[
        rounding_tolerance,
        "reconciliation_status"
    ] = "ROUNDING_TOLERANCE"

    reconciliation.loc[
        amount_mismatch,
        "reconciliation_status"
    ] = "AMOUNT_MISMATCH"

    reconciliation["currency"] = "BRL"

    reconciliation.to_csv(
        OUTPUT_DIR / "order_payment_reconciliation.csv",
        index=False,
        encoding="utf-8-sig"
    )

    # --------------------------------------------------
    # SAVE VALIDATION SUMMARY
    # --------------------------------------------------

    validation_df = pd.DataFrame(validation_rows)

    validation_df.to_csv(
        VALIDATION_DIR / "olist_cleaning_summary.csv",
        index=False,
        encoding="utf-8-sig"
    )

    print("\n" + "-" * 50)
    print("OLIST CLEANING COMPLETED")
    print(f"Source files processed: {len(FILES)}")
    print(f"Cleaned files saved in: {OUTPUT_DIR}")
    print(
        "Reconciliation report saved: "
        "order_payment_reconciliation.csv"
    )
    print(
        "Validation summary saved: "
        "olist_cleaning_summary.csv"
    )

    print("\nRECONCILIATION STATUS:")
    print(
        reconciliation["reconciliation_status"]
        .value_counts(dropna=False)
        .to_string()
    )


if __name__ == "__main__":
    main()

