# V2 Boundary 场景分析

## 1. 指标与分布

Boundary 用于验证 Agent 提问后，用户明确表示某属性没有偏好时，系统能否记录 neutral、停止施加该条件并避免重复询问。

| 指标 | V1.1 | V2 | Δ |
|---|---:|---:|---:|
| Hits / 10 | 3 | 6 | +3 |
| Hit@10 | 0.300000 | 0.600000 | +0.300000 |
| MRR | 0.170000 | 0.470000 | +0.300000 |
| MTTC | 8.100000 | 5.900000 | -2.200000 |

首次命中为 turn 1：2、turn 2：1、turn 3：1、turn 4：2。命中 rank 均值 1.833333、方差 2.138889、范围 1–5。

## 2. 已证实的行为与失败

- 10 个 session 中有 6 次 evaluator 的标准 no-preference 回复实际进入 Agent；V1.1 为 0，说明 Boundary 主路径已经接通。
- Boundary 共发生 19 次追问，其中 use_case 6、feature 4、material 4、size 3、category 1、style 1；没有观察到同一 neutral 属性再次被询问。
- V1.1 的 3 个新增命中为 `public_0104`、`public_0169`、`public_0192`，分别在 turn 4、4、3 命中。
- 4 个 miss 中，2 个候选缺失；`public_0035` 和 `public_0112` 的目标在候选中，最佳完整 rank 分别为17和14。
- `public_0035`、`public_0112` 在 turn 1 即 `ask_attribute=null`，因此 Boundary no-preference 分支仍未触发，随后进入固定重试。

## 3. 合理推断

no-preference 本身已被正确消费，但某些类别在 question policy 中没有得到可问属性，导致 Boundary 测试仍绕过 neutral。需要保证每个可识别类别至少有一个安全 fallback 问题，并记录“不问”的明确 reason。

对于已经三问结束的 miss，继续重复相同 Top 10 不会验证更多 Boundary 行为；应明确返回完成状态或触发不同候选探索策略。

## 4. 证据边界

现有 trace 没有直接保存 neutral_attributes/asked_attributes 的 state snapshot；“未重复询问”可由外部 ask 序列证实，但内部 neutral 是否正确写入只能由单测和行为间接支持。候选内 rank 14/17 也不能证明排在前面的商品更差。

## 5. 代表案例

- 成功：`public_0041`，turn 1 问 use_case，用户 no-preference 后 turn 2 目标到 rank 1；neutral 后没有重复问 use_case。
- 成功：`public_0104`，category no-preference 后继续问其他属性，turn 4 material 回答使目标到 rank 1。
- 失败：`public_0035`，从 turn 1 起从未提问，目标虽在候选中但最佳 rank 17，后续九轮固定重试。

## 6. 1–5号修改建议

| 成员 | 建议 | 预期交付物 | 验收标准 |
|---|---|---|---|
| 1号 | 补齐 Walking 等低覆盖类别的安全 fallback 属性 | playbook coverage 清单 | 每个评测类别至少有可解释候选问题或明确跳过原因 |
| 2号 | 输出 neutral/asked state，并为 `ask=null` 增加 reason code | Boundary state trace | no-preference 后清除对应 active 值且永不重问 |
| 3号 | neutral 后重新构造不含该属性的 query/filter | before/after route trace | neutral 属性不出现在 matched terms；候选无异常缩水 |
| 4号 | 对候选内 rank 14/17 检查类别与当前回答匹配分 | score breakdown | 不损害现有6个 hit的前提下改善 K1 |
| 5号 | 将 no-preference 触发率、重复问率列为独立 gate | Boundary regression 表 | 触发可审计、重复问率为0、四场景均无非法输出 |

## 7. 下一版观察指标

Boundary 追问覆盖率、no-preference 触发率、neutral 写入率、重复问率、neutral 前后候选变化、候选内转 Top 10 比例和停止轮次。
