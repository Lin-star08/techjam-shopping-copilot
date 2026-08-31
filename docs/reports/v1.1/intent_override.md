# v1.1 Intent Override 场景分析报告

## 1. 指标与命中分布

| 数据范围 | 样本数 | Hits | Misses | Hit@10 | MRR | MTTC |
|---|---:|---:|---:|---:|---:|---:|
| Full public | 30 | 5 | 25 | 0.166667 | 0.097778 | 9.833333 |
| Development | 23 | 4 | 19 | 0.173913 | 0.123188 | 9.782609 |
| Internal holdout | 7 | 1 | 6 | 0.142857 | 0.014286 | 10.000000 |

相对 V1 新增 1 个 holdout 命中，但 Full MRR 从 0.111111 降至 0.097778。5 个有效命中全部发生在 turn 4，排名为 1、1、2、3、10。

描述性统计（population variance）：Hit 方差 0.138889；RR 方差 0.069477；完成轮次均值 9.833333、方差 6.805556、标准差 2.608746、极值 4–11；5 个命中的 rank 均值 3.400000、方差 11.440000、极值 1–10。rank 方差较高正是 rank-10 新命中与高位命中并存的结果。

## 2. 未识别原因

### 已证实

1. 25 个 miss 分为：12 个目标只在 override 生效前出现、生效后消失；13 个目标从未进入任何轮次最终 Top 10。V1 的 pre-only 数由 13 降到 12，never-seen 仍为 13。
2. 至少一个有效轮次中，20/30 个目标进入 filter 后候选，完整 RRF Top 50 有 11 个、Top 10 有 5 个；因此 15 个 miss 属于候选内排序损失，10 个是有效轮次候选缺失。
3. 新命中 `public_0125` 在 turn 1 已 rank 3，但按规则不能计分；override 后 turn 4 以 rank 10 合法命中。
4. shared hits 中 `public_0046` rank 3→2，`public_0166` rank 1→3，另外两条不变。新增的 rank-10 命中不足以抵消已有高排名下降，所以 MRR 下降。
5. 210 个通用重试轮次没有追问；所有有效命中仍只发生在 override 消息到达当轮。
6. RRF 能利用保留的 category/current-state route，但 state 的跨属性 override 语义没有变化：只替换同 attribute 旧值。

### 合理推断

1. 当前等权 RRF 改善了生效后候选组合，但对“新值必须高于旧软偏好”的 recency 优先级表达不足。
2. 15 个候选内 miss 中，部分目标只来自 category 或单一 route；需要专门的“保留类别 + 新值”联合 route，而不是单纯降低 RRF cutoff。
3. holdout 首次从 0/7 变为 1/7 是正向信号，但唯一命中为 rank 10，稳定性仍弱。

### 证据边界

候选漏斗只统计 override 已生效的 eligible turns，因此可以区分生效后候选缺失与排序损失；但缺少逐属性 state/score 快照，尚不能把 15 个候选内 miss 进一步全部判为旧意图污染或新值权重不足。

## 3. 代表性 public 案例

以下案例只用于错误分析，不得转化为 public set 硬编码。

| Sample | V1 → V1.1 | 观察 |
|---|---|---|
| `public_0125` | miss → turn 4 rank 10 | Acrylic override 带来首个 holdout 命中，但排名处于边界。 |
| `public_0046` | rank 3 → rank 2 | Wool override 得到多路线融合增益。 |
| `public_0166` | rank 1 → rank 3 | 仍命中但高位回退，说明等权 RRF 不保证新明确需求的最优排名。 |

## 4. 5 人分工修改建议

| 成员 | 修改建议 | 预期交付 | 验收标准 |
|---|---|---|---|
| 1号 | 标注 override 新值在 category/material/feature 中的区分度和同义表达。 | Override 属性覆盖表 | 来自 catalog；不依据 public target 调词。 |
| 2号 | 定义句级 override 的保留/失效范围并输出逐轮 state snapshot。 | override 状态规范、测试 | 新值生效；被否定软偏好不残留；仍有效类别保留。 |
| 3号 | 增加“类别 + 新值”专用 route，并追踪 10 个候选缺失案例的通用模式。 | eligible-turn recall ablation | Candidate Recall 提升；只统计 override 后轮次。 |
| 4号 | RRF 加 recency/explicit 权重，invalidated 值贡献必须为 0。 | override score breakdown | Full/Development MRR 不低于 V1；新命中不只停留在 rank 10。 |
| 5号 | 同时维护 pre-only、never-seen、candidate-miss 和 rank churn。 | Intent gate 表 | 提前命中不计分；holdout 保持非零；高位命中回退必须报警。 |

## 5. 下一版本观察项

- Eligible-turn Candidate Recall@50/100、Top 10 和 MRR。
- Override 新值、保留类别、invalidated 旧值的独立 score 分量。
- 12 个 pre-only 与 13 个 never-seen 的分别转化率。
- Holdout 1/7 的重复运行稳定性及 rank 10 边界风险。
