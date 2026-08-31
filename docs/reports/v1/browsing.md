# v1 Browsing 场景分析报告

## 1. 场景与指标

Browsing 首轮只有宽泛类别，必须靠追问、画像弱信号或多样化候选逐步缩小范围。V1 已保存 profile 和 state，也实现相关 route，但没有 clarification policy。

| 数据范围 | 样本数 | Hits | Misses | Hit@10 | MRR | MTTC |
|---|---:|---:|---:|---:|---:|---:|
| Full public | 80 | 2 | 78 | 0.025000 | 0.004514 | 10.750000 |
| Development | 60 | 1 | 59 | 0.016667 | 0.004167 | 10.833333 |
| Internal holdout | 20 | 1 | 19 | 0.050000 | 0.005556 | 10.500000 |

所有指标与 V0 完全一致。仍只有 `public_0081`（rank 9）和 `public_0134`（rank 4）在第 1 轮命中。

## 2. 未识别原因

### 已证实

1. 78 个 miss 的目标在 782 个 Browsing 响应的最终 Top 10 中从未出现；非空 `ask_attribute` 为 0。
2. 首轮失败后产生 702 个固定重试轮次。78 条未在首轮结束的会话均只有两种推荐列表：首轮列表，以及第 2–10 轮完全相同的公共列表。
3. evaluator 重试句 `Those options ... Ask me about one specific attribute.` 没有被 `is_generic_message` 判为 generic，因此路线顺序仍从 current-message 开始，而不是从保留类别/画像开始。
4. `merge_candidates` 按路线顺序去重，并在 100 个首次出现 ID 后停止；相同商品的后续 route evidence 只合并 matched terms，不会改变顺序。
5. V1 保存 user profile，但 profile 路线排在 current-message/current-state/category 之后；最终结果与 V0 完全一致，说明它在本评测上没有形成可观测收益。
6. 离线候选诊断在 Top 100 找到 27/80 个目标，在 Top 50 找到 15/80 个目标，而 final Top 10 只有 2/80。

### 合理推断

1. 最大瓶颈仍是零追问：隐藏的 material、style、feature 无法披露，仅凭宽类别无法稳定定位唯一目标。
2. 至少 25 个最终 miss 的目标已在重建候选 Top 100 中出现；接入真实融合/重排有提升空间，但候选外的 53 个目标仍需要更好的 query 或追问。
3. profile route 的“已实现”不等于“已生效”。没有 route-level score 和公平融合时，弱画像信号很容易被前置路线截断。

### 证据边界

候选诊断不是正式 Agent 输出的原生 trace，filter 路径也有轻微差异，因此 27/80 只能作为候选覆盖诊断，不能逐条直接认定 K1。当前也没有候选熵、属性信息增益和 profile score，无法证明应该优先问哪一个具体属性。

## 3. 代表性 public 案例

以下案例仅用于错误分析，不得转化为 public set 特判。

| Sample | V1 结果 | 观察 |
|---|---|---|
| `public_0006` | 全程 miss | Basketball Men 的目标需要 polyester、透气等区分信息；Agent 没有追问，第 2–10 轮固定重复。 |
| `public_0007` | 全程 miss | Tunics 类别内部候选密集，size/style/material 未被披露。 |
| `public_0081` | 第 1 轮 rank 9 | 与 V0 相同的边缘自然命中，不是多轮或 profile 带来的改善。 |

## 4. 5 人分工修改建议

| 成员 | 修改建议 | 预期交付 | 验收标准 |
|---|---|---|---|
| 1号 | 为高频类别给出 2–3 个高信息增益属性及 catalog 覆盖率。 | category question playbook、候选缩减估计 | 问题来自 catalog 统计；不利用 public target 内容写规则。 |
| 2号 | 实现一次一个属性的 clarification policy，并维护 asked/neutral。 | Browsing policy、状态测试 | 模糊首轮能提出合法问题；同属性不重复；回答后状态正确更新。 |
| 3号 | 修正 generic 判定或为 evaluator 的“ask me”反馈建立明确策略分支；记录各 route candidate rank。 | generic/clarification routing、candidate trace | 固定重试句不再走纯 current-message 死循环；回答后候选发生可解释变化。 |
| 4号 | 接入 RRF 和候选多样性；profile 只能弱加分，不能覆盖当前表达。 | 融合与 diversity ablation | route evidence 真正影响 final score；profile on/off 可测，且无显著其他场景回归。 |
| 5号 | 记录 ask rate、有效回答率、重复列表率、候选缩减和首次命中轮次。 | Browsing trace 表、dev/holdout 对比 | 非空 ask rate > 0；重复问题率 0；702 个无信息重试显著下降；Hit@10 高于 V1。 |

## 5. V2 观察指标

- 非空 `ask_attribute` 比例、问题可回答率、重复问题率和 neutral 后重复率。
- 回答前后 Candidate Recall@50/100、候选量/熵和目标 rank 变化。
- 重复 Top 10 的连续轮次数，不能再由第 2 轮重复到第 10 轮。
- Profile 与 clarification 分开 ablation，避免无法归因。
