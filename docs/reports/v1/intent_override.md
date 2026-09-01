# v1 Intent Override 场景分析报告

## 1. 场景与指标

Intent Override 在第 3 或第 4 轮声明新需求；生效前的推荐不能计分。V1 已有 `SessionState`、`invalidated_slots` 和 override 解析，但最终候选顺序仍以当前消息路线为先。

| 数据范围 | 样本数 | Hits | Misses | Hit@10 | MRR | MTTC |
|---|---:|---:|---:|---:|---:|---:|
| Full public | 30 | 4 | 26 | 0.133333 | 0.111111 | 10.066667 |
| Development | 23 | 4 | 19 | 0.173913 | 0.144928 | 9.782609 |
| Internal holdout | 7 | 0 | 7 | 0.000000 | 0.000000 | 11.000000 |

Hit@10 与 V0 完全相同；MRR 从 0.104167 升至 0.111111，唯一关键变化是 `public_0046` 从 rank 8 升至 rank 3。4 个有效命中仍全部发生在第 4 轮，排名为 1、1、1、3。

## 2. 未识别原因

### 已证实

1. 30 条中有 16 条在 override 生效前出现过目标，但提前命中按 evaluator 规则不计分。
2. 26 个 miss 仍精确分为：13 个只在 override 前出现、生效后消失；13 个从未进入任意一轮 Top 10。与 V0 的失败结构完全相同。
3. V1 虽保存 session state，但 30 条场景没有新增命中，internal holdout 仍为 0/7。
4. override 后 `current_message` 路线仍排在 `current_state` 和 `category` 之前；`merge_candidates` 不做 RRF，后置路线不能把多路线支持转化为更高最终分数。
5. `SessionState._replace_active` 只替换“同一 attribute”的旧值。如果“ignore earlier preference”从旧 feature/style 切到新 material，旧的不同属性软偏好不会被这条 override 自动整体作废。
6. 216 个通用重试轮次中 `ask_attribute` 全为 null；override 首轮失败后没有额外信息增益。

### 合理推断

1. 状态能力存在但被候选合并顺序弱化，是 Hit@10 没有变化的主要嫌疑：保留的类别在 state/category 路线中，当前轮单个高频材质词却优先占据最终候选。
2. `public_0046` 的 wool 区分度较高，V1 过滤/字段权重把它从 rank 8 推到 3；这只改善 MRR，不能证明 override 机制已普遍生效。
3. 对跨属性 override，仅按同属性 invalidation 可能保留已被用户否定的旧偏好，未来接入真正 RRF/重排后可能形成 S2 旧意图污染。

### 证据边界

当前 full trace 没有输出逐轮 state、route rank、filter reason 和 score 分解，所以不能仅凭 final Top 10 判定某条失败究竟是解析、状态、召回还是排序。候选诊断的 Intent 统计可能选中 override 前的最佳轮次，不得当作“生效后 candidate recall”。下一版必须按 eligible turn 单独记录候选漏斗。

## 3. 代表性 public 案例

以下案例仅用于错误分析，不得转化为 public set 特判。

| Sample | V1 结果 | 观察 |
|---|---|---|
| `public_0004` | 生效前 rank 1，override 后 miss | Tops & Tees 的旧描述能找到目标；切换为 polyester 后目标消失，状态/类别证据没有进入最终 Top 10。 |
| `public_0046` | 第 4 轮 rank 3 | wool override 从 V0 rank 8 提升到 3，是排序改善案例，但没有增加 Hit 数。 |
| `public_0002` | 全程 miss | leather override 未使目标进入 Top 10，代表 13 个“从未出现”案例。 |

## 4. 5 人分工修改建议

| 成员 | 修改建议 | 预期交付 | 验收标准 |
|---|---|---|---|
| 1号 | 补齐 override 常见属性及类别联用词典，区分高频材质与高区分 feature。 | override 词典、类别—属性组合建议 | 来自 catalog，不使用 public target；列出覆盖率和歧义。 |
| 2号 | 明确定义句级 override：哪些旧槽位继续有效、哪些旧 soft preference 应整体失效；输出逐轮 state snapshot。 | override 状态规范与测试 | 同属性旧值进入 invalidated；“ignore earlier preference”不残留被否定的旧软偏好；类别按规则保留。 |
| 3号 | 生成“保留类别 + 新值”的专用 route，并使正式 Agent 与诊断共享同一 pipeline。 | eligible-turn route trace、候选漏斗 | 生效后 query 同时包含有效类别和新值；可区分 R1/F1。 |
| 4号 | 接入 recency-aware RRF；新明确值最高权重，invalidated 值权重为 0。 | override rerank、score breakdown | score 中无失效值贡献；13 个 pre-only miss 至少有部分转为生效后命中，且提前命中仍不计分。 |
| 5号 | 固定检查 turn 3/4 eligibility、pre-only、never-seen 和 holdout 0/7。 | Intent churn 表、dev/holdout 报告 | 每条 miss 有阶段标签；holdout 有改善；不得通过提前推荐虚增分数。 |

## 5. V2 观察指标

- Override 生效后的 Candidate Recall@50/100、Hit@10 和 MRR，禁止与生效前轮次混算。
- `invalidated_slots` 在 query/filter/final score 中的泄漏次数，目标为 0。
- 13 个 pre-only miss 的转化率、13 个 never-seen miss 的候选覆盖率。
- Internal holdout 7 条逐条 trace；V1 仍为 0/7，是明确 gate。
