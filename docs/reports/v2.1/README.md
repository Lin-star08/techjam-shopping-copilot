# V2.1 Evidence-aware Retrieval 四场景分析总览

## 1. 版本范围

本目录评估 `origin/dev` commit `0eb12aa`。当前 `feature/evaluation` 仍在 `5e4e8ae`，且包含尚未提交的 V1–V2 评测产物，因此本次从远端提交导出隔离副本执行，没有切换、合并或覆盖现有工作区。

相对 V2 commit `964072b`，V2.1 修改 `starter/agent.py`、`starter/retrieval.py`、`starter/ranking.py` 及对应测试/诊断工具；evaluator 和 public 数据未改。主要变化包括字段化 route、category+requirement、relaxed、same-category popular、动态 route budget、商品级 matched evidence，以及 evidence-aware RRF。

正式默认配置为 `mild_evidence_light`：`rrf_k=60`，mild route 权重，hard evidence `0.025`、soft evidence `0.01`、boost 上限 `0.12`。

报告中的 public 案例仅用于错误分析和通用回归，不得写入 Agent、索引、词典、规则或调参逻辑。

## 2. 数据与复现

- 正式结果：`results/v2.1-evidence.json`
- 对比基线：`results/v2-dialogue.json`
- 固定切分：`docs/internal_split.json`（development 150 / internal holdout 50）
- 正式命令：`env -u RANKING_CONFIG_NAME python3 -m evaluator.local_evaluator --output results/v2.1-evidence.json`
- 全量 trace：`env -u RANKING_CONFIG_NAME python3 -m evaluator.debug_trace --all --output /tmp/v2.1_all_traces.json`
- 测试：`python3 -m unittest discover -s tests -v`，132/132 通过
- 正式运行：110.62 秒；确定性复跑 114.78 秒，两份 JSON SHA-256 均为 `e70215df0c9df59a1bd3726d0e26fda5b6ff350a9376db35c656a2a039328d90`
- 模型、API、网络和 token 成本：均为 0

生产路径 runtime audit 记录 filter 前后、完整 rank、route evidence 和 evidence boost；逐 session 的 hit、turn、rank 与正式结果完全一致。临时 trace/audit 不纳入 Git。

## 3. 总体结果

| 数据范围 | 样本数 | V2.1 Hit@10 | Δ vs V2 | V2.1 MRR | Δ vs V2 | V2.1 MTTC | Δ vs V2 | Technical Δ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Full public | 200 | 0.515000 | +0.105000 | 0.246766 | +0.026978 | 6.450000 | -0.980000 | +0.080194 |
| Development | 150 | 0.513333 | +0.140000 | 0.239040 | +0.057323 | 6.500000 | -1.280000 | +0.112797 |
| Internal holdout | 50 | 0.520000 | 0 | 0.269944 | -0.064056 | 6.300000 | -0.080000 | -0.017617 |

| 场景 | Hits / Misses | Hit@10 | Δ | MRR | Δ | MTTC | Δ | 报告 |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Buying | 49 / 31 | 0.612500 | +0.137500 | 0.278090 | +0.038651 | 5.412500 | -1.125000 | [查看](buying.md) |
| Intent Override | 12 / 18 | 0.400000 | +0.133333 | 0.260833 | +0.097500 | 8.166667 | -0.933333 | [查看](intent_override.md) |
| Browsing | 37 / 43 | 0.462500 | +0.087500 | 0.195476 | +0.005446 | 6.862500 | -1.025000 | [查看](browsing.md) |
| Boundary | 5 / 5 | 0.500000 | -0.100000 | 0.364286 | -0.105714 | 6.300000 | +0.400000 | [查看](boundary.md) |

V2.1 共命中 103 条。相对 V2 新增 36 条、丢失 15 条、共有 67 条，净增 21 条；shared hit 中 22 个 rank 提升、22 个不变、23 个下降。整体增益真实，但 churn 很大。

## 4. Development / Holdout Gate

Development 新增 29、丢失 8，净增 21；holdout 新增 7、丢失 7，Hit 数完全不变。Holdout 的 19 个 shared hit 中 4 个 rank 提升、8 个不变、7 个下降，且替换进来的新 hit 多为较后排名，因此 MRR 从 `0.334000` 降到 `0.269944`，Technical 从 `0.452600` 降到 `0.434983`。

