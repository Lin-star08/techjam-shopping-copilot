# V2 逐轮典型案例册

## 1. 统计口径

本报告基于 V2 的 200 条全量 trace。`活跃会话`表示该轮实际调用 Agent；`条件命中率`为本轮首次命中数除以本轮活跃会话数。Intent Override 生效前即使目标出现也不计分。

| Turn | 活跃会话 | 首次命中 | 条件命中率 | 累计命中 | 典型成功 | 典型失败 |
|---:|---:|---:|---:|---:|---|---|
| 1 | 200 | 36 | 18.0000% | 36/200 | `public_0050` rank 2 | `public_0110` miss，随后问 material |
| 2 | 164 | 3 | 1.8293% | 39/200 | `public_0110` rank 1 | `public_0009` 仍 miss |
| 3 | 161 | 26 | 16.1491% | 65/200 | `public_0014` rank 2 | `public_0022` 仍 miss |
| 4 | 135 | 17 | 12.5926% | 82/200 | `public_0104` rank 1 | `public_0125` miss |
| 5 | 118 | 0 | 0% | 82/200 | 无 | `public_0054` miss |
| 6 | 118 | 0 | 0% | 82/200 | 无 | `public_0150` rank 11 边界 miss |
| 7 | 118 | 0 | 0% | 82/200 | 无 | `public_0035` 从未提问 |
| 8 | 118 | 0 | 0% | 82/200 | 无 | `public_0003` 候选缺失 |
| 9 | 118 | 0 | 0% | 82/200 | 无 | `public_0180` 候选缺失 |
| 10 | 118 | 0 | 0% | 82/200 | 无 | `public_0112` 最佳完整 rank 14 |

以下 public 案例只用于错误分析和通用回归，不能转化为 session、商品 ID、标题或隐藏答案特判。

## 2. Turn 1：保留单轮能力

- 成功：`public_0050`，Boundary，Industrial & Construction Boots，初始 rank 2。
- 失败：`public_0110`，Browsing，Athletic Socks，目标未进 Top 10；Agent 问 material。
- 结论：36 个 turn-1 hit 比 V1.1 多 4 个，但 V2 的主要增益不再局限于首轮。

## 3. Turn 2：第一问的直接收益有限

- 成功：`public_0110` 回答 wool 与材质配比后，目标从 miss 到 rank 1。
- 失败：`public_0009` 对 use_case 没有额外偏好，目标仍 miss，Agent 转问 feature。
- 结论：仅3个首次命中，说明第一问若选择宽泛 use_case，常不足以改变结果；应按类别和候选熵选择属性。

## 4. Turn 3：最高边际收益轮

- 成功：`public_0014` 在 material 回答后由 miss 到 rank 2。
- 失败：`public_0022` 前两问均没有新增偏好，第三问才转向 material，本轮仍未命中。
- 结论：26个新增 hit 是单轮最高值。很多会话在第一问 neutral 后，第二个高价值属性才产生可检索信息。

## 5. Turn 4：最后一次有效增长

- 成功：`public_0104` 在 category no-preference、use_case neutral 后，material 回答使目标到 rank 1。
- 失败：`public_0125` 的 Acrylic override 生效后目标未进 Top 10，完整候选最佳 rank 13。
- 结论：17个新增 hit；同时也是三问上限或 override 生效后的主要终点。

## 6. Turn 5：进入零收益平台

- 成功：无。
- 失败：`public_0054` 已完成三次追问，目标在候选中最佳 rank 23，V1.1 hit 在此版本回归。
- 结论：从本轮开始不再提问且没有新信息，但 evaluator 仍继续调用。

## 7. Turn 6：Top-10 边界不能自愈

- 成功：无。
- 失败：`public_0150` 的目标最佳完整 rank 11；相同状态和相同列表不会把它推进前十。
- 结论：rank 11–20 应进入显式匹配重排实验，而不是增加无变化轮次。

## 8. Turn 7：部分会话仍从未进入追问

- 成功：无。
- 失败：`public_0035` 从 turn 1 起 `ask_attribute=null`，Boundary no-preference 从未触发；目标最佳完整 rank 17。
- 结论：问题策略需要明确的 `no_question_reason`，区分“信息已足够”“无 playbook 覆盖”“达到上限”。

## 9. Turn 8：召回缺失无法靠重复列表恢复

- 成功：无。
- 失败：`public_0003` 在 override 生效后的可计分轮次始终不在 filter 后候选。
- 结论：需要 category+new-value 联合 route 与逐 route recall，而不是重复同一 RRF 输入。

## 10. Turn 9：完成追问后仍可能候选缺失

- 成功：无。
- 失败：`public_0180` 已经历 no-preference 和具体回答，目标仍未进入候选。
- 结论：有用户增量不代表检索正确消费了该增量；必须记录回答→query→route 的链路。

## 11. Turn 10：终止轮仍无新行为

- 成功：无。
- 失败：`public_0112` 从未提问，目标虽在候选中但最佳完整 rank 14。
- 结论：118 个 miss 最终按 turn 11 计入 MTTC。turn 5–10 共708次调用、零新增 hit，是 V2 最大的剩余效率浪费。

## 12. 下一版逐轮 Gate

1. 每个 turn 2+ 新命中必须保存 ask、reply、state delta、route delta、完整 rank delta。
2. 第一问具体回答率、neutral 率和新增 hit 分开报告；不能只报总 ask 数。
3. 三问后无新 state 时应停止或切换候选探索，turn 5–10 调用数应显著低于708。
4. 对每个无成功轮仍保留至少一个 R1/F1/K1 失败案例，避免平均指标掩盖死循环。
