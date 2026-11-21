
from pathlib import Path
import pandas as pd

# =====================================================
# SalesSight 360
# Phase 1 - Data Relationship and Quality Validation
# This script reads raw files only. It does not modify them.
# =====================================================

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "01_Data" / "01_Raw"

OUTPUT = (
    ROOT / "01_Data" / "04_Data_Dictionary"
    / "Relationship_Validation"
)
OUTPUT.mkdir(parents=True, exist_ok=True)

results = []


def load_csv(folder, filename):
    path = RAW / folder / filename

    for encoding in ["utf-8-sig", "utf-8", "cp1252"]:
        try:
            return pd.read_csv(
                path,
                encoding=encoding,
                low_memory=False
            )
        except UnicodeDecodeError:
            continue

    raise ValueError(f"Could not read {filename}")


def add_result(check, value, details):
    results.append({
        "check": check,
        "result": value,
        "details": details
    })


def check_unique(df, column, dataset):
    duplicate_count = int(df[column].duplicated().sum())

    add_result(
        f"{dataset}: duplicate {column}",
        duplicate_count,
        "Expected zero only if this column is a unique key."
    )


def check_foreign_key(child, child_column,
                      parent, parent_column, relationship):

    child_values = child[child_column].dropna()
    parent_values = set(parent[parent_column].dropna())

    unmatched = int((~child_values.isin(parent_values)).sum())

    add_result(
        relationship,
        unmatched,
        f"Non-null child values without a matching parent. "
        f"Checked {len(child_values):,} child rows."
    )


