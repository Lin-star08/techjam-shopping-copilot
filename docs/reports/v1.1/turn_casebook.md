# v1.1 逐轮典型案例册

## 1. 口径

本报告基于 V1.1 的 200 条全量 trace。`活跃会话`表示该轮实际调用了 Agent；`首次命中`只统计 evaluator 允许计分后第一次进入 Top 10。Intent Override 生效前即使目标出现也不算成功。

以下 public 案例只用于错误分析和回归验证，不得转化为商品 ID、标题或消息特判。

| Turn | 活跃会话 | 首次命中 | 条件命中率 | 累计命中 | 典型成功 | 典型失败 |
|---:|---:|---:|---:|---:|---|---|
| 1 | 200 | 32 | 16.0000% | 32/200 | `public_0050` rank 2 | `public_0006` miss |
| 2 | 168 | 1 | 0.5952% | 33/200 | `public_0041` rank 1 | `public_0053` miss |
| 3 | 167 | 0 | 0% | 33/200 | 无 | `public_0002` override miss |
| 4 | 167 | 5 | 2.9940% | 38/200 | `public_0125` rank 10 | `public_0004` miss |
| 5 | 162 | 0 | 0% | 38/200 | 无 | `public_0001` miss |
| 6 | 162 | 0 | 0% | 38/200 | 无 | `public_0006` miss |
| 7 | 162 | 0 | 0% | 38/200 | 无 | `public_0035` miss |
| 8 | 162 | 0 | 0% | 38/200 | 无 | `public_0002` miss |
| 9 | 162 | 0 | 0% | 38/200 | 无 | `public_0053` miss |
| 10 | 162 | 0 | 0% | 38/200 | 无 | `public_0007` miss |

## 2. Turn 1：主要收益轮次

- 成功：`public_0050`，Boundary，Industrial & Construction Boots，目标 rank 2。RRF 用类别路线共识直接命中。
- 失败：`public_0006`，Browsing，Basketball Men。目标未进入 Top 10，Agent 也没有询问 polyester/透气性等属性。
- 结论：32/38 个最终命中来自本轮。V1.1 仍主要是单轮检索系统；下一步必须把宽类别失败导向有效追问。

## 3. Turn 2：唯一后续直接命中

- 成功：`public_0041`，Boundary，turn 1 miss，turn 2 rank 1。
- 失败：`public_0053`，Buying，目标在完整候选中最佳 RRF rank 13，仍未进 Top 10。
- 结论：成功轮只收到固定“Ask me about one specific attribute”反馈，`ask_attribute` 仍为 null。命中来自保存状态参与融合，不是获得了新信息，因此不能当作 clarification 成功。

## 4. Turn 3：无首次命中

- 成功：无。
- 失败：`public_0002`，Intent Override 在本轮切换为 leather，目标仍未进入 Top 10。
- 结论：部分会话在 turn 3 才进入有效 override，但新高频材质没有与保留类别形成足够强的最终排序证据。需由2号检查 state、3号检查联合 route、4号检查 recency 权重。

## 5. Turn 4：Override 的全部有效收益

- 成功：`public_0125`，Intent Override，Acrylic 生效后 rank 10；生效前 turn 1 rank 3 不计分。
- 失败：`public_0004`，polyester 生效后目标仍缺失，后续推荐无法恢复。
- 结论：本轮新增 5 个命中，全部来自 Intent Override。rank 10 的新增命中与已有高位排名回退共同导致 Intent Hit 上升但 MRR 下降。

## 6. Turn 5：进入无信息平台期

- 成功：无。
- 失败：`public_0001`，Buying，Jewelry Necklaces + alloy；目标仍不在 Top 10。
- 结论：162 条会话从本轮开始直到 turn 10 均无新命中。固定反馈没有触发追问，列表在同一会话内停止变化。

## 7. Turn 6：Browsing 仍无收敛

- 成功：无。
- 失败：`public_0006`，Basketball Men，和 turn 2–5 相同的状态相关列表继续重复。
- 结论：RRF 让不同 session 的重试列表不再完全相同，但没有新增用户属性时，同一 session 仍无信息增益。

## 8. Turn 7：Boundary 行为仍未被测试

- 成功：无。
- 失败：`public_0035`，Boundary，Athletic Walking。Agent 从未提问，no-preference 分支未触发。
- 结论：Boundary 的 3/10 推荐命中不能替代 neutral/asked 行为验收；该失败应由2号优先建立端到端路径。

## 9. Turn 8：Override 后重试无恢复

- 成功：无。
- 失败：`public_0002`，leather override 已生效多轮，目标仍未出现。
- 结论：状态持久化本身不足以恢复目标。需要输出 eligible-turn route rank，区分类别联合召回缺失与排序不足。

## 10. Turn 9：已召回目标仍可能持续排在前十外

- 成功：无。
- 失败：`public_0053`，目标存在于候选但最佳 RRF rank 13。
- 结论：这是明确 K1 案例；继续相同重试不会改变权重或证据，应由4号通过通用 weighted RRF 修复。

## 11. Turn 10：终止轮

- 成功：无。
- 失败：`public_0007`，Browsing，Tunics 目标在 10 轮内未命中。
- 结论：162 个会话最终按 turn 11 计入 MTTC。turn 5–10 共 972 次调用没有产生任何新命中，是当前最明显的效率浪费。

## 12. 下一版逐轮验收

1. Turn 2/3 应出现由追问回答驱动的新增命中，并保存新增属性证据。
2. Turn 5–10 的活跃会话数应显著下降；连续相同 Top 10 应触发换问或停止。
3. 每个 turn 2+ success 必须标注：新消息、state delta、候选 rank delta、最终 rank。
4. 对没有 success 的轮次仍保留至少一个失败案例，防止平均指标掩盖死循环。
