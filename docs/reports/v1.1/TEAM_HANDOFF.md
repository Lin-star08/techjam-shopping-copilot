# V1.1 Evaluation 组内交接表

## 1. 一页概览

| 项目 | 内容 |
|---|---|
| 评估版本 | V1.1，Git commit `5e4e8ae` |
| 本批交付 | 正式指标、四场景分析、逐轮案例、版本对比、1–4号成员专项建议 |
| 当前结论 | V1.1 保留为下一轮实验基线 |
| 分工原则 | 1号管数据知识，2号管状态策略，3号管检索约束，4号管融合排序，5号管评估 Gate |
| 实验原则 | 一次只改变一个主要因素；只用 development 调参，冻结后再看 holdout |
| 数据红线 | Public 案例只能用于错误分析和回归验证；不得把 sample ID、目标 ASIN、目标标题或隐藏意图写入 Agent、索引、规则或调参逻辑 |

### 当前正式指标

| Hit@10 | MRR | MTTC | Technical Score |
|---:|---:|---:|---:|
| `0.190000` | `0.093456` | `9.180000` | `0.159437` |

## 2. 文件导航

以下路径均相对于仓库根目录。

| 文件 | 路径 | 用途 | 使用人 |
|---|---|---|---|
| 正式评测结果 | `results/v1.1-rrf.json` | 200 条会话的总体、分场景和逐 session 结果 | 全员；5号维护 |
| V1.1 总报告 | `docs/reports/v1.1/README.md` | 指标、方差、加权口径、核心结论和报告入口 | 全员 |
| Buying 报告 | `docs/reports/v1.1/buying.md` | 明确需求、filter、召回和排序问题 | 1–4号 |
| Browsing 报告 | `docs/reports/v1.1/browsing.md` | 宽类别、零追问、候选缺失和排序问题 | 1–4号 |
| Intent Override 报告 | `docs/reports/v1.1/intent_override.md` | override 生效轮、状态与 recency 问题 | 2–4号 |
| Boundary 报告 | `docs/reports/v1.1/boundary.md` | no-preference/neutral 未端到端触发的问题 | 1–4号 |
| 逐轮案例册 | `docs/reports/v1.1/turn_casebook.md` | Turn 1–10 的成功、失败、活跃会话和首次命中 | 全员；5号回归使用 |
| 版本横向对比 | `docs/reports/v1.1/version_comparison.md` | V0/V1/V1.1、方差、micro/macro 和权重分解 | 全员；5号决策使用 |
| 1号专项建议 | `docs/reports/v1.1/team/member_1_data_knowledge.md` | 词典、类别属性统计、字段覆盖、question playbook | 1号 |
| 2号专项建议 | `docs/reports/v1.1/team/member_2_state_policy.md` | State、override、neutral、asked 和追问策略 | 2号 |
| 3号专项建议 | `docs/reports/v1.1/team/member_3_retrieval_filter.md` | 多路召回、联合 query、filter 和 fallback | 3号 |
| 4号专项建议 | `docs/reports/v1.1/team/member_4_ranking_weights.md` | Weighted RRF、显式需求权重和重排实验 | 4号 |
| 实验总台账 | `experiments.md` | 每版 commit、命令、指标、结论和是否保留 | 5号维护；全员查阅 |
| 失败分类 | `docs/failure_cases.md` | R1/F1/K1/S1/Q1 等统一问题编码 | 全员；5号维护 |
| 结果目录说明 | `results/README.md` | 正式结果命名和版本索引 | 全员 |
| 固定切分 | `docs/internal_split.json` | Development 150 / holdout 50 固定集合 | 5号使用；其他成员不得重抽 |

## 3. 成员分工

