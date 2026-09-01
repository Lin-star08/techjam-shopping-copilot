# Failure Cases and Taxonomy

本文件由 5 号维护，用于把“没命中”转化为可定位、可验证的工程问题。Public ground truth 只允许在评估和错误分析阶段使用。

## v0 概览

| 场景 | Hits | Misses | 首要观察 |
|---|---:|---:|---|
| Buying | 19 | 61 | 有明确条件时 BM25 有一定效果，但仍存在大量召回/排序失败。 |
| Browsing | 2 | 78 | 初始消息信息少，无追问的单轮检索几乎失效。 |
| Intent Override | 4 | 26 | 无状态 Agent 不能可靠处理旧需求失效和新需求覆盖。 |
| Boundary | 0 | 10 | 无追问和 no-preference 策略，全部失败。 |
| Overall | 25 | 175 | 需要状态、有效追问、多路召回和重排共同改善。 |

## v1 概览

| 场景 | Hits | Misses | Δ Hits vs v0 | 首要观察 |
|---|---:|---:|---:|---|
| Buying | 20 | 60 | +1 | 新增 2 个、回归 1 个；候选覆盖提升未稳定转化为前十。 |
| Browsing | 2 | 78 | 0 | 零追问，702 个固定重试轮次，指标完全不变。 |
| Intent Override | 4 | 26 | 0 | MRR 略升但失败结构不变；13 个 pre-only、13 个 never-seen。 |
| Boundary | 0 | 10 | 0 | neutral 结构已存在但未被 end-to-end 触发。 |
| Overall | 26 | 174 | +1 | 状态/约束/多路召回已接线，顺序式 merge 和零追问成为主要瓶颈。 |

V1 详细证据见 `docs/reports/v1/README.md`。离线候选诊断与 Agent 正式 filter 路径不完全相同，未取得原生 route/filter trace 前，不对单条 miss 强制指定 R1、F1 或 K1。

## v1.1 概览

| 场景 | Hits | Misses | Δ Hits vs v1 | 候选内 miss | 候选缺失 | 首要观察 |
|---|---:|---:|---:|---:|---:|---|
| Buying | 24 | 56 | +4 net | 37 | 19 | RRF 明显增益，但 1 个 V1 hit 回归且 development MRR 下降。 |
| Browsing | 6 | 74 | +4 | 37 | 37 | 候选与排序各占一半，仍无追问后的命中。 |
| Intent Override | 5 | 25 | +1 | 15 | 10 | Holdout 首次命中，但 Full MRR 下降。 |
| Boundary | 3 | 7 | +3 | 5 | 2 | 推荐命中改善，但 no-preference 仍未触发。 |
| Overall | 38 | 162 | +12 net | 94 | 68 | 全路线 RRF 有效，下一瓶颈是显式需求权重、召回缺失和 clarification。 |

“候选内 miss”表示目标在至少一个有效轮次进入实际 filter 后候选，但完整 RRF rank 未进入 Top 10；“候选缺失”表示有效轮次均未进入该集合。V1.1 详细证据见 `docs/reports/v1.1/README.md`。

## v2 概览

| 场景 | Hits | Misses | Δ Hits vs v1.1 | 候选内 miss | 候选缺失 | 首要观察 |
|---|---:|---:|---:|---:|---:|---|
| Buying | 38 | 42 | +14 net | 25 | 17 | 追问新增10个后置命中，但仍有1个V1.1 hit回归。 |
| Browsing | 30 | 50 | +24 | 28 | 22 | 24个新增hit全部发生在turn 2–4，追问首次产生大规模收益。 |
| Intent Override | 8 | 22 | +3 net | 15 | 7 | 20/30在override前曾出现目标；生效后排序仍是主桶。 |
| Boundary | 6 | 4 | +3 | 2 | 2 | 6次no-preference端到端触发，但2个session从未提问。 |
| Overall | 82 | 118 | +44 net | 70 | 48 | clarification显著改善召回与排序输入；三问后仍有708次零收益调用。 |

V2 候选漏斗按“至少一个可计分轮次进入生产 hard filter 后集合”统计；runtime audit 的逐session hit、turn、rank与正式结果完全一致。观察到1个session在某个有效轮次被filter移除，但后续重新进入候选，因此不把最终失败简单归为F1。详细证据见 `docs/reports/v2/README.md`。

## v2.1 概览

