
from pathlib import Path
import pandas as pd

# ==================================================
# SALESSIGHT 360
# Phase 1 - KPI Calculation and Validation
# ==================================================

ROOT = Path(__file__).resolve().parents[2]

DATA = ROOT / "01_Data" / "02_Cleaned"

OLIST = DATA / "Olist_Ecommerce"
MARKETING = DATA / "Olist_Marketing_Funnel"
RETAIL = DATA / "Online_Retail_II"

OUTPUT_DIR = ROOT / "02_Python_ETL" / "03_Data_Validation"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "kpi_validation_results.csv"

results = []


def add_result(dataset, kpi, value, unit, status, note):
    results.append({
        "dataset": dataset,
        "kpi_name": kpi,
        "calculated_value": value,
        "unit": unit,
        "validation_status": status,
        "validation_note": note
    })


def read_csv(folder, filename):
    path = folder / filename

    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")

    return pd.read_csv(path)


def require_columns(df, columns, filename):
    missing = [col for col in columns if col not in df.columns]

    if missing:
        raise ValueError(
            f"{filename} is missing required columns: {missing}"
        )


# ==================================================
# 1. OLIST E-COMMERCE
# ==================================================

print("\nVALIDATING OLIST E-COMMERCE KPIs")

orders = read_csv(OLIST, "olist_orders_dataset.csv")
items = read_csv(OLIST, "olist_order_items_dataset.csv")
payments = read_csv(OLIST, "olist_order_payments_dataset.csv")
reconciliation = read_csv(OLIST, "order_payment_reconciliation.csv")

require_columns(
    orders,
    ["order_id", "order_status"],
    "olist_orders_dataset.csv"
)

require_columns(
    items,
    ["order_id", "price", "freight_value"],
    "olist_order_items_dataset.csv"
)

require_columns(
    reconciliation,
    ["reconciliation_status"],
    "order_payment_reconciliation.csv"
)

items["price"] = pd.to_numeric(items["price"], errors="coerce")
items["freight_value"] = pd.to_numeric(
    items["freight_value"], errors="coerce"
)

# Aggregate items before joining to orders.
order_values = (
    items.groupby("order_id", as_index=False)
    .agg(
        item_value=("price", "sum"),
        freight_value=("freight_value", "sum")
    )
)

order_values["order_total"] = (
    order_values["item_value"] + order_values["freight_value"]
)

order_summary = orders.merge(
    order_values,
    on="order_id",
    how="left",
    validate="one_to_one"
)

delivered = order_summary[
    order_summary["order_status"] == "delivered"
].copy()

delivered_with_items = delivered[
    delivered["order_total"].notna()
]

total_delivered_revenue = delivered_with_items["order_total"].sum()

total_delivered_orders = delivered["order_id"].nunique()

average_order_value = (
    total_delivered_revenue / len(delivered_with_items)
    if len(delivered_with_items) > 0 else 0
)

total_orders = orders["order_id"].nunique()

canceled_orders = orders[
    orders["order_status"] == "canceled"
]["order_id"].nunique()

unavailable_orders = orders[
    orders["order_status"] == "unavailable"
]["order_id"].nunique()

cancellation_rate = (
    canceled_orders / total_orders * 100 if total_orders else 0
)

unavailable_rate = (
    unavailable_orders / total_orders * 100 if total_orders else 0
)

status_counts = reconciliation[
    "reconciliation_status"
].value_counts()

matched = int(status_counts.get("MATCHED", 0))
tolerance = int(status_counts.get("ROUNDING_TOLERANCE", 0))
mismatch = int(status_counts.get("AMOUNT_MISMATCH", 0))

both_records = matched + tolerance + mismatch

payment_reconciliation_rate = (
    matched / both_records * 100 if both_records else 0
)

add_result(
    "Olist E-commerce",
    "Total Delivered Revenue",
    round(total_delivered_revenue, 2),
    "BRL",
    "PASS",
    "Delivered orders with item records; includes freight."
)

add_result(
    "Olist E-commerce",
    "Total Delivered Orders",
    total_delivered_orders,
    "Count",
    "PASS",
    "Distinct delivered orders."
)

add_result(
    "Olist E-commerce",
    "Average Order Value",
    round(average_order_value, 2),
    "BRL",
    "PASS",
    "Average based on delivered orders with item records."
)

add_result(
    "Olist E-commerce",
    "Cancellation Rate",
    round(cancellation_rate, 2),
    "Percentage",
    "PASS",
    f"{canceled_orders} canceled / {total_orders} total orders."
)

