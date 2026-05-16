-- Monthly onboarding report during 2024:
-- 1. Total new customers (distinct customer_id) registered per registration_channel.
-- 2. Average day difference between registration_date and first transaction date (order_date).
-- Only include customers who have made at least one purchase.
-- This report is used for onboarding optimization.

WITH first_transaction AS (

    SELECT
        customer_id,
        MIN(order_date) AS first_order_date

    FROM order_detail

    GROUP BY customer_id
)

SELECT
    EXTRACT(MONTH FROM c.registration_date) AS bulan,

    c.registration_channel,

    COUNT(DISTINCT c.customer_id) AS total_new_customer,

    ROUND(
        AVG(
            first_order_date::date
            -
            c.registration_date::date
        ),
        2
    ) AS avg_days_to_first_transaction

FROM customer_detail c

INNER JOIN first_transaction f
ON c.customer_id = f.customer_id

WHERE c.registration_date BETWEEN '2024-01-01'
AND '2024-12-31'

GROUP BY bulan, c.registration_channel

ORDER BY bulan ASC, c.registration_channel ASC;