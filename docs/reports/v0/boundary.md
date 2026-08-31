# v0 Boundary 场景分析报告

## 1. 场景与指标

Boundary 用于检查用户对被问属性没有偏好时，Agent 能否接受该边界、停止重复追问，并换用其他属性或直接推荐。

| 数据范围 | 样本数 | Hits | Misses | Hit@10 | MRR | MTTC |
|---|---:|---:|---:|---:|---:|---:|
| Full public | 10 | 0 | 10 | 0.000000 | 0.000000 | 11.000000 |
| Development | 7 | 0 | 7 | 0.000000 | 0.000000 | 11.000000 |
| Internal holdout | 3 | 0 | 3 | 0.000000 | 0.000000 | 11.000000 |

该场景没有命中排名或有效命中轮次，所有 miss 按规则记为第 11 轮。

## 2. 目标未识别的原因

### Trace 已证实

1. 10 条会话全部失败，目标从未进入 Agent 返回的 Top 10。
2. Agent 始终返回 `ask_attribute=null`，所以模拟器的 Boundary no-preference 分支一次都没有被触发。
3. 首轮失败后累计产生 90 个通用重试轮次，全部使用相同消息和同一组 Top 10。
4. 因为从未问属性，v0 既没有机会获得 no-preference 回复，也没有机会证明 neutral、换问和停止追问逻辑是否正确。
5. 全部响应结构合法且无异常，失败来自策略缺失。

### 结合实现的合理推断

1. Boundary 的核心不是要求每轮都追问，而是要求系统在一次属性被拒绝后正确处理 neutral。v0 连第一次追问都没有，因此整个场景能力不可用。
2. 没有 `neutral` 和 `asked` 状态，未来即使简单加入追问，也可能反复询问同一属性。
3. 没有类别级替代属性顺序和 fallback；无法在材质无偏好时转向用途、style、size 或直接推荐。
4. 10 个 miss 中 5 个目标缺 description，但所有目标有 features；数据稀疏不足以解释 0/10，首要问题仍是交互策略。

### 当前不能确认

由于 no-preference 分支从未触发，现有 v0 不能评估“收到 neutral 后是否会重复问”“是否错误地把 neutral 当成硬条件”或“换问能否缩小候选”。这些必须在下一版 trace 中验证，而不能根据 v0 推断为已经发生的具体 bug。

## 3. 代表性案例

以下案例只用于错误分析，不得写入 Agent 规则。

| Sample | 首轮类别 | 隐藏可披露信息 | 观察 |
|---|---|---|---|
| `public_0035` | Athletic Walking | fabric、textile、rubber sole | Agent 未问任何属性，随后 9 轮重复通用结果，最终 miss。 |
| `public_0041` | Tees & Blouses Tunics | polyester、size/care、closure | Agent 未触发 no-preference，也未换问 size/style/material，最终 miss。 |
| `public_0050` | Industrial & Construction Boots | leather、sole、shaft | 类别较明确，但没有追问或 fallback，目标仍未进 Top 10。 |

## 4. 按团队分工的修改意见

| 成员 | 修改建议 | 预期交付 | 验收标准 |
|---|---|---|---|
| 1号：数据洞察与商品知识 | 为重点类别提供有顺序的替代属性，避免第一个属性无偏好后无路可走。 | category-to-question playbook、替代属性列表 | 每个重点类别至少有 2–3 个可解释的候选属性；不依据 public target 定制。 |
| 2号：对话状态与策略 | 首次 no-preference 后将属性加入 `neutral`，同时保留 `asked`；换问其他属性或停止追问。 | neutral/asked 状态逻辑、Boundary 场景测试 | neutral 属性不再被问、不参与硬约束；下一轮决策可解释且不死循环。 |
| 3号：检索与约束工程 | neutral 后使用剩余有效状态和类别路线；提供合法、非空、去重的 fallback。 | boundary fallback、candidate interface | 即使没有新属性值也能返回有效候选；neutral 不会导致全部候选被过滤。 |
| 4号：融合排序与调参 | neutral 属性权重归零；用剩余明确需求、软偏好和弱 profile 排序。 | neutral-aware rerank、score 分解 | final score 不包含 neutral 属性贡献；profile 不压过其他明确需求。 |
| 5号：评估实验与交付 | 对 10 条 Boundary 逐条检查首问、no-preference、下一步和重复属性。 | Boundary trace 表、回归清单、dev/holdout 指标 | 重复询问 neutral 属性次数为 0；输出始终合法；场景至少产生有效命中并降低 MTTC。 |

## 5. 下一版本观察项

- Boundary 首次有效追问比例和 no-preference 分支触发比例。
- neutral 属性重复询问次数，目标必须为 0。
- 收到 neutral 后，候选是否保持非空、合法、唯一。
- 换问次数与 MTTC；不能为了避免重复而无上限地连续追问。
- 由于 holdout 只有 3 条，除指标外必须保留逐条行为 trace 作为验收证据。
