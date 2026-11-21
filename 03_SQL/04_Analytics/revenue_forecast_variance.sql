
/*
PROJECT: SalesSight 360
MODULE: Revenue Forecast and Variance Analysis
DATASET: Olist Brazilian E-Commerce
CURRENCY: BRL

METHOD:
Three-month moving average baseline.

PERIOD:
December 2016 to August 2018.

MISSING MONTH:
November 2016 treated as zero delivered revenue
because no delivered revenue record was available.

EVALUATION:
21 historical observations.

MAE: R$127,390.70
RMSE: R$161,058.95
AVERAGE VARIANCE: R$94,141.95
ORIGINAL MAPE: 3791.54%
FILTERED MAPE: 24.67%

FILTERED MAPE RULE:
Months with actual revenue below R$100,000
were excluded.

LIMITATION:
Historical in-sample baseline comparison.
Not an independent forecast accuracy test.
Not a weighted CRM pipeline forecast.
*/


-- STEP 1: Monthly Revenue and Three-Month Moving Average Forecast

USE salessight360;

WITH RECURSIVE calendar AS (

    SELECT DATE('2016-09-01') AS month_start

    UNION ALL

    SELECT DATE_ADD(month_start, INTERVAL 1 MONTH)
    FROM calendar
    WHERE month_start < '2018-08-01'

),

monthly_revenue AS (

    SELECT
        DATE(
            DATE_FORMAT(
                o.order_purchase_timestamp,
                '%Y-%m-01'
            )
        ) AS month_start,

        SUM(oi.price + oi.freight_value)
            AS actual_revenue

    FROM olist_orders o

    INNER JOIN olist_order_items oi
        ON o.order_id = oi.order_id

    WHERE o.order_status = 'delivered'

    GROUP BY month_start

),

complete_months AS (

    SELECT
        c.month_start,
        COALESCE(m.actual_revenue, 0)
            AS actual_revenue

    FROM calendar c

    LEFT JOIN monthly_revenue m
        ON c.month_start = m.month_start

)

SELECT
    DATE_FORMAT(month_start, '%Y-%m') AS revenue_month,
    ROUND(actual_revenue, 2) AS actual_revenue_brl,

    ROUND(
        AVG(actual_revenue) OVER (
            ORDER BY month_start
            ROWS BETWEEN 3 PRECEDING AND 1 PRECEDING
        ), 2
    ) AS forecast_revenue_brl

FROM complete_months

ORDER BY month_start;

-- STEP 2: Monthly Revenue Forecast and Variance Analysis

USE salessight360;

WITH RECURSIVE calendar AS (

    SELECT DATE('2016-09-01') AS month_start

    UNION ALL

    SELECT DATE_ADD(month_start, INTERVAL 1 MONTH)
    FROM calendar
    WHERE month_start < '2018-08-01'

),

monthly_revenue AS (

    SELECT
        DATE(
            DATE_FORMAT(
                o.order_purchase_timestamp,
                '%Y-%m-01'
            )
        ) AS month_start,

        SUM(oi.price + oi.freight_value)
            AS actual_revenue

    FROM olist_orders o

    INNER JOIN olist_order_items oi
        ON o.order_id = oi.order_id

    WHERE o.order_status = 'delivered'

    GROUP BY month_start

),

complete_months AS (

    SELECT
        c.month_start,
        COALESCE(m.actual_revenue, 0)
            AS actual_revenue

    FROM calendar c

    LEFT JOIN monthly_revenue m
        ON c.month_start = m.month_start

),

forecast_calculation AS (

    SELECT
        month_start,
        actual_revenue,

        AVG(actual_revenue) OVER (
            ORDER BY month_start
            ROWS BETWEEN 3 PRECEDING AND 1 PRECEDING
        ) AS forecast_revenue,

        COUNT(*) OVER (
            ORDER BY month_start
            ROWS BETWEEN 3 PRECEDING AND 1 PRECEDING
        ) AS previous_month_count

    FROM complete_months

)

SELECT
    DATE_FORMAT(month_start, '%Y-%m') AS revenue_month,

    ROUND(actual_revenue, 2) AS actual_revenue_brl,

    ROUND(forecast_revenue, 2) AS forecast_revenue_brl,

    ROUND(actual_revenue - forecast_revenue, 2)
        AS variance_brl,

    ROUND(
        (actual_revenue - forecast_revenue)
        * 100.0 / NULLIF(forecast_revenue, 0),
        2
    ) AS variance_pct

