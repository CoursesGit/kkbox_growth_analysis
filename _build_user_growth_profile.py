import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"C:\Users\Administrator\Desktop\kkbox_growth_analysis")
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
OUT = ROOT / "outputs"
START = pd.Timestamp("2015-07-01")
AS_OF = pd.Timestamp("2015-10-16")

# One row per registered user in the approved analysis window.
members = pd.read_csv(
    RAW / "members_v3.csv",
    usecols=["msno", "registered_via", "registration_init_time"],
    dtype={"msno": "string", "registered_via": "Int16", "registration_init_time": "Int32"},
)
members["registration_date"] = pd.to_datetime(
    members["registration_init_time"].astype("string"), format="%Y%m%d", errors="coerce"
)
profile = (
    members.loc[
        members.registration_date.between(START, AS_OF),
        ["msno", "registration_date", "registered_via"],
    ]
    .sort_values(["registration_date", "msno"])
    .reset_index(drop=True)
)
if profile.msno.isna().any() or profile.msno.duplicated().any():
    raise ValueError("user_growth_profile grain violation: msno must be present and unique")

n = len(profile)
user_index = pd.Index(profile.msno)
reg_days = profile.registration_date.to_numpy(dtype="datetime64[D]")
as_of_day = np.datetime64(AS_OF.date(), "D")

activation_eligible = reg_days + np.timedelta64(6, "D") <= as_of_day
d1_eligible = reg_days + np.timedelta64(1, "D") <= as_of_day
d3_eligible = reg_days + np.timedelta64(3, "D") <= as_of_day
d7_eligible = reg_days + np.timedelta64(7, "D") <= as_of_day
first7_eligible = activation_eligible.copy()

activated = np.full(n, np.nan)
d1 = np.full(n, np.nan)
d3 = np.full(n, np.nan)
d7 = np.full(n, np.nan)
active_days = np.full(n, np.nan)
play_count = np.full(n, np.nan)
total_secs = np.full(n, np.nan)

activated[activation_eligible] = 0
d1[d1_eligible] = 0
d3[d3_eligible] = 0
d7[d7_eligible] = 0
active_days[first7_eligible] = 0
play_count[first7_eligible] = 0
total_secs[first7_eligible] = 0

negative_secs_used = 0
matched_log_rows = 0
first7_log_rows = 0
usecols = [
    "msno", "date", "num_25", "num_50", "num_75", "num_985", "num_100", "total_secs"
]
for chunk in pd.read_csv(
    RAW / "user_logs.csv",
    usecols=usecols,
    dtype={"msno": "string", "date": "Int32"},
    chunksize=1_000_000,
):
    chunk = chunk.loc[chunk.date.between(20150701, 20151016)]
    if chunk.empty:
        continue
    ids = user_index.get_indexer(chunk.msno)
    matched = ids >= 0
    if not matched.any():
        continue
    chunk = chunk.loc[matched].reset_index(drop=True)
    ids = ids[matched]
    matched_log_rows += len(chunk)
    log_days = pd.to_datetime(
        chunk.date.astype("string"), format="%Y%m%d", errors="raise"
    ).to_numpy(dtype="datetime64[D]")
    offsets = (log_days - reg_days[ids]).astype("timedelta64[D]").astype(np.int16)

    for target_day, values, eligibility in (
        (1, d1, d1_eligible), (3, d3, d3_eligible), (7, d7, d7_eligible)
    ):
        hit = offsets == target_day
        if hit.any():
            hit_ids = ids[hit]
            values[hit_ids[eligibility[hit_ids]]] = 1

    early = (offsets >= 0) & (offsets <= 6) & first7_eligible[ids]
    if early.any():
        early_ids = ids[early]
        first7_log_rows += int(early.sum())
        activated[early_ids] = 1
        np.add.at(active_days, early_ids, 1)
        plays = (
            chunk.loc[early, ["num_25", "num_50", "num_75", "num_985", "num_100"]]
            .fillna(0)
            .sum(axis=1)
            .to_numpy(dtype="float64")
        )
        np.add.at(play_count, early_ids, plays)
        secs = chunk.loc[early, "total_secs"].fillna(0).to_numpy(dtype="float64")
        negative_secs_used += int((secs < 0).sum())
        secs = np.where(secs < 0, 0, secs)
        np.add.at(total_secs, early_ids, secs)

profile["activated_flag"] = pd.array(activated, dtype="Int8")
profile["d1_retained"] = pd.array(d1, dtype="Int8")
profile["d3_retained"] = pd.array(d3, dtype="Int8")
profile["d7_retained"] = pd.array(d7, dtype="Int8")
profile["first_7_active_days"] = pd.array(active_days, dtype="Int8")
profile["first_7_play_count"] = pd.array(play_count, dtype="Int64")
profile["first_7_total_secs"] = pd.array(total_secs, dtype="Float64")
profile["activation_eligible_flag"] = pd.array(activation_eligible.astype(np.int8), dtype="Int8")
profile["d1_eligible_flag"] = pd.array(d1_eligible.astype(np.int8), dtype="Int8")
profile["d3_eligible_flag"] = pd.array(d3_eligible.astype(np.int8), dtype="Int8")
profile["d7_eligible_flag"] = pd.array(d7_eligible.astype(np.int8), dtype="Int8")
profile["first_7_eligible_flag"] = pd.array(first7_eligible.astype(np.int8), dtype="Int8")
profile["data_as_of_date"] = AS_OF

