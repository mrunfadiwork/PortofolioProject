-- analysis of channel performance (web, app, offline) in 2024:

-- 1. Total orders (distinct) and revenue (after_discount) per month.
-- 2. Calculate the MoM revenue growth per month compared to the same month in 2023.
WITH monthly_revenue AS (

    SELECT 
        EXTRACT(YEAR FROM order_date) AS tahun,
        EXTRACT(MONTH FROM order_date) AS bulan,
        channel_type,
        COUNT(DISTINCT transaction_id) AS total_order,
        SUM(after_discount) AS revenue

    FROM order_detail

    WHERE channel_type IN ('Website', 'App Store', 'Offline Store')
    AND order_date BETWEEN '2023-01-01 00:00:00'
    AND '2024-12-31 23:59:59'

    GROUP BY tahun, bulan, channel_type
)

SELECT
    bulan,
    channel_type,

    MAX(
        CASE
            WHEN tahun = 2023 THEN total_order
        END
    ) AS total_order_2023,

    MAX(
        CASE
            WHEN tahun = 2024 THEN total_order
        END
    ) AS total_order_2024,

    MAX(
        CASE
            WHEN tahun = 2023 THEN revenue
        END
    ) AS revenue_2023,

    MAX(
        CASE
            WHEN tahun = 2024 THEN revenue
        END
    ) AS revenue_2024,

    ROUND(
        (
            (
                MAX(CASE WHEN tahun = 2024 THEN revenue END)::numeric
                -
                MAX(CASE WHEN tahun = 2023 THEN revenue END)::numeric
            )
            /
            NULLIF(
                MAX(CASE WHEN tahun = 2023 THEN revenue END)::numeric,
                0
            )
        ) * 100,
        2
    ) AS MOM_Growth_23vs24

FROM monthly_revenue

GROUP BY bulan, channel_type

ORDER BY bulan ASC, channel_type ASC;