| 场景 | Hits | Misses | Δ Hits vs v2 | 候选内 miss | 候选缺失 | 首要观察 |
|---|---:|---:|---:|---:|---:|---|
| Buying | 49 | 31 | +11 net | 13 | 18 | miss归因：R1 6 / R3 11 / F1 1 / K1 13。 |
| Browsing | 37 | 43 | +7 net | 25 | 18 | miss归因：R1 6 / R3 12 / K1 25。 |
| Intent Override | 12 | 18 | +4 net | 8 | 10 | miss归因：R1 7 / R3 3 / K1 8。 |
| Boundary | 5 | 5 | -1 net | 2 | 3 | miss归因：R1 1 / R3 2 / K1 2。 |
| Overall | 103 | 97 | +21 net | 48 | 49 | miss归因：R1 20 / R3 28 / F1 1 / K1 48。 |

V2.1新增R3证据：候选在某个启用route内已被召回，但按route顺序收集前100个唯一ASIN时，后置route尚未合并就被截断。97个miss已按互斥主因逐条重放，详见`docs/reports/v2.1/miss_attribution.md`。`public_0104`、`public_0169`仅作证明机制与回归测试的案例，不得硬编码。

## Failure Taxonomy

每个失败案例选择一个主因，可以添加次因，但不要重复计数。

| Code | 类型 | 判定标准 | 主要责任模块 | 推荐证据 |
|---|---|---|---|---|
| E1 | Agent 异常/非法输出 | `respond` 抛异常，或 message/recommendations 结构非法 | 集成/交付 | trace 中的 error、raw response |
| S1 | 状态未更新 | 用户新条件没有进入 current state | State Manager | 每轮 state snapshot |
| S2 | 旧意图污染 | override 后旧条件仍参与过滤、召回或排序 | State Manager | invalidated/current state、matched terms |
| S3 | Neutral 处理错误 | 用户无偏好后仍重复追问或继续施加该条件 | State/Clarification | asked/neutral、后续 ask_attribute |
| C1 | 约束解析错误 | 明确条件被分错字段、硬软等级或值 | Parser/Filter | parsed constraints、原始消息 |
| F1 | Hard filter 误删 | 目标原本在候选中，过滤后消失 | Hard Filter | filter 前后候选、filter reason |
| R1 | 召回缺失 | 所有召回路线都未找回目标 | Retrieval | 每条 route 的候选 ID/rank |
| R2 | 路线覆盖不足 | 目标只在某条路线可找回，但该路线缺失或权重过低 | Retrieval/Fusion | route、route_rank、route_score |
| R3 | 前融合候选截断 | 目标已在启用route中召回，但在统一融合前因总量/顺序截断丢失 | Retrieval/Fusion | 未截断route列表、merge前后ASIN、route顺序 |
| K1 | 排序失败 | 目标已召回，但最终不在 Top 10 | Fusion/Rerank | pre-rerank rank、final rank/score |
| K2 | 排名偏后 | 已命中 Top 10，但排名明显落后于相关性更低商品 | Rerank | Top 10 特征与 score 分解 |
| Q1 | 追问无价值 | 问题没有缩小候选或无法获得新约束 | Clarification | ask_attribute、回复、候选数量变化 |
| Q2 | 重复追问 | 已问过或已 neutral 的属性再次被询问 | Clarification | asked/neutral 历史 |
| D1 | 数据缺失/稀疏 | price、description、features 等缺失导致无法可靠判定 | Data/Parser | 商品字段完整性 |
| P1 | Profile 过强 | 画像弱信号压过用户当前明确表达 | Rerank | profile 与 explicit score 分量 |
| O1 | 其他/待定 | 当前 trace 仍不足以归因 | 5 号复盘 | 缺少的证据和下一步采集计划 |

## 分析步骤

1. 从正式 results 中筛出 miss 或排名靠后的 hit。
2. 使用独立 trace runner 重放指定 `sample_id`，不要修改官方 evaluator。
3. 检查异常、状态、过滤、各召回路线、最终排序、追问，按顺序定位第一个错误环节。
4. 记录一个主 failure code、证据、负责人和建议实验。
5. 修复后用相同 sample 重放，再跑完整 development 与 holdout，避免只修单例。

示例命令：

```bash
python3 -m evaluator.debug_trace \
  --sample-id public_0002 \
  --output /tmp/public_0002_trace.json
```

## 案例记录模板

### `sample_id` / 版本

- 场景：
- Git commit：
- 结果：miss / hit@rank / first-hit turn
- 主 failure code：
- 次 failure code：
- 关键轮次：
- 证据：
- 建议负责人：
- 建议的单变量实验：
- 修复后复测结果：
