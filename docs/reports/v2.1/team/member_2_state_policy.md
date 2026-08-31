# 2号成员：V2.1 State、Intent与追问建议

## 1. 先读

1. `docs/reports/v2.1/turn_casebook.md`
2. `docs/reports/v2.1/intent_override.md`
3. `docs/reports/v2.1/boundary.md`
4. `starter/state.py`、`intent.py`、`dialogue_policy.py`

## 2. 直接证据

- 408次追问、81次具体回答、234次无额外偏好；no-preference仍有6次且未重复问neutral属性。
- turn5首次出现2个无新属性命中：固定重试消息改变intent/route，说明路由决策对措辞敏感。
- Intent有19个session在override前出现目标；生效后Hit提高到12/30，但候选覆盖从23降到20。
- turn6–10仍有485次零收益调用。

## 3. 分阶段任务

### A. 决策可审计

Debug输出intent、parsed constraints、state before/after、asked、neutral、invalidated、question/stop reason和建议route mode。

验收：正式响应合同不变；每个turn5路由切换可解释；override旧值不回流。

### B. 保持语义连续

固定“Those options...”不应覆盖已有购物意图或让有效属性从route query消失。Intent识别应结合session state，通用重试只表达“不满意”，不应变成新需求。

验收：相同active state下，通用重试不会无理由重置route；若切探索策略，必须有显式reason。

### C. 停止策略

三问后state无变化时结束或触发可解释的探索route；避免turn6–10重复。

验收：零收益调用显著低于485；Boundary重复问率保持0；Intent eligible指标不降。

## 4. 交接

给3号active/invalidated/neutral和route mode；给4号current-turn/override/neutral标记；给5号策略参数、单测、预期轮次变化和风险。
