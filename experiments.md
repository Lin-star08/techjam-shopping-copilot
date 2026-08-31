# TechJam 实验记录

本文档由 5 号维护，是所有功能是否进入最终版本的唯一实验台账。每个主要实验必须绑定 Git commit，并同时记录总体与四类场景指标。

## 实验规则

1. 一次实验只改变一个主要因素；混合改动必须拆开或明确标记为不可归因。
2. 日常调参只看固定 development split；阶段性候选才查看 internal holdout。
3. Public ground truth 仅用于评分和错误分析，不得进入 Agent、检索索引、规则或切分逻辑。
4. 不修改 `evaluator/local_evaluator.py` 或 `data/public_set.jsonl` 来获得报告分数。
5. 每次运行前执行测试，并记录 Git commit、配置、模型/API、token、成本和延迟。
6. 总分之外必须检查 Buying、Browsing、Intent Override、Boundary，显著场景退化必须解释。
7. 不能稳定复现、无法解释或只改善 development 而伤害 holdout 的功能，默认不进入 final。

## 固定数据切分

- 文件：`docs/internal_split.json`
- 方法：按 `scenario_type` 分层，再以固定 seed 对 `sample_id` 做 SHA-256 排序。
- Development：150 条。
- Internal holdout：50 条，包含 Buying 20、Browsing 20、Intent Override 7、Boundary 3。
- 切分不读取目标商品进行选择；中途不得重抽。

## v0-baseline

- 状态：已复现并锁定
- Git commit：`3407835`
- Agent：标准库 SQLite FTS5 BM25，无状态、无 LLM、无网络依赖
- 主要能力：仅根据当前一轮消息检索；无 State、Filter、Profile、Multi-route、Clarification、Rerank
- 运行命令：`python3 -m evaluator.local_evaluator --output results/v0-baseline.json`
- 单元测试：5/5 通过（含固定切分与 Intent Override trace 语义测试）
- Token：prompt 0 / completion 0 / total 0
- 模型/API 成本：0

| 数据范围 | 样本数 | Hit@10 | MRR | MTTC |
|---|---:|---:|---:|---:|
| Overall | 200 | 0.125000 | 0.068034 | 9.810000 |
| Buying | 80 | 0.237500 | 0.126508 | 8.625000 |
| Browsing | 80 | 0.025000 | 0.004514 | 10.750000 |
| Intent Override | 30 | 0.133333 | 0.104167 | 10.066667 |
| Boundary | 10 | 0.000000 | 0.000000 | 11.000000 |

补充观察：共命中 25 条，其中 21 条在第 1 轮命中，4 条在第 4 轮命中。Browsing 仅命中 2/80，Boundary 为 0/10，是后续实验的重点监控场景。

Trace 冒烟验证：`public_0002` 成功重放 10 轮，无 Agent 异常；override 在第 3 轮生效，v0 最终 miss。逐轮 trace 只写入临时目录，不作为正式指标来源。

完整结果：`results/v0-baseline.json`

## v1-state-retrieval

- 日期/负责人：2026-08-30 / 5号评估
- 状态：正式评测完成；保留为中间版本，不作为 final
- Git commit：`c8b4812`
- 对比基线：`v0-baseline`（tag `V0`）
- 改动性质：集成包，包含词典、约束解析、SessionState、安全 hard filter、多路召回和 profile route；不是可单独归因的单变量 ablation
- 排序边界：`starter/ranking.py` 已有 RRF，但 `Agent.respond` 未调用；当前使用顺序式 `merge_candidates`
- Clarification：未接入，`ask_attribute` 始终为 null
- 模型/API/网络依赖：无
- 运行命令：`python3 -m evaluator.local_evaluator --output results/v1-state.json`
- 测试：`python3 -m unittest discover -s tests -v`，57/57 通过；当前环境未安装 pytest
- 正式评测耗时：约 28.46 秒
- 全量 trace：1,778 个 respond 调用，平均 6.782 ms、P95 44.978 ms、最大 382.595 ms
- Token：prompt 0 / completion 0 / total 0
- 模型/API 成本：0

| 数据范围 | 样本数 | Hit@10 | Δ vs V0 | MRR | Δ vs V0 | MTTC | Δ vs V0 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Full public | 200 | 0.130000 | +0.005000 | 0.068942 | +0.000908 | 9.760000 | -0.050000 |
| Development | 150 | 0.113333 | +0.006666 | 0.065886 | -0.003233 | 9.946667 | -0.066666 |
| Internal holdout | 50 | 0.180000 | 0 | 0.078111 | +0.013333 | 9.200000 | 0 |
| Buying | 80 | 0.250000 | +0.012500 | 0.126176 | -0.000332 | 8.500000 | -0.125000 |
| Browsing | 80 | 0.025000 | 0 | 0.004514 | 0 | 10.750000 | 0 |
| Intent Override | 30 | 0.133333 | 0 | 0.111111 | +0.006944 | 10.066667 | 0 |
| Boundary | 10 | 0.000000 | 0 | 0.000000 | 0 | 11.000000 | 0 |