按仓库既定 gate，“只改善 development 而伤害 holdout 的功能默认不进入 final”。因此 V2.1 应保留为实验候选，但暂不替换 V2 final baseline。

## 5. 描述性统计与加权口径

以下均为 population variance；miss 的完成轮次按 11 计。

| 范围 | Hit 方差 | RR 方差 | 完成轮次方差 | 完成轮次极值 | 命中 rank 均值 | rank 方差 | rank 极值 |
|---|---:|---:|---:|---|---:|---:|---|
| Overall | 0.249775 | 0.126816 | 20.277500 | 1–11 | 3.990291 | 8.203789 | 1–10 |
| Buying | 0.237344 | 0.128613 | 20.542344 | 1–11 | 4.142857 | 8.122449 | 1–10 |
| Browsing | 0.248594 | 0.100554 | 20.468594 | 1–11 | 4.432432 | 8.515705 | 1–10 |
| Intent Override | 0.240000 | 0.155116 | 12.072222 | 3–11 | 2.666667 | 5.222222 | 1–8 |
| Boundary | 0.250000 | 0.194337 | 22.410000 | 1–11 | 2.400000 | 5.440000 | 1–7 |

正式 micro 场景权重为 Buying 0.40、Browsing 0.40、Intent 0.15、Boundary 0.05。四场景等权 macro 仅作诊断：Hit `0.493750`、MRR `0.274671`、MTTC `6.685417`、Technical-like `0.415568`。

V2.1 Technical Score 的 Hit、MRR、Efficiency 分量分别为 `0.257500`、`0.074030`、`0.091000`，合计 `0.422530`。

## 6. 逐轮与运行性能

| Turn | 活跃会话 | 首次命中 | 累计命中 |
|---:|---:|---:|---:|
| 1 | 200 | 46 | 46 |
| 2 | 154 | 17 | 63 |
| 3 | 137 | 19 | 82 |
| 4 | 118 | 19 | 101 |
| 5 | 99 | 2 | 103 |
| 6–10 | 每轮 97 | 0 | 103 |

- 全量 trace 共 1,193 次调用，全部响应合法、无异常。
- `ask_attribute` 共 408 次；具体约束回答 81 次、无额外偏好 234 次、Boundary no-preference 6 次。
- turn 5 的 2 个新 hit 没有新增属性，来自固定重试消息改变 intent/route 选择，应归因于 fallback 路由行为，不是 clarification 成功。
- turn 6–10 仍有 485 次零收益调用；相邻 Top 10 完全重复 548 次。
- 单轮平均 60.844 ms、P95 166.539 ms、最大 1296.558 ms。V2 分别为 16.212、66.120、197.777 ms；V2.1 平均约 3.75 倍、P95 约 2.52 倍、最大约 6.56 倍。

详细案例见 [逐轮案例册](turn_casebook.md)。

## 7. 候选漏斗与 evidence

| 场景 | Hit | R1 纯召回 | R3 融合前截断 | F1 过滤误删 | K1 rank 11–20 | K1 rank 21–100 |
|---|---:|---:|---:|---:|---:|---:|
| Buying | 49 | 6 | 11 | 1 | 6 | 7 |
| Browsing | 37 | 6 | 12 | 0 | 10 | 15 |
| Intent Override | 12 | 7 | 3 | 0 | 4 | 4 |
| Boundary | 5 | 1 | 2 | 0 | 1 | 1 |
| Overall | 103 | 20 | 28 | 1 | 21 | 27 |

V2 的覆盖为 152/200，V2.1 为151/200，几乎不变；但候选内 miss 从70降到48，说明主要收益是候选到 Top 10 的转化。原先49个“候选缺失”经未截断route回放后可拆为R1 20、R3 28、F1 1。151个进入 filter 后候选的目标全部至少一次带有显式 evidence 和正 boost，但这不证明 boost 是全部收益来源，因为竞争商品也会获得 boost。97个miss的逐条证据见[未命中归因报告](miss_attribution.md)。

### 已证实的前融合截断

