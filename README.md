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
3. **Growth Monitoring**：监控每日新增和来源结构，识别 2015-10-07 断点，并判断变化是否持续。
4. **Source Diagnosis**：验证 `registered_via=4` 的增量贡献和异常持续性。
5. **User Quality Diagnosis**：比较 Source4 与异常前主要新增来源 Source3、Source7、Source9，并保留非Source4整体作为参考，分析激活、短期留存与首周行为。
6. **Hypothesis & A/B Test**：区分事实与原因假设，先检查H3数据口径风险，再设计首次体验优化实验。

## Key Findings

- 截至2015-10-16，观察到2015-10-07之后持续性的新增规模和来源结构变化，不是单日峰值；仍需结合业务活动记录确认是否存在渠道、营销活动或数据口径因素影响。
- `registered_via=4`贡献主要新增增量，并从异常前的小规模来源转为新增结构中的主要来源；在业务映射和口径检查完成前，不能把Source4直接解释为真实新增渠道。
- D7 Retention只覆盖2015-10-07至2015-10-09注册且截至分析日已经成熟的cohort。该范围内Source4 Activation不低，但D1、D7 Retention及完整首周使用深度低于主要同期来源。10月10日以后注册用户没有完整D7，不能进入D7比较，只能使用已成熟D1/D3和截至观察日的首周早期行为作为补充信号。
- 数据支持的阶段性判断是：Source4用户完成首次激活后，在注册后的早期持续使用阶段出现流失风险；不能据此推断长期习惯或长期价值。
- 数据不能单独确认因果原因；“首次体验承接不足”是优先待验证假设，不是已证明结论。

Source3、Source7和Source9是异常发生前的主要新增来源，因此用于重点横向比较；项目同时保留非Source4整体作为总体参考，避免事后挑选对照组。

## Pre-experiment Data-definition Check

在针对Source4设计实验前，需要优先排查H3：

1. 确认`registered_via=4`业务含义和映射规则稳定；
2. 排查10月7日前后是否存在埋点变化；
3. 排查注册规则或入口变化；
4. 排查渠道分类变化；
5. 排查用户迁移或批量导入。

若H3尚未排除，不能直接认为Source4代表真实新增渠道。只有在未发现明显口径问题后，H2才作为基于早期行为特征提出的优先验证方向：它具备产品可干预性，并可以通过A/B Test验证，但仍不是已确认原因。

## A/B Test Proposal

- 实验对象：在完成Source4业务映射与H3口径检查后，新注册的Source4用户
- 实验单位：用户 `msno`
- 随机化：稳定哈希后 50/50 分流
- Control：现有新用户体验流程
- Treatment：优化首次体验流程
- Primary Metric：D7 Retention
- Secondary Metrics：首周活跃天数、播放次数、播放时长
- Long-term Metric：D30 Retention，仅待数据成熟后用于长期验证

历史D7规划基线仅来自2015-10-07至2015-10-09的成熟cohort，不代表10月7日以后全部Source4用户。

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
