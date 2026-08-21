from pathlib import Path
import nbformat as nbf

ROOT = Path(r"C:\Users\Administrator\Desktop\kkbox_growth_analysis")
NB = ROOT / "notebooks"
NB.mkdir(parents=True, exist_ok=True)


def md(text):
    return nbf.v4.new_markdown_cell(text.strip() + "\n")


def code(text):
    return nbf.v4.new_code_cell(text.strip() + "\n")


def write(name, cells):
    nb = nbf.v4.new_notebook()
    nb["cells"] = cells
    nb["metadata"]["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
    nb["metadata"]["language_info"] = {"name": "python", "version": "3"}
    nbf.write(nb, NB / name)


common_setup = r'''
from pathlib import Path
import json
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

PROJECT_ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
AS_OF_DATE = pd.Timestamp("2015-10-16")
ANALYSIS_START = pd.Timestamp("2015-07-01")
pd.set_option("display.max_columns", 50)
'''


write("00_Business_Context.ipynb", [
    md('''
# 00 Business Context

## Business Question

近期新增用户增长是否健康？新增规模或来源结构发生异常后，哪类用户贡献了主要变化，该类用户是否存在短期留存和首周使用风险？

## Analysis Objective

模拟2015年10月中旬订阅制音乐平台增长分析场景。使用2015-07-01至2015-10-16数据监控新增用户、定位来源结构异常、评估目标来源用户质量，并提出可验证的产品实验方案。

本项目不从D30下降开始，不分析Source 4长期价值，也不包含真实实验结果。

## Data Used

- `members_v3.csv`：用户注册日期及匿名注册来源。
- `user_logs.csv`：用户活动、精确日留存及首周播放行为。
- `transactions.csv`：辅助数据，不用于核心结论。
- `data/processed/user_growth_profile.csv`：本项目主要用户级分析底表，一行一个`msno`。

排除：`user_logs_v2.csv`、`transactions_v2.csv`、`train_v2.csv`。

## Key Metrics

- Daily New Users：按注册日期统计唯一新增用户。
- Source Mix：每日各`registered_via`人数及占比。
- Activation：Day0–Day6至少存在一个活动日志。
- D1/D3/D7 Retention：注册后第1/3/7个自然日存在活动。
- First 7 Active Days：Day0–Day6活跃日期数。
- First 7 Play Count：Day0–Day6五档播放次数合计。
- First 7 Total Seconds：Day0–Day6播放时长，负值按0累计。
- D30 Retention：仅作为未来实验长期验证指标。
'''),
    md('''
## Analysis Chain

1. Data Audit：确认数据范围、质量、字段和观察窗口。
2. Growth Monitoring：发现2015-10-07新增规模和来源结构异常。
3. Source Diagnosis：确认`registered_via=4`贡献主要新增增量，并核查数据口径风险。
4. User Quality Diagnosis：比较Source 4与同期Source 3/7/9的Activation、D1/D3/D7和首周使用深度。
5. Hypothesis & A/B Test：提出H1/H2/H3，选择H2作为优先验证方向并设计随机实验。

## Observation-window Rules

数据截止日固定为2015-10-16。未成熟指标必须为NULL：

| Metric | Last eligible registration date |
|---|---|
| D1 | 2015-10-15 |
| D3 | 2015-10-13 |
| Activation / First 7 Days | 2015-10-10 |
| D7 | 2015-10-09 |
| D30 | 当前不用于历史分析证据 |

## Interpretation Boundaries

- `registered_via=4`只能称为Source 4或`registered_via=4`来源用户，不能命名为广告渠道。
- 行为差异是观察性证据，不是产品或渠道动作的因果证明。
- “首次体验承接不足”是待验证假设，不是已确认原因。
- 当前没有assignment、exposure或实验结果数据。
''')
])


write("01_Data_Audit.ipynb", [
    md('''
# 01 Data Audit

## Business Question

原始数据的范围、字段、日期、用户覆盖和业务粒度是否足以支持截至2015-10-16的增长分析？

## Analysis Objective

复核Phase 2已经完成的原始数据审计，确认Members主键、注册日期、来源字段、用户日日志粒度、负播放时长和交易表可用性。本Notebook读取已生成审计产物，不重新扫描大型原始日志。

## Data Used

- `outputs/data_audit_table_summary.csv`
- `outputs/data_audit_2015-07-01_2015-10-16.json`
- `outputs/user_growth_profile_validation.json`

## Key Metrics

- 表行数、字段、日期范围、唯一用户数和数据粒度。
- Members：重复`msno`、无效注册日期、缺失`registered_via`。
- Logs：用户覆盖、负`total_secs`、缺失值、重复`msno+date`。
- Transactions：日期及用户覆盖，仅确认辅助可用性。
'''),
    code(common_setup),
    code('''
audit_summary = pd.read_csv(OUTPUTS_DIR / "data_audit_table_summary.csv")
audit = json.loads((OUTPUTS_DIR / "data_audit_2015-07-01_2015-10-16.json").read_text(encoding="utf-8"))
profile_validation = json.loads((OUTPUTS_DIR / "user_growth_profile_validation.json").read_text(encoding="utf-8"))
display(audit_summary)
'''),
    md('''
## Table Structure and Grain

- `members_v3.csv`：一行一个注册用户，`msno`为用户主键。
- `user_logs.csv`：一行一个用户日，业务键为`msno + date`。
- `transactions.csv`：一行一笔交易，同一用户同日可以存在多笔交易。
'''),
    code('''
quality_rows = []
for table_name, table in audit["tables"].items():
    for check, value in table.get("quality", {}).items():
        quality_rows.append({"table": table_name, "check": check, "value": value})
quality_checks = pd.DataFrame(quality_rows)
display(quality_checks)
'''),
    md('''
## User-growth Profile Validation

底表必须保持一行一个`msno`；未成熟行为指标为NULL，成熟但未发生行为才为0。
'''),
    code('''
profile_validation_summary = pd.DataFrame({
    "check": ["rows", "unique_msno", "duplicate_msno", "registration_date_min", "registration_date_max",
              "negative_total_secs_set_to_zero", "active_days_out_of_range",
              "negative_output_play_count", "negative_output_total_secs"],
    "value": [profile_validation[k] for k in ["rows", "unique_msno", "duplicate_msno",
              "registration_date_min", "registration_date_max", "negative_total_secs_set_to_zero",
              "active_days_out_of_range", "negative_output_play_count", "negative_output_total_secs"]]
})
display(profile_validation_summary)
assert profile_validation["rows"] == profile_validation["unique_msno"]
assert profile_validation["duplicate_msno"] == 0
assert all(v["non_null_when_ineligible"] == 0 and v["null_when_eligible"] == 0
           for v in profile_validation["null_rule_checks"].values())
'''),
    md('''
## Data-quality Conclusion

三张保留表可用于后续分析。Members主键、注册日期及来源字段通过检查；目标窗口日志无重复用户日。负`total_secs`只在时长累计时按0处理，不删除对应活跃日志。Transactions仅保留辅助用途。该结论不涉及新增异常或用户质量判断。
''')
])


write("02_Growth_Monitoring.ipynb", [
    md('''
# 02 Growth Monitoring

## Business Question

2015年7月至10月的新增用户规模是否发生明显且持续的异常变化？

## Analysis Objective

计算每日新增、7日移动平均和每日Source Mix，定位变化日期并验证异常是否持续。本Notebook只回答“发生了什么”，不分析用户质量或原因。

## Data Used

- `data/processed/user_growth_profile.csv`
- 仅使用`msno`、`registration_date`、`registered_via`。

## Key Metrics

- Daily New Users。
- 7-day Moving Average。
- 各Source每日新增人数及占比。
- 异常前、断点日和异常后日均新增。
'''),
    code(common_setup),
    code('''
users = pd.read_csv(
    PROCESSED_DIR / "user_growth_profile.csv",
    usecols=["msno", "registration_date", "registered_via"],
    dtype={"msno": "string", "registered_via": "Int16"},
    parse_dates=["registration_date"],
)
assert users.msno.is_unique
calendar = pd.date_range(ANALYSIS_START, AS_OF_DATE)
daily = (users.groupby("registration_date").msno.nunique()
         .reindex(calendar, fill_value=0).rename("new_users")
         .rename_axis("registration_date").reset_index())
daily["moving_avg_7d"] = daily.new_users.rolling(7, min_periods=1).mean()
daily.head()
'''),
    code('''
source_mix = (users.groupby(["registration_date", "registered_via"]).msno.nunique()
              .rename("source_new_users").reset_index())
source_mix = source_mix.merge(
    daily[["registration_date", "new_users"]].rename(columns={"new_users": "daily_new_users"}),
    on="registration_date", how="left")
source_mix["source_share"] = source_mix.source_new_users / source_mix.daily_new_users
source_mix.head()
'''),
    code('''
periods = [
    ("Historical baseline", "2015-07-01", "2015-09-30"),
    ("Pre-break", "2015-10-01", "2015-10-06"),
    ("Break date", "2015-10-07", "2015-10-07"),
    ("Post-break", "2015-10-08", "2015-10-16"),
]
period_summary = []
for label, start, end in periods:
    frame = daily[daily.registration_date.between(start, end)]
    period_summary.append({
        "period": label, "days": len(frame), "new_users": int(frame.new_users.sum()),
        "avg_daily_new_users": frame.new_users.mean(),
        "std_daily_new_users": frame.new_users.std(ddof=0),
        "min_daily_new_users": int(frame.new_users.min()),
        "max_daily_new_users": int(frame.new_users.max()),
    })
period_summary = pd.DataFrame(period_summary)
display(period_summary)
'''),
    code('''
fig, ax = plt.subplots(figsize=(12, 4.5))
ax.plot(daily.registration_date, daily.new_users, label="Daily New Users", linewidth=1.2)
ax.plot(daily.registration_date, daily.moving_avg_7d, label="7-day Moving Average", linewidth=2)
ax.axvline(pd.Timestamp("2015-10-07"), color="tab:red", linestyle="--", label="2015-10-07")
ax.set(title="Daily New Users | 2015-07-01 to 2015-10-16", xlabel="Registration Date", ylabel="New Users")
ax.grid(alpha=.25); ax.legend(); fig.tight_layout(); plt.show()
'''),
    code('''
oct_source = source_mix[source_mix.registration_date.ge("2015-10-01")]
pivot = oct_source.pivot(index="registration_date", columns="registered_via", values="source_new_users").fillna(0)
fig, ax = plt.subplots(figsize=(12, 4.5))
pivot.plot.area(ax=ax, stacked=True)
ax.axvline(pd.Timestamp("2015-10-07"), color="black", linestyle="--")
ax.set(title="Daily Registration Source Mix", xlabel="Registration Date", ylabel="New Users")
fig.tight_layout(); plt.show()
'''),
    md('''
## Monitoring Conclusion

2015-10-07新增规模出现明显变化；2015-10-08至2015-10-16继续维持高位，因此不是单日峰值。同期注册来源结构出现离散变化。本章不解释变化原因，也不评价Source 4用户质量。
''')
])


write("03_Source_Diagnosis.ipynb", [
    md('''
# 03 Source Diagnosis

## Business Question

哪个匿名注册来源贡献了2015-10-07后的主要新增变化？该变化是否可能受到数据口径影响？

## Analysis Objective

比较异常前后各`registered_via`的新增人数、占比和增量贡献，验证Source 4是否成为主要新增来源。本Notebook进行结构贡献分析，不解释具体业务原因。

## Data Used

- `data/processed/user_growth_profile.csv`
- `outputs/growth_daily_new_users.csv`
- `outputs/growth_daily_source_mix.csv`

## Key Metrics

- 各Source新增用户数、日均新增及占比。
- Source 4绝对增量和净增长贡献率。
- 非Source 4新增趋势。
- 10月7日至16日Source 4占比范围。
'''),
    code(common_setup),
    code('''
users = pd.read_csv(
    PROCESSED_DIR / "user_growth_profile.csv",
    usecols=["msno", "registration_date", "registered_via"],
    dtype={"msno": "string", "registered_via": "Int16"},
    parse_dates=["registration_date"],
)
assert users.msno.is_unique
'''),
    code('''
periods = [
    ("Historical baseline", "2015-07-01", "2015-09-30"),
    ("Pre-break", "2015-10-01", "2015-10-06"),
    ("Break date", "2015-10-07", "2015-10-07"),
    ("Post-break", "2015-10-08", "2015-10-16"),
]
rows = []
for label, start, end in periods:
    frame = users[users.registration_date.between(start, end)]
    days = (pd.Timestamp(end) - pd.Timestamp(start)).days + 1
    for source, group in frame.groupby("registered_via"):
        rows.append({"period": label, "registered_via": int(source), "users": len(group),
                     "avg_daily_users": len(group) / days, "source_share": len(group) / len(frame)})
source_period = pd.DataFrame(rows)
display(source_period[source_period.registered_via.isin([3, 4, 7, 9])])
'''),
    code('''
summary = []
for label, start, end in periods[1:]:
    frame = users[users.registration_date.between(start, end)]
    days = (pd.Timestamp(end) - pd.Timestamp(start)).days + 1
    s4 = int(frame.registered_via.eq(4).sum())
    summary.append({"period": label, "days": days, "total_users": len(frame),
                    "avg_daily_total": len(frame) / days, "source4_users": s4,
                    "avg_daily_source4": s4 / days, "source4_share": s4 / len(frame),
                    "avg_daily_non_source4": (len(frame) - s4) / days})
diagnosis = pd.DataFrame(summary)
pre = diagnosis.iloc[0]
diagnosis["total_daily_delta_vs_pre"] = diagnosis.avg_daily_total - pre.avg_daily_total
diagnosis["source4_daily_delta_vs_pre"] = diagnosis.avg_daily_source4 - pre.avg_daily_source4
diagnosis["source4_increment_contribution"] = (
    diagnosis.source4_daily_delta_vs_pre / diagnosis.total_daily_delta_vs_pre.replace(0, np.nan))
display(diagnosis)
'''),
    code('''
daily = users.groupby("registration_date").size().rename("total_users").reset_index()
s4_daily = users[users.registered_via.eq(4)].groupby("registration_date").size().rename("source4_users").reset_index()
daily = daily.merge(s4_daily, on="registration_date", how="left").fillna({"source4_users": 0})
daily["non_source4_users"] = daily.total_users - daily.source4_users
daily["source4_share"] = daily.source4_users / daily.total_users
display(daily[daily.registration_date.between("2015-10-01", "2015-10-16")])
'''),
    md('''
## Data-definition Risk Check

在解释Source 4之前，业务侧需要核查：

- `registered_via`映射或编码规则是否在10月7日变化；
- 是否存在注册入口重分类；
- 是否存在批量用户迁移或补录；
- 是否存在埋点或产品版本变更；
- Source 4是否代表真实新增用户群。

公开数据不能回答这些问题。

## Source Diagnosis Conclusion

Source 4在异常前属于小规模来源，10月7日后成为主要新增来源并贡献主要新增增量。该结论是注册结构的描述性分解，不能将Source 4直接解释为广告渠道，也不证明具体业务原因。
''')
])


write("04_User_Quality_Diagnosis.ipynb", [
    md('''
# 04 User Quality Diagnosis

## Business Question

Source 4成为主要新增来源后，其Activation、短期留存和首周使用深度是否与同期主要来源存在差异？

## Analysis Objective

分别检查历史成熟用户和2015-10-07至2015-10-09同期成熟cohort，比较Source 4与Source 3/7/9，并使用两比例检验评估D7差异。本章只描述数据观察，不解释原因。

## Data Used

- `data/processed/user_growth_profile.csv`

## Key Metrics

- Activation Rate。
- D1/D3/D7 Retention。
- First 7 Active Days。
- First 7 Play Count。
- First 7 Total Seconds。
- D7差异、95%置信区间和双侧两比例z检验。
'''),
    code(common_setup),
    code('''
columns = ["msno", "registration_date", "registered_via", "activated_flag", "d1_retained",
           "d3_retained", "d7_retained", "first_7_active_days", "first_7_play_count",
           "first_7_total_secs", "activation_eligible_flag", "d1_eligible_flag",
           "d3_eligible_flag", "d7_eligible_flag", "first_7_eligible_flag"]
profile = pd.read_csv(PROCESSED_DIR / "user_growth_profile.csv", usecols=columns,
                      dtype={"msno": "string", "registered_via": "Int16"},
                      parse_dates=["registration_date"])
assert profile.msno.is_unique
historical = profile[profile.registration_date.le("2015-10-09")].copy()
post = historical[historical.registration_date.between("2015-10-07", "2015-10-09")].copy()
print(f"Historical mature users: {len(historical):,}")
print(f"Post-anomaly mature users: {len(post):,}")
'''),
    code('''
def quality_summary(frame, scope):
    rows = []
    for source, group in frame[frame.registered_via.isin([3, 4, 7, 9])].groupby("registered_via"):
        rows.append({
            "scope": scope, "registered_via": int(source), "users": len(group),
            "activation_n": int(group.activation_eligible_flag.sum()),
            "activation_rate": group.loc[group.activation_eligible_flag.eq(1), "activated_flag"].mean(),
            "d1_n": int(group.d1_eligible_flag.sum()),
            "d1_retention": group.loc[group.d1_eligible_flag.eq(1), "d1_retained"].mean(),
            "d3_n": int(group.d3_eligible_flag.sum()),
            "d3_retention": group.loc[group.d3_eligible_flag.eq(1), "d3_retained"].mean(),
            "d7_n": int(group.d7_eligible_flag.sum()),
            "d7_retained_users": int(group.loc[group.d7_eligible_flag.eq(1), "d7_retained"].sum()),
            "d7_retention": group.loc[group.d7_eligible_flag.eq(1), "d7_retained"].mean(),
            "first_7_n": int(group.first_7_eligible_flag.sum()),
            "avg_first_7_active_days": group.loc[group.first_7_eligible_flag.eq(1), "first_7_active_days"].mean(),
            "avg_first_7_play_count": group.loc[group.first_7_eligible_flag.eq(1), "first_7_play_count"].mean(),
            "avg_first_7_total_secs": group.loc[group.first_7_eligible_flag.eq(1), "first_7_total_secs"].mean(),
        })
    return pd.DataFrame(rows)

historical_quality = quality_summary(historical, "historical_mature")
post_quality = quality_summary(post, "post_anomaly_2015-10-07_to_09")
display(historical_quality)
display(post_quality)
'''),
    code('''
def two_proportion_test(x1, n1, x2, n2):
    p1, p2 = x1/n1, x2/n2
    diff = p1 - p2
    se_diff = math.sqrt(p1*(1-p1)/n1 + p2*(1-p2)/n2)
    ci = (diff - 1.95996398454*se_diff, diff + 1.95996398454*se_diff)
    pooled = (x1+x2)/(n1+n2)
    se_null = math.sqrt(pooled*(1-pooled)*(1/n1+1/n2))
    z = diff/se_null
    p_value = math.erfc(abs(z)/math.sqrt(2))
    return diff, ci[0], ci[1], z, p_value

s4 = post_quality[post_quality.registered_via.eq(4)].iloc[0]
tests = []
for comparator in [3, 7, 9]:
    other = post_quality[post_quality.registered_via.eq(comparator)].iloc[0]
    result = two_proportion_test(int(s4.d7_retained_users), int(s4.d7_n),
                                 int(other.d7_retained_users), int(other.d7_n))
    tests.append({"comparison": f"Source4 - Source{comparator}", "difference_pp": result[0]*100,
                  "ci95_low_pp": result[1]*100, "ci95_high_pp": result[2]*100,
                  "z_stat": result[3], "p_value_two_sided": result[4]})
d7_tests = pd.DataFrame(tests)
display(d7_tests)
'''),
    code('''
plot = post_quality.set_index("registered_via")
fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
plot[["activation_rate", "d1_retention", "d3_retention", "d7_retention"]].plot.bar(ax=axes[0])
axes[0].set(title="Activation and Retention | 2015-10-07 to 09", ylabel="Rate", xlabel="registered_via")
plot[["avg_first_7_active_days", "avg_first_7_play_count"]].plot.bar(ax=axes[1])
axes[1].set(title="First-week Engagement", xlabel="registered_via")
fig.tight_layout(); plt.show()
'''),
    md('''
## User-quality Conclusion

同期cohort中，Source 4的Activation不低；D1开始落后，D7明显低于Source 3/7/9。Source 4首周活跃天数、播放次数和播放时长也较低。D7差异的95%置信区间不跨0。

这些结果说明首次活动后的持续使用存在风险，但不能确定差异原因。统计显著不等于因果关系成立。
''')
])


write("05_Hypothesis_and_AB_Test.ipynb", [
    md('''
# 05 Hypothesis and A/B Test

## Business Question

哪些原因可能解释Source 4首次活动后的持续使用差异？如何通过未来随机实验验证可干预的产品假设？

## Analysis Objective

提出H1/H2/H3，区分可进一步数据验证与必须实验验证的问题，选择H2作为优先实验方向，并完成上线前A/B Test设计。本Notebook不生成实验结果。

## Data Used

- `outputs/quality_metrics_post_anomaly_cohort.csv`：Source 4 D7规划基线。
- `outputs/growth_october_daily_validation.csv`：Source 4近期新增流量。
- 当前没有真实assignment、exposure或post-treatment结果。

## Key Metrics

- Primary：D7 Retention。
- Secondary：首7天活跃天数、播放次数、播放时长。
- Long-term：D30 Retention，仅在未来实验cohort成熟后验证。
- Planning Inputs：baseline、MDE、alpha、power、样本量和招募周期。
'''),
    code(common_setup),
    md('''
## Hypothesis Framework

### H1：用户来源质量问题

Source 4用户可能具有不同的注册意图或用户构成。需要来源映射、设备、入口、注册前行为和流量真实性数据进一步验证；首次体验实验不能单独确认H1。

### H2：首次体验承接不足

Source 4多数用户能够活动，但后续回访和首周使用较低，可能与首次体验后的内容承接有关。该解释与行为阶段一致，但尚未被证明，需要随机实验验证。

### H3：注册流程或入口差异

10月7日可能存在注册入口、编码、埋点、产品版本或用户迁移变化。需要业务映射和变更日志核查；在确认Source 4代表真实新用户群之前不应上线实验。

## Selected Experimental Hypothesis

选择H2作为优先实验方向，因为它具有产品可干预性，并可使用D7在较短周期内验证。选择H2不等于排除H1或H3。
'''),
    md('''
## Experiment Design

### Population

实验上线后新注册、`registered_via=4`且通过业务映射确认的用户。历史用户不能事后伪随机分组。

### Experimental Unit and Randomization

- 实验单位：`msno`。
- 50/50用户级稳定Hash分流。
- 固定`experiment_id`和salt。
- 同一用户始终处于同一组。
- 主要分析采用Intent-to-Treat。
- 同时记录assignment和真实exposure。

### Control

当前新用户体验流程。

### Treatment

优化首次体验流程，例如简短偏好选择、个性化初始内容和首次播放后的连续内容承接。若多个组件同时上线，实验只能评价整体Treatment效果。

### Metrics

- Primary：D7 Retention。
- Secondary：First 7 Active Days、First 7 Play Count、First 7 Total Seconds。
- Diagnostic：Activation、D1、D3和Treatment曝光率。
- Guardrails：播放失败、异常退出、加载失败、通知退订和应用崩溃。
- Long-term：D30 Retention，仅作为后续长期验证。
'''),
    code('''
quality = pd.read_csv(OUTPUTS_DIR / "quality_metrics_post_anomaly_cohort.csv")
flow = pd.read_csv(OUTPUTS_DIR / "growth_october_daily_validation.csv", parse_dates=["registration_date"])
baseline_d7 = float(quality.loc[quality.registered_via.eq(4), "d7_retention"].iloc[0])
recent_flow = flow[flow.registration_date.between("2015-10-07", "2015-10-16")]
avg_daily_source4 = recent_flow.source4_new_users.mean()
print(f"Source 4 D7 planning baseline: {baseline_d7:.4%}")
print(f"Source 4 average daily new users: {avg_daily_source4:,.1f}")
'''),
    code('''
# Planning assumptions only; MDE is not an observed or promised uplift.
alpha = 0.05
power = 0.80
absolute_mde = 0.003
z_alpha = 1.959963984540054
z_power = 0.8416212335729143
target_rate = baseline_d7 + absolute_mde
p_bar = (baseline_d7 + target_rate) / 2
n_per_group = math.ceil((
    z_alpha * math.sqrt(2*p_bar*(1-p_bar)) +
    z_power * math.sqrt(baseline_d7*(1-baseline_d7) + target_rate*(1-target_rate))
)**2 / absolute_mde**2)
total_sample = 2 * n_per_group
recruitment_days = total_sample / avg_daily_source4
planning = pd.DataFrame([{
    "baseline_d7": baseline_d7, "absolute_mde": absolute_mde,
    "alpha": alpha, "power": power, "allocation": "50/50 two-sided",
    "sample_per_group": n_per_group, "total_sample": total_sample,
    "avg_daily_source4": avg_daily_source4,
    "estimated_recruitment_days": recruitment_days,
    "estimated_complete_d7_days": recruitment_days + 7,
    "estimated_complete_d30_days": recruitment_days + 30,
}])
display(planning)
'''),
    md('''
## Readout and Governance

- 第一批D7在入组后7天成熟；完整D7在最后一批入组用户达到Day7后读取。
- 第一批D30在入组后30天成熟；完整D30只作为长期复核。
- 正式读取前检查样本量、SRM、日志完整性、assignment、exposure及护栏指标。
- 达到预设样本量和成熟窗口后，才计算Control/Treatment差异、置信区间和p值。

## Experiment-design Conclusion

本Notebook完成的是上线前设计。H2仍是待验证假设；当前没有真实实验分组、Treatment曝光、uplift、p值、置信区间或实验成功结论。
''')
])

print("Created final notebook set:")
for path in sorted(NB.glob("*.ipynb")):
    if path.name[:2].isdigit() and path.name in {
        "00_Business_Context.ipynb", "01_Data_Audit.ipynb", "02_Growth_Monitoring.ipynb",
        "03_Source_Diagnosis.ipynb", "04_User_Quality_Diagnosis.ipynb", "05_Hypothesis_and_AB_Test.ipynb"
    }:
        print(path.name)
