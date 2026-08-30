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
