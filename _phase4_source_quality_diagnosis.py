import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"C:\Users\Administrator\Desktop\kkbox_growth_analysis")
PROFILE = ROOT / "data" / "processed" / "user_growth_profile.csv"
OUT = ROOT / "outputs"
MAIN_SOURCES = [3, 4, 7, 9]

cols = [
    "msno", "registration_date", "registered_via",
    "activated_flag", "d1_retained", "d3_retained", "d7_retained",
    "first_7_active_days", "first_7_play_count", "first_7_total_secs",
    "activation_eligible_flag", "d1_eligible_flag", "d3_eligible_flag",
    "d7_eligible_flag", "first_7_eligible_flag",
]
profile = pd.read_csv(
    PROFILE,
    usecols=cols,
    dtype={"msno": "string", "registered_via": "Int16"},
    parse_dates=["registration_date"],
)
if profile.msno.duplicated().any():
    raise ValueError("user_growth_profile grain violation")

historical = profile.loc[profile.registration_date.le("2015-10-09")].copy()
post = historical.loc[historical.registration_date.between("2015-10-07", "2015-10-09")].copy()


def sample_summary(df, scope):
    rows = []
    for source, group in df.groupby("registered_via", dropna=False):
        rows.append({
            "scope": scope,
            "registered_via": int(source),
            "users": int(len(group)),
            "activation_eligible_users": int(group.activation_eligible_flag.sum()),
            "d1_eligible_users": int(group.d1_eligible_flag.sum()),
            "d3_eligible_users": int(group.d3_eligible_flag.sum()),
            "d7_eligible_users": int(group.d7_eligible_flag.sum()),
            "first_7_eligible_users": int(group.first_7_eligible_flag.sum()),
        })
    return pd.DataFrame(rows)


def quality_summary(df, scope):
    rows = []
    for source, group in df.loc[df.registered_via.isin(MAIN_SOURCES)].groupby("registered_via"):
        activation = group.loc[group.activation_eligible_flag.eq(1), "activated_flag"]
        d1 = group.loc[group.d1_eligible_flag.eq(1), "d1_retained"]
        d3 = group.loc[group.d3_eligible_flag.eq(1), "d3_retained"]
        d7 = group.loc[group.d7_eligible_flag.eq(1), "d7_retained"]
        first7 = group.loc[group.first_7_eligible_flag.eq(1)]
        rows.append({
            "scope": scope,
            "registered_via": int(source),
            "users": int(len(group)),
            "activation_n": int(len(activation)),
            "activation_users": int(activation.sum()),
            "activation_rate": float(activation.mean()),
            "d1_n": int(len(d1)),
            "d1_retained_users": int(d1.sum()),
            "d1_retention": float(d1.mean()),
            "d3_n": int(len(d3)),
            "d3_retained_users": int(d3.sum()),
            "d3_retention": float(d3.mean()),
            "d7_n": int(len(d7)),
            "d7_retained_users": int(d7.sum()),
            "d7_retention": float(d7.mean()),
            "first_7_n": int(len(first7)),
            "avg_first_7_active_days": float(first7.first_7_active_days.mean()),
            "avg_first_7_play_count": float(first7.first_7_play_count.mean()),
            "avg_first_7_total_secs": float(first7.first_7_total_secs.mean()),
            "median_first_7_active_days": float(first7.first_7_active_days.median()),
            "median_first_7_play_count": float(first7.first_7_play_count.median()),
            "median_first_7_total_secs": float(first7.first_7_total_secs.median()),
        })
    return pd.DataFrame(rows).sort_values("registered_via")


samples = pd.concat([
    sample_summary(historical, "historical_mature_2015-07-01_to_2015-10-09"),
    sample_summary(post, "post_anomaly_cohort_2015-10-07_to_2015-10-09"),
], ignore_index=True)
quality_historical = quality_summary(
    historical, "historical_mature_2015-07-01_to_2015-10-09"
)
quality_post = quality_summary(
    post, "post_anomaly_cohort_2015-10-07_to_2015-10-09"
)