`retrieve_route_candidates(..., limit=100)` 按 route 顺序调用 `merge_candidates`；实现一旦收集到100个唯一 ASIN 就立即返回，后续 route 无法进入融合。Boundary 回归 `public_0104` 和 `public_0169` 在关键属性回答轮分别位于 `current_message` rank 1，也出现在多个字段/relaxed/fallback route，却因前序 route 先填满100个候选而被截掉。这是已证实的 R3 前融合候选截断，不是 evidence boost 排序失败。

## 8. Development-only 配置消融

除默认 light 外，其他配置仅在 development 150 条运行，未查看 holdout。

| 配置 | Hit@10 | MRR | MTTC | Technical | gained/lost vs light | shared rank ↑ / = / ↓ |
|---|---:|---:|---:|---:|---:|---:|
| equal | 0.513333 | 0.236183 | 6.493333 | 0.417655 | 0 / 0 | 7 / 62 / 8 |
| mild（无 evidence） | 0.513333 | 0.236976 | 6.500000 | 0.417759 | 0 / 0 | 5 / 65 / 7 |
| mild + tiny | 0.513333 | 0.238587 | 6.500000 | 0.418243 | 0 / 0 | 1 / 73 / 3 |
| mild + light（正式） | 0.513333 | 0.239040 | 6.500000 | 0.418379 | — | — |
| mild + medium | 0.513333 | 0.243577 | 6.500000 | 0.419740 | 0 / 0 | 3 / 74 / 0 |

新检索管线的 equal 相对 V2 development equal 已将 Hit 从0.373333升至0.513333，是主要增益来源。mild route 权重与 light evidence 只提供小幅 MRR 增益。Medium 在 development 上严格优于 light 的 shared rank churn，但在修复截断和延迟前不应打开 holdout。

## 9. 已证实、合理推断与证据边界

### 已证实

1. Overall、Buying、Browsing、Intent 三项指标改善；Boundary 三项均退化。
2. Development Technical 提高0.112797，holdout Technical 下降0.017617。
3. 36 gained / 15 lost 和 shared rank 22/22/23 表明版本 churn 很高，不能只看净 Hit。
4. 候选覆盖未提高，候选内 miss 减少22；V2.1 的主要净收益来自融合前候选结构与重排转化。
5. 前融合 sequential Top-100 截断会丢失后置 route 的高位目标，是可复现回归机制。

### 合理推断

1. 动态 route 和字段化检索扩大了单轮计算量，解释平均与尾延迟明显上升；仍需 route 级 profiling 才能分摊具体成本。
2. Holdout MRR 回归可能来自候选替换和 evidence 过强共同作用；现有数据不能把两者完全拆开。
3. Medium evidence 值得作为下一 development 候选，但必须先冻结候选集，否则无法单独归因。

### 证据边界

Runtime audit 能看到目标 evidence 和完整 rank，但没有人工相关性标签，不能断言所有前排竞争商品不相关。Ablation 只在 development 比较配置；除正式 light 外没有查看 holdout。V2.1 同时改变检索 route、候选预算、权重和 evidence，full-version 增益不能归给单一模块。

## 10. 交付索引与 Gate

- [组内交接说明](TEAM_HANDOFF.md)
- [97 个 miss 逐条归因](miss_attribution.md)
- [97 个 miss Scenario Type 与归因 Word 报告](V2.1_97_Misses_Scenario_Attribution_Report.docx)
- [V3 多维识别率提升路线图（Word）](V3_Multidimensional_Improvement_Roadmap.docx)
- [V3 99% Hit@10 数据规律与四人工作流](V3_99_Hit10_Team_Workflow.md)
- [逐轮案例册](turn_casebook.md)
- [V0–V2.1 横向对比](version_comparison.md)
- [1号专项](team/member_1_data_knowledge.md)
- [2号专项](team/member_2_state_policy.md)
- [3号专项](team/member_3_retrieval_filter.md)
- [4号专项](team/member_4_ranking_weights.md)

Gate 结论：保留 `0eb12aa` 作为实验候选，不替换 V2 final baseline。优先修复前融合 Top-100 截断并做 route 性能 profiling；随后在冻结候选集上单独评估 evidence medium，只有 holdout MRR/Technical 不再退化且 Boundary 恢复后才能升级。
