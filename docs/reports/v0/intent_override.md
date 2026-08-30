# v0 Intent Override 场景分析报告

## 1. 场景与指标

Intent Override 会先表达旧偏好，再在第 3 或第 4 轮给出新的有效条件。官方规则不允许在新意图发送前计为命中。系统需要保留仍有效的类别，作废旧条件，并用新条件重新检索。

| 数据范围 | 样本数 | Hits | Misses | Hit@10 | MRR | MTTC |
|---|---:|---:|---:|---:|---:|---:|
| Full public | 30 | 4 | 26 | 0.133333 | 0.104167 | 10.066667 |
| Development | 23 | 4 | 19 | 0.173913 | 0.135870 | 9.782609 |
| Internal holdout | 7 | 0 | 7 | 0.000000 | 0.000000 | 11.000000 |

30 条中，12 条在第 3 轮发生 override，18 条在第 4 轮发生 override。4 个有效命中全部发生在第 4 轮，排名分别为 1、1、1、8。

## 2. 目标未识别的原因

### Trace 已证实

1. 30 条会话中有 16 条曾在 override 生效前把目标放进 Top 10，但这些结果按规则不能计分。
2. 26 个 miss 可精确分成两组：13 个目标只在生效前出现、生效后消失；另外 13 个目标从未进入任何一轮 Top 10。
3. Agent 没有提出任何追问，失败会话累计产生 216 个通用重试轮次。
4. v0 没有状态快照；`reset` 不保存 profile 或槽位，`respond` 只读取当前一轮 `user_message`。
5. 全部响应合法且无异常，失败不是接口错误。

### 结合实现的合理推断

1. override 消息通常只包含新条件，例如 `leather` 或 `polyester`，不再包含原始类别。v0 只搜索当前消息，因而丢失仍然有效的类别上下文。
2. v0 并没有把历史拼接进查询，所以当前版本的主要问题不是“旧条件污染”，而是“完全没有显式状态”。但未来一旦引入 history/state，如果不维护 `invalidated`，旧条件污染会成为高风险回归。
3. 新条件常是高频材质或功能词；不与类别组合时搜索范围过宽，目标容易掉出 Top 10。
4. 没有 override 专用重排规则，无法保证新明确条件压过旧偏好、profile 或其他软信号。

### 当前不能确认

对于生效后未进入 Top 10 的目标，现有日志无法判断它们是完全未召回，还是排在第 11 名以后。对于生效前已出现但生效后消失的 13 条，可以确认上下文切换改变了 Top 10，但不能仅凭最终列表确定具体是类别丢失、词法竞争还是排序权重导致。

## 3. 代表性案例

以下案例只用于错误分析，不得写入 Agent 规则。

| Sample | Override 行为 | 结果 | 观察 |
|---|---|---|---|
| `public_0004` | 第 3 轮由长款 camisole 偏好切换为 `polyester` | 第 1 轮目标 rank 1，但生效后不再进入 Top 10，最终 miss | 典型的“生效前找到、生效后丢失”；新消息没有携带 Tops & Tees 类别。 |
| `public_0002` | 第 3 轮由 buckle 偏好切换为 `leather` | 全程未进入 Top 10 | 单独搜索高频材质词不足以定位目标男士皮带。 |
| `public_0046` | 第 4 轮切换为 `wool` | 第 4 轮 rank 8 命中 | 新条件具有较强区分度时，无状态 BM25 仍可能偶然成功。 |

## 4. 按团队分工的修改意见

| 成员 | 修改建议 | 预期交付 | 验收标准 |
|---|---|---|---|
| 1号：数据洞察与商品知识 | 整理材质、用途、closure、feature 等 override 常见属性及同义表达。 | override 属性词典、歧义说明、类别关联建议 | 词典从 catalog 可见字段生成；不使用 public target 建立商品 ID 规则。 |
| 2号：对话状态与策略 | 实现 `current_slots`、`invalidated`、`asked`、`neutral`；新值覆盖旧值但保留无冲突类别。 | State Manager、turn 3/4 场景测试、状态快照 | override 后旧值不再出现在 current state；类别保留；新值成为当前明确条件。 |
| 3号：检索与约束工程 | 使用 current state 构造“保留类别 + 新条件”查询，并提供 current-message/current-state 两条路线。 | override retrieval、统一候选及 route 证据 | override 后查询不只包含单个材质词；目标候选可追踪来自哪条路线。 |
| 4号：融合排序与调参 | 新明确条件设为最高优先级，旧条件权重归零；融合时避免 profile 抵消新意图。 | recency-aware rerank、score 分解、权重 ablation | final score 中看不到 invalidated 旧值贡献；新明确条件违反项显著降权。 |
| 5号：评估实验与交付 | 固定 turn 3/4 回归集，分别检查生效前不可计分、生效后命中、旧值污染。 | override trace 表、dev/holdout 指标、失败分类更新 | 所有提前命中仍不计分；holdout 不再保持 0/7；每个 miss 能区分状态、候选或排序阶段。 |

## 5. 下一版本观察项

- override 生效后目标进入候选池和最终 Top 10 的比例。
- `invalidated` 旧值在 query、matched terms、filter reason、final score 中的出现次数，应为 0。
- 第 3/4 轮首次命中率和 MTTC。
- Development 与 holdout 分开记录；当前 holdout 7 条全 miss，样本少但必须作为回归报警信号。
