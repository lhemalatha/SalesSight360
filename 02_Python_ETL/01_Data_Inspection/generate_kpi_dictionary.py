
from pathlib import Path
import pandas as pd

# --------------------------------------------------
# SALESSIGHT 360
# Phase 1 - KPI Dictionary
# --------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]

OUTPUT_DIR = ROOT / "01_Data" / "04_Data_Dictionary"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "salesight_kpi_dictionary.csv"

kpis = [

    {
        "dataset": "Olist E-commerce",
        "kpi_name": "Total Delivered Revenue",
        "definition": "Total item price plus freight for delivered orders with item records.",
        "formula": "SUM(order-level item price + freight_value) for delivered orders",
        "currency": "BRL",
        "limitation": "Represents delivered order value including freight, not profit. Aggregate item values at order level before joining payments."
    },
    {
        "dataset": "Olist E-commerce",
        "kpi_name": "Total Delivered Orders",
        "definition": "Number of distinct orders with delivered status.",
        "formula": "COUNT DISTINCT order_id WHERE order_status = delivered",
        "currency": "Not applicable",
        "limitation": "Measures delivered orders, not all orders."
    },
    {
        "dataset": "Olist E-commerce",
        "kpi_name": "Average Order Value",
        "definition": "Average item and freight value per delivered order.",
        "formula": "Total Delivered Revenue / Total Delivered Orders",
        "currency": "BRL",
        "limitation": "Use distinct delivered orders and order-level totals."
    },
    {
        "dataset": "Olist E-commerce",
        "kpi_name": "Cancellation Rate",
        "definition": "Share of orders with canceled status.",
        "formula": "Canceled Orders / Total Orders * 100",
        "currency": "Percentage",
        "limitation": "Unavailable orders are reported separately."
    },
    {
        "dataset": "Olist E-commerce",
        "kpi_name": "Unavailable Order Rate",
        "definition": "Share of orders with unavailable status.",
        "formula": "Unavailable Orders / Total Orders * 100",
        "currency": "Percentage",
        "limitation": "Not included in canceled orders."
    },
    {
        "dataset": "Olist E-commerce",
        "kpi_name": "Payment Reconciliation Rate",
        "definition": "Share of orders with exact payment and item-plus-freight amount matches.",
        "formula": "MATCHED Orders / Orders with Item and Payment Records * 100",
        "currency": "Percentage",
        "limitation": "ROUNDING_TOLERANCE and AMOUNT_MISMATCH are excluded from the exact-match numerator and reported separately."
    },
    {
        "dataset": "Olist E-commerce",
        "kpi_name": "Payment Mismatch Count",
        "definition": "Number of orders with payment differences greater than the 0.01 BRL tolerance.",
        "formula": "COUNT orders WHERE reconciliation_status = AMOUNT_MISMATCH",
        "currency": "Count",
        "limitation": "Differences are unexplained by available source fields; do not adjust amounts."
    },
    {
        "dataset": "Marketing Funnel",
        "kpi_name": "Total Marketing Qualified Leads",
        "definition": "Number of distinct marketing qualified lead IDs.",
        "formula": "COUNT DISTINCT mql_id",
        "currency": "Count",
        "limitation": "Represents qualified leads in the available dataset."
    },
    {
        "dataset": "Marketing Funnel",
        "kpi_name": "Total Closed Deals",
        "definition": "Number of distinct MQL IDs present in the closed deals dataset.",
        "formula": "COUNT DISTINCT mql_id in closed deals",
        "currency": "Count",
        "limitation": "Represents recorded closed deals, not all sales opportunities."
    },
    {
        "dataset": "Marketing Funnel",
        "kpi_name": "MQL-to-Closed-Deal Conversion Rate",
        "definition": "Share of distinct marketing qualified leads that appear in the closed deals dataset.",
        "formula": "Distinct Closed Deal MQL IDs / Distinct MQL IDs * 100",
        "currency": "Percentage",
        "limitation": "This is an observed dataset conversion rate, not a complete CRM stage conversion rate."
    },
    {
        "dataset": "Online Retail II",
        "kpi_name": "Net Transaction Value",
        "definition": "Sum of quantity multiplied by unit price, retaining negative quantities.",
        "formula": "SUM(Quantity * Price)",
        "currency": "GBP",
        "limitation": "Includes recorded returns and cancellation invoice rows. Report gross sales separately if needed."
    },
    {
        "dataset": "Online Retail II",
        "kpi_name": "Invoice Count",
        "definition": "Number of distinct invoice IDs.",
        "formula": "COUNT DISTINCT Invoice",
        "currency": "Count",
        "limitation": "Cancellation invoices are included unless explicitly filtered."
    },
    {
        "dataset": "Online Retail II",
        "kpi_name": "Return Indicator Count",
        "definition": "Number of transaction rows with negative quantity.",
        "formula": "COUNT rows WHERE Quantity < 0",
        "currency": "Count",
        "limitation": "Negative quantity indicates a possible return or credit transaction, not a confirmed refund."
    },
    {
        "dataset": "Online Retail II",
        "kpi_name": "Cancellation Invoice Count",
        "definition": "Number of distinct invoice IDs beginning with C.",
        "formula": "COUNT DISTINCT Invoice WHERE Invoice starts with C",
        "currency": "Count",
        "limitation": "Cancellation invoice identification follows the source invoice convention."
    }
]

df = pd.DataFrame(kpis)

df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)

print("\nSALESSIGHT 360 - KPI DICTIONARY")
print("-" * 50)
print(f"Total KPIs documented: {len(df)}")
print(f"Output file: {OUTPUT_FILE}")
print("\nKPIs by dataset:")
print(df.groupby("dataset")["kpi_name"].count().to_string())
print("\nKPI dictionary generated successfully.")
