# v1.1 RRF 四场景分析总览

## 1. 版本范围

本目录评估 Git commit `5e4e8ae`。相对 V1 commit `c8b4812`，产品代码只修改 `starter/agent.py`：将各 route 候选展开、按 ASIN 做一次安全过滤，再把保留的全部 route evidence 交给 `rerank_candidates` 做 RRF。

这个集成同时移除了 V1 `merge_candidates(limit=100)` 的提前截断，因此实验应解释为“RRF 接线 + 全路线候选进入融合”，不能把全部收益只归因于 RRF 公式。

报告仅用于错误分析。public `sample_id`、目标商品和隐藏意图不得写入 Agent、索引、规则或调参逻辑。

## 2. 数据与复现

- 正式结果：`results/v1.1-rrf.json`
- 对比版本：`results/v1-state.json`
- 固定切分：`docs/internal_split.json`（development 150 / internal holdout 50）
- 正式命令：`python3 -m evaluator.local_evaluator --output results/v1.1-rrf.json`
- 全量 trace：`python3 -m evaluator.debug_trace --all --output /tmp/v1.1_all_traces.json`
- 候选漏斗：在临时目录运行 runtime hook，记录实际 Agent filter 前后集合及完整 RRF rank；未修改仓库代码
- 测试：`python3 -m unittest discover -s tests -v`，60/60 通过
- 正式运行时间：31.82 秒；token/API 成本为 0

## 3. 总体结果

| 数据范围 | 样本数 | V1.1 Hit@10 | Δ vs V1 | V1.1 MRR | Δ vs V1 | V1.1 MTTC | Δ vs V1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Full public | 200 | 0.190000 | +0.060000 | 0.093456 | +0.024514 | 9.180000 | -0.580000 |
| Development | 150 | 0.153333 | +0.040000 | 0.067053 | +0.001167 | 9.546667 | -0.400000 |
| Internal holdout | 50 | 0.300000 | +0.120000 | 0.172667 | +0.094556 | 8.080000 | -1.120000 |

| 场景 | Hits / Misses | Hit@10 | Δ | MRR | Δ | MTTC | Δ | 报告 |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Buying | 24 / 56 | 0.300000 | +0.050000 | 0.154563 | +0.028387 | 8.000000 | -0.500000 | [查看](buying.md) |
| Intent Override | 5 / 25 | 0.166667 | +0.033334 | 0.097778 | -0.013333 | 9.833333 | -0.233334 | [查看](intent_override.md) |
| Browsing | 6 / 74 | 0.075000 | +0.050000 | 0.021161 | +0.016647 | 10.250000 | -0.500000 | [查看](browsing.md) |
| Boundary | 3 / 7 | 0.300000 | +0.300000 | 0.170000 | +0.170000 | 8.100000 | -2.900000 | [查看](boundary.md) |

## 4. 描述性统计与加权口径

以下方差均为 population variance（除以 N）；miss 的完成轮次按 evaluator 记为 11。Hit 是 0/1 变量，其方差等于 `p(1-p)`。

| 范围 | Hit 方差 | RR 方差 | 完成轮次方差 | 完成轮次极值 | 命中 rank 均值 | rank 方差 | rank 极值 |
|---|---:|---:|---:|---|---:|---:|---|
| Overall | 0.153900 | 0.062422 | 14.317600 | 1–11 | 3.894737 | 9.041551 | 1–10 |
| Buying | 0.210000 | 0.100325 | 21.000000 | 1–11 | 3.875000 | 9.026042 | 1–10 |
| Browsing | 0.069375 | 0.007464 | 6.937500 | 1–11 | 5.000000 | 8.000000 | 2–10 |
| Intent Override | 0.138889 | 0.069477 | 6.805556 | 4–11 | 3.400000 | 11.440000 | 1–10 |
| Boundary | 0.210000 | 0.100100 | 19.690000 | 1–11 | 2.666667 | 2.888889 | 1–5 |