- 主要改善：Buying 新增 `public_0053` rank 6、`public_0065` rank 9；Intent `public_0046` 从 rank 8 升至 3。
- 主要退化：Buying `public_0156` 从 V0 rank 1 变为 miss；development MRR 从 0.069119 降至 0.065886。
- Failure taxonomy 变化：候选诊断表明部分 O1/R1 可进一步定位到“候选已覆盖但 final Top 10 丢失”的 K1 嫌疑；因缺少 Agent 原生 route/filter trace，暂不逐条强制改码。
- 可复现性：正式 evaluator、固定 split、全量 trace 和候选诊断均已运行；结果文件未手工编辑。
- 结论：保留为 V1 中间检查点。总体净增仅 1/200，Browsing/Boundary 无变化，且存在 rank-1 回归；下一步分别评估 RRF 集成和 clarification，禁止再次混成不可归因实验。
- 完整报告：`docs/reports/v1/README.md`
- 完整结果：`results/v1-state.json`

## v1.1-rrf

- 日期/负责人：2026-08-30 / 5号评估
- 状态：正式评测完成；保留并作为下一实验基线
- Git commit：`5e4e8ae`
- 对比版本：`v1-state-retrieval`（commit `c8b4812`）
- 主要改动：`Agent.respond` 接入 RRF；各 route 全量展开后过滤并融合，不再使用 `merge_candidates(limit=100)`
- 归因边界：同时改变了融合算法和候选提前截断，不能将全部收益只归因于 RRF 公式
- RRF 配置：`rrf_k=60`、所有 route 默认等权 1.0
- Clarification：仍未接入，`ask_attribute` 始终为 null
- 模型/API/网络依赖：无
- 运行命令：`python3 -m evaluator.local_evaluator --output results/v1.1-rrf.json`
- 测试：`python3 -m unittest discover -s tests -v`，60/60 通过
- 正式评测耗时：31.82 秒
- 全量 trace：1,674 个 respond 调用，平均 7.811 ms、P95 49.928 ms、最大 161.140 ms
- Token：prompt 0 / completion 0 / total 0
- 模型/API 成本：0

| 数据范围 | 样本数 | Hit@10 | Δ vs V1 | MRR | Δ vs V1 | MTTC | Δ vs V1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Full public | 200 | 0.190000 | +0.060000 | 0.093456 | +0.024514 | 9.180000 | -0.580000 |
| Development | 150 | 0.153333 | +0.040000 | 0.067053 | +0.001167 | 9.546667 | -0.400000 |
| Internal holdout | 50 | 0.300000 | +0.120000 | 0.172667 | +0.094556 | 8.080000 | -1.120000 |
| Buying | 80 | 0.300000 | +0.050000 | 0.154563 | +0.028387 | 8.000000 | -0.500000 |
| Browsing | 80 | 0.075000 | +0.050000 | 0.021161 | +0.016647 | 10.250000 | -0.500000 |
| Intent Override | 30 | 0.166667 | +0.033334 | 0.097778 | -0.013333 | 9.833333 | -0.233334 |
| Boundary | 10 | 0.300000 | +0.300000 | 0.170000 | +0.170000 | 8.100000 | -2.900000 |

- 版本 churn：新增 13 个 hit、丢失 1 个，净增 12 个；shared hits 25 个。
- 主要改善：四场景 Hit 均提升；Boundary 0/10→3/10；重试推荐从 V1 全局 1 组变为 61 组。
- 主要退化：Buying `public_0053` rank 6→miss（实际候选最佳 RRF rank 13）；Intent MRR 下降；Buying development MRR 下降。
- 候选漏斗：filter 后候选覆盖 Buying 61/80、Browsing 43/80、Intent 20/30、Boundary 8/10。
- 可复现性：正式 evaluator、固定 split、全量 trace 和 runtime candidate hook 均完成；正式结果未手工编辑。
- 结论：保留。下一步把 explicit/recency weighted RRF 与 clarification 分开评估。
- 完整报告：`docs/reports/v1.1/README.md`
- 横向对比：`docs/reports/v1.1/version_comparison.md`
- 逐轮案例：`docs/reports/v1.1/turn_casebook.md`
- 队友专项：`docs/reports/v1.1/team/`（1–4号各一份）
- 完整结果：`results/v1.1-rrf.json`

## v2-dialogue

