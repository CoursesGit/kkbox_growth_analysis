-- Data audit: 2015-07-01 through 2015-10-16.
SET @analysis_start=DATE('2015-07-01'); SET @data_as_of=DATE('2015-10-16');
SELECT 'members_v3' table_name,COUNT(*) rows_n,COUNT(DISTINCT msno) users_n,
MIN(STR_TO_DATE(CAST(registration_init_time AS CHAR),'%Y%m%d')) min_date,
MAX(STR_TO_DATE(CAST(registration_init_time AS CHAR),'%Y%m%d')) max_date FROM members_v3
UNION ALL SELECT 'user_logs',COUNT(*),COUNT(DISTINCT msno),
MIN(STR_TO_DATE(CAST(date AS CHAR),'%Y%m%d')),MAX(STR_TO_DATE(CAST(date AS CHAR),'%Y%m%d')) FROM user_logs
UNION ALL SELECT 'transactions',COUNT(*),COUNT(DISTINCT msno),
MIN(STR_TO_DATE(CAST(transaction_date AS CHAR),'%Y%m%d')),
MAX(STR_TO_DATE(CAST(transaction_date AS CHAR),'%Y%m%d')) FROM transactions;
SELECT COUNT(*) duplicated_msno_groups FROM
(SELECT msno FROM members_v3 GROUP BY msno HAVING COUNT(*)>1) d;
SELECT SUM(registration_date IS NULL) invalid_dates,
SUM(registration_date<@analysis_start OR registration_date>@data_as_of) outside_window,
SUM(registered_via IS NULL) missing_registered_via FROM
(SELECT STR_TO_DATE(CAST(registration_init_time AS CHAR),'%Y%m%d') registration_date,
registered_via FROM members_v3) m;
SELECT MIN(STR_TO_DATE(CAST(date AS CHAR),'%Y%m%d')) min_log_date,
MAX(STR_TO_DATE(CAST(date AS CHAR),'%Y%m%d')) max_log_date,
COUNT(DISTINCT msno) log_users,SUM(total_secs<0) negative_secs_rows FROM user_logs;
SELECT COALESCE(SUM(n-1),0) exact_duplicate_rows FROM
(SELECT msno,date,num_25,num_50,num_75,num_985,num_100,num_unq,total_secs,COUNT(*) n
FROM user_logs GROUP BY msno,date,num_25,num_50,num_75,num_985,num_100,num_unq,total_secs
HAVING COUNT(*)>1) d;
-- Transactions: availability only.
SELECT COUNT(*) rows_n,COUNT(DISTINCT msno) users_n FROM transactions;