metric_pairs = [
    ("activated_flag", "activation_eligible_flag"),
    ("d1_retained", "d1_eligible_flag"),
    ("d3_retained", "d3_eligible_flag"),
    ("d7_retained", "d7_eligible_flag"),
    ("first_7_active_days", "first_7_eligible_flag"),
    ("first_7_play_count", "first_7_eligible_flag"),
    ("first_7_total_secs", "first_7_eligible_flag"),
]
null_rule_checks = {}
for metric, eligible in metric_pairs:
    bad_unobserved = int(profile.loc[profile[eligible].eq(0), metric].notna().sum())
    bad_observed = int(profile.loc[profile[eligible].eq(1), metric].isna().sum())
    null_rule_checks[metric] = {
        "non_null_when_ineligible": bad_unobserved,
        "null_when_eligible": bad_observed,
    }
    if bad_unobserved or bad_observed:
        raise ValueError(f"eligibility/null rule failed for {metric}")

invariants = {
    "rows": int(len(profile)),
    "unique_msno": int(profile.msno.nunique()),
    "duplicate_msno": int(profile.msno.duplicated().sum()),
    "registration_date_min": str(profile.registration_date.min().date()),
    "registration_date_max": str(profile.registration_date.max().date()),
    "matched_log_rows": matched_log_rows,
    "first7_log_rows": first7_log_rows,
    "negative_total_secs_set_to_zero": negative_secs_used,
    "active_days_out_of_range": int(
        ((profile.first_7_active_days < 0) | (profile.first_7_active_days > 7)).fillna(False).sum()
    ),
    "negative_output_play_count": int((profile.first_7_play_count < 0).fillna(False).sum()),
    "negative_output_total_secs": int((profile.first_7_total_secs < 0).fillna(False).sum()),
    "eligibility_counts": {
        col: int(profile[col].sum())
        for col in [
            "activation_eligible_flag", "d1_eligible_flag", "d3_eligible_flag",
            "d7_eligible_flag", "first_7_eligible_flag"
        ]
    },
    "null_rule_checks": null_rule_checks,
}
if invariants["active_days_out_of_range"] or invariants["negative_output_play_count"] or invariants["negative_output_total_secs"]:
    raise ValueError("profile invariant check failed")

schema = {
    "table": "user_growth_profile",
    "grain": "one row per msno",
    "analysis_window": {"start": str(START.date()), "end": str(AS_OF.date())},
    "columns": [
        {"name": c, "dtype": str(profile[c].dtype), "nullable": bool(profile[c].isna().any())}
        for c in profile.columns
    ],
    "metric_definitions": {
        "activated_flag": "1 if at least one log exists from Day0 through Day6; NULL if that window is immature",
        "d1_retained": "1 if a log exists exactly on registration_date + 1 day; NULL if immature",
        "d3_retained": "1 if a log exists exactly on registration_date + 3 days; NULL if immature",
        "d7_retained": "1 if a log exists exactly on registration_date + 7 days; NULL if immature",
        "first_7_active_days": "distinct active dates from Day0 through Day6; NULL if immature",
        "first_7_play_count": "Day0-Day6 sum of num_25 + num_50 + num_75 + num_985 + num_100; NULL if immature",
        "first_7_total_secs": "Day0-Day6 sum of total_secs with negative values replaced by zero; NULL if immature",
    },
}

PROCESSED.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)
profile.to_csv(PROCESSED / "user_growth_profile.csv", index=False, date_format="%Y-%m-%d")

# Reproducible mixed sample: random rows plus boundary dates where eligibility changes.
random_sample = profile.sample(n=20, random_state=20251016)
boundary_sample = profile.loc[
    profile.registration_date.isin(pd.to_datetime(["2015-10-09", "2015-10-10", "2015-10-13", "2015-10-15", "2015-10-16"]))
].groupby("registration_date", group_keys=False).head(2)
sample = pd.concat([random_sample, boundary_sample]).drop_duplicates("msno")
sample.to_csv(OUT / "user_growth_profile_validation_sample.csv", index=False, date_format="%Y-%m-%d")
(OUT / "user_growth_profile_schema.json").write_text(
    json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8"
)
(OUT / "user_growth_profile_validation.json").write_text(
    json.dumps(invariants, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(json.dumps(invariants, ensure_ascii=False, indent=2))
print(sample.to_string(index=False))