| 成员 | 先读 | 重点问题 | 必须交付 | 交给谁 |
|---|---|---|---|---|
| **1号：数据词典与商品知识** | `member_1_data_knowledge.md`、`browsing.md`、`buying.md` | 68 个候选缺失 miss；字段覆盖、category alias、属性同义词、高价值追问属性 | 基于 `data/catalog.jsonl` 的可复现词典、字段覆盖统计、category question playbook、生成命令 | playbook → 2号；alias/字段规范 → 3号；属性可靠度 → 4号；commit/实验说明 → 5号 |
| **2号：状态与对话策略** | `member_2_state_policy.md`、`turn_casebook.md`、`intent_override.md`、`boundary.md` | `ask_attribute` 始终为空；Turn 5–10 共 972 次零收益调用；override 旧值失效范围；no-preference 未触发 | clarification policy、逐轮 state snapshot、override/neutral/asked 测试、端到端 trace | state/query → 3号；explicit/recency/neutral 信号 → 4号；逐轮结果 → 5号 |
| **3号：检索与约束工程** | `member_3_retrieval_filter.md`、四场景报告的候选漏斗、`failure_cases.md` | 68 个候选缺失 miss；Agent 与诊断 pipeline 一致性；逐轮 filter reason；“保留类别 + 当前新值”联合 route | 统一候选构造接口、route evidence、filter 前后诊断、Candidate Recall@50/100、fallback 统计 | 完整候选/route evidence → 4号；漏斗、误删、延迟 → 5号 |
| **4号：融合与重排** | `member_4_ranking_weights.md`、`version_comparison.md`、`buying.md`、`intent_override.md` | 94 个候选内 miss；`public_0053` rank-13 回归；Intent MRR、Buying development MRR 下降 | Weighted RRF 单变量实验、route/explicit/recency score breakdown、参数表、gained/lost/rank churn | 候选配置、commit、参数、指标、回归案例 → 5号 |
| **5号：评估与最终 Gate** | `experiments.md`、`version_comparison.md`、`turn_casebook.md`、`failure_cases.md`、`internal_split.json` | 控制单变量；统一跑测试、正式 evaluator、固定切分和 trace | 记录 micro/macro、方差、极值、候选漏斗、gained/lost hit；决定是否通过 Gate | 汇总并登记正式 ablation |

### 5号 Gate 判定

| 必查项 | 通过要求 |
|---|---|
| 总分 | 不能只看 Technical Score |
| 场景行为 | Intent 和 Boundary 行为必须检查 |
| 数据切分 | Development 与 holdout 都必须报告 |
| 回归 | 检查原有高位命中是否退化 |
| 工程成本 | 成本与延迟必须在可接受范围内 |

## 4. 推荐执行顺序

| 顺序 | 负责人 | 动作 | 完成标志 |
|---:|---|---|---|
| 1 | 1号 | 产出 catalog 驱动的词典与 question playbook | 数据产物可复现，并交给2、3、4号 |
| 2 | 2号 | 在现有 state 上接入 clarification，补 override/neutral 测试 | 状态与逐轮行为有端到端 trace |
| 3 | 3号 | 统一候选诊断接口，补候选缺失和联合 route | 候选接口及 route evidence 冻结 |
| 4 | 4号 | 先单独做 Weighted RRF，再单独加入 explicit/recency | 两类实验可分别归因 |
| 5 | 5号 | 对每个 commit 分别跑完整 evaluation | 每个版本均有独立记录和 Gate 结论 |

| 并行安排 | 规则 |
|---|---|
| 1号 + 3号 | 可并行准备数据与召回 |
| 2号 | 可独立完成状态测试 |
| 4号 | 必须等3号候选接口冻结后再接线 |

> 禁止把以上能力一次性合并后再评测，否则无法判断增益来自哪里。

## 5. 每次交接清单

| 必填项 | 需要写清楚的内容 |
|---|---|
| Git commit | 完整 SHA |
| 唯一主要改动 | 本次只改变了什么 |
| 预期影响 | 预计改善的场景与指标 |
| 参数 | 参数名、取值和默认值 |
| 验证方式 | 新增测试及运行命令 |
| 风险 | 已知风险和可能退化的场景 |
| 环境要求 | 是否需要模型、网络、密钥或新增依赖 |
| 数据查看范围 | Development 指标；holdout 是否已查看 |
| 案例 | 2–3 个成功案例和 2–3 个失败/回归案例 |

> 信息不完整时，5号只能做冒烟检查，不得登记为正式 ablation。

## 6. 统一复现命令

| 目的 | 命令 |
|---|---|
| 运行测试 | `python3 -m unittest discover -s tests -v` |
| 生成正式结果 | `python3 -m evaluator.local_evaluator --output results/<version>.json` |
| 生成全量 trace | `python3 -m evaluator.debug_trace --all --output /tmp/<version>_traces.json` |

| 禁止修改 | 原因 |
|---|---|
| `evaluator/local_evaluator.py` | 不能通过改评测器提高分数 |
| `data/public_set.jsonl` | 不能污染或针对 public set 调优 |
| `docs/internal_split.json` | 固定 split 不得为提高分数而重抽 |

## 7. 下一版本计划

| 版本 | 唯一主要改动 | 目的 |
|---|---|---|
| V1.2 | Weighted RRF / explicit-recency 排序实验 | 单独判断排序带来的增益 |
| V1.3 | 在冻结排序上接入 clarification 与 neutral 行为 | 单独判断对话策略带来的增益 |

这样5号可以明确区分排序与对话的贡献，避免产生无法归因的混合版本。
