
from pathlib import Path
import pandas as pd

# --------------------------------------------------
# SALESSIGHT 360
# Phase 1 - Olist Marketing Funnel Data Cleaning
# --------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = ROOT / "01_Data" / "01_Raw" / "Olist_Marketing_Funnel"
OUTPUT_DIR = ROOT / "01_Data" / "02_Cleaned" / "Olist_Marketing_Funnel"
VALIDATION_DIR = ROOT / "02_Python_ETL" / "03_Data_Validation"

ECOMMERCE_CLEAN_DIR = (
    ROOT / "01_Data" / "02_Cleaned" / "Olist_Ecommerce"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
VALIDATION_DIR.mkdir(parents=True, exist_ok=True)

FILES = [
    "olist_marketing_qualified_leads_dataset.csv",
    "olist_closed_deals_dataset.csv",
]

DATE_COLUMNS = {
    "olist_marketing_qualified_leads_dataset.csv": [
        "first_contact_date",
    ],
    "olist_closed_deals_dataset.csv": [
        "won_date",
    ],
}

NUMERIC_COLUMNS = {
    "olist_closed_deals_dataset.csv": [
        "average_stock",
        "declared_product_catalog_size",
        "declared_monthly_revenue",
    ],
}



def clean_text_columns(df):
    """Safely trim text columns and preserve missing values."""
    for column in df.select_dtypes(include=["object", "string"]).columns:
        df[column] = (
            df[column]
            .astype("string")
            .str.strip()
            .replace("", pd.NA)
        )

    return df



def main():

    print("\nSALESSIGHT 360 - MARKETING FUNNEL CLEANING")
    print("-" * 55)

    validation_rows = []
    cleaned_data = {}

    # --------------------------------------------------
    # LOAD AND CLEAN BOTH DATASETS
    # --------------------------------------------------

    for filename in FILES:

        source_path = RAW_DIR / filename

        if not source_path.exists():
            raise FileNotFoundError(
                f"Required source file not found: {source_path}"
            )

        df = pd.read_csv(source_path, low_memory=False)

        original_rows = len(df)

        df = clean_text_columns(df)

        # Convert date columns.
        for column in DATE_COLUMNS.get(filename, []):
            if column in df.columns:
                df[column] = pd.to_datetime(
                    df[column],
                    errors="coerce"
                )

        # Convert numeric columns.
        for column in NUMERIC_COLUMNS.get(filename, []):
            if column in df.columns:
                df[column] = pd.to_numeric(
                    df[column],
                    errors="coerce"
                )

        duplicate_rows = int(df.duplicated().sum())

        # Preserve all records.
        output_path = OUTPUT_DIR / filename

        df.to_csv(
            output_path,
            index=False,
            encoding="utf-8-sig"
        )

        cleaned_data[filename] = df

        validation_rows.append({
            "file_name": filename,
            "original_rows": original_rows,
            "cleaned_rows": len(df),
            "exact_duplicate_rows_retained": duplicate_rows,
            "missing_cells_after_cleaning": int(
                df.isna().sum().sum()
            ),
            "status": "SUCCESS",
        })

        print(
            f"Cleaned: {filename} | "
            f"Rows: {len(df):,} | "
            f"Duplicates retained: {duplicate_rows:,}"
        )

    # --------------------------------------------------
    # MQL ID RELATIONSHIP VALIDATION
    # --------------------------------------------------

    leads = cleaned_data[
        "olist_marketing_qualified_leads_dataset.csv"
    ]

    deals = cleaned_data[
        "olist_closed_deals_dataset.csv"
    ]

    lead_ids = set(leads["mql_id"].dropna())

    missing_deal_mql_ids = int(deals["mql_id"].isna().sum())

    unmatched_deals = deals[
        deals["mql_id"].notna()
        & ~deals["mql_id"].isin(lead_ids)
    ].copy()

    matched_deals = deals[
        deals["mql_id"].notna()
        & deals["mql_id"].isin(lead_ids)
    ]

    mql_validation = pd.DataFrame([
        {
            "validation": "Closed deals to marketing leads",
            "total_closed_deals": len(deals),
            "matched_records": len(matched_deals),
            "unmatched_records": len(unmatched_deals),
            "missing_mql_id_records": missing_deal_mql_ids,
            "status": (
                "PASS"
                if len(unmatched_deals) == 0
                else "REVIEW"
            ),
        }
    ])

    mql_validation.to_csv(
        VALIDATION_DIR / "marketing_funnel_mql_validation.csv",
        index=False,
        encoding="utf-8-sig"
    )

    unmatched_deals.to_csv(
        VALIDATION_DIR / "unmatched_marketing_deals.csv",
        index=False,
        encoding="utf-8-sig"
    )

    # --------------------------------------------------
    # SELLER ID CROSS-DATASET VALIDATION
    # --------------------------------------------------

    sellers_path = (
        ECOMMERCE_CLEAN_DIR / "olist_sellers_dataset.csv"
    )

    if not sellers_path.exists():
        raise FileNotFoundError(
            f"Cleaned ecommerce sellers file not found: {sellers_path}"
        )

    sellers = pd.read_csv(
        sellers_path,
        dtype={"seller_id": "string"},
        low_memory=False
    )

    ecommerce_seller_ids = set(
        sellers["seller_id"].dropna()
    )

    deals["seller_id"] = deals["seller_id"].astype("string")

    unmatched_sellers = deals[
        deals["seller_id"].notna()
        & ~deals["seller_id"].isin(ecommerce_seller_ids)
    ].copy()

    matched_sellers = deals[
        deals["seller_id"].notna()
        & deals["seller_id"].isin(ecommerce_seller_ids)
    ]

    seller_validation = pd.DataFrame([
        {
            "validation": "Marketing funnel sellers to ecommerce sellers",
            "total_closed_deals": len(deals),
            "matched_seller_records": len(matched_sellers),
            "unmatched_seller_records": len(unmatched_sellers),
            "missing_seller_id_records": int(
                deals["seller_id"].isna().sum()
            ),
            "status": (
                "PASS"
                if len(unmatched_sellers) == 0
                else "REVIEW - DIFFERENT SOURCE DATASETS"
            ),
        }
    ])

    seller_validation.to_csv(
        VALIDATION_DIR / "marketing_funnel_seller_validation.csv",
        index=False,
        encoding="utf-8-sig"
    )

    unmatched_sellers.to_csv(
        VALIDATION_DIR / "unmatched_funnel_seller_ids.csv",
        index=False,
        encoding="utf-8-sig"
    )

    # --------------------------------------------------
    # SAVE CLEANING SUMMARY
    # --------------------------------------------------

    validation_df = pd.DataFrame(validation_rows)

    validation_df.to_csv(
        VALIDATION_DIR / "marketing_funnel_cleaning_summary.csv",
        index=False,
        encoding="utf-8-sig"
    )

    # --------------------------------------------------
    # FINAL OUTPUT
    # --------------------------------------------------

    print("\n" + "-" * 55)
    print("MARKETING FUNNEL CLEANING COMPLETED")

    print(f"Source files processed: {len(FILES)}")
    print(f"Cleaned files saved in: {OUTPUT_DIR}")

    print("\nMQL RELATIONSHIP VALIDATION:")
    print(mql_validation.to_string(index=False))

    print("\nSELLER CROSS-DATASET VALIDATION:")
    print(seller_validation.to_string(index=False))

    print("\nVALIDATION REPORTS SAVED:")
    print("- marketing_funnel_cleaning_summary.csv")
    print("- marketing_funnel_mql_validation.csv")
    print("- unmatched_marketing_deals.csv")
    print("- marketing_funnel_seller_validation.csv")
    print("- unmatched_funnel_seller_ids.csv")


if __name__ == "__main__":
    main()