add_result(
    "Olist E-commerce",
    "Unavailable Order Rate",
    round(unavailable_rate, 2),
    "Percentage",
    "PASS",
    f"{unavailable_orders} unavailable / {total_orders} total orders."
)

add_result(
    "Olist E-commerce",
    "Payment Reconciliation Rate",
    round(payment_reconciliation_rate, 2),
    "Percentage",
    "REVIEW",
    f"Exact matches only: {matched}; rounding tolerance: {tolerance}; mismatches: {mismatch}."
)

add_result(
    "Olist E-commerce",
    "Payment Mismatch Count",
    mismatch,
    "Count",
    "PASS",
    "Orders classified as AMOUNT_MISMATCH."
)


# ==================================================
# 2. OLIST MARKETING FUNNEL
# ==================================================

print("\nVALIDATING MARKETING FUNNEL KPIs")

leads = read_csv(
    MARKETING,
    "olist_marketing_qualified_leads_dataset.csv"
)

deals = read_csv(
    MARKETING,
    "olist_closed_deals_dataset.csv"
)

require_columns(leads, ["mql_id"], "marketing qualified leads")
require_columns(deals, ["mql_id"], "closed deals")

total_mqls = leads["mql_id"].nunique()
total_closed_deals = deals["mql_id"].nunique()

conversion_rate = (
    total_closed_deals / total_mqls * 100 if total_mqls else 0
)

add_result(
    "Marketing Funnel",
    "Total Marketing Qualified Leads",
    total_mqls,
    "Count",
    "PASS",
    "Distinct MQL IDs in the leads dataset."
)

add_result(
    "Marketing Funnel",
    "Total Closed Deals",
    total_closed_deals,
    "Count",
    "PASS",
    "Distinct MQL IDs in the closed deals dataset."
)

add_result(
    "Marketing Funnel",
    "MQL-to-Closed-Deal Conversion Rate",
    round(conversion_rate, 2),
    "Percentage",
    "REVIEW",
    "Dataset-level ratio; not a complete CRM stage conversion rate."
)


# ==================================================
# 3. ONLINE RETAIL II
# ==================================================

print("\nVALIDATING ONLINE RETAIL II KPIs")


def load_retail_file(filename):
    df = read_csv(RETAIL, filename)

    require_columns(
        df,
        ["Invoice", "Quantity", "Price"],
        filename
    )

    df["Quantity"] = pd.to_numeric(
        df["Quantity"], errors="coerce"
    )

    df["Price"] = pd.to_numeric(
        df["Price"], errors="coerce"
    )

    return df


retail_2009 = load_retail_file(
    "online_retail_2009_2010_cleaned.csv"
)

retail_2010 = load_retail_file(
    "online_retail_2010_2011_cleaned.csv"
)

retail = pd.concat(
    [retail_2009, retail_2010],
    ignore_index=True
)

retail["Invoice"] = retail["Invoice"].astype("string").str.strip()

retail["line_value"] = retail["Quantity"] * retail["Price"]

net_transaction_value = retail["line_value"].sum()

invoice_count = retail["Invoice"].nunique()

return_count = int((retail["Quantity"] < 0).sum())

cancellation_count = retail.loc[
    retail["Invoice"].str.startswith("C", na=False),
    "Invoice"
].nunique()

add_result(
    "Online Retail II",
    "Net Transaction Value",
    round(net_transaction_value, 2),
    "GBP",
    "PASS",
    "Includes negative quantities and cancellation invoice rows."
)

add_result(
    "Online Retail II",
    "Invoice Count",
    invoice_count,
    "Count",
    "PASS",
    "Distinct invoice IDs, including cancellation invoices."
)

add_result(
    "Online Retail II",
    "Return Indicator Count",
    return_count,
    "Count",
    "PASS",
    "Rows with negative quantity; not confirmed refunds."
)

add_result(
    "Online Retail II",
    "Cancellation Invoice Count",
    cancellation_count,
    "Count",
    "PASS",
    "Distinct invoice IDs beginning with C."
)


# ==================================================
# 4. SAVE VALIDATION RESULTS
# ==================================================

result_df = pd.DataFrame(results)

result_df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)

print("\n" + "=" * 55)
print("SALESSIGHT 360 - KPI VALIDATION SUMMARY")
print("=" * 55)

print(f"Total KPIs calculated: {len(result_df)}")

print("\nKPIs by dataset:")
print(result_df.groupby("dataset")["kpi_name"].count().to_string())

print("\nValidation statuses:")
print(result_df["validation_status"].value_counts().to_string())

print(f"\nOutput saved: {OUTPUT_FILE}")
print("\nKPI CALCULATION COMPLETED")
