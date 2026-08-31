# V2.1 逐轮典型案例册

## 1. 统计口径

`活跃会话`为该轮实际调用Agent的session；`条件命中率`为本轮首次命中/活跃会话。Intent Override生效前目标出现不计分。

| Turn | 活跃会话 | 首次命中 | 条件命中率 | 累计命中 | 典型成功 | 典型失败 |
|---:|---:|---:|---:|---:|---|---|
| 1 | 200 | 46 | 23.0000% | 46/200 | `public_0035` rank1 | `public_0104` miss |
| 2 | 154 | 17 | 11.0390% | 63/200 | `public_0019` rank1 | `public_0026` miss |
| 3 | 137 | 19 | 13.8686% | 82/200 | `public_0009` rank1 | `public_0043` miss |
| 4 | 118 | 19 | 16.1017% | 101/200 | `public_0046` rank1 | `public_0023` miss |
| 5 | 99 | 2 | 2.0202% | 103/200 | `public_0061` rank3 | `public_0098` miss |
| 6 | 97 | 0 | 0% | 103/200 | 无 | `public_0098` rank11 |
| 7 | 97 | 0 | 0% | 103/200 | 无 | `public_0104` 候选截断 |
| 8 | 97 | 0 | 0% | 103/200 | 无 | `public_0023` rank17 |
| 9 | 97 | 0 | 0% | 103/200 | 无 | `public_0003` 候选缺失 |
| 10 | 97 | 0 | 0% | 103/200 | 无 | `public_0180` rank19 |

案例仅用于错误分析和通用回归，不能转化为public ID、ASIN或隐藏答案特判。

## 2. Turn 1：新route带来更多直接命中

- 成功：`public_0035`，Boundary，V2最佳完整rank17，V2.1由多路category/evidence支持直接到rank1。
- 失败：`public_0104`，Boundary，初始类别未召回目标，继续询问use_case。
- 结论：46个首轮hit比V2多10个，字段/类别route已显著改变首轮候选。

## 3. Turn 2：neutral后route切换产生大量收益

- 成功：`public_0019`，Browsing，feature回答后rank1。
- 失败：`public_0026`，Buying，具体feature回答后目标仍在Top10外。
- 结论：17个新hit，远高于V2的3个；但部分仅由“无额外偏好”改变intent/route，必须区分新信息收益与路由切换收益。

## 4. Turn 3：具体属性与override共同生效

- 成功：`public_0009`，feature回答后rank1。
- 失败：`public_0043`，cotton尚未在本轮披露，目标继续缺失。
- 结论：19个新hit；question sequence仍决定用户何时给出真正可检索值。

## 5. Turn 4：Intent Override主要结算轮

- 成功：`public_0046`，wool override生效后rank1。
- 失败：`public_0023`，Hand Wash Only生效后目标在候选内最佳rank17。
- 结论：19个新hit，其中Intent本场景有11个；候选内排序与新值evidence是主线。

## 6. Turn 5：首次出现无新属性命中

- 成功：`public_0045` rank7、`public_0061` rank3。
- 失败：`public_0098` 目标最佳完整rank11。
- 结论：两个成功都只收到固定重试消息，state没有新属性；命中来自消息被重新识别后route集合变化，不应记为clarification收益。相同需求因措辞变化才恢复，说明路由策略不连续。

## 7. Turn 6：近边界排序停止变化

- 成功：无。
- 失败：`public_0098`仍为完整rank11。
- 结论：没有新state时，继续相同融合不会自动跨过Top10边界。

## 8. Turn 7：前融合截断无法靠重复恢复

- 成功：无。
- 失败：`public_0104`的目标在关键属性轮进入多个route高位，却从未进入合并Top100；固定重试轮又失去属性消息。
- 结论：需要修候选合并和state route，而不是增加轮次。

## 9. Turn 8：候选内Intent回归

- 成功：无。
- 失败：`public_0023`在override后最佳完整rank17。
- 结论：这是明确K1；需要score breakdown，不应归给召回。

## 10. Turn 9：纯候选缺失

- 成功：无。
- 失败：`public_0003`的目标在所有可计分轮次均未进入filter后候选。
- 结论：需按未截断route检查R1/R2，不能靠evidence boost修复不存在的候选。

## 11. Turn 10：终止轮仍无新行为

- 成功：无。
- 失败：`public_0180`，Boundary，候选内最佳rank19。
- 结论：turn 6–10共有485次零收益调用；应加入完成状态或新探索策略。

## 12. 下一版逐轮Gate

1. 每个turn 2+ hit标注state delta、intent、route delta、完整rank和evidence delta。
2. 将“新属性命中”和“通用重试切route命中”分开统计。
3. 任一启用route的rank1目标不得被前融合Top100顺序截断。
4. turn 6–10调用数应显著低于485；无state变化时停止或显式换路。
