
from pathlib import Path
import pandas as pd

# --------------------------------------------------
# SALESSIGHT 360
# Phase 1 - Data Dictionary Generation
# --------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]

CLEANED_DIR = ROOT / "01_Data" / "02_Cleaned"
DICTIONARY_DIR = ROOT / "01_Data" / "04_Data_Dictionary"

DICTIONARY_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = DICTIONARY_DIR / "salesight_data_dictionary.csv"

SOURCE_DESCRIPTIONS = {
    "Olist_Ecommerce": "Public Brazilian e-commerce transaction dataset. Currency: BRL.",
    "Olist_Marketing_Funnel": "Public Brazilian marketing qualified leads and closed deals dataset.",
    "Online_Retail_II": "Public UK online retail transaction dataset. Currency: GBP.",
}


def main():

    print("\nSALESSIGHT 360 - DATA DICTIONARY")
    print("-" * 55)

    dictionary_rows = []

    for source_folder in CLEANED_DIR.iterdir():

        if not source_folder.is_dir():
            continue

        source_name = source_folder.name
        source_description = SOURCE_DESCRIPTIONS.get(
            source_name,
            "Cleaned dataset"
        )

        for file_path in source_folder.glob("*.csv"):

            print(f"Inspecting: {file_path.name}")

            df = pd.read_csv(
                file_path,
                low_memory=False
            )

            for column in df.columns:

                series = df[column]

                non_null_values = series.dropna()

                sample_values = (
                    non_null_values.astype(str)
                    .drop_duplicates()
                    .head(3)
                    .tolist()
                )

                dictionary_rows.append({
                    "source_dataset": source_name,
                    "source_description": source_description,
                    "file_name": file_path.name,
                    "column_name": column,
                    "data_type": str(series.dtype),
                    "total_rows": len(df),
                    "non_null_count": int(series.notna().sum()),
                    "missing_count": int(series.isna().sum()),
                    "missing_percentage": round(
                        series.isna().mean() * 100, 2
                    ),
                    "sample_values": " | ".join(sample_values),
                })

    dictionary_df = pd.DataFrame(dictionary_rows)

    dictionary_df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print("\n" + "-" * 55)
    print("DATA DICTIONARY GENERATED SUCCESSFULLY")
    print(f"Total columns documented: {len(dictionary_df):,}")
    print(f"Output file: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
