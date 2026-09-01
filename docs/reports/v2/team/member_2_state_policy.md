# 2号成员：V2 State、Override、Neutral 与追问建议

## 1. 你先看哪些文件

1. `docs/reports/v2/turn_casebook.md`
2. `docs/reports/v2/intent_override.md`
3. `docs/reports/v2/boundary.md`
4. `starter/state.py`、`starter/intent.py`、`starter/dialogue_policy.py`、`starter/constraints.py`

## 2. V2 给你的直接证据

- `ask_attribute` 从 V1.1 的0次变为438次；90次得到具体约束，273次得到“没有额外偏好”。
- 82个 hit 中46个发生在 turn 2–4，说明对话状态已经产生真实收益。
- Boundary 有6次 no-preference 进入 Agent，未观察到同一 neutral 属性被重复询问。
- Intent 30条中20条在 override 前曾出现目标；override 后仍有22个 miss。
- turn 5–10 有708次调用、0个新 hit；达到三问上限后系统只返回固定结果。
- `public_0035`、`public_0112` 从首轮起 `ask_attribute=null`，但 trace 没有说明为什么不问。

## 3. 分阶段任务

### 阶段 A：让状态可审计

在内部 debug trace 中输出每轮 parsed constraints、state before/after、asked、neutral、invalidated 和 intent result；不得泄漏到正式响应合同。

验收：任意 override/no-preference session 都能回答“哪个值何时进入、失效或变 neutral”；正式 API 字段不变。

### 阶段 B：提高问题价值

QuestionPolicy 输入应包含已知属性、neutral、问过属性、候选分布或至少类别 playbook 信息。增加 `decision_reason` 供 debug 使用，例如 `enough_information`、`question_limit`、`no_covered_attribute`、`last_turn`。

验收：不重复问 asked/neutral；已有两个有效非类别信号时停止；首问具体回答率提升；`ask=null` 均有原因。

### 阶段 C：停止与恢复策略

三问后若 state 不再变化，应明确结束对话或通知3号切换探索 route，不能继续相同列表到turn 10。Override 到来必须优先处理，不能被“已达到提问上限”阻断状态更新。

验收：turn 5–10零收益调用显著低于708；Intent eligible-turn 指标不下降；Boundary 重复问率保持0。

## 4. 必测回归

- no-preference 使用 last asked attribute，并从 active state 清除该属性。
- neutral 属性不再从 profile 恢复，也不会再次被问。
- 同属性 override 将旧值放入 invalidated，只保留新值参与当前 query/filter。
- override 生效前目标出现不计分。
- 问题上限、最后一轮、未知类别和已有足够信息均有稳定行为。

## 5. 给其他成员的交接

- 给1号：实际缺少 playbook 覆盖的类别和 `no_covered_attribute` 统计。
- 给3号：规范化 state snapshot、active/invalidated/neutral 值。
- 给4号：current-turn 与 override 标记，供 recency/explicit score 使用。
- 给5号：单一主要改动、策略参数、测试、预期影响轮次及风险。