- 日期/负责人：2026-08-30 / 5号评估
- 状态：正式评测完成；保留并作为下一版本基线
- Git commit：`964072b`（`origin/dev`）
- 对比版本：`v1.1-rrf`（commit `5e4e8ae`）
- 评测隔离：当前 `feature/evaluation` 仍在 `5e4e8ae` 且有未提交报告；从 `origin/dev` 导出隔离副本运行，未切换或合并工作区
- 改动性质：16个提交组成的集成包，包含意图识别、neutral/override state、最多三次追问、知识资产更新和可配置RRF框架；不能做单模块因果归因
- 正式RRF配置：`equal`，`rrf_k=60`，所有route权重1.0；默认排序权重与V1.1一致
- 模型/API/网络依赖：无
- 正式命令：`env -u RANKING_CONFIG_NAME python3 -m evaluator.local_evaluator --output results/v2-dialogue.json`
- 测试：`python3 -m unittest discover -s tests -v`，84/84通过
- 正式评测耗时：39.35秒；确定性复跑40.37秒，两份JSON SHA-256完全一致
- 全量trace：1,368个respond调用，全部合法、0异常；平均16.212 ms、P95 66.120 ms、最大197.777 ms
- 对话行为：438次追问、90次具体约束回答、273次无额外偏好、6次Boundary no-preference
- Token：prompt 0 / completion 0 / total 0
- 模型/API成本：0

| 数据范围 | 样本数 | Hit@10 | Δ vs V1.1 | MRR | Δ vs V1.1 | MTTC | Δ vs V1.1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Full public | 200 | 0.410000 | +0.220000 | 0.219788 | +0.126332 | 7.430000 | -1.750000 |
| Development | 150 | 0.373333 | +0.220000 | 0.181717 | +0.114664 | 7.780000 | -1.766667 |
| Internal holdout | 50 | 0.520000 | +0.220000 | 0.334000 | +0.161333 | 6.380000 | -1.700000 |
| Buying | 80 | 0.475000 | +0.175000 | 0.239439 | +0.084876 | 6.537500 | -1.462500 |
| Browsing | 80 | 0.375000 | +0.300000 | 0.190030 | +0.168869 | 7.887500 | -2.362500 |
| Intent Override | 30 | 0.266667 | +0.100000 | 0.163333 | +0.065555 | 9.100000 | -0.733333 |
| Boundary | 10 | 0.600000 | +0.300000 | 0.470000 | +0.300000 | 5.900000 | -2.200000 |

- Technical Score：0.342336（V1.1为0.159437，Δ +0.182899）
- 版本churn：新增46个hit、丢失2个、shared 36个，净增44个；lost为Buying `public_0054`、Intent `public_0125`
- 候选漏斗：152/200目标在至少一个可计分轮次进入filter后候选；118个miss中48个候选缺失、70个候选内rank>10
- 逐轮：turn 1/2/3/4首次命中分别为36/3/26/17；turn 5–10共708次调用且0新增hit
- Development-only权重消融：`mild`与`stronger`均维持Hit 0.373333和MTTC 7.78，但MRR分别降至0.180616、0.180124；均未打开holdout
- 可复现性：正式结果确定性复跑、固定split、全量trace和生产路径runtime audit均完成；audit逐session与正式hit/turn/rank完全一致
- 结论：保留默认equal版本。下一步将问题信息价值、候选召回、显式/recency重排和三问后停止策略拆成独立实验
- 完整报告：`docs/reports/v2/README.md`
- 横向对比：`docs/reports/v2/version_comparison.md`
- 逐轮案例：`docs/reports/v2/turn_casebook.md`
- 队友专项：`docs/reports/v2/team/`（1–4号各一份）
- 完整结果：`results/v2-dialogue.json`

## v2.1-evidence

- 日期/负责人：2026-08-31 / 5号评估
- 状态：正式评测完成；保留为实验候选，暂不替换V2 final baseline
- Git commit：`0eb12aa`（`origin/dev`）
- 对比版本：`v2-dialogue`（commit `964072b`）
- 评测隔离：当前`feature/evaluation`仍在`5e4e8ae`且有未提交报告；从`origin/dev`导出隔离副本运行，未切换或合并工作区
- 改动性质：6个提交组成的集成包；字段化route、category+requirement、relaxed/same-category route、动态route budget、商品matched evidence和evidence-aware RRF
- 正式配置：`mild_evidence_light`；`rrf_k=60`、mild route权重、hard evidence 0.025、soft evidence 0.01、boost上限0.12
- 模型/API/网络依赖：无
- 正式命令：`env -u RANKING_CONFIG_NAME python3 -m evaluator.local_evaluator --output results/v2.1-evidence.json`
- 测试：132/132通过
- 正式评测耗时：110.62秒；确定性复跑114.78秒，两份JSON SHA-256均为`e70215df0c9df59a1bd3726d0e26fda5b6ff350a9376db35c656a2a039328d90`
- 全量trace：1,193次respond，全部合法、0异常；mean 60.844 ms、P95 166.539 ms、max 1296.558 ms
- Token：prompt 0 / completion 0 / total 0；模型/API成本0

