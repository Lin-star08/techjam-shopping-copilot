# v1.1 Boundary 场景分析报告

## 1. 指标与命中分布

| 数据范围 | 样本数 | Hits | Misses | Hit@10 | MRR | MTTC |
|---|---:|---:|---:|---:|---:|---:|
| Full public | 10 | 3 | 7 | 0.300000 | 0.170000 | 8.100000 |
| Development | 7 | 1 | 6 | 0.142857 | 0.028571 | 9.571429 |
| Internal holdout | 3 | 2 | 1 | 0.666667 | 0.500000 | 4.666667 |

相对 V1 从 0/10 提升到 3/10，排名分别为 1、2、5；两个命中在 turn 1，一个命中在 turn 2。由于 holdout 只有 3 条，2/3 的结果不能当作稳定总体估计。

描述性统计（population variance）：Hit 方差 0.210000；RR 方差 0.100100；完成轮次均值 8.100000、方差 19.690000、标准差 4.437342、极值 1–11；3 个命中的 rank 均值 2.666667、方差 2.888889、极值 1–5。样本仅 10 条，极值和方差必须配合逐条 trace 解读。

## 2. 未识别原因与能力边界

### 已证实

1. 至少一个有效轮次中，8/10 个目标进入 filter 后候选，完整 RRF Top 50 有 5 个，最终 Top 10 有 3 个。7 个 miss 中，5 个属于候选内排序损失，2 个属于候选缺失。
2. 新命中 `public_0041` 在 turn 1 未出现，turn 2 rank 1；用户只发送固定“请问一个属性”的反馈，Agent 没有真正提问或获得属性值。命中来自保留类别/state 参与 RRF，而不是 no-preference 处理。
3. 另外两个新命中 `public_0050` rank 2、`public_0131` rank 5，均发生在 turn 1。
4. 74 个 Boundary 响应中 `ask_attribute` 全为 null；模拟器 no-preference 分支仍然一次都没有触发。
5. 64 个通用重试轮次形成 4 组状态相关列表，不再是 V1 的全局固定一组。
6. 当前 0→3 的指标提升证明 RRF 改善了宽类别排序，但不能证明 neutral/asked 行为已通过端到端验收。

### 合理推断

1. 5 个候选内 miss 仍有排序提升空间；2 个候选缺失则需要召回或追问。
2. `public_0041` 表明状态 route 可以带来后续命中，但这种“没有新信息的第二轮命中”可能依赖 route 组合变化，不等同于真正对话收敛。
3. 如果接入 clarification，现有 neutral parser/state 单元能力才会进入真实路径；届时需要重新评估，不能沿用本版 3/10 作为 neutral 成功率。

### 证据边界

no-preference 未发生，因此无法评价 neutral 属性是否会被重复询问、是否污染 profile 或是否正确换问。本报告只确认 RRF 带来的推荐命中，不把它表述为 Boundary 交互能力已经完成。

## 3. 代表性 public 案例

以下案例只用于错误分析，不得转化为 public set 硬编码。

| Sample | V1 → V1.1 | 观察 |
|---|---|---|
| `public_0041` | miss → turn 2 rank 1 | Tunics；state/category 参与 RRF 后命中，但 no-preference 没有触发。 |
| `public_0050` | miss → turn 1 rank 2 | Industrial & Construction Boots；宽类别融合直接改善。 |
| `public_0131` | miss → turn 1 rank 5 | Leg Warmers；类别路线共同支持产生新增命中。 |

## 4. 5 人分工修改建议

| 成员 | 修改建议 | 预期交付 | 验收标准 |
|---|---|---|---|
| 1号 | 提供 Boundary 类别的有序替代属性和覆盖率。 | Question fallback playbook | 每类至少两个属性；来源为 catalog。 |
| 2号 | 把 clarification 接入 Agent；收到 no-preference 后写入 neutral/asked 并换问或停止。 | Boundary end-to-end trace | no-preference 实际触发；neutral 不重复问、不参与约束。 |
| 3号 | 对 2 个候选缺失类改善 recall；输出 neutral 前后 route/filter 证据。 | Boundary candidate trace | 候选非空合法；neutral 不导致目标误删。 |
| 4号 | 对 5 个候选内 miss 调整 route 权重，同时将 neutral 属性贡献设为 0。 | neutral-aware score breakdown | RRF 收益保留；score 中无 neutral 属性贡献。 |
| 5号 | 将“推荐命中”和“neutral 行为通过”设为两个独立 gate。 | 10 条行为矩阵、dev/holdout 报告 | 重复 neutral 属性为 0；不能用直接命中替代交互验收。 |

## 5. 下一版本观察项

- 首次有效提问率、no-preference 触发率、neutral 重复询问次数。
- 5 个候选内 miss 和 2 个候选缺失的分别改善。
- Turn 2 命中是否由新信息驱动，而非无信息路线切换。
- 3 条 holdout 逐条 trace，不只汇报 0.666667。
