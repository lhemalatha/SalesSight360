from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="SalesSight360 | Sales Analytics", page_icon="📊", layout="wide")

# Data files stay in the original SalesSight360 cleaned-data folders.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = PROJECT_ROOT / "01_Data" / "02_Cleaned"

FILES = {
    "orders": DATA_ROOT / "Olist_Ecommerce" / "olist_orders_dataset.csv",
    "items": DATA_ROOT / "Olist_Ecommerce" / "olist_order_items_dataset.csv",
    "payments": DATA_ROOT / "Olist_Ecommerce" / "olist_order_payments_dataset.csv",
    "customers": DATA_ROOT / "Olist_Ecommerce" / "olist_customers_dataset.csv",
    "products": DATA_ROOT / "Olist_Ecommerce" / "olist_products_dataset.csv",
    "mql": DATA_ROOT / "Olist_Marketing_Funnel" / "olist_marketing_qualified_leads_dataset.csv",
    "deals": DATA_ROOT / "Olist_Marketing_Funnel" / "olist_closed_deals_dataset.csv",
}

@st.cache_data
def load_data():
    missing = [str(p) for p in FILES.values() if not p.exists()]
    if missing:
        raise FileNotFoundError("Required CSV files were not found:\n" + "\n".join(missing))
    orders = pd.read_csv(FILES["orders"], parse_dates=["order_purchase_timestamp"])
    items = pd.read_csv(FILES["items"])
    payments = pd.read_csv(FILES["payments"])
    customers = pd.read_csv(FILES["customers"])
    products = pd.read_csv(FILES["products"])
    mql = pd.read_csv(FILES["mql"], parse_dates=["first_contact_date"])
    deals = pd.read_csv(FILES["deals"], parse_dates=["won_date"])

    # One row per order in the sales model; item revenue is the sum of item prices.
    item_sales = items.groupby("order_id", as_index=False).agg(
        item_revenue=("price", "sum"),
        freight_revenue=("freight_value", "sum"),
        item_count=("order_item_id", "count"),
        product_count=("product_id", "nunique"),
    )
    payment_totals = payments.groupby("order_id", as_index=False).agg(
        payment_value=("payment_value", "sum"),
        payment_types=("payment_type", "nunique"),
    )
    data = orders.merge(item_sales, on="order_id", how="left")
    data = data.merge(payment_totals, on="order_id", how="left")
    data = data.merge(customers[["customer_id", "customer_unique_id", "customer_city", "customer_state"]],
                      on="customer_id", how="left")
    data = data.merge(items[["order_id", "product_id"]].drop_duplicates().merge(
        products[["product_id", "product_category_name"]], on="product_id", how="left"
    ).groupby("order_id", as_index=False)["product_category_name"].first(),
        on="order_id", how="left")
    data["order_month"] = data["order_purchase_timestamp"].dt.to_period("M").astype(str)
    data["item_revenue"] = data["item_revenue"].fillna(0)
    data["payment_value"] = data["payment_value"].fillna(0)
    return data, mql, deals

st.title("📊 SalesSight360")
st.caption("Sales Revenue & Customer Analytics | Interactive portfolio dashboard | Source: Olist public dataset")

try:
    sales, mql, deals = load_data()
except Exception as e:
    st.error(str(e))
    st.info("Check that this app is saved in SalesSight360/08_Streamlit/app.py and the cleaned CSV folders are present.")
    st.stop()

