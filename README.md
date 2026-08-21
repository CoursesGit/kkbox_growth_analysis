# KKBOX 新用户增长异常诊断与留存优化分析

## Business Overview

本项目模拟订阅制音乐平台增长分析场景。分析身份为 2015 年 10 月中旬的 KKBOX 增长分析师，数据截止日期为 **2015-10-16**。

核心问题是：如何通过新增用户监控识别来源结构异常，并判断新增用户质量风险。分析链路为：**新增监控 → Source 拆解 → 用户质量分析 → 假设提出 → A/B Test 设计**。

项目截止于实验方案设计阶段，没有真实 A/B Test 结果。D30 Retention 仅作为未来实验的长期验证指标，不作为当前分析证据。

## Data Sources

| 数据表 | 用途 |
|---|---|
| `members_v3.csv` | 用户注册日期与 `registered_via` |
| `user_logs.csv` | 激活、D1/D3/D7 留存与首周行为 |
| `transactions.csv` | 仅作可用性审计，不支撑核心结论 |

`user_logs_v2.csv`、`transactions_v2.csv`、`train_v2.csv` 不进入当前分析。原始和处理后 CSV 不提交 Git；请将原始文件放入 `data/raw/`，核心分析优先读取 `data/processed/user_growth_profile.csv`。

## Data Processing

分析窗口固定为 **2015-07-01 至 2015-10-16**。项目构建一行一个用户的 `user_growth_profile`，包含注册来源、Activation、D1/D3/D7 Retention、首周活跃天数、播放次数、播放时长及各指标成熟度字段。

未成熟指标保留为 `NULL`，不以 0 代替；负值 `total_secs` 在聚合前按 0 处理。

## Analysis Workflow

1. **Business Context**：明确业务问题、边界和指标体系。
2. **Data Audit**：检查粒度、范围、用户覆盖及关键质量问题。
3. **Growth Monitoring**：监控每日新增和来源结构，识别 2015-10-07 断点。
4. **Source Diagnosis**：验证 `registered_via=4` 的增量贡献和异常持续性。
5. **User Quality Diagnosis**：比较 Source4 与 Source3、Source7、Source9 的激活、短期留存与首周行为。
6. **Hypothesis & A/B Test**：区分事实与原因假设，设计首次体验优化实验。

## Key Findings

- 2015-10-07 出现明显新增规模断点，且持续至项目截止日，不是单日峰值。
- `registered_via=4` 贡献主要新增增量，并由小规模来源转为主要新增来源。
- 2015-10-07 至 2015-10-09 已成熟 cohort 中，Source4 Activation 不低，但 D1、D7 Retention 及首周使用深度低于主要同期来源，风险出现在首次活动后的持续使用阶段。
- 数据不能单独确认因果原因；“首次体验承接不足”是优先待验证假设，不是已证明结论。

## A/B Test Proposal

- 实验对象：2015-10-07 以后注册的 Source4 新用户
- 实验单位：用户 `msno`
- 随机化：稳定哈希后 50/50 分流
- Control：现有新用户体验流程
- Treatment：优化首次体验流程
- Primary Metric：D7 Retention
- Secondary Metrics：首周活跃天数、播放次数、播放时长
- Long-term Metric：D30 Retention，仅待数据成熟后用于长期验证

样本量与周期属于实验规划，不代表实验结果。仓库中没有真实实验结果、实验成功结论或实际提升百分比。

## Project Structure

```text
kkbox_growth_analysis/
├── notebooks/
│   ├── 00_Business_Context.ipynb
│   ├── 01_Data_Audit.ipynb
│   ├── 02_Growth_Monitoring.ipynb
│   ├── 03_Source_Diagnosis.ipynb
│   ├── 04_User_Quality_Diagnosis.ipynb
│   └── 05_Hypothesis_and_AB_Test.ipynb
├── sql/
│   ├── 00_data_validation.sql
│   ├── 01_user_growth_profile.sql
│   ├── 02_growth_monitoring.sql
│   ├── 03_source_quality_analysis.sql
│   └── 04_ab_test_planning.sql
├── data/raw/                 # 本地原始数据
├── data/processed/           # 本地处理数据
├── outputs/                  # 审计与验证产物
└── README.md
```

## Technical Skills

- Python / Pandas
- SQL
- Statistical Testing
- Cohort Analysis
- A/B Test Design