def two_proportion_test(x1, n1, x2, n2):
    p1, p2 = x1 / n1, x2 / n2
    diff = p1 - p2
    se_diff = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    low, high = diff - 1.95996398454 * se_diff, diff + 1.95996398454 * se_diff
    pooled = (x1 + x2) / (n1 + n2)
    se_null = math.sqrt(pooled * (1 - pooled) * (1 / n1 + 1 / n2))
    z = diff / se_null if se_null else 0.0
    pvalue = math.erfc(abs(z) / math.sqrt(2))
    return p1, p2, diff, low, high, z, pvalue


test_rows = []
for scope, q in [("historical_mature", quality_historical), ("post_anomaly_cohort", quality_post)]:
    s4 = q.loc[q.registered_via.eq(4)].iloc[0]
    for comparator in [3, 7, 9]:
        other = q.loc[q.registered_via.eq(comparator)].iloc[0]
        result = two_proportion_test(
            int(s4.d7_retained_users), int(s4.d7_n),
            int(other.d7_retained_users), int(other.d7_n),
        )
        test_rows.append({
            "scope": scope,
            "comparison": f"Source4 - Source{comparator}",
            "source4_retained": int(s4.d7_retained_users),
            "source4_n": int(s4.d7_n),
            "comparator_retained": int(other.d7_retained_users),
            "comparator_n": int(other.d7_n),
            "source4_d7": result[0],
            "comparator_d7": result[1],
            "difference": result[2],
            "difference_pp": result[2] * 100,
            "ci95_low": result[3],
            "ci95_high": result[4],
            "ci95_low_pp": result[3] * 100,
            "ci95_high_pp": result[4] * 100,
            "z_stat": result[5],
            "p_value_two_sided": result[6],
        })

    other_group = historical if scope == "historical_mature" else post
    other_group = other_group.loc[other_group.registered_via.isin([3, 7, 9]) & other_group.d7_eligible_flag.eq(1)]
    result = two_proportion_test(
        int(s4.d7_retained_users), int(s4.d7_n),
        int(other_group.d7_retained.sum()), int(len(other_group)),
    )
    test_rows.append({
        "scope": scope,
        "comparison": "Source4 - pooled Source3/7/9",
        "source4_retained": int(s4.d7_retained_users),
        "source4_n": int(s4.d7_n),
        "comparator_retained": int(other_group.d7_retained.sum()),
        "comparator_n": int(len(other_group)),
        "source4_d7": result[0], "comparator_d7": result[1],
        "difference": result[2], "difference_pp": result[2] * 100,
        "ci95_low": result[3], "ci95_high": result[4],
        "ci95_low_pp": result[3] * 100, "ci95_high_pp": result[4] * 100,
        "z_stat": result[5], "p_value_two_sided": result[6],
    })

tests = pd.DataFrame(test_rows)

validation = {
    "historical_mature_users": int(len(historical)),
    "post_anomaly_cohort_users_all_sources": int(len(post)),
    "post_anomaly_source4_users": int(post.registered_via.eq(4).sum()),
    "all_historical_rows_d7_eligible": bool(historical.d7_eligible_flag.eq(1).all()),
    "all_post_rows_d7_eligible": bool(post.d7_eligible_flag.eq(1).all()),
    "main_sources": MAIN_SOURCES,
    "statistical_method": "Two-sided pooled two-proportion z test; unpooled Wald 95% confidence interval for p(Source4)-p(comparator).",
}

OUT.mkdir(parents=True, exist_ok=True)
samples.to_csv(OUT / "quality_sample_definition.csv", index=False)
quality_historical.to_csv(OUT / "quality_metrics_historical_mature.csv", index=False)
quality_post.to_csv(OUT / "quality_metrics_post_anomaly_cohort.csv", index=False)
tests.to_csv(OUT / "quality_d7_proportion_tests.csv", index=False)
(OUT / "quality_diagnosis_validation.json").write_text(
    json.dumps(validation, ensure_ascii=False, indent=2), encoding="utf-8"
)

print("SAMPLE DEFINITIONS")
print(samples.loc[samples.registered_via.isin(MAIN_SOURCES)].to_string(index=False))
print("\nHISTORICAL MATURE QUALITY")
print(quality_historical.to_string(index=False))
print("\nPOST-ANOMALY COHORT QUALITY")
print(quality_post.to_string(index=False))
print("\nD7 TESTS")
print(tests.to_string(index=False))
print("\nVALIDATION")
print(json.dumps(validation, ensure_ascii=False, indent=2))
