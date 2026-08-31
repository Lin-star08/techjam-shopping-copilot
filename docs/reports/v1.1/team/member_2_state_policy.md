# 2号成员：状态、Override、Neutral 与追问策略修改建议

## 1. 本阶段目标

让现有 `SessionState` 真正驱动多轮信息增益。V1.1 已证明状态 route 能改变排序，但 1,674 个响应中 `ask_attribute` 全为空；除 Intent Override 外，系统几乎没有真实对话收敛。

逐轮证据：turn 1 命中 32 条、turn 2 命中 1 条、turn 4 命中 5 条；turn 3、5–10 均为 0。turn 2 的唯一命中没有获得新属性，只是状态 route 重新参与融合。

## 2. 分阶段任务

### 阶段 A：状态语义收口（P0）

1. 为每轮输出开发期 state snapshot：`current_slots`、`hard_constraints`、`soft_preferences`、`invalidated_slots`、`asked_attributes`、`neutral_attributes`。
2. 明确句级 override 规则：“ignore earlier preference”是否只替换同属性，还是作废此前某组软偏好；类别在无冲突时保留。
3. Neutral 只能清除对应属性，不得变成字符串 `no_preference` 参与检索或排序。

预期交付：状态转移表、turn 3/4 override 测试、neutral/asked 测试及可选 debug snapshot。

验收：失效值不再进入 query/filter/score；同一 neutral 属性不再问；类别和新明确值能跨轮保存。

### 阶段 B：Clarification Policy 接线（P0）

1. 首轮宽泛或候选不确定时，从1号 playbook 中选择一个未问、非 neutral、可回答的属性。
2. 一轮最多问一个属性；已有足够明确需求或候选高度集中时直接推荐。
3. evaluator 固定反馈“Ask me about one specific attribute”必须触发 clarification 分支，不能继续当普通商品查询文本。
4. 回答没有新值时，将对应属性标为 neutral/asked，换问下一个属性或停止。

预期交付：`choose_ask_attribute(state, candidate_summary)`、策略测试、Buying/Browsing/Boundary 端到端 trace。

验收：非空 ask rate > 0；重复问题率为 0；Boundary no-preference 实际触发；用户回答后候选或排名发生可解释变化。

### 阶段 C：多轮回归（P1）

1. 固定检查 turn 1–10 的首次命中分布，目标是 turn 2/3/5+ 出现由新信息驱动的命中。
2. Intent Override 只在生效后计分；提前命中不能算成功。
3. 对追问数量设上限，避免通过无限提问降低用户体验或制造偶然命中。

验收：MTTC 改善不是单纯因为更多 turn 1 直接命中；每个 turn 2+ hit 都能指出新增属性及 state 变化。

## 3. 典型案例对应

| 案例 | 状态/策略问题 | 修改方向 |
|---|---|---|
| `public_0041` / Boundary success | turn 2 rank 1，但没有提问或用户新信息 | 保留该 state-route 能力，同时补上真正 ask→neutral 路径；不能把它算作 neutral 成功。 |
| `public_0004` / Intent failure | polyester override 后目标仍不进 Top 10 | 输出 override 前后 state；确认类别保留、旧偏好失效范围和新 material 状态。 |
| `public_0006` / Browsing failure | turn 1–10 均无追问 | 用类别 playbook 询问 material/feature，回答后重新检索。 |

## 4. 行为验收清单

- `ask_attribute` 只能取合同允许值或 null。
- asked/neutral 属性不重复问。
- no-preference 不进入 hard/soft query。
- override 生效轮次和 evaluator eligibility 一致。
- 每轮 debug trace 能解释“为什么问/为什么不问”。
- 追问策略只用 catalog/state 信息，不读取 public ground truth。
