# V2 Dialogue 四场景分析总览

## 1. 版本范围

本目录评估 `origin/dev` commit `964072b`。当前评测分支 `feature/evaluation` 仍在 `5e4e8ae`，且保存着尚未提交的 V1/V1.1 产物，因此本次从 `origin/dev` 导出隔离副本运行，没有切换、合并或覆盖现有工作区。

相对 V1.1，V2 是包含多项改动的集成版本：接入意图识别、对话状态与最多三次追问，补充 neutral/override 处理，更新产品知识资产，并加入可选 RRF 权重配置。默认配置仍为 `rrf_k=60`、所有 route 等权 1.0。因此结果不能只归因于某一个类或某一条规则。

报告中的 public `sample_id` 仅用于错误分析和通用回归验证，不得写入 Agent、索引、规则、词典或调参逻辑。

## 2. 数据与复现

- 正式结果：`results/v2-dialogue.json`
- 对比基线：`results/v1.1-rrf.json`
- 固定切分：`docs/internal_split.json`（development 150 / internal holdout 50）
- 正式命令：`env -u RANKING_CONFIG_NAME python3 -m evaluator.local_evaluator --output results/v2-dialogue.json`
- 全量 trace：`env -u RANKING_CONFIG_NAME python3 -m evaluator.debug_trace --all --output /tmp/v2_all_traces.json`
- 测试：`python3 -m unittest discover -s tests -v`，84/84 通过
- 正式运行时间：39.35 秒；确定性复跑 40.37 秒，两份 JSON SHA-256 均为 `ff383baecbae21fae0ac05b5b1f3ceae16e3d545113f09300748efc5144b51f9`
- 模型、API、网络和 token 成本：均为 0

候选漏斗通过临时 runtime audit 复刻生产 `Agent.respond` 路径，逐 session 的 hit、turn、rank 与正式结果完全一致；临时脚本和 trace 不作为提交产物。

## 3. 总体结果

| 数据范围 | 样本数 | V2 Hit@10 | Δ vs V1.1 | V2 MRR | Δ vs V1.1 | V2 MTTC | Δ vs V1.1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Full public | 200 | 0.410000 | +0.220000 | 0.219788 | +0.126332 | 7.430000 | -1.750000 |
| Development | 150 | 0.373333 | +0.220000 | 0.181717 | +0.114664 | 7.780000 | -1.766667 |
| Internal holdout | 50 | 0.520000 | +0.220000 | 0.334000 | +0.161333 | 6.380000 | -1.700000 |

| 场景 | Hits / Misses | Hit@10 | Δ | MRR | Δ | MTTC | Δ | 报告 |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Buying | 38 / 42 | 0.475000 | +0.175000 | 0.239439 | +0.084876 | 6.537500 | -1.462500 | [查看](buying.md) |
| Intent Override | 8 / 22 | 0.266667 | +0.100000 | 0.163333 | +0.065555 | 9.100000 | -0.733333 | [查看](intent_override.md) |
| Browsing | 30 / 50 | 0.375000 | +0.300000 | 0.190030 | +0.168869 | 7.887500 | -2.362500 | [查看](browsing.md) |
| Boundary | 6 / 4 | 0.600000 | +0.300000 | 0.470000 | +0.300000 | 5.900000 | -2.200000 | [查看](boundary.md) |

V2 共命中 82 条。相对 V1.1 新增 46 条、丢失 2 条、共有 36 条，净增 44 条。两个回归为 Buying `public_0054` 和 Intent Override `public_0125`。

## 4. 描述性统计与加权口径

以下均为 population variance（除以 N）；miss 的完成轮次按 evaluator 记为 11。

| 范围 | Hit 方差 | RR 方差 | 完成轮次方差 | 完成轮次极值 | 命中 rank 均值 | rank 方差 | rank 极值 |
|---|---:|---:|---:|---|---:|---:|---|
| Overall | 0.241900 | 0.123644 | 18.955100 | 1–11 | 3.463415 | 7.882808 | 1–10 |
| Buying | 0.249375 | 0.135990 | 22.523594 | 1–11 | 4.236842 | 11.022853 | 1–10 |
| Browsing | 0.234375 | 0.098944 | 16.499844 | 1–11 | 3.100000 | 4.756667 | 1–10 |
| Intent Override | 0.195556 | 0.100989 | 9.956667 | 3–11 | 2.375000 | 2.484375 | 1–5 |
| Boundary | 0.240000 | 0.208100 | 18.290000 | 1–11 | 1.833333 | 2.138889 | 1–5 |

正式 overall 是按样本数自然加权的 micro 指标，四场景权重分别为 Buying 0.40、Browsing 0.40、Intent 0.15、Boundary 0.05。四场景等权 macro 仅作公平性诊断：Hit `0.429167`、MRR `0.265701`、MTTC `7.356250`、Technical-like `0.367169`。

官方 Technical Score 为 `0.50×Hit + 0.30×MRR + 0.20×Efficiency`。V2 三项贡献分别为 `0.205000`、`0.065936`、`0.071400`，合计 `0.342336`。

## 5. 逐轮与对话行为

