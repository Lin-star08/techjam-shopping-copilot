# v1 State + Retrieval 四场景分析总览

## 1. 版本范围

本目录评估 Git commit `c8b4812` 上的 V1。相对 V0，V1 已接入商品词典、约束解析、会话状态、安全 hard filter 和多路召回；`starter/ranking.py` 中虽已有 RRF 实现，但 `Agent.respond` 尚未调用它，当前最终顺序仍由 `merge_candidates` 的路线先后决定。Agent 仍固定返回 `ask_attribute=null`。

报告只用于错误分析和下一轮实验设计。文中 public `sample_id`、目标标题及隐藏意图不得进入 Agent、索引、规则或参数调优逻辑。

## 2. 数据与复现

- 正式结果：`results/v1-state.json`
- 对比基线：`results/v0-baseline.json`
- 固定切分：`docs/internal_split.json`（development 150 / internal holdout 50）
- 正式命令：`python3 -m evaluator.local_evaluator --output results/v1-state.json`
- 全量 trace：`python3 -m evaluator.debug_trace --all --output /tmp/v1_all_traces.json`
- 候选诊断：`python3 tools/diagnose_retrieval.py`
- 测试：`python3 -m unittest discover -s tests -v`，57/57 通过
- 运行时间：约 28.46 秒；token 和 API 成本均为 0

## 3. 总体结果与 V0 对比

| 数据范围 | 样本数 | V1 Hit@10 | Δ vs V0 | V1 MRR | Δ vs V0 | V1 MTTC | Δ vs V0 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Full public | 200 | 0.130000 | +0.005000 | 0.068942 | +0.000908 | 9.760000 | -0.050000 |
| Development | 150 | 0.113333 | +0.006666 | 0.065886 | -0.003233 | 9.946667 | -0.066666 |
| Internal holdout | 50 | 0.180000 | +0.000000 | 0.078111 | +0.013333 | 9.200000 | +0.000000 |

| 场景 | 样本 | Hits / Misses | Hit@10 | Δ | MRR | Δ | MTTC | Δ | 报告 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Buying | 80 | 20 / 60 | 0.250000 | +0.012500 | 0.126176 | -0.000332 | 8.500000 | -0.125000 | [查看](buying.md) |
| Intent Override | 30 | 4 / 26 | 0.133333 | 0 | 0.111111 | +0.006944 | 10.066667 | 0 | [查看](intent_override.md) |
| Browsing | 80 | 2 / 78 | 0.025000 | 0 | 0.004514 | 0 | 10.750000 | 0 | [查看](browsing.md) |
| Boundary | 10 | 0 / 10 | 0 | 0 | 0 | 0 | 11.000000 | 0 | [查看](boundary.md) |

## 4. 结论

### 已证实

1. V1 共命中 26 条，比 V0 净增 1 条：`public_0053`、`public_0065` 从 miss 变为 Buying hit，`public_0156` 从 V0 rank 1 退化为 miss。
2. 22 个命中发生在第 1 轮，4 个 Intent Override 命中发生在第 4 轮；V1 仍没有靠追问实现的后续收敛。
3. 200 条会话、1,778 个响应均合法且无异常，但非空 `ask_attribute` 为 0。
4. 失败后仍有 1,548 个通用重试轮次：Buying 540、Intent Override 216、Browsing 702、Boundary 90。
5. evaluator 的固定重试句没有被 `is_generic_message` 判为 generic；`current_message` 路线因此排在最前，`merge_candidates` 又按首次出现顺序截断。所有通用重试轮次最终仍返回同一组 Top 10，已保存的状态没有进入最终前十。
6. 重建候选池诊断显示目标进入候选 Top 100 的比例明显高于最终 Hit@10：Buying 0.625、Browsing 0.3375、Boundary 0.7；说明候选池到最终 Top 10 的损失很大。

### 合理推断

1. V1 的小幅增益主要来自部分明确条件的过滤，而不是多轮状态或真正的多路线融合。
2. `merge_candidates` 的路线优先顺序支配最终排名；后置的 state/category/profile 路线即使找回目标，也可能无法改变 Top 10。
3. Intent Override 的状态结构已经存在，但类别和新值能否被正确解析、进入有效约束，以及能否参与最终排序仍不稳定。

### 证据边界

正式结果和全量 trace 只保存最终 Top 10。候选诊断是按当前检索函数重建的离线观测，不是 Agent 自身逐轮导出的 route/score 日志；其中 Intent Override 的统计还可能选到生效前的最佳轮次，且诊断 filter 只读取 `state.hard_constraints`，与 Agent 的 fallback 约束路径不完全相同。因此候选召回比例可用于定位“最终排序存在损失”，但不能直接给每个 miss 强行归因，也不能据此证明 hard filter 从未误删目标。

## 5. V1 Gate 结论

V1 可作为“状态、约束和多路召回已接线”的中间版本保留，但不应直接作为 final：总体提升只有 1/200，development MRR 下降，Browsing/Boundary 完全不变，并出现 1 条原 rank-1 回归。下一实验应优先接入真实融合排序和 clarification policy，并分别做单变量 ablation。
