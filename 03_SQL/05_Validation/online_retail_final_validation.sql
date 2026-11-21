/*
PROJECT: SalesSight 360
MODULE: Online Retail II Final Validation

VALIDATION RESULTS:

Total rows: 1,067,371
Net transaction value: GBP 19,287,250.57
Missing customer IDs: 243,007
Cancellation rows: 19,494
A-prefix rows: 6
Negative quantity rows: 22,950

STATUS: ALL 6 VALIDATION CHECKS PASSED

Original source transactions retained.
No records deleted during validation.
*/

USE salessight360;

SELECT
    COUNT(*) AS total_rows,
    ROUND(SUM(line_value_gbp), 2) AS net_transaction_value_gbp,
    SUM(CASE WHEN Customer_ID IS NULL THEN 1 ELSE 0 END)
        AS missing_customer_ids,
    SUM(CASE WHEN Invoice LIKE 'C%' THEN 1 ELSE 0 END)
        AS cancellation_rows,
    SUM(CASE WHEN Invoice LIKE 'A%' THEN 1 ELSE 0 END)
        AS special_prefix_rows,
    SUM(CASE WHEN Quantity < 0 THEN 1 ELSE 0 END)
        AS negative_quantity_rows
FROM online_retail_transactions;