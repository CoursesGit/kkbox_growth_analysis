/*
MySQL validation queries.

Expected imported tables:
  new_user_anomaly_base
    msno VARCHAR(64) PRIMARY KEY,
    registration_date DATE, registration_month CHAR(7), registered_via INT,
    period_group VARCHAR(16), first_active_date DATE, days_to_first_activity INT,
    first_7d_active_days INT, first_7d_total_secs DECIMAL(18,3),
    first_7d_num_100 BIGINT, d7_retained TINYINT, d30_retained TINYINT

  new_user_transaction_features
    msno VARCHAR(64) PRIMARY KEY,
    registration_date DATE, registered_via INT,
    has_transaction_30d TINYINT, transaction_count_30d INT,
    paid_transaction_count_30d INT, revenue_30d DECIMAL(18,2),
    first_transaction_date DATE, days_to_first_transaction INT,
    first_payment_plan_days INT, first_actual_amount_paid DECIMAL(18,2),
    first_is_auto_renew TINYINT, any_auto_renew_30d TINYINT,
    any_cancel_30d TINYINT
*/

WITH scoped AS (
    SELECT *,
           CASE
               WHEN registration_date BETWEEN '2015-07-01' AND '2015-09-30' THEN 'baseline'
               WHEN registration_date BETWEEN '2015-10-01' AND '2015-10-06' THEN 'oct_01_06'
               WHEN registration_date BETWEEN '2015-10-07' AND '2015-10-31' THEN 'oct_07_31'
           END AS analysis_period
    FROM new_user_anomaly_base
    WHERE registration_date BETWEEN '2015-07-01' AND '2015-10-31'
), source_counts AS (
    SELECT analysis_period, registered_via, COUNT(DISTINCT msno) AS users
    FROM scoped
    GROUP BY analysis_period, registered_via
), period_totals AS (
    SELECT analysis_period, COUNT(DISTINCT msno) AS total_users
    FROM scoped
    GROUP BY analysis_period
)
SELECT c.analysis_period, c.registered_via, c.users,
       c.users / NULLIF(t.total_users, 0) AS user_share
FROM source_counts c
JOIN period_totals t ON c.analysis_period = t.analysis_period
ORDER BY c.analysis_period, c.registered_via;

WITH cohort AS (
    SELECT *
    FROM new_user_anomaly_base
    WHERE registration_date BETWEEN '2015-10-07' AND '2015-10-31'
      AND registered_via IN (3, 4, 7, 9)
)
SELECT registered_via,
       COUNT(DISTINCT msno) AS users,
       AVG(CASE WHEN first_active_date IS NOT NULL THEN 1.0 ELSE 0.0 END) AS activated_user_rate,
       AVG(days_to_first_activity) AS avg_days_to_first_activity,
       AVG(first_7d_active_days) AS avg_first_7d_active_days,
       AVG(first_7d_total_secs) AS avg_first_7d_total_secs,
       AVG(first_7d_num_100) AS avg_first_7d_num_100,
       AVG(CASE WHEN d7_retained = 1 THEN 1.0 ELSE 0.0 END) AS d7_retention,
       AVG(CASE WHEN d30_retained = 1 THEN 1.0 ELSE 0.0 END) AS d30_retention
FROM cohort
GROUP BY registered_via
ORDER BY registered_via;

WITH joined AS (
    SELECT b.msno, b.registered_via, b.d7_retained, b.d30_retained,
           t.has_transaction_30d, t.transaction_count_30d,
           t.paid_transaction_count_30d, t.revenue_30d,
           t.first_is_auto_renew, t.any_auto_renew_30d, t.any_cancel_30d
    FROM new_user_anomaly_base b
    JOIN new_user_transaction_features t ON b.msno = t.msno
    WHERE b.registration_date BETWEEN '2015-10-07' AND '2015-10-31'
      AND b.registered_via IN (3, 4, 7, 9)
)
SELECT registered_via,
       COUNT(DISTINCT msno) AS users,
       AVG(CASE WHEN d7_retained = 1 THEN 1.0 ELSE 0.0 END) AS d7_retention,
       AVG(CASE WHEN d30_retained = 1 THEN 1.0 ELSE 0.0 END) AS d30_retention,
       AVG(CASE WHEN has_transaction_30d = 1 THEN 1.0 ELSE 0.0 END) AS transaction_rate_30d,
       AVG(transaction_count_30d) AS avg_transaction_count_30d,
       AVG(CASE WHEN paid_transaction_count_30d > 0 THEN 1.0 ELSE 0.0 END) AS paying_user_rate,
       AVG(CASE WHEN first_is_auto_renew = 1 THEN 1.0 ELSE 0.0 END) AS first_auto_renew_rate,
       AVG(CASE WHEN any_auto_renew_30d = 1 THEN 1.0 ELSE 0.0 END) AS any_auto_renew_rate_30d,
       AVG(CASE WHEN any_cancel_30d = 1 THEN 1.0 ELSE 0.0 END) AS any_cancel_rate_30d,
       AVG(revenue_30d) AS avg_revenue_30d,
       SUM(revenue_30d) AS total_revenue_30d
FROM joined
GROUP BY registered_via
ORDER BY registered_via;