# Global filters
with st.sidebar:
    st.header("Dashboard Filters")
    states = sorted(sales["customer_state"].dropna().unique().tolist())
    selected_states = st.multiselect("Customer state", states, default=[])
    statuses = sorted(sales["order_status"].dropna().unique().tolist())
    selected_statuses = st.multiselect("Order status", statuses, default=["delivered"] if "delivered" in statuses else statuses)
    min_date = sales["order_purchase_timestamp"].min().date()
    max_date = sales["order_purchase_timestamp"].max().date()
    date_range = st.date_input("Purchase date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)

filtered = sales.copy()
if selected_states:
    filtered = filtered[filtered["customer_state"].isin(selected_states)]
if selected_statuses:
    filtered = filtered[filtered["order_status"].isin(selected_statuses)]
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
    filtered = filtered[
        filtered["order_purchase_timestamp"].dt.date.between(start_date, end_date)
    ]

page = st.sidebar.radio(
    "Report Pages",
    ["Executive Overview", "Revenue Analysis", "Orders & Payments", "Customer Analytics", "Marketing Funnel"]
)

# Shared calculations
total_revenue = filtered["item_revenue"].sum()
total_orders = filtered["order_id"].nunique()
unique_customers = filtered["customer_unique_id"].nunique()
average_order_value = total_revenue / total_orders if total_orders else 0
monthly = filtered.groupby("order_month", as_index=False).agg(
    revenue=("item_revenue", "sum"), orders=("order_id", "nunique")
).sort_values("order_month")

def kpi_row():
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Item Revenue", f"R$ {total_revenue:,.2f}")
    c2.metric("Orders", f"{total_orders:,}")
    c3.metric("Unique Customers", f"{unique_customers:,}")
    c4.metric("Average Order Value", f"R$ {average_order_value:,.2f}")

if page == "Executive Overview":
    st.subheader("Executive Overview")
    kpi_row()
    left, right = st.columns(2)
    with left:
        st.plotly_chart(px.line(monthly, x="order_month", y="revenue", markers=True,
                               title="Monthly Item Revenue", labels={"order_month":"Month","revenue":"Revenue (R$)"}),
                         use_container_width=True)
    with right:
        status = filtered.groupby("order_status", as_index=False)["order_id"].nunique().sort_values("order_id", ascending=False)
        st.plotly_chart(px.bar(status, x="order_status", y="order_id", title="Orders by Status",
                               labels={"order_status":"Order Status","order_id":"Orders"}),
                         use_container_width=True)
    state_sales = filtered.groupby("customer_state", as_index=False).agg(
        revenue=("item_revenue", "sum"), orders=("order_id", "nunique")
    ).sort_values("revenue", ascending=False).head(10)
    st.plotly_chart(px.bar(state_sales, x="customer_state", y="revenue", title="Top 10 States by Item Revenue",
                           labels={"customer_state":"State","revenue":"Revenue (R$)"}),
                     use_container_width=True)

elif page == "Revenue Analysis":
    st.subheader("Revenue Analysis")
    kpi_row()
    left, right = st.columns(2)
    with left:
        st.plotly_chart(px.line(monthly, x="order_month", y="revenue", markers=True,
                               title="Monthly Revenue Trend", labels={"order_month":"Month","revenue":"Revenue (R$)"}),
                         use_container_width=True)
    with right:
        category = filtered.groupby("product_category_name", as_index=False)["item_revenue"].sum()
        category = category.sort_values("item_revenue", ascending=False).head(12)
        st.plotly_chart(px.bar(category, x="item_revenue", y="product_category_name", orientation="h",
                               title="Top Product Categories by Revenue",
                               labels={"item_revenue":"Revenue (R$)","product_category_name":"Category"}),
                         use_container_width=True)
    st.dataframe(monthly.rename(columns={"order_month":"Month","revenue":"Item Revenue (R$)","orders":"Orders"}),
                 use_container_width=True, hide_index=True)

elif page == "Orders & Payments":
    st.subheader("Orders & Payments")
    kpi_row()
    payment_types = pd.read_csv(FILES["payments"]).merge(filtered[["order_id"]].drop_duplicates(), on="order_id")
    pay = payment_types.groupby("payment_type", as_index=False).agg(
        payment_amount=("payment_value","sum"), payment_records=("order_id","count")
    ).sort_values("payment_amount", ascending=False)
    left, right = st.columns(2)
    with left:
        st.plotly_chart(px.bar(pay, x="payment_type", y="payment_amount", title="Payment Value by Type",
                               labels={"payment_type":"Payment Type","payment_amount":"Payment Value (R$)"}),
                         use_container_width=True)
    with right:
        st.plotly_chart(px.histogram(filtered, x="item_count", nbins=15, title="Order Items per Order",
                                    labels={"item_count":"Items in Order","count":"Orders"}),
                         use_container_width=True)
    st.caption("Revenue is calculated from order-item price. Payment value includes payment records and may include freight or other order charges.")

elif page == "Customer Analytics":
    st.subheader("Customer Analytics")
    kpi_row()
    customer_summary = filtered.groupby("customer_state", as_index=False).agg(
        customers=("customer_unique_id","nunique"),
        orders=("order_id","nunique"),
        revenue=("item_revenue","sum")
    ).sort_values("customers", ascending=False).head(15)
    left, right = st.columns(2)
    with left:
        st.plotly_chart(px.bar(customer_summary, x="customer_state", y="customers",
                               title="Unique Customers by State",
                               labels={"customer_state":"State","customers":"Unique Customers"}),
                         use_container_width=True)
    with right:
        st.plotly_chart(px.scatter(customer_summary, x="orders", y="revenue", size="customers",
                                  hover_name="customer_state", title="State-Level Orders vs Revenue",
                                  labels={"orders":"Orders","revenue":"Revenue (R$)"}),
                         use_container_width=True)
    city_summary = filtered.groupby("customer_city", as_index=False).agg(
        customers=("customer_unique_id","nunique"), revenue=("item_revenue","sum")
    ).sort_values("revenue", ascending=False).head(10)
    st.plotly_chart(px.bar(city_summary, x="customer_city", y="revenue", title="Top 10 Cities by Item Revenue",
                           labels={"customer_city":"City","revenue":"Revenue (R$)"}),
                     use_container_width=True)

else:
    st.subheader("Marketing Funnel")
    st.caption("Marketing funnel uses the source marketing dataset and is not affected by order-date/state filters.")
    if mql.empty:
        st.warning("Marketing Qualified Leads data is empty.")
    else:
        mql_count = mql["mql_id"].nunique()
        won_count = deals["mql_id"].nunique() if not deals.empty else 0
        conversion = won_count / mql_count * 100 if mql_count else 0
        a, b, c = st.columns(3)
        a.metric("Marketing Qualified Leads", f"{mql_count:,}")
        b.metric("Closed Deals", f"{won_count:,}")
        c.metric("MQL to Closed Conversion", f"{conversion:.2f}%")
        origin = mql.groupby("origin", dropna=False, as_index=False)["mql_id"].nunique()
        origin = origin.rename(columns={"mql_id":"leads"}).sort_values("leads", ascending=False)
        st.plotly_chart(px.bar(origin, x="origin", y="leads", title="MQLs by Lead Origin",
                               labels={"origin":"Lead Origin","leads":"MQLs"}),
                         use_container_width=True)
        won = mql[["mql_id","origin"]].merge(deals[["mql_id"]].drop_duplicates().assign(closed=1),
                                             on="mql_id", how="left")
        won["closed"] = won["closed"].fillna(0)
        origin_conversion = won.groupby("origin", dropna=False, as_index=False).agg(
            leads=("mql_id","nunique"), closed=("closed","sum")
        )
        origin_conversion["conversion_pct"] = origin_conversion["closed"] / origin_conversion["leads"] * 100
        st.plotly_chart(px.bar(origin_conversion.sort_values("conversion_pct", ascending=False),
                               x="origin", y="conversion_pct", title="MQL-to-Closed Conversion by Lead Origin",
                               labels={"origin":"Lead Origin","conversion_pct":"Conversion (%)"}),
                         use_container_width=True)
        st.dataframe(origin_conversion, use_container_width=True, hide_index=True)

st.divider()
st.caption("SalesSight360 | Portfolio analytics project | Dataset: Olist public e-commerce and marketing funnel data")
