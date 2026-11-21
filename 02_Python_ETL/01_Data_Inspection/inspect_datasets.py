
from pathlib import Path
import pandas as pd
import traceback

# ==========================================
# SalesSight 360 - Dataset Inspection
# Phase 1: Data Foundation
# ==========================================

# Locate the main project folder automatically
PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_FOLDER = PROJECT_ROOT / "01_Data" / "01_Raw"
REPORT_FOLDER = (
    PROJECT_ROOT
    / "01_Data"
    / "04_Data_Dictionary"
    / "Inspection_Reports"
)

REPORT_FOLDER.mkdir(parents=True, exist_ok=True)

TEXT_REPORT = REPORT_FOLDER / "dataset_inspection_report.txt"
CSV_REPORT = REPORT_FOLDER / "dataset_inventory.csv"

SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls"}

inventory = []
report_lines = []

def load_csv(file_path):
    """Load CSV using common encodings."""
    encodings = ["utf-8-sig", "utf-8", "cp1252"]

    for encoding in encodings:
        try:
            return pd.read_csv(
                file_path,
                encoding=encoding,
                low_memory=False
            )
        except UnicodeDecodeError:
            continue

    raise ValueError("Unable to read CSV with supported encodings.")


def inspect_dataframe(df, file_path, sheet_name=""):
    """Inspect one dataset or Excel sheet."""

    rows, columns = df.shape
    duplicate_count = int(df.duplicated().sum())
    missing_cells = int(df.isna().sum().sum())

    missing_by_column = df.isna().sum()
    missing_by_column = missing_by_column[missing_by_column > 0]

    report_lines.append("\n" + "=" * 75)
    report_lines.append(f"FILE: {file_path.name}")

    if sheet_name:
        report_lines.append(f"SHEET: {sheet_name}")

    report_lines.append("=" * 75)

    report_lines.append(f"Rows: {rows:,}")
    report_lines.append(f"Columns: {columns}")
    report_lines.append(f"Duplicate rows: {duplicate_count:,}")
    report_lines.append(f"Missing cells: {missing_cells:,}")

    report_lines.append("\nCOLUMN NAMES AND DATA TYPES:")

    for column in df.columns:
        report_lines.append(
            f"{column} : {df[column].dtype}"
        )

    report_lines.append("\nMISSING VALUES:")

    if missing_by_column.empty:
        report_lines.append("No missing values found.")
    else:
        for column, count in missing_by_column.items():
            percentage = (count / rows * 100) if rows else 0

            report_lines.append(
                f"{column}: {count:,} ({percentage:.2f}%)"
            )

    report_lines.append("\nFIRST FIVE ROWS:")
    report_lines.append(df.head().to_string(index=False))

    inventory.append({
        "file_name": file_path.name,
        "file_path": str(file_path.relative_to(PROJECT_ROOT)),
        "sheet_name": sheet_name,
        "rows": rows,
        "columns": columns,
        "duplicate_rows": duplicate_count,
        "missing_cells": missing_cells,
        "status": "SUCCESS"
    })


def main():

    print("\n" + "=" * 60)
    print("SALESSIGHT 360 - DATASET INSPECTION")
    print("=" * 60)

    print(f"\nProject folder: {PROJECT_ROOT}")
    print(f"Raw data folder: {RAW_FOLDER}")

    if not RAW_FOLDER.exists():
        print("\nERROR: Raw data folder does not exist.")
        return

    files = [
        path for path in RAW_FOLDER.rglob("*")
        if path.is_file()
        and path.suffix.lower() in SUPPORTED_EXTENSIONS
        and not path.name.startswith("~$")
    ]

    if not files:
        print("\nNo CSV or Excel files found.")
        print("Please check your dataset folder locations.")
        return

    print(f"\nFound {len(files)} dataset file(s).")

    for file_number, file_path in enumerate(files, start=1):

        print("\n" + "-" * 60)
        print(f"Inspecting {file_number}/{len(files)}: {file_path.name}")

        try:
            if file_path.suffix.lower() == ".csv":

                df = load_csv(file_path)
                inspect_dataframe(df, file_path)

            elif file_path.suffix.lower() in [".xlsx", ".xls"]:

                excel_sheets = pd.read_excel(
                    file_path,
                    sheet_name=None
                )

                for sheet_name, df in excel_sheets.items():
                    inspect_dataframe(
                        df,
                        file_path,
                        sheet_name
                    )

            print("Inspection completed successfully.")

        except Exception as error:

            print(f"Inspection failed: {error}")

            inventory.append({
                "file_name": file_path.name,
                "file_path": str(file_path.relative_to(PROJECT_ROOT)),
                "sheet_name": "",
                "rows": None,
                "columns": None,
                "duplicate_rows": None,
                "missing_cells": None,
                "status": f"ERROR: {error}"
            })

            report_lines.append(
                f"\nERROR inspecting {file_path.name}: {error}"
            )

    # Save inventory as CSV
    inventory_df = pd.DataFrame(inventory)
    inventory_df.to_csv(CSV_REPORT, index=False)

    # Save detailed text report
    with open(TEXT_REPORT, "w", encoding="utf-8") as report:
        report.write(
            "SALESSIGHT 360 - DATASET INSPECTION REPORT\n"
        )
        report.write("\n".join(report_lines))

    print("\n" + "=" * 60)
    print("DATASET INSPECTION FINISHED")
    print("=" * 60)

    print(f"\nInventory saved at:\n{CSV_REPORT}")
    print(f"\nDetailed report saved at:\n{TEXT_REPORT}")

    print("\nINSPECTION SUMMARY:")
    print(inventory_df.to_string(index=False))


if __name__ == "__main__":
    main()
