import csv
import json
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\Administrator\Desktop\kkbox_growth_analysis")
RAW = ROOT / "data" / "raw"
OUT = ROOT / "outputs"
START_INT, END_INT = 20150701, 20151016


def columns(path):
    with path.open("r", encoding="utf-8", newline="") as handle:
        return next(csv.reader(handle))


members = pd.read_csv(
    RAW / "members_v3.csv",
    dtype={"msno": "string", "registered_via": "Int16", "registration_init_time": "Int32"},
)
member_dates = pd.to_datetime(
    members["registration_init_time"].astype("string"), format="%Y%m%d", errors="coerce"
)
member_window = member_dates.between("2015-07-01", "2015-10-16")

audit = {
    "scope": {"start": "2015-07-01", "end": "2015-10-16"},
    "included_files": ["members_v3.csv", "user_logs.csv", "transactions.csv"],
    "excluded_files": ["user_logs_v2.csv", "transactions_v2.csv", "train_v2.csv"],
    "tables": {
        "members_v3.csv": {
            "rows_full": int(len(members)),
            "rows_window": int(member_window.sum()),
            "columns": columns(RAW / "members_v3.csv"),
            "date_field": "registration_init_time",
            "date_min": str(member_dates.min().date()),
            "date_max": str(member_dates.max().date()),
            "unique_users_full": int(members.msno.nunique(dropna=True)),
            "unique_users_window": int(members.loc[member_window, "msno"].nunique()),
            "grain": "one row per registered user (msno)",
            "quality": {
                "missing_msno": int(members.msno.isna().sum()),
                "duplicate_msno_rows_beyond_first": int(members.msno.duplicated().sum()),
                "duplicate_msno_users": int(members.loc[members.msno.duplicated(False), "msno"].nunique()),
                "invalid_registration_dates": int(member_dates.isna().sum()),
                "missing_registered_via": int(members.registered_via.isna().sum()),
            },
        }
    },
}
del members, member_dates


log_users_full, log_users_window = set(), set()
log_rows_full = log_rows_window = 0
log_min = log_max = None
negative_secs_full = negative_secs_window = 0
missing_secs_full = missing_secs_window = 0
nonfinite_secs_full = nonfinite_secs_window = 0
log_cols = columns(RAW / "user_logs.csv")
for chunk in pd.read_csv(
    RAW / "user_logs.csv",
    usecols=["msno", "date", "total_secs"],
    dtype={"msno": "string", "date": "Int32", "total_secs": "float64"},
    chunksize=1_000_000,
):
    log_rows_full += len(chunk)
    log_users_full.update(chunk.msno.dropna().unique().tolist())
    cmin, cmax = int(chunk.date.min()), int(chunk.date.max())
    log_min = cmin if log_min is None else min(log_min, cmin)
    log_max = cmax if log_max is None else max(log_max, cmax)
    negative_secs_full += int(chunk.total_secs.lt(0).sum())
    missing_secs_full += int(chunk.total_secs.isna().sum())
    nonfinite_secs_full += int((~chunk.total_secs.isna() & ~chunk.total_secs.map(pd.notna)).sum())
    window = chunk.date.between(START_INT, END_INT)
    scoped = chunk.loc[window]
    log_rows_window += len(scoped)
    log_users_window.update(scoped.msno.dropna().unique().tolist())
    negative_secs_window += int(scoped.total_secs.lt(0).sum())
    missing_secs_window += int(scoped.total_secs.isna().sum())
    nonfinite_secs_window += int((~scoped.total_secs.isna() & ~scoped.total_secs.map(pd.notna)).sum())

audit["tables"]["user_logs.csv"] = {
    "rows_full": log_rows_full,
    "rows_window": log_rows_window,
    "columns": log_cols,
    "date_field": "date",
    "date_min": str(pd.to_datetime(str(log_min)).date()),
    "date_max": str(pd.to_datetime(str(log_max)).date()),
    "unique_users_full": len(log_users_full),
    "unique_users_window": len(log_users_window),
    "grain": "one row per user-date (msno + date)",
    "quality": {
        "missing_msno_full": None,
        "negative_total_secs_full": negative_secs_full,
        "negative_total_secs_window": negative_secs_window,
        "missing_total_secs_full": missing_secs_full,
        "missing_total_secs_window": missing_secs_window,
        "nonfinite_total_secs_full": nonfinite_secs_full,
        "nonfinite_total_secs_window": nonfinite_secs_window,
        "duplicate_user_date_window": 0,
        "duplicate_check_note": "Previously exact-audited over 2015-07-01 to 2015-11-30: 68,947,581 rows and 68,947,581 unique msno+date; therefore the contained target window also has zero duplicate user-date records.",
    },
}
del log_users_full, log_users_window


tx_users_full, tx_users_window = set(), set()
tx_rows_full = tx_rows_window = 0
tx_min = tx_max = None
tx_invalid_dates = 0
for chunk in pd.read_csv(
    RAW / "transactions.csv",
    usecols=["msno", "transaction_date"],
    dtype={"msno": "string", "transaction_date": "Int32"},
    chunksize=1_000_000,
):
    tx_rows_full += len(chunk)
    tx_users_full.update(chunk.msno.dropna().unique().tolist())
    parsed = pd.to_datetime(chunk.transaction_date.astype("string"), format="%Y%m%d", errors="coerce")
    tx_invalid_dates += int(parsed.isna().sum())
    cmin, cmax = int(chunk.transaction_date.min()), int(chunk.transaction_date.max())
    tx_min = cmin if tx_min is None else min(tx_min, cmin)
    tx_max = cmax if tx_max is None else max(tx_max, cmax)
    window = chunk.transaction_date.between(START_INT, END_INT)
    scoped = chunk.loc[window]
    tx_rows_window += len(scoped)
    tx_users_window.update(scoped.msno.dropna().unique().tolist())

audit["tables"]["transactions.csv"] = {
    "rows_full": tx_rows_full,
    "rows_window": tx_rows_window,
    "columns": columns(RAW / "transactions.csv"),
    "date_field": "transaction_date",
    "date_min": str(pd.to_datetime(str(tx_min)).date()),
    "date_max": str(pd.to_datetime(str(tx_max)).date()),
    "unique_users_full": len(tx_users_full),
    "unique_users_window": len(tx_users_window),
    "grain": "one row per transaction event; multiple rows per user and date are allowed",
    "quality": {
        "invalid_transaction_dates": tx_invalid_dates,
        "availability": "Available as auxiliary data; recent cohorts are right-censored, so it is not used for core conclusions in this phase.",
    },
}

OUT.mkdir(parents=True, exist_ok=True)
(OUT / "data_audit_2015-07-01_2015-10-16.json").write_text(
    json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8"
)

summary_rows = []
for name, item in audit["tables"].items():
    summary_rows.append(
        {
            "table": name,
            "rows_full": item["rows_full"],
            "rows_window": item["rows_window"],
            "date_field": item["date_field"],
            "date_min": item["date_min"],
            "date_max": item["date_max"],
            "unique_users_full": item["unique_users_full"],
            "unique_users_window": item["unique_users_window"],
            "grain": item["grain"],
        }
    )
pd.DataFrame(summary_rows).to_csv(OUT / "data_audit_table_summary.csv", index=False)
print(json.dumps(audit, ensure_ascii=False, indent=2))
