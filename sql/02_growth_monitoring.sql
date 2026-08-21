-- Growth monitoring and source diagnosis only.
WITH d AS(SELECT registration_date,COUNT(*) new_users FROM user_growth_profile
WHERE registration_date BETWEEN '2015-07-01' AND '2015-10-16' GROUP BY registration_date)
SELECT registration_date,new_users,AVG(new_users) OVER
(ORDER BY registration_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) new_users_7d_ma
FROM d ORDER BY registration_date;
WITH s AS(SELECT registration_date,registered_via,COUNT(*) source_users
FROM user_growth_profile WHERE registration_date BETWEEN '2015-07-01' AND '2015-10-16'
GROUP BY registration_date,registered_via),
t AS(SELECT registration_date,SUM(source_users) total_users FROM s GROUP BY registration_date)
SELECT s.registration_date,s.registered_via,s.source_users,t.total_users,
s.source_users/NULLIF(t.total_users,0) source_share FROM s JOIN t USING(registration_date)
ORDER BY s.registration_date,s.source_users DESC;
WITH x AS(SELECT registration_date,registered_via,CASE
WHEN registration_date BETWEEN '2015-10-01' AND '2015-10-06' THEN 'pre'
WHEN registration_date='2015-10-07' THEN 'break' ELSE 'post' END period
FROM user_growth_profile WHERE registration_date BETWEEN '2015-10-01' AND '2015-10-16')
SELECT period,COUNT(*) new_users,COUNT(DISTINCT registration_date) days_n,
COUNT(*)/COUNT(DISTINCT registration_date) avg_daily_new_users,
SUM(registered_via=4) source4_users,SUM(registered_via=4)/COUNT(*) source4_share
FROM x GROUP BY period ORDER BY MIN(registration_date);
