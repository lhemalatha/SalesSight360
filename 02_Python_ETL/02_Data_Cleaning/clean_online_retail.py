
from pathlib import Path
import pandas as pd

# --------------------------------------------------
# SALESSIGHT 360
# Phase 1 - Online Retail II Data Cleaning
# --------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = ROOT / "01_Data" / "01_Raw" / "Online_Retail_II"
OUTPUT_DIR = ROOT / "01_Data" / "02_Cleaned" / "Online_Retail_II"
VALIDATION_DIR = ROOT / "02_Python_ETL" / "03_Data_Validation"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
VALIDATION_DIR.mkdir(parents=True, exist_ok=True)

SOURCE_FILE = RAW_DIR / "online_retail_II.xlsx"

SHEETS = [
    "Year 2009-2010",
    "Year 2010-2011",
]


def clean_text_columns(df):
    """Safely trim text columns and preserve missing values."""
    for column in df.select_dtypes(
        include=["object", "string"]
    ).columns:
        df[column] = (
            df[column]
            .astype("string")
            .str.strip()
            .replace("", pd.NA)
        )

    return df


def main():

    print("\nSALESSIGHT 360 - ONLINE RETAIL II CLEANING")
    print("-" * 55)

    if not SOURCE_FILE.exists():
        raise FileNotFoundError(
            f"Excel source file not found: {SOURCE_FILE}"
        )

    validation_rows = []

    # --------------------------------------------------
    # PROCESS BOTH EXCEL SHEETS SEPARATELY
    # --------------------------------------------------

    for sheet_name in SHEETS:

        print(f"\nProcessing: {sheet_name}")

        df = pd.read_excel(
            SOURCE_FILE,
            sheet_name=sheet_name
        )

        original_rows = len(df)

        df = clean_text_columns(df)

        # Standardize column names.
        df.columns = [
            str(column).strip().replace(" ", "_")
            for column in df.columns
        ]

        # Convert date column.
        df["InvoiceDate"] = pd.to_datetime(
            df["InvoiceDate"],
            errors="coerce"
        )

        # Convert numeric columns.
        for column in ["Quantity", "Price", "Customer_ID"]:
            if column in df.columns:
                df[column] = pd.to_numeric(
                    df[column],
                    errors="coerce"
                )

        # Identify returns and cancellation invoices.
        df["is_return"] = df["Quantity"].lt(0)

        df["is_cancellation_invoice"] = (
            df["Invoice"]
            .astype("string")
            .str.upper()
            .str.startswith("C", na=False)
        )

        # Calculate line value without removing negative quantities.
        df["line_value_gbp"] = (
            df["Quantity"] * df["Price"]
        )

        # Record source period.
        df["source_period"] = sheet_name

        duplicate_rows = int(df.duplicated().sum())

        # Preserve every record.
        output_name = (
            "online_retail_2009_2010_cleaned.csv"
            if sheet_name == "Year 2009-2010"
            else "online_retail_2010_2011_cleaned.csv"
        )

        df.to_csv(
            OUTPUT_DIR / output_name,
            index=False,
            encoding="utf-8-sig"
        )

        validation_rows.append({
            "source_sheet": sheet_name,
            "original_rows": original_rows,
            "cleaned_rows": len(df),
            "exact_duplicate_rows_retained": duplicate_rows,
            "missing_customer_ids": int(
                df["Customer_ID"].isna().sum()
            ),
            "negative_quantity_rows": int(
                df["is_return"].sum()
            ),
            "cancellation_invoice_rows": int(
                df["is_cancellation_invoice"].sum()
            ),
            "invalid_invoice_dates": int(
                df["InvoiceDate"].isna().sum()
            ),
            "zero_or_negative_price_rows": int(
                df["Price"].le(0).sum()
            ),
            "status": "SUCCESS",
        })

        print(f"Original rows: {original_rows:,}")
        print(f"Cleaned rows: {len(df):,}")
        print(f"Duplicate rows retained: {duplicate_rows:,}")
        print(
            "Missing customer IDs: "
            f"{df['Customer_ID'].isna().sum():,}"
        )
        print(
            f"Return rows: {df['is_return'].sum():,}"
        )
        print(
            "Cancellation invoice rows: "
            f"{df['is_cancellation_invoice'].sum():,}"
        )

    # --------------------------------------------------
    # SAVE VALIDATION SUMMARY
    # --------------------------------------------------

    validation_df = pd.DataFrame(validation_rows)

    validation_df.to_csv(
        VALIDATION_DIR / "online_retail_cleaning_summary.csv",
        index=False,
        encoding="utf-8-sig"
    )

    print("\n" + "-" * 55)
    print("ONLINE RETAIL II CLEANING COMPLETED")
    print(f"Cleaned files saved in: {OUTPUT_DIR}")
    print(
        "Validation report saved: "
        "online_retail_cleaning_summary.csv"
    )

    print("\nFINAL VALIDATION SUMMARY:")
    print(validation_df.to_string(index=False))


if __name__ == "__main__":
    main()
