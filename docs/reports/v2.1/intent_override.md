# V2.1 Intent Override 场景分析

## 1. 指标与分布

| 指标 | V2 | V2.1 | Δ |
|---|---:|---:|---:|
| Hits / 30 | 8 | 12 | +4 net |
| Hit@10 | 0.266667 | 0.400000 | +0.133333 |
| MRR | 0.163333 | 0.260833 | +0.097500 |
| MTTC | 9.100000 | 8.166667 | -0.933333 |

1个hit在turn3，11个在turn4；命中rank均值2.666667、方差5.222222、范围1–8。

相对V2新增5、丢失1、shared 7；shared rank提升2、不变4、下降1。

## 2. 已证实失败结构

- 19/30个session在override生效前至少一次出现目标，共25个pre-override target turn，均未错误计分。
- 生效后候选覆盖20/30，比V2的23下降3；18个miss可归为R1纯召回7、R3融合前截断3、K1-near 4、K1-deep 4。
- 候选内miss从15降到8，MRR大幅改善；但候选缺失从7升到10。
- 唯一lost `public_0023`：override前rank1但不可计分，生效后目标仍在候选、最佳完整rank17。

## 3. 合理推断与边界

current-message、relaxed和requirement evidence提高了override后候选的高位转化；但动态route预算和Top100截断减少了部分候选覆盖。必须把“召回到候选”和“evidence重排”拆开验证。

Trace未保存所有竞争商品的invalidated evidence，因此不能仅凭目标下降认定旧值污染；现有单测证明invalidated/neutral不会boost，但还需session级score审计。完整清单见[未命中归因](miss_attribution.md)。

## 4. 代表案例

- 成功：`public_0002`，leather在turn3生效但仍miss，turn4通用回复后rank2。
- 成功：`public_0125`，V2回归案例在V2.1恢复，override后进入Top10。
- 失败：`public_0023`，Hand Wash Only生效后目标最佳完整rank17，是明确候选内排序回归。

## 5. 1–5号建议

| 成员 | 修改建议 | 交付物 | 验收标准 |
|---|---|---|---|
| 1号 | 规范override短语与属性分类 | value normalization | 新旧值落入正确slot且不过度泛化 |
| 2号 | 输出active/invalidated/intent before-after | state trace | 旧值不进入query/evidence，生效轮语义正确 |
| 3号 | 给override route保留独立候选配额 | route budget测试 | 候选覆盖恢复到至少23/30 |
| 4号 | 单独评估override evidence/recency | score ablation | eligible MRR提高且pre-old evidence为0 |
| 5号 | 统计pre-only、post-recall、post-rank | Intent gate | 生效后指标与churn完整 |

## 6. 下一版指标

Eligible候选覆盖、pre-only session、旧值evidence残留、override route配额、post-rank转化、shared rank和lost hit。