| 数据范围 | 样本数 | Hit@10 | Δ vs V2 | MRR | Δ vs V2 | MTTC | Δ vs V2 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Full public | 200 | 0.515000 | +0.105000 | 0.246766 | +0.026978 | 6.450000 | -0.980000 |
| Development | 150 | 0.513333 | +0.140000 | 0.239040 | +0.057323 | 6.500000 | -1.280000 |
| Internal holdout | 50 | 0.520000 | 0 | 0.269944 | -0.064056 | 6.300000 | -0.080000 |
| Buying | 80 | 0.612500 | +0.137500 | 0.278090 | +0.038651 | 5.412500 | -1.125000 |
| Browsing | 80 | 0.462500 | +0.087500 | 0.195476 | +0.005446 | 6.862500 | -1.025000 |
| Intent Override | 30 | 0.400000 | +0.133333 | 0.260833 | +0.097500 | 8.166667 | -0.933333 |
| Boundary | 10 | 0.500000 | -0.100000 | 0.364286 | -0.105714 | 6.300000 | +0.400000 |

- Technical：0.422530，Δ +0.080194
- Dev/Holdout gate：development Technical 0.305582→0.418379；holdout 0.452600→0.434983，按既定规则未过final gate
- Churn：新增36、丢失15、shared 67，净增21；shared rank 22提升/22不变/23下降
- 候选漏斗：151/200覆盖；97个miss互斥归因为R1纯召回20、R3融合前截断28、F1过滤误删1、K1 rank 11–20为21、K1 rank 21–100为27
- 已证实回归：顺序Top100让后置route高位目标在融合前丢失；Boundary两个lost在关键轮次均为current-message rank1
- 对话：408次追问；turn1–5首次命中46/17/19/19/2；turn6–10共485次调用且0新增hit
- Development-only消融：equal/mild/tiny/light/medium的Hit均0.513333；MRR依次0.236183/0.236976/0.238587/0.239040/0.243577；除正式light外均未看holdout
- 结论：保留实验候选。先修Top100截断、Boundary和性能；候选冻结后再评估medium，holdout不过gate不升级
- 完整报告：`docs/reports/v2.1/README.md`
- 未命中归因：`docs/reports/v2.1/miss_attribution.md`
- 横向对比：`docs/reports/v2.1/version_comparison.md`
- 逐轮案例：`docs/reports/v2.1/turn_casebook.md`
- 队友专项：`docs/reports/v2.1/team/`
- 完整结果：`results/v2.1-evidence.json`

## 功能交接要求

2、3、4 号交付待评估版本时，必须同时提供：

- Git commit SHA；
- 唯一主要改动；
- 预期改善的场景和指标；
- 新增或变化的参数；
- 已知风险及可能退化的场景；
- 最小复现命令；
- 是否需要模型、网络、密钥或新增依赖。

资料不完整时可以跑冒烟测试，但不得把结果标记为正式 ablation。

## 实验模板

复制本节，为每个版本建立独立条目。

### vX-名称

- 日期/负责人：
- Git commit：
- 对比基线：
- 唯一主要改动：
- 预期改善场景/指标：
- 配置和参数：
- 模型/API/网络依赖：
- 测试结果：
- 运行命令：
- 总运行时间与单轮延迟：
- Prompt / completion tokens：
- 估算成本：

| 数据范围 | 样本数 | Hit@10 | MRR | MTTC | 相对基线变化 |
|---|---:|---:|---:|---:|---|
| Development | 150 |  |  |  |  |
| Internal holdout | 50 |  |  |  |  |
| Buying |  |  |  |  |  |
| Browsing |  |  |  |  |  |
| Intent Override |  |  |  |  |  |
| Boundary |  |  |  |  |  |

- 主要改善案例：
- 主要退化案例：
- Failure taxonomy 变化：
- 可复现性检查：
- 结论：保留 / 回退 / 待验证
- 下一步：

## Final Gate

最终候选必须满足：

- 官方 evaluator 可完整运行；
- 全部测试通过；
- 输出接口合法，商品 ID 有效且唯一；
- development 与 internal holdout 均有记录；
- 四类场景指标齐全；
- Intent Override 和 no-preference 有 trace 证据；
- 模型、成本、token、延迟、限制和 fallback 已披露；
- 仓库不包含 API key、私有数据或无关大文件。
