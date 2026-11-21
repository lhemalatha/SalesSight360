
/*
PROJECT: SalesSight 360
MODULE: Online Retail II Analytics

SOURCE:
UCI Online Retail II
PERIOD: December 2009 - December 2011
CURRENCY: GBP (£)

DATASET OVERVIEW:
Transaction rows: 1,067,371
Unique invoices: 53,628
Unique customers: 5,942
Unique products: 5,131
Countries: 43

TOTAL NET TRANSACTION VALUE:
£19,287,250.57

IMPORTANT:
- Negative quantities are retained.
- Cancellation invoices are retained.
- A-prefix invoices are separately identified.
- Missing customer IDs are not treated as customers.
- All results represent transaction data, not profit.
*/

USE salessight360;


/* 1. DATASET OVERVIEW */

SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT Invoice) AS unique_invoices,
    COUNT(DISTINCT Customer_ID) AS unique_customers,
    COUNT(DISTINCT StockCode) AS unique_products,
    COUNT(DISTINCT Country) AS unique_countries,
    ROUND(SUM(line_value_gbp), 2) AS net_value_gbp
FROM online_retail_transactions;


/* 2. MONTHLY REVENUE */

SELECT
    DATE_FORMAT(InvoiceDate, '%Y-%m') AS sales_month,
    COUNT(*) AS transaction_rows,
    COUNT(DISTINCT Invoice) AS unique_invoices,
    ROUND(SUM(line_value_gbp), 2) AS net_revenue_gbp
FROM online_retail_transactions
WHERE InvoiceDate IS NOT NULL
GROUP BY DATE_FORMAT(InvoiceDate, '%Y-%m')
ORDER BY sales_month;


/* 3. COUNTRY PERFORMANCE */

SELECT
    Country,
    COUNT(*) AS transaction_rows,
    COUNT(DISTINCT Invoice) AS unique_invoices,
    COUNT(DISTINCT Customer_ID) AS unique_customers,
    ROUND(SUM(line_value_gbp), 2) AS net_revenue_gbp
FROM online_retail_transactions
GROUP BY Country
ORDER BY net_revenue_gbp DESC;


/* 4. TOP PRODUCTS */

SELECT
    StockCode,
    MAX(Description) AS product_description,
    SUM(Quantity) AS net_quantity_sold,
    COUNT(DISTINCT Invoice) AS unique_invoices,
    ROUND(SUM(line_value_gbp), 2) AS net_revenue_gbp
FROM online_retail_transactions
WHERE StockCode IS NOT NULL
GROUP BY StockCode
ORDER BY net_revenue_gbp DESC
LIMIT 15;


/* 5. RETURNS AND CANCELLATIONS */

SELECT
    CASE
        WHEN Invoice LIKE 'C%' THEN 'Cancellation Invoice'
        WHEN Quantity < 0 THEN 'Negative Quantity'
        ELSE 'Regular Transaction'
    END AS transaction_type,
    COUNT(*) AS transaction_rows,
    COUNT(DISTINCT Invoice) AS unique_invoices,
    SUM(Quantity) AS net_quantity,
    ROUND(SUM(line_value_gbp), 2) AS net_value_gbp
FROM online_retail_transactions
GROUP BY transaction_type;


/* 6. TOP CUSTOMERS */

SELECT
    Customer_ID,
    COUNT(DISTINCT Invoice) AS unique_invoices,
    COUNT(*) AS transaction_rows,
    SUM(Quantity) AS net_quantity,
    ROUND(SUM(line_value_gbp), 2) AS net_revenue_gbp
FROM online_retail_transactions
WHERE Customer_ID IS NOT NULL
GROUP BY Customer_ID
ORDER BY net_revenue_gbp DESC
LIMIT 15;


/* 7. INVOICE PREFIX ANALYSIS */

SELECT
    CASE
        WHEN Invoice LIKE 'C%' THEN 'C - Cancellation'
        WHEN Invoice LIKE 'A%' THEN 'A - Special prefix'
        ELSE 'Regular prefix'
    END AS invoice_type,
    COUNT(DISTINCT Invoice) AS unique_invoices,
    COUNT(*) AS transaction_rows,
    ROUND(SUM(line_value_gbp), 2) AS net_value_gbp
FROM online_retail_transactions
WHERE Invoice IS NOT NULL
GROUP BY invoice_type;


/* END OF ONLINE RETAIL II ANALYTICS */
