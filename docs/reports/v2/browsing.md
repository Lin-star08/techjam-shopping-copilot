# V2 Browsing 场景分析

## 1. 指标与分布

Browsing 表示用户给出宽泛类别但仍在探索，初始消息缺少具体偏好。

| 指标 | V1.1 | V2 | Δ |
|---|---:|---:|---:|
| Hits / 80 | 6 | 30 | +24 |
| Hit@10 | 0.075000 | 0.375000 | +0.300000 |
| MRR | 0.021161 | 0.190030 | +0.168869 |
| MTTC | 10.250000 | 7.887500 | -2.362500 |

V2 有 30 hit、50 miss。首次命中为 turn 1：6、turn 2：2、turn 3：17、turn 4：5。命中 rank 均值 3.100000、方差 4.756667、范围 1–10。

## 2. 已证实的改进与失败

- 相对 V1.1 新增的 24 个 hit 全部发生在 turn 2–4，且没有 lost hit；这是 V2 最清晰的追问收益场景。
- Browsing 共发生 198 次追问：use_case 60、material 49、style 27、size 27、feature 18、category 17。
- 57 次用户回复提供具体约束，124 次表示没有额外偏好。
- 生产候选覆盖 58/80；50 个 miss 中，22 个候选缺失，28 个候选已存在但完整 rank > 10。
- 仍有 50 个会话进入 turn 5–10，产生 300 次零新增命中调用。

## 3. 合理推断

material 问题在多个类别中直接带来高位命中，而 use_case 更常先得到 neutral。可基于类别字段覆盖、候选熵和已知维度重排问题优先级，让第一问更可能获得可检索值。

Browsing 的候选缺失与候选内 miss 接近，说明只优化问法或只优化排序都不够：具体回答必须同时进入联合 category+attribute route，并在融合中获得足够权重。

## 4. 证据边界

当前 trace 能看到 ask、回复和最终 rank，但没有记录每次问题前后的候选数、熵或 route contribution。因此“某问题信息价值更高”目前主要由命中案例支持，不能直接推出全量因果排序。候选缺失也不能仅凭 Top 10 trace判定，本文使用了与正式结果逐 session 对齐的 runtime audit。

## 5. 代表案例

- 成功：`public_0110`，Athletic Socks。turn 1 问 material，turn 2 收到 wool 配比后目标直接到 rank 1，是高价值首问案例。
- 成功：`public_0014`，Briefs。use_case 无新增信息，第二问 material 得到 cotton 配比，turn 3 目标到 rank 2。
- 失败：`public_0150`，目标已在候选中但最佳完整 rank 11，只差一个名次；适合作为通用 K1 边界回归，不得做 ID 特判。

## 6. 1–5号修改建议

| 成员 | 建议 | 预期交付物 | 验收标准 |
|---|---|---|---|
| 1号 | 统计宽类别下 material/style/feature 的覆盖率与信息增益 | Browsing question playbook v2 | 首问具体回答率及候选缩减率均可报告 |
| 2号 | 依据已问、neutral 和候选变化选择下一问；三问后明确停止 | clarification 状态机与策略测试 | 无重复问；每问有 state delta；停止行为可 trace |
| 3号 | 将追问回答构造成 category+attribute 联合 route，补22个候选缺失 | route recall 报告 | Browsing 候选覆盖高于58/80，且无其他场景显著回归 |
| 4号 | 对具体回答增加显式匹配分，优先审计 rank 11–20 | rerank breakdown | `rank 11–20 → Top 10` 的收益和 lost hit 同时披露 |
| 5号 | 分别统计 first-question 与 second/third-question 的边际收益 | per-question eval 表 | 报告 active、answer、new hit、rank delta、延迟 |

## 7. 下一版观察指标

问题级具体回答率、候选缩减率、每问新增 hit、turn 2/3/4 条件命中率、候选覆盖、rank 11–20 转化率、三问后重复调用数。
