/*
KKBox processed-table import for MySQL 8.0 / MySQL Workbench.

Run SHOW VARIABLES LIKE 'local_infile' first.
- If Value = ON: run the complete script in the existing Local instance MySQL80 connection.
- If Value = OFF: do not change server configuration. Create the tables with this
  script, then use Workbench's Table Data Import Wizard for the two CSV files and
  run the integrity-check section below.

Only these processed files are referenced:
  data/processed/new_user_anomaly_base.csv
  data/processed/new_user_transaction_features.csv
*/

SHOW VARIABLES LIKE 'local_infile';

CREATE DATABASE IF NOT EXISTS kkbox_growth_analysis
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;
USE kkbox_growth_analysis;

DROP TABLE IF EXISTS new_user_transaction_features;
DROP TABLE IF EXISTS new_user_anomaly_base;

CREATE TABLE new_user_anomaly_base (
    msno                       VARCHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    registration_date          DATE NOT NULL,
    registration_month         CHAR(7) NOT NULL,
    registered_via             SMALLINT NOT NULL,
    period_group               VARCHAR(16) NOT NULL,
    first_active_date          DATE NULL,
    days_to_first_activity     SMALLINT UNSIGNED NULL,
    first_7d_active_days       TINYINT UNSIGNED NOT NULL,
    first_7d_total_secs        DECIMAL(18,3) NOT NULL,
    first_7d_num_100           INT UNSIGNED NOT NULL,
    d7_retained                TINYINT UNSIGNED NOT NULL,
    d30_retained               TINYINT UNSIGNED NOT NULL,
    PRIMARY KEY (msno),
    INDEX idx_anomaly_registration_date (registration_date),
    INDEX idx_anomaly_source_date (registered_via, registration_date),
    CONSTRAINT chk_anomaly_active_days CHECK (first_7d_active_days BETWEEN 0 AND 7),
    CONSTRAINT chk_anomaly_d7 CHECK (d7_retained IN (0, 1)),
    CONSTRAINT chk_anomaly_d30 CHECK (d30_retained IN (0, 1))
) ENGINE=InnoDB;

CREATE TABLE new_user_transaction_features (
    msno                           VARCHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    registration_date              DATE NOT NULL,
    registered_via                 SMALLINT NOT NULL,
    has_transaction_30d            TINYINT UNSIGNED NOT NULL,
    transaction_count_30d          SMALLINT UNSIGNED NOT NULL,
    paid_transaction_count_30d     SMALLINT UNSIGNED NOT NULL,
    revenue_30d                     DECIMAL(14,2) NOT NULL,
    first_transaction_date          DATE NULL,
    days_to_first_transaction       TINYINT UNSIGNED NULL,
    first_payment_plan_days         SMALLINT UNSIGNED NULL,
    first_actual_amount_paid        DECIMAL(12,2) NULL,
    first_is_auto_renew             TINYINT UNSIGNED NULL,
    any_auto_renew_30d              TINYINT UNSIGNED NOT NULL,
    any_cancel_30d                  TINYINT UNSIGNED NOT NULL,
    PRIMARY KEY (msno),
    INDEX idx_tx_registration_date (registration_date),
    INDEX idx_tx_source_date (registered_via, registration_date),
    CONSTRAINT fk_tx_user FOREIGN KEY (msno)
        REFERENCES new_user_anomaly_base (msno),
    CONSTRAINT chk_tx_has_transaction CHECK (has_transaction_30d IN (0, 1)),
    CONSTRAINT chk_tx_first_auto CHECK (first_is_auto_renew IS NULL OR first_is_auto_renew IN (0, 1)),
    CONSTRAINT chk_tx_any_auto CHECK (any_auto_renew_30d IN (0, 1)),
    CONSTRAINT chk_tx_any_cancel CHECK (any_cancel_30d IN (0, 1)),
    CONSTRAINT chk_tx_days CHECK (days_to_first_transaction IS NULL OR days_to_first_transaction BETWEEN 0 AND 30)
) ENGINE=InnoDB;

LOAD DATA LOCAL INFILE
  'data/processed/new_user_anomaly_base.csv'
INTO TABLE new_user_anomaly_base
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(
    @msno, @registration_date, @registration_month, @registered_via,
    @period_group, @first_active_date, @days_to_first_activity,
    @first_7d_active_days, @first_7d_total_secs, @first_7d_num_100,
    @d7_retained, @d30_retained
)
SET
    msno = @msno,
    registration_date = STR_TO_DATE(@registration_date, '%Y-%m-%d'),
    registration_month = @registration_month,
    registered_via = CAST(@registered_via AS UNSIGNED),
    period_group = @period_group,
    first_active_date = STR_TO_DATE(NULLIF(@first_active_date, ''), '%Y-%m-%d'),
    days_to_first_activity = CAST(NULLIF(@days_to_first_activity, '') AS UNSIGNED),
    first_7d_active_days = CAST(@first_7d_active_days AS UNSIGNED),
    first_7d_total_secs = CAST(@first_7d_total_secs AS DECIMAL(18,3)),
    first_7d_num_100 = CAST(@first_7d_num_100 AS UNSIGNED),
    d7_retained = CAST(@d7_retained AS UNSIGNED),
    d30_retained = CAST(TRIM(TRAILING '\r' FROM @d30_retained) AS UNSIGNED);