FROM forecast_calculation

WHERE previous_month_count = 3

ORDER BY month_start;

-- STEP 3: Forecast Evaluation Metrics

USE salessight360;

WITH RECURSIVE calendar AS (

    SELECT DATE('2016-09-01') AS month_start

    UNION ALL

    SELECT DATE_ADD(month_start, INTERVAL 1 MONTH)
    FROM calendar
    WHERE month_start < '2018-08-01'

),

monthly_revenue AS (

    SELECT
        DATE(
            DATE_FORMAT(
                o.order_purchase_timestamp,
                '%Y-%m-01'
            )
        ) AS month_start,

        SUM(oi.price + oi.freight_value)
            AS actual_revenue

    FROM olist_orders o

    INNER JOIN olist_order_items oi
        ON o.order_id = oi.order_id

    WHERE o.order_status = 'delivered'

    GROUP BY month_start

),

complete_months AS (

    SELECT
        c.month_start,
        COALESCE(m.actual_revenue, 0) AS actual_revenue

    FROM calendar c

    LEFT JOIN monthly_revenue m
        ON c.month_start = m.month_start

),

forecast_calculation AS (

    SELECT
        month_start,
        actual_revenue,

        AVG(actual_revenue) OVER (
            ORDER BY month_start
            ROWS BETWEEN 3 PRECEDING AND 1 PRECEDING
        ) AS forecast_revenue,

        COUNT(*) OVER (
            ORDER BY month_start
            ROWS BETWEEN 3 PRECEDING AND 1 PRECEDING
        ) AS previous_month_count

    FROM complete_months

),

evaluation AS (

    SELECT
        actual_revenue,
        forecast_revenue,

        actual_revenue - forecast_revenue AS variance

    FROM forecast_calculation

    WHERE previous_month_count = 3

)

SELECT
    COUNT(*) AS evaluated_months,

    ROUND(AVG(ABS(variance)), 2)
        AS mean_absolute_error_brl,

    ROUND(SQRT(AVG(variance * variance)), 2)
        AS root_mean_squared_error_brl,

    ROUND(AVG(variance), 2)
        AS average_variance_brl,

    ROUND(
        AVG(ABS(variance) / NULLIF(actual_revenue, 0))
        * 100,
        2
    ) AS original_mape_pct

FROM evaluation;

-- STEP 4: Filtered MAPE (Actual Revenue >= R$100,000)

USE salessight360;

WITH RECURSIVE calendar AS (

    SELECT DATE('2016-09-01') AS month_start

    UNION ALL

    SELECT DATE_ADD(month_start, INTERVAL 1 MONTH)
    FROM calendar
    WHERE month_start < '2018-08-01'

),

monthly_revenue AS (

    SELECT
        DATE(
            DATE_FORMAT(
                o.order_purchase_timestamp,
                '%Y-%m-01'
            )
        ) AS month_start,

        SUM(oi.price + oi.freight_value)
            AS actual_revenue

    FROM olist_orders o

    INNER JOIN olist_order_items oi
        ON o.order_id = oi.order_id

    WHERE o.order_status = 'delivered'

    GROUP BY month_start

),

complete_months AS (

    SELECT
        c.month_start,
        COALESCE(m.actual_revenue, 0) AS actual_revenue

    FROM calendar c

    LEFT JOIN monthly_revenue m
        ON c.month_start = m.month_start

),

forecast_calculation AS (

    SELECT
        month_start,
        actual_revenue,

        AVG(actual_revenue) OVER (
            ORDER BY month_start
            ROWS BETWEEN 3 PRECEDING AND 1 PRECEDING
        ) AS forecast_revenue,

        COUNT(*) OVER (
            ORDER BY month_start
            ROWS BETWEEN 3 PRECEDING AND 1 PRECEDING
        ) AS previous_month_count

    FROM complete_months

),

evaluation AS (

    SELECT
        actual_revenue,
        forecast_revenue

    FROM forecast_calculation

    WHERE previous_month_count = 3

)

SELECT
    COUNT(*) AS eligible_months,

    ROUND(
        AVG(
            ABS(actual_revenue - forecast_revenue)
            / NULLIF(actual_revenue, 0)
        ) * 100,
        2
    ) AS filtered_mape_pct

FROM evaluation

WHERE actual_revenue >= 100000;
