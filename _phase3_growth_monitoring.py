import json
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\Administrator\Desktop\kkbox_growth_analysis")
PROFILE = ROOT / "data" / "processed" / "user_growth_profile.csv"
OUT = ROOT / "outputs"
START = pd.Timestamp("2015-07-01")
END = pd.Timestamp("2015-10-16")

# Phase 3 intentionally reads registration fields only.
users = pd.read_csv(
    PROFILE,
    usecols=["msno", "registration_date", "registered_via"],
    dtype={"msno": "string", "registered_via": "Int16"},
    parse_dates=["registration_date"],
)
users = users.loc[users.registration_date.between(START, END)].copy()
if users.msno.duplicated().any():
    raise ValueError("user_growth_profile must contain one row per msno")

calendar = pd.date_range(START, END, freq="D")
daily = (
    users.groupby("registration_date").msno.nunique()
    .reindex(calendar, fill_value=0)
    .rename("new_users")
    .rename_axis("registration_date")
    .reset_index()
)
daily["moving_avg_7d"] = daily.new_users.rolling(7, min_periods=1).mean()

source_counts = (
    users.groupby(["registration_date", "registered_via"]).msno.nunique()
    .rename("source_new_users")
    .reset_index()
)
source_counts = source_counts.merge(
    daily[["registration_date", "new_users"]].rename(columns={"new_users": "daily_new_users"}),
    on="registration_date",
    how="left",
)
source_counts["source_share"] = source_counts.source_new_users / source_counts.daily_new_users

periods = [
    ("Historical baseline", "2015-07-01", "2015-09-30"),
    ("Pre-break recent baseline", "2015-10-01", "2015-10-06"),
    ("Break date", "2015-10-07", "2015-10-07"),
    ("Post-break", "2015-10-08", "2015-10-16"),
    ("Break and post-break", "2015-10-07", "2015-10-16"),
]
summary_rows = []
for label, start, end in periods:
    start_ts, end_ts = pd.Timestamp(start), pd.Timestamp(end)
    d = daily.loc[daily.registration_date.between(start_ts, end_ts)]
    scoped_users = users.loc[users.registration_date.between(start_ts, end_ts)]
    s4 = int(scoped_users.registered_via.eq(4).sum())
    total = int(d.new_users.sum())
    days = int(len(d))
    summary_rows.append(
        {
            "period": label,
            "start_date": start,
            "end_date": end,
            "days": days,
            "new_users": total,
            "avg_daily_new_users": total / days,
            "std_daily_new_users": float(d.new_users.std(ddof=0)),
            "min_daily_new_users": int(d.new_users.min()),
            "max_daily_new_users": int(d.new_users.max()),
            "source4_new_users": s4,
            "avg_daily_source4_new_users": s4 / days,
            "source4_share": s4 / total,
            "non_source4_new_users": total - s4,
            "avg_daily_non_source4_new_users": (total - s4) / days,
        }
    )
period_summary = pd.DataFrame(summary_rows)

pre = period_summary.loc[period_summary.period.eq("Pre-break recent baseline")].iloc[0]
break_day = period_summary.loc[period_summary.period.eq("Break date")].iloc[0]
post = period_summary.loc[period_summary.period.eq("Post-break")].iloc[0]
break_post = period_summary.loc[period_summary.period.eq("Break and post-break")].iloc[0]

def compare(row):
    total_delta = row.avg_daily_new_users - pre.avg_daily_new_users
    s4_delta = row.avg_daily_source4_new_users - pre.avg_daily_source4_new_users
    return {
        "total_daily_delta": total_delta,
        "total_daily_pct_change": total_delta / pre.avg_daily_new_users,
        "source4_daily_delta": s4_delta,
        "source4_share_change_pp": (row.source4_share - pre.source4_share) * 100,
        "source4_increment_contribution": s4_delta / total_delta if total_delta else None,
        "non_source4_daily_delta": row.avg_daily_non_source4_new_users - pre.avg_daily_non_source4_new_users,
    }

october = daily.loc[daily.registration_date.between("2015-10-01", END)].copy()
october_s4 = source_counts.loc[source_counts.registered_via.eq(4), [
    "registration_date", "source_new_users", "source_share"
]].rename(columns={"source_new_users": "source4_new_users", "source_share": "source4_share"})
october = october.merge(october_s4, on="registration_date", how="left")
october[["source4_new_users", "source4_share"]] = october[["source4_new_users", "source4_share"]].fillna(0)

validation = {
    "analysis_window": {"start": str(START.date()), "end": str(END.date()), "days": len(daily)},
    "total_registered_users": int(daily.new_users.sum()),
    "overall_daily_statistics": {
        "mean": float(daily.new_users.mean()),
        "std_population": float(daily.new_users.std(ddof=0)),
        "median": float(daily.new_users.median()),
        "min": int(daily.new_users.min()),
        "min_date": str(daily.loc[daily.new_users.idxmin(), "registration_date"].date()),
        "max": int(daily.new_users.max()),
        "max_date": str(daily.loc[daily.new_users.idxmax(), "registration_date"].date()),
    },
    "break_date_vs_pre": compare(break_day),
    "post_break_vs_pre": compare(post),
    "break_and_post_vs_pre": compare(break_post),
    "persistence": {
        "post_break_days": int(len(october.loc[october.registration_date.between("2015-10-08", END)])),
        "post_break_days_above_pre_daily_average": int(
            october.loc[october.registration_date.between("2015-10-08", END), "new_users"]
            .gt(pre.avg_daily_new_users).sum()
        ),
        "post_break_source4_share_min": float(
            october.loc[october.registration_date.between("2015-10-08", END), "source4_share"].min()
        ),
        "post_break_source4_share_max": float(
            october.loc[october.registration_date.between("2015-10-08", END), "source4_share"].max()
        ),
    },
}

OUT.mkdir(parents=True, exist_ok=True)
daily.to_csv(OUT / "growth_daily_new_users.csv", index=False, date_format="%Y-%m-%d")
source_counts.to_csv(OUT / "growth_daily_source_mix.csv", index=False, date_format="%Y-%m-%d")
period_summary.to_csv(OUT / "growth_period_summary.csv", index=False)
october.to_csv(OUT / "growth_october_daily_validation.csv", index=False, date_format="%Y-%m-%d")
(OUT / "growth_monitoring_validation.json").write_text(
    json.dumps(validation, ensure_ascii=False, indent=2), encoding="utf-8"
)

chart_spec = """# Growth Monitoring chart specification

1. Daily New Users line chart
   - X: registration_date
   - Y: new_users
   - Overlay: moving_avg_7d
   - Reference line: 2015-10-07

2. Daily Registration Source Mix stacked area/column chart
   - X: registration_date
   - Legend: registered_via
   - Y: source_new_users
   - Highlight registered_via=4; do not assign a business channel name.

3. Source Mix 100% stacked column chart
   - X: registration_date
   - Legend: registered_via
   - Y: source_share
   - Reference line: 2015-10-07

4. October anomaly validation combo chart
   - Columns: daily_new_users and source4_new_users
   - Line: source4_share
   - Date range: 2015-10-01 through 2015-10-16

5. Period comparison chart
   - Compare 2015-10-01~06, 2015-10-07, and 2015-10-08~16
   - Metrics: avg_daily_new_users, avg_daily_source4_new_users, source4_share
"""
(OUT / "growth_monitoring_chart_spec.md").write_text(chart_spec, encoding="utf-8")

print(period_summary.to_string(index=False))
print(json.dumps(validation, ensure_ascii=False, indent=2))
