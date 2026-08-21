-- Mature history and the 2015-10-07 to 2015-10-09 focus cohort.
SELECT registered_via,COUNT(*) users_n,
AVG(CASE WHEN activation_eligible_flag=1 THEN activated_flag END) activation_rate,
AVG(CASE WHEN d1_eligible_flag=1 THEN d1_retained END) d1_rate,
AVG(CASE WHEN d3_eligible_flag=1 THEN d3_retained END) d3_rate,
AVG(CASE WHEN d7_eligible_flag=1 THEN d7_retained END) d7_rate,
SUM(first_7_eligible_flag) first_week_n,
AVG(CASE WHEN first_7_eligible_flag=1 THEN first_7_active_days END) avg_active_days,
AVG(CASE WHEN first_7_eligible_flag=1 THEN first_7_play_count END) avg_plays,
AVG(CASE WHEN first_7_eligible_flag=1 THEN first_7_total_secs END) avg_secs
FROM user_growth_profile WHERE registration_date BETWEEN '2015-07-01' AND '2015-10-09'
AND registered_via IN(3,4,7,9) GROUP BY registered_via;
SELECT registered_via,COUNT(*) users_n,
AVG(CASE WHEN activation_eligible_flag=1 THEN activated_flag END) activation_rate,
AVG(CASE WHEN d1_eligible_flag=1 THEN d1_retained END) d1_rate,
AVG(CASE WHEN d3_eligible_flag=1 THEN d3_retained END) d3_rate,
AVG(CASE WHEN d7_eligible_flag=1 THEN d7_retained END) d7_rate,
AVG(CASE WHEN first_7_eligible_flag=1 THEN first_7_active_days END) avg_active_days,
AVG(CASE WHEN first_7_eligible_flag=1 THEN first_7_play_count END) avg_plays,
AVG(CASE WHEN first_7_eligible_flag=1 THEN first_7_total_secs END) avg_secs
FROM user_growth_profile WHERE registration_date BETWEEN '2015-10-07' AND '2015-10-09'
AND registered_via IN(3,4,7,9) GROUP BY registered_via;
-- Counts for the D7 two-proportion tests performed in Python.
SELECT registered_via,SUM(d7_retained) retained_n,COUNT(*) eligible_n
FROM user_growth_profile WHERE registration_date BETWEEN '2015-10-07' AND '2015-10-09'
AND registered_via IN(3,4,7,9) AND d7_eligible_flag=1 GROUP BY registered_via;