def main():

    print("\nSALESSIGHT 360 - RELATIONSHIP VALIDATION")
    print("=" * 60)

    # -----------------------------
    # Load Olist datasets
    # -----------------------------

    customers = load_csv(
        "Olist_Ecommerce", "olist_customers_dataset.csv"
    )

    orders = load_csv(
        "Olist_Ecommerce", "olist_orders_dataset.csv"
    )

    items = load_csv(
        "Olist_Ecommerce", "olist_order_items_dataset.csv"
    )

    payments = load_csv(
        "Olist_Ecommerce", "olist_order_payments_dataset.csv"
    )

    products = load_csv(
        "Olist_Ecommerce", "olist_products_dataset.csv"
    )

    sellers = load_csv(
        "Olist_Ecommerce", "olist_sellers_dataset.csv"
    )

    reviews = load_csv(
        "Olist_Ecommerce", "olist_order_reviews_dataset.csv"
    )

    leads = load_csv(
        "Olist_Marketing_Funnel",
        "olist_marketing_qualified_leads_dataset.csv"
    )

    closed_deals = load_csv(
        "Olist_Marketing_Funnel",
        "olist_closed_deals_dataset.csv"
    )

    # -----------------------------
    # 1. Primary-key checks
    # -----------------------------

    check_unique(customers, "customer_id", "Customers")
    check_unique(orders, "order_id", "Orders")
    check_unique(products, "product_id", "Products")
    check_unique(sellers, "seller_id", "Sellers")
    check_unique(leads, "mql_id", "Marketing leads")

    # -----------------------------
    # 2. Foreign-key checks
    # -----------------------------

    check_foreign_key(
        orders, "customer_id",
        customers, "customer_id",
        "Orders -> Customers"
    )

    check_foreign_key(
        items, "order_id",
        orders, "order_id",
        "Order items -> Orders"
    )

    check_foreign_key(
        items, "product_id",
        products, "product_id",
        "Order items -> Products"
    )

    check_foreign_key(
        items, "seller_id",
        sellers, "seller_id",
        "Order items -> Sellers"
    )

    check_foreign_key(
        payments, "order_id",
        orders, "order_id",
        "Payments -> Orders"
    )

    check_foreign_key(
        reviews, "order_id",
        orders, "order_id",
        "Reviews -> Orders"
    )

    check_foreign_key(
        closed_deals, "mql_id",
        leads, "mql_id",
        "Closed deals -> Marketing leads"
    )

    check_foreign_key(
        closed_deals, "seller_id",
        sellers, "seller_id",
        "Closed deals -> Sellers"
    )

    # -----------------------------
    # 3. Order status distribution
    # -----------------------------

    status_counts = (
        orders["order_status"]
        .value_counts(dropna=False)
        .rename_axis("order_status")
        .reset_index(name="order_count")
    )

    status_counts.to_csv(
        OUTPUT / "order_status_distribution.csv",
        index=False
    )

    for _, row in status_counts.iterrows():
        add_result(
            f"Order status: {row['order_status']}",
            int(row["order_count"]),
            "Number of orders in this status."
        )

    # -----------------------------
    # 4. Order date range
    # -----------------------------

    purchase_dates = pd.to_datetime(
        orders["order_purchase_timestamp"],
        errors="coerce"
    )

    add_result(
        "Order purchase date range",
        f"{purchase_dates.min()} to {purchase_dates.max()}",
        f"Invalid or missing dates: {purchase_dates.isna().sum()}"
    )

    # -----------------------------
    # 5. Item and payment totals
    # -----------------------------

    item_totals = (
        items.groupby("order_id", as_index=False)
        .agg(
            item_value=("price", "sum"),
            freight_value=("freight_value", "sum")
        )
    )

    payment_totals = (
        payments.groupby("order_id", as_index=False)
        .agg(payment_value=("payment_value", "sum"))
    )

    comparison = item_totals.merge(
        payment_totals,
        on="order_id",
        how="outer",
        indicator=True
    )

    comparison["difference"] = (
        comparison["payment_value"]
        - comparison["item_value"]
        - comparison["freight_value"]
    )

    comparison["difference"] = comparison["difference"].round(2)

    comparison.to_csv(
        OUTPUT / "order_payment_comparison.csv",
        index=False
    )

    add_result(
        "Orders with both item and payment records",
        int((comparison["_merge"] == "both").sum()),
        "Orders present in both aggregated item and payment data."
    )

    add_result(
        "Orders with unmatched item/payment records",
        int((comparison["_merge"] != "both").sum()),
        "Investigate before deciding whether records should be excluded."
    )

    add_result(
        "Orders with non-zero payment difference",
        int((comparison["difference"].abs() > 0.01).sum()),
        "Payment total compared with item value plus freight. "
        "Differences need investigation; they are not automatically errors."
    )

    # -----------------------------
    # 6. Online Retail II checks
    # -----------------------------

    retail_file = RAW / "Online_Retail_II" / "online_retail_II.xlsx"

    retail_sheets = pd.read_excel(
        retail_file,
        sheet_name=None
    )

    for sheet_name, retail in retail_sheets.items():

        quantity_negative = int(
            (retail["Quantity"] < 0).sum()
        )

        price_nonpositive = int(
            (retail["Price"] <= 0).sum()
        )

        missing_customer = int(
            retail["Customer ID"].isna().sum()
        )

        cancellation_invoices = int(
            retail["Invoice"].astype(str)
            .str.startswith("C", na=False).sum()
        )

        add_result(
            f"{sheet_name}: negative quantity rows",
            quantity_negative,
            "Rows with Quantity below zero. Inspect cancellation/return patterns."
        )

        add_result(
            f"{sheet_name}: zero or negative price rows",
            price_nonpositive,
            "Rows with Price less than or equal to zero."
        )

        add_result(
            f"{sheet_name}: missing customer IDs",
            missing_customer,
            "Rows without Customer ID."
        )

        add_result(
            f"{sheet_name}: cancellation invoice rows",
            cancellation_invoices,
            "Invoice values beginning with C; investigate before revenue calculation."
        )

    # -----------------------------
    # 7. Save validation reports
    # -----------------------------

    report = pd.DataFrame(results)

    report.to_csv(
        OUTPUT / "relationship_validation_report.csv",
        index=False
    )

    print("\nVALIDATION COMPLETED")
    print("=" * 60)
    print(report.to_string(index=False))

    print("\nReports saved in:")
    print(OUTPUT)

    print("\nNo raw dataset was changed.")


if __name__ == "__main__":
    main()