V1.1 的 Overall 完成轮次方差高于 V1 的 10.442400，因为更多 turn-1 hit 与仍存在的 turn-11 miss 拉开了两端；它不能单独解释为运行不稳定。命中 rank 方差由 V1 的 10.692308 降至 9.041551，是更直接的排名离散度改善信号。

正式总体是按样本数加权的 micro 指标：Buying 0.40、Browsing 0.40、Intent 0.15、Boundary 0.05。作为场景公平性诊断，四场景等权 macro 为 Hit 0.210417、MRR 0.110876、MTTC 9.045833；macro 不替代官方成绩。

官方 Technical Score 固定为 `0.50×Hit + 0.30×MRR + 0.20×Efficiency`，V1.1 三项贡献分别为 0.095000、0.028037、0.036400，总计 0.159437。完整权重与版本解释见 [横向版本报告](version_comparison.md)。

## 5. 已证实结论

1. V1.1 共命中 38 条，相对 V1 新增 13 条、丢失 1 条，净增 12 条。四个场景 Hit@10 均提高。
2. 38 个命中分布为 turn 1 共 32 条、turn 2 共 1 条、turn 4 共 5 条。`public_0041` 是首个由已保存状态改变后续结果而在第 2 轮命中的案例，但该轮没有获得新的用户属性。
3. 1,674 个响应全部合法且无异常，`ask_attribute` 仍全部为 null。
4. 通用重试轮次由 V1 的 1,548 降至 1,444；这些轮次的推荐结果从全局唯一 1 组增加为 61 组，证明 state/category 等后置 route 已能影响最终排序。
5. 对至少一个有效轮次的真实候选漏斗：Buying 61/80 个目标在 filter 后候选中、24 个进 Top 10；Browsing 43/80→6；Intent 20/30→5；Boundary 8/10→3。
6. V1 唯一丢失命中为 Buying `public_0053`：目标仍在 filter 后候选中，但最佳 RRF rank 为 13，因此可确认为 K1 排序回归。

## 6. 合理推断与证据边界

### 合理推断

1. 多路线共同支持的商品获得 RRF 累积分，解释了 Boundary、Browsing 和 Buying 的普遍增益。
2. 等权 RRF 不理解需求强弱；只在一条高质量 current-message route 中出现的目标，可能输给多个弱 route 重复出现的商品，`public_0053` 是实际风险。
3. holdout 增幅远大于 development，说明方向有效但方差较大，不能据此直接锁定最终权重。

### 证据边界

候选漏斗通过临时 runtime hook 观察当前 Agent 的实际 filter 输入输出和完整 RRF rank，未进入正式结果文件。它能区分“候选不存在”和“候选存在但排在 Top 10 外”，但还没有保存每个非目标商品的显式需求匹配分、route 权重贡献或相关性标签，因此不能证明某个竞争商品一定不相关。一次会话的目标也可能在某轮被 filter 排除、在另一轮重新出现，filter 风险必须按轮次审计。

## 7. 扩展交付索引

- [组内交接说明：文件位置与成员使用方法](TEAM_HANDOFF.md)
- [逐轮成功/失败案例册](turn_casebook.md)
- [V0 / V1 / V1.1 横向对比](version_comparison.md)
- [1号：数据词典与商品知识](team/member_1_data_knowledge.md)
- [2号：状态、Override、Neutral 与追问](team/member_2_state_policy.md)
- [3号：检索、Hard Filter 与 Fallback](team/member_3_retrieval_filter.md)
- [4号：融合、重排与权重实验](team/member_4_ranking_weights.md)

## 8. Gate 结论

V1.1 应保留并作为下一版本基线：总体、development、holdout 及四场景 Hit 都提高，Technical Score 从 0.110483 升至 0.159437。不过 Intent MRR 下降、Buying 有 1 个命中回归，clarification 仍完全缺失。下一步应将“显式需求加权”和“追问策略”拆成两个独立实验。
