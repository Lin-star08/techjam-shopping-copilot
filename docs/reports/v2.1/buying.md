# V2.1 Buying 场景分析

## 1. 指标与分布

| 指标 | V2 | V2.1 | Δ |
|---|---:|---:|---:|
| Hits / 80 | 38 | 49 | +11 net |
| Hit@10 | 0.475000 | 0.612500 | +0.137500 |
| MRR | 0.239439 | 0.278090 | +0.038651 |
| MTTC | 6.537500 | 5.412500 | -1.125000 |

首次命中：turn 1/2/3/4/5 分别为26/10/8/3/2。命中 rank 均值4.142857、方差8.122449、范围1–10。

相对V2，Buying新增16个hit、丢失5个、shared 33个；shared rank提升14、不变10、下降9。

## 2. 已证实失败结构

- filter后候选覆盖62/80，比V2少1；31个miss可归为R1纯召回6、R3融合前截断11、F1过滤误删1、K1-near 6、K1-deep 7。
- 原先18个“候选缺失”中只有6个是所有route均未召回；11个已在route内出现但被顺序Top100截断。`public_0156`是唯一F1：`category=bag`与catalog复数`Bags`的exact-token不一致导致误删。
- 候选内miss从25降至13，解释了主要净收益；候选缺失反而从17升到18。
- 140次追问只得到18次具体回答，89次表示没有额外偏好；use_case仍占56次。
- 5个V2 hit回归中，`public_0026`最佳完整rank17，属于候选内排序回归；`public_0200`等目标则未进入生产候选。
- turn 5 的 `public_0045`、`public_0061` 在无新属性时首次命中，证明固定重试消息改变route选择，但也暴露同一state因措辞变化产生不连续结果。

## 3. 合理推断与边界

字段化 requirement route 与 evidence提高了候选转Top10效率；但当前目标只要进入候选就普遍获得boost，无法仅凭目标boost证明排序相关性。需比较竞争商品的matched attribute和score breakdown。

未截断route回放已区分R1、R3和F1；仍不能仅凭目标存在断言当前Top10竞争商品不相关。完整清单见[未命中归因](miss_attribution.md)。

## 4. 代表案例

- 成功：`public_0017`，turn 1 miss，turn 2即使use_case无额外偏好，目标仍到rank3；属于route/state fallback带来的早期命中。
- 成功：`public_0045`，turn 4仍miss，turn 5固定重试消息后到rank7；不是新用户信息带来的成功。
- 失败：`public_0026`，V2曾命中，V2.1目标仍在候选但最佳完整rank17。

案例只用于通用错误分析，不得做public ID或商品特判。

## 5. 1–5号建议

| 成员 | 修改建议 | 交付物 | 验收标准 |
|---|---|---|---|
| 1号 | 区分真实requirement词与Imported/Fabric等低区分词 | requirement词强度表 | 基于catalog统计，不使用public目标 |
| 2号 | 已有硬条件时减少低价值use_case追问；解释turn5路由切换 | policy reason/state trace | 相同state不因通用重试产生不可解释跳变 |
| 3号 | 输出未截断逐route候选，修复顺序Top-100 | route funnel | 候选覆盖不低于V2的63/80，后置route高位项不丢 |
| 4号 | 审计13个候选内miss与5个lost hit的完整贡献 | score breakdown | Hit提升同时保护shared MRR和rank1–3 |
| 5号 | Buying dev/holdout、turn5命中和churn独立gate | 实验表 | gained/lost、候选覆盖、延迟齐全 |

## 6. 下一版指标

候选覆盖、Top100截断损失、候选内转化率、具体回答率、turn5无信息命中数、shared rank churn和P95延迟。