| Turn | 活跃会话 | 首次命中 | 累计命中 |
|---:|---:|---:|---:|
| 1 | 200 | 36 | 36 |
| 2 | 164 | 3 | 39 |
| 3 | 161 | 26 | 65 |
| 4 | 135 | 17 | 82 |
| 5 | 118 | 0 | 82 |
| 6 | 118 | 0 | 82 |
| 7 | 118 | 0 | 82 |
| 8 | 118 | 0 | 82 |
| 9 | 118 | 0 | 82 |
| 10 | 118 | 0 | 82 |

- 全量 trace 共 1,368 次调用，全部响应合法、无异常。
- `ask_attribute` 共出现 438 次：use_case 142、style 79、material 73、size 54、feature 46、category 36、color 8。
- 用户给出 90 次具体约束回答、273 次“没有额外偏好”和 6 次 Boundary no-preference 回答。
- 82 个命中中有 46 个发生在 turn 2–4，证明 V2 首次把真实对话增量转化为指标收益。
- turn 5–10 仍有 708 次调用且零新增命中；全量有 646 次相邻 Top 10 完全重复，说明三次追问后的停止策略仍未与 evaluator 提前终止联动。
- 平均单次响应 16.212 ms，P95 66.120 ms，最大 197.777 ms。

详细案例见 [逐轮案例册](turn_casebook.md)。

## 6. 候选漏斗

“候选覆盖”表示目标在至少一个可计分轮次进入生产 hard filter 后的实际融合集合。

| 场景 | 可计分候选覆盖 | Hit | miss：候选缺失 | miss：候选内 rank > 10 |
|---|---:|---:|---:|---:|
| Buying | 63 / 80 | 38 | 17 | 25 |
| Browsing | 58 / 80 | 30 | 22 | 28 |
| Intent Override | 23 / 30 | 8 | 7 | 15 |
| Boundary | 8 / 10 | 6 | 2 | 2 |
| Overall | 152 / 200 | 82 | 48 | 70 |

V1.1 的 162 个 miss 中有 68 个候选缺失、94 个候选内排序失败；V2 分别降至 48 和 70。召回与排序两端都改善，但 K1 仍是更大的剩余桶。

## 7. Development-only 权重消融

V2 的 `mild` 与 `stronger` 只在固定 development 150 条上运行；未对这两个配置查看 holdout。

| 配置 | Hit@10 | MRR | MTTC | Technical | gained / lost vs equal |
|---|---:|---:|---:|---:|---:|
| equal（正式 V2） | 0.373333 | 0.181717 | 7.780000 | 0.305582 | — |
| mild | 0.373333 | 0.180616 | 7.780000 | 0.305251 | 0 / 0 |
| stronger | 0.373333 | 0.180124 | 7.780000 | 0.305104 | 0 / 0 |

两组预设均未改善 Hit 或 MTTC，并轻微伤害 MRR，故不进入 holdout gate。这个结果只否定当前两组预设，不能证明所有 weighted RRF 都无效。

## 8. 已证实结论、合理推断与边界

### 已证实

1. V2 在 overall、development、holdout 和四个场景的三项核心指标上均优于 V1.1。
2. Browsing 的 24 个新增命中全部发生在 turn 2–4；clarification 是该场景增益的直接行为条件。
3. Boundary 已有 6 次 no-preference 回复进入 Agent，且 3 个 V1.1 未命中案例在后续轮次命中，neutral 路径已端到端生效。
4. 118 个 miss 中 70 个目标曾进入过滤后候选但仍在 Top 10 外，排序仍是最大单一失败桶。
5. `public_0156` 是唯一观察到目标在某个可计分轮次被 filter 移除的样本，但下一轮目标重新进入候选且最佳完整 rank 96；不能把该 session 的最终失败只归因于 filter。

### 合理推断

1. V2 大部分收益来自追问后披露属性与保存状态共同改变召回/融合，而不是权重配置；默认权重与 V1.1 相同，且两组非默认权重没有改善 development。
2. use_case 共问 142 次但大量回答为“没有额外偏好”，说明 question playbook 的信息价值估计仍有优化空间。
3. turn 5 后停止提问但继续重复推荐，是 MTTC 剩余损失的主要来源之一；需要停止协议或候选探索策略，而不是继续相同列表。

### 证据边界

候选审计能区分目标是否进入生产 filter 后集合以及完整 RRF rank，但没有人工相关性标签，也没有保存每个竞争商品的显式需求匹配分，因此不能断言所有排在目标前的商品都不相关。V2 同时合入多个模块，不能将总增益精确拆分给 intent、state、playbook 或某一次数据资产更新；后续必须做单变量 ablation。

## 9. 扩展交付索引

- [组内交接说明](TEAM_HANDOFF.md)
- [逐轮成功/失败案例册](turn_casebook.md)
- [V0 / V1 / V1.1 / V2 横向对比](version_comparison.md)
- [1号：数据词典与商品知识](team/member_1_data_knowledge.md)
- [2号：State、Override、Neutral 与追问](team/member_2_state_policy.md)
- [3号：检索、Hard Filter 与 Fallback](team/member_3_retrieval_filter.md)
- [4号：融合、重排与权重实验](team/member_4_ranking_weights.md)

## 10. Gate 结论

V2 默认等权版本应保留，并成为下一轮基线。`mild`/`stronger` 不进入 holdout。下一步应拆成三个实验：追问信息价值排序、候选内显式需求重排、turn 5 后停止/换路策略；禁止再次混成无法归因的集成包。
