# V2.1 Browsing 场景分析

## 1. 指标与分布

| 指标 | V2 | V2.1 | Δ |
|---|---:|---:|---:|
| Hits / 80 | 30 | 37 | +7 net |
| Hit@10 | 0.375000 | 0.462500 | +0.087500 |
| MRR | 0.190030 | 0.195476 | +0.005446 |
| MTTC | 7.887500 | 6.862500 | -1.025000 |

首次命中turn 1/2/3/4为17/6/9/5。命中rank均值4.432432、方差8.515705。

相对V2新增14、丢失7、shared 23；shared rank提升6、不变5、下降12。Hit明显增加，但MRR只小幅提高，正是排名后移与回归抵消的结果。

## 2. 已证实失败结构

- 候选覆盖62/80，比V2的58提高4；43个miss可归为R1纯召回6、R3融合前截断12、K1-near 10、K1-deep 15。
- 原先18个“候选缺失”中有12个实际已被route召回；排序桶的最佳rank分布从11到100，不能用一个统一boost解释。
- 175次追问得到48次具体回答、101次无额外偏好；use_case 57次、material 41次。
- 7个lost中，`public_0043`、`public_0063`、`public_0122`、`public_0134`完全未进入生产候选；`public_0086`仍在候选但最佳rank13。
- 近边界miss `public_0098`最佳完整rank11。

## 3. 合理推断与边界

字段category和same-category route改善了宽类别首轮命中，但候选顺序截断可能让后置current-message/attribute route失效。MRR几乎不变说明不能只继续扩路；应控制候选质量与高位相关性。

当前没有人工相关性标签，shared rank下降不能自动判定为质量下降；但官方MRR下降或小幅增长是需要保护的客观信号。完整清单见[未命中归因](miss_attribution.md)。

## 4. 代表案例

- 成功：`public_0019`，feature回答后turn2 rank1。
- 成功：`public_0015`，初始宽类别在V2 miss，V2.1 turn1 rank7，体现新类别route收益。
- 失败：`public_0043`，V2 turn4 hit，V2.1在cotton回答后仍未进入前100生产候选。

## 5. 1–5号建议

| 成员 | 修改建议 | 交付物 | 验收标准 |
|---|---|---|---|
| 1号 | 提升宽类别leaf alias和高区分属性 | playbook/alias覆盖表 | 类别覆盖可复现，低区分问题降权 |
| 2号 | 依据候选变化选择下一问 | question delta trace | 每问记录候选/rank变化，避免无价值问答 |
| 3号 | route预算改为配额/round-robin，不让前序类别route占满100 | 候选合并实现与测试 | 后置route rank1不可被截掉，覆盖不回退 |
| 4号 | 保护shared高位结果，审计rank11–20 | rerank churn报告 | shared rank下降数显著减少，MRR实质提升 |
| 5号 | Hit与MRR同时gate | Browsing评测表 | 不接受只增后排hit而大量降rank的版本 |

## 6. 下一版指标

逐route召回、截断前后覆盖、首轮命中、rank11–20转化、shared rank churn、每问边际收益和延迟。