SHOW WARNINGS LIMIT 100;

LOAD DATA LOCAL INFILE
  'data/processed/new_user_transaction_features.csv'
INTO TABLE new_user_transaction_features
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(
    @msno, @registration_date, @registered_via, @has_transaction_30d,
    @transaction_count_30d, @paid_transaction_count_30d, @revenue_30d,
    @first_transaction_date, @days_to_first_transaction,
    @first_payment_plan_days, @first_actual_amount_paid,
    @first_is_auto_renew, @any_auto_renew_30d, @any_cancel_30d
)
SET
    msno = @msno,
    registration_date = STR_TO_DATE(@registration_date, '%Y-%m-%d'),
    registered_via = CAST(@registered_via AS UNSIGNED),
    has_transaction_30d = CAST(@has_transaction_30d AS UNSIGNED),
    transaction_count_30d = CAST(@transaction_count_30d AS UNSIGNED),
    paid_transaction_count_30d = CAST(@paid_transaction_count_30d AS UNSIGNED),
    revenue_30d = CAST(@revenue_30d AS DECIMAL(14,2)),
    first_transaction_date = STR_TO_DATE(NULLIF(@first_transaction_date, ''), '%Y-%m-%d'),
    days_to_first_transaction = CAST(NULLIF(@days_to_first_transaction, '') AS UNSIGNED),
    first_payment_plan_days = CAST(NULLIF(@first_payment_plan_days, '') AS UNSIGNED),
    first_actual_amount_paid = CAST(NULLIF(@first_actual_amount_paid, '') AS DECIMAL(12,2)),
    first_is_auto_renew = CAST(NULLIF(@first_is_auto_renew, '') AS UNSIGNED),
    any_auto_renew_30d = CAST(@any_auto_renew_30d AS UNSIGNED),
    any_cancel_30d = CAST(TRIM(TRAILING '\r' FROM @any_cancel_30d) AS UNSIGNED);

SHOW WARNINGS LIMIT 100;

/* Stop here if either actual_rows or unique_users differs from expected_rows. */
SELECT
    'new_user_anomaly_base' AS table_name,
    628250 AS expected_rows,
    COUNT(*) AS actual_rows,
    COUNT(DISTINCT msno) AS unique_users,
    COUNT(*) - COUNT(DISTINCT msno) AS duplicate_msno,
    MIN(registration_date) AS min_registration_date,
    MAX(registration_date) AS max_registration_date
FROM new_user_anomaly_base
UNION ALL
SELECT
    'new_user_transaction_features',
    213113,
    COUNT(*),
    COUNT(DISTINCT msno),
    COUNT(*) - COUNT(DISTINCT msno),
    MIN(registration_date),
    MAX(registration_date)
FROM new_user_transaction_features;

SELECT
    SUM(msno IS NULL) AS null_msno,
    SUM(registration_date IS NULL) AS null_registration_date,
    SUM(registration_month IS NULL) AS null_registration_month,
    SUM(registered_via IS NULL) AS null_registered_via,
    SUM(period_group IS NULL) AS null_period_group,
    SUM(first_active_date IS NULL) AS null_first_active_date,
    SUM(days_to_first_activity IS NULL) AS null_days_to_first_activity,
    SUM(first_7d_active_days IS NULL) AS null_first_7d_active_days,
    SUM(first_7d_total_secs IS NULL) AS null_first_7d_total_secs,
    SUM(first_7d_num_100 IS NULL) AS null_first_7d_num_100,
    SUM(d7_retained IS NULL) AS null_d7_retained,
    SUM(d30_retained IS NULL) AS null_d30_retained
FROM new_user_anomaly_base;

SELECT
    SUM(msno IS NULL) AS null_msno,
    SUM(registration_date IS NULL) AS null_registration_date,
    SUM(registered_via IS NULL) AS null_registered_via,
    SUM(has_transaction_30d IS NULL) AS null_has_transaction_30d,
    SUM(transaction_count_30d IS NULL) AS null_transaction_count_30d,
    SUM(paid_transaction_count_30d IS NULL) AS null_paid_transaction_count_30d,
    SUM(revenue_30d IS NULL) AS null_revenue_30d,
    SUM(first_transaction_date IS NULL) AS null_first_transaction_date,
    SUM(days_to_first_transaction IS NULL) AS null_days_to_first_transaction,
    SUM(first_payment_plan_days IS NULL) AS null_first_payment_plan_days,
    SUM(first_actual_amount_paid IS NULL) AS null_first_actual_amount_paid,
    SUM(first_is_auto_renew IS NULL) AS null_first_is_auto_renew,
    SUM(any_auto_renew_30d IS NULL) AS null_any_auto_renew_30d,
    SUM(any_cancel_30d IS NULL) AS null_any_cancel_30d
FROM new_user_transaction_features;

SELECT registered_via, COUNT(*) AS users
FROM new_user_anomaly_base
GROUP BY registered_via
ORDER BY registered_via;

SELECT registered_via, COUNT(*) AS users
FROM new_user_transaction_features
GROUP BY registered_via
ORDER BY registered_via;
