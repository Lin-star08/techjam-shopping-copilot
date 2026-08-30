# v0 Baseline 四场景分析总览

## 1. 分析目的

本目录分析弱 BM25 baseline 在 Buying、Intent Override、Browsing 和 Boundary 四类场景中的表现，解释目标商品未进入有效 Top 10 的已知原因，并把改进方向映射到 5 人团队分工。

报告只用于错误分析和下一阶段实验设计。文中出现的 public `sample_id`、目标标题和隐藏意图信息不得进入 Agent、检索索引、规则或参数调优逻辑。

## 2. 数据来源与方法

- 正式结果：`results/v0-baseline.json`
- 固定切分：`docs/internal_split.json`
- Agent：SQLite FTS5 BM25，仅使用当前轮消息，无状态、无追问、无画像使用
- Trace：使用 `python3 -m evaluator.debug_trace --all` 在临时目录重放 200 条会话

Trace 复核结果：200 条会话共命中 25 条；Agent 无异常和非法响应，但 `ask_attribute` 始终为 `null`。所有失败后的通用反馈轮次都搜索同一句话，并返回完全相同的一组 Top 10。

## 3. 总体与分场景结果

| 数据范围 | 样本数 | Hit@10 | MRR | MTTC |
|---|---:|---:|---:|---:|
| Full public | 200 | 0.125000 | 0.068034 | 9.810000 |
| Development | 150 | 0.106667 | 0.069119 | 10.013333 |
| Internal holdout | 50 | 0.180000 | 0.064778 | 9.200000 |

| 场景 | 样本数 | Hits | Misses | Hit@10 | MRR | MTTC | 报告 |
|---|---:|---:|---:|---:|---:|---:|---|
| Buying | 80 | 19 | 61 | 0.237500 | 0.126508 | 8.625000 | [查看](buying.md) |
| Intent Override | 30 | 4 | 26 | 0.133333 | 0.104167 | 10.066667 | [查看](intent_override.md) |
| Browsing | 80 | 2 | 78 | 0.025000 | 0.004514 | 10.750000 | [查看](browsing.md) |
| Boundary | 10 | 0 | 10 | 0.000000 | 0.000000 | 11.000000 | [查看](boundary.md) |

## 4. 跨场景结论

### 已证实

1. 25 个命中中，21 个发生在第 1 轮，另外 4 个发生在 Intent Override 的第 4 轮。v0 基本没有有效的多轮收敛能力。
2. Agent 在全部 200 条会话中没有提出任何结构化追问。
3. 失败后累计出现 1,557 个通用重试轮次：Buying 549、Intent Override 216、Browsing 702、Boundary 90。
4. 通用重试消息完全相同；无状态 BM25 因此反复返回同一组 Top 10，后续轮次没有信息增益。
5. `reset` 不使用 `user_profile`，除记录 session ID 外不保存任何对话状态。

### 合理推断

1. Buying 的明确约束只是 FTS OR 查询中的普通词，类别或常见词命中可能压过真正同时满足约束的商品。
2. Browsing 和 Boundary 的初始类别信息不足；没有追问时，继续增加轮次不会改善候选。
3. Intent Override 只搜索新一轮文本，导致类别等仍然有效的上下文丢失。

### 证据边界

v0 只输出最终 Top 10，没有保存更大的召回池、route、pre-rerank rank 或 score 分解。因此“目标未进入 Top 10”只能确认最终候选缺失，不能进一步确定它是完全未被召回，还是被召回后排在第 11 名及以后。各报告不会把这种情况武断标记为纯召回失败或纯排序失败。

## 5. 建议优先级

1. 先解决对话状态、有效追问和通用重试死循环。
2. 再加入高置信 hard filter 与多路召回，确保目标进入候选池。
3. 最后通过可解释融合和重排改善 MRR。
4. 每个主要能力单独做 ablation，并同时检查 development、holdout 与四类场景。
