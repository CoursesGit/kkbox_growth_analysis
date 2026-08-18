/*
  KKBox Source 4 A/B test planning validation

  Historical baseline and traffic planning only.
  This script does not create pseudo Control/Treatment groups and does not
  estimate uplift, confidence intervals, p-values, or experiment significance.
*/

USE kkbox_growth_analysis;

/* 1. Source 4 users registered from 2015-10-07 through 2015-10-31. */
SELECT
    COUNT(DISTINCT msno) AS source4_oct7_31_users
FROM new_user_anomaly_base
WHERE registered_via = 4
  AND registration_date BETWEEN '2015-10-07' AND '2015-10-31';

/* 2. Historical Source 4 D30 baseline for the same cohort. */
SELECT
    COUNT(DISTINCT msno) AS users,
    AVG(d30_retained) AS source4_d30_baseline
FROM new_user_anomaly_base
WHERE registered_via = 4
  AND registration_date BETWEEN '2015-10-07' AND '2015-10-31';

/* 3. Historical daily eligible new-user volume. */
SELECT
    registration_date,
    COUNT(DISTINCT msno) AS source4_daily_new_users
FROM new_user_anomaly_base
WHERE registered_via = 4
  AND registration_date BETWEEN '2015-10-07' AND '2015-10-31'
GROUP BY registration_date
ORDER BY registration_date;

/* 4. Historical average daily eligible new-user volume (planning proxy). */
SELECT
    AVG(daily_users) AS source4_avg_daily_new_users
FROM (
    SELECT
        registration_date,
        COUNT(DISTINCT msno) AS daily_users
    FROM new_user_anomaly_base
    WHERE registered_via = 4
      AND registration_date BETWEEN '2015-10-07' AND '2015-10-31'
    GROUP BY registration_date
) AS daily_source4;
