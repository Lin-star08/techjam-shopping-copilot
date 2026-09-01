# V2 Buying 场景分析

## 1. 指标与分布

Buying 表示用户初始轮已经给出商品类别和一个关键要求。

| 指标 | V1.1 | V2 | Δ |
|---|---:|---:|---:|
| Hits / 80 | 24 | 38 | +14 net |
| Hit@10 | 0.300000 | 0.475000 | +0.175000 |
| MRR | 0.154563 | 0.239439 | +0.084876 |
| MTTC | 8.000000 | 6.537500 | -1.462500 |

V2 有 38 hit、42 miss。首次命中分布为 turn 1：28，turn 3：7，turn 4：3；命中 rank 均值 4.236842、方差 11.022853、范围 1–10。

相对 V1.1，Buying 新增 15 个 hit、丢失 1 个，净增 14 个。15 个新增命中中，5 个在 turn 1、7 个在 turn 3、3 个在 turn 4。

## 2. 已证实的失败结构

- 生产候选覆盖 63/80；42 个 miss 中，17 个在所有可计分轮次均未进入 filter 后候选，属于 R1/F1 尚不可细分的候选缺失桶。
- 另外 25 个 miss 的目标已经进入 filter 后候选，但完整 RRF rank 始终大于 10，属于 K1 排序桶。
- Buying 共发生 147 次追问，但只有 18 次得到具体约束回答，105 次得到“没有额外偏好”。use_case 54 次、style 34 次，是最常问的两个属性。
- `public_0156` 在 turn 1 被解析出的 `category=bag` filter 移除，turn 2 后重新进入候选但最佳完整 rank 96。这里同时存在 C1/F1 风险和 K1，不能只修 filter 就宣称恢复。

## 3. 合理推断

初始 key requirement 已提供时，仍优先问 use_case 往往得不到新增信息。先评估现有约束是否足够区分候选，再选择与类别高覆盖且能补充新维度的属性，可能用更少轮次取得同等命中。

25 个候选内 miss 多于 17 个候选缺失，说明 Buying 下一步应优先补显式需求匹配/recency 的重排分；但 `public_0054` 的最佳完整 rank 23 表明简单把一个 route 全局加权未必足够。

## 4. 证据边界

Runtime audit 能证明目标是否在生产候选集合及其完整 RRF rank，不能证明前排竞品不相关，也没有记录每个竞品对 key requirement 的语义满足度。17 个候选缺失可能是纯召回缺失，也可能是某轮 filter 排除后在其他轮次未重新召回；必须增加逐 route/filter reason 后再细分。

## 5. 代表案例

- 成功：`public_0042`，Watches。turn 1–2 miss，feature 回答在 turn 3 使目标到 rank 1，属于有效追问带来的新命中。
- 成功：`public_0022`，Casual Dresses。前两次问题无新增偏好，turn 4 的 cotton/soft/breathable 回答使目标到 rank 1；说明 material 有价值，但前两问存在轮次成本。
- 失败：`public_0054`，V1.1 曾命中，V2 在三次追问后仍 miss；目标在候选内最佳 rank 23，是明确 K1 回归案例。

案例只用于错误分析与通用回归，不得转化为 public session、商品 ID 或标题特判。

## 6. 1–5号修改建议

| 成员 | 建议 | 预期交付物 | 验收标准 |
|---|---|---|---|
| 1号 | 按类别统计 key requirement 后最有增益的第二属性；降低泛化 use_case 的优先级 | Buying category→attribute 信息价值表 | development 具体回答率提高，且不使用 ground truth 选问 |
| 2号 | 已有一个硬条件时动态判断是否追问；连续 neutral 后提前停止或换维度 | policy 决策表、state delta trace | 不重复问已知/neutral 属性；turn 2–4 新命中不下降 |
| 3号 | 对17个候选缺失输出逐 route recall 与 filter reason | route/filter 漏斗报告 | 每个 miss 可稳定归入 R1 或 F1，候选覆盖高于63/80 |
| 4号 | 为当前显式要求增加独立匹配分，保留 RRF 为召回共识分 | score breakdown 与单变量重排实验 | 修复候选内 miss 时不新增 lost hit；MRR、Hit 同时报表 |
| 5号 | 锁定 `public_0054`、`public_0156` 与 turn-3/4 成功案例做回归 | Buying gate 表 | dev/holdout 分开；gained/lost、rank churn、MTTC 均记录 |

## 7. 下一版观察指标

候选覆盖、候选内转 Top 10 比例、具体回答率、每次追问后的候选/rank delta、turn 1/3/4 命中分布、lost hits 和 Buying dev/holdout MRR。
