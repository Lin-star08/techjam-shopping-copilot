# v0 Browsing 场景分析报告

## 1. 场景与指标

Browsing 的首轮只有宽泛类别，用户仍在探索。系统应通过高价值追问获得新约束，或用多路线和轻量画像信号形成有区分度的候选。

| 数据范围 | 样本数 | Hits | Misses | Hit@10 | MRR | MTTC |
|---|---:|---:|---:|---:|---:|---:|
| Full public | 80 | 2 | 78 | 0.025000 | 0.004514 | 10.750000 |
| Development | 60 | 1 | 59 | 0.016667 | 0.004167 | 10.833333 |
| Internal holdout | 20 | 1 | 19 | 0.050000 | 0.005556 | 10.500000 |

仅 `public_0081` 和 `public_0134` 命中，分别位于 rank 9 和 rank 4，且都发生在第 1 轮。

## 2. 目标未识别的原因

### Trace 已证实

1. 78 个 miss 的目标在所有轮次中都没有进入返回 Top 10。
2. Agent 在全部 Browsing 会话中从未设置非空 `ask_attribute`。
3. 首轮失败后累计产生 702 个通用重试轮次；这些轮次使用完全相同的用户消息和同一组 Top 10。
4. 每条失败会话实际只有两种推荐列表：首轮类别查询结果，以及之后重复的通用查询结果。轮数增加没有带来信息增益。
5. `user_profile` 虽然在 reset 时传入，但 v0 不保存也不使用；profile 不能帮助模糊场景缩小范围。
6. 全部响应合法且无异常。

### 结合实现的合理推断

1. 初始消息只有宽泛类别，例如 `Basketball Men` 或 `Tunics`。50,000 商品中同类候选很多，仅靠类别 BM25 难以把唯一目标放进前十。
2. 没有 clarification policy，模拟客户无法披露材质、功能、closure 等隐藏约束。
3. 没有 category/attribute/profile 等多路召回，也没有类别内多样性控制，Top 10 容易集中在少数高 BM25 商品。
4. 78 个 miss 中有 43 个目标缺 description，但 features 均非空；缺描述会减少文本证据，却不是零追问和重复列表的根本原因。

### 当前不能确认

目标未进入最终 Top 10 不等于完全没有被更大候选池召回。v0 没有记录候选池大小、候选熵、类别内覆盖或 pre-rerank rank，因此无法量化“追问某属性预计能缩小多少候选”，也无法区分召回与重排损失。

## 3. 代表性案例

以下案例只用于错误分析，不得写入 Agent 规则。

| Sample | 首轮类别 | 目标 | 观察 |
|---|---|---|---|
| `public_0006` | Basketball Men | Pro Club heavyweight mesh basketball shorts | 目标未进 Top 10；材质、透气性等高价值信息从未通过追问披露。 |
| `public_0007` | Tees & Blouses Tunics | RITERA plus-size cold-shoulder tunic | 目标未进 Top 10；类别内商品密集，缺少 size/style/material 区分。 |
| `public_0081` | Underwear Undershirts | Fruit of the Loom V-neck T-shirt | 第 1 轮 rank 9 偶然命中，说明宽类别查询存在少量自然命中，但排名较后且不可稳定复制。 |

## 4. 按团队分工的修改意见

| 成员 | 修改建议 | 预期交付 | 验收标准 |
|---|---|---|---|
| 1号：数据洞察与商品知识 | 为重点类别统计最有区分度的材质、用途、style、size、feature，并给出前三个追问属性。 | category playbook、属性覆盖率、候选缩减估计 | 属性来自 catalog 统计；每类问题能解释预期信息价值。 |
| 2号：对话状态与策略 | 根据缺失槽位和候选不确定性选择一个追问；维护 asked/neutral，避免重复。 | clarification policy、Browsing 状态测试 | 首轮模糊时能问一个有效属性；已回答或 neutral 属性不再重复询问。 |
| 3号：检索与约束工程 | 增加 category、current-state、attribute 和 profile 弱信号路线，并确保合法 fallback。 | multi-route retrieval、candidate interface | 新回复能改变至少一条路线或候选；单一路线失败时仍有其他候选来源。 |
| 4号：融合排序与调参 | 融合多路线，控制类别内候选多样性；profile 仅作弱加分。 | RRF/normalized fusion、diversity 指标、ablation | profile 不压过当前明确需求；候选不被一个高频品牌或词法模板垄断。 |
| 5号：评估实验与交付 | 记录问题价值、候选缩减率、重复问题率和追问后的命中变化。 | Browsing 实验表、代表 trace、dev/holdout 对比 | 重复问题率为 0；有效回复后候选或排名发生可解释变化；Browsing 指标优于 v0。 |

## 5. 下一版本观察项

- 非空 `ask_attribute` 比例、重复问题率和 neutral 后重复率。
- 每次追问前后的候选数量、候选熵和目标候选排名。
- 首次命中轮次分布；不能只靠增加问题提高 Hit@10 而显著恶化 MTTC。
- Profile 开关 ablation，确认弱画像信号确实有帮助且不会覆盖当前需求。
