# v1 Boundary 场景分析报告

## 1. 场景与指标

Boundary 用来验证：Agent 提问后，用户表示该属性无偏好时，系统是否记录 neutral、停止重复询问并换问或推荐。V1 已实现 neutral 数据结构和单元测试，但 Agent 没有提出问题，因此真实评测未进入该分支。

| 数据范围 | 样本数 | Hits | Misses | Hit@10 | MRR | MTTC |
|---|---:|---:|---:|---:|---:|---:|
| Full public | 10 | 0 | 10 | 0.000000 | 0.000000 | 11.000000 |
| Development | 7 | 0 | 7 | 0.000000 | 0.000000 | 11.000000 |
| Internal holdout | 3 | 0 | 3 | 0.000000 | 0.000000 | 11.000000 |

所有指标与 V0 完全一致，没有命中排名；10 个 miss 均按第 11 轮计算。

## 2. 未识别原因

### 已证实

1. 100 个 Boundary 响应全部合法且无异常，但 `ask_attribute` 始终为 null。
2. 模拟器的 no-preference 回复一次都没有触发；V1 的 `neutral_attributes`、`asked_attributes` 和 no-preference parser 只通过了单元测试，没有经过 end-to-end evaluation。
3. 10 条会话各自产生 9 个通用重试，共 90 轮；每条会话只有首轮列表和公共重试列表两种结果。
4. 目标从未进入 final Top 10，但离线重建候选池在 Top 50 找到 3/10、Top 100 找到 7/10，候选到最终输出存在明显损失。
5. `Agent.respond` 固定返回 `ask_attribute: None`，因此仅修改 state/neutral parser 不可能改变 Boundary 评测路径。

### 合理推断

1. 7 个目标已在重建候选 Top 100 中出现，融合排序可能带来部分直接命中；其余 3 个仍需要更好召回或追问。
2. Boundary 的首要缺口是 clarification 接线，而不是 neutral 容器本身。只有 Agent 真正问出属性，才能验证 neutral 是否会阻断重复提问和 profile 污染。
3. 固定重试句未被识别为 generic，加上顺序式 merge，使已保存类别和 profile 无法改变最终 Top 10。

### 证据边界

因为 no-preference 从未发生，不能声称 V1 在真实会话中已经正确处理 neutral，也不能声称存在“重复询问 neutral 属性”的实际 bug。候选诊断同样不是 Agent 原生逐路 trace，7/10 不等于已有 7 条确定 K1。

## 3. 代表性 public 案例

以下案例仅用于错误分析，不得转化为 public set 特判。

| Sample | V1 结果 | 观察 |
|---|---|---|
| `public_0035` | 全程 miss | Athletic Walking；Agent 从未问 material/feature，no-preference 分支无法触发。 |
| `public_0041` | 全程 miss | Tunics；已有 neutral parser 不会自动产生问题，行为与 V0 相同。 |
| `public_0050` | 全程 miss | Industrial & Construction Boots；类别较具体，但没有换问或融合 fallback。 |

## 4. 5 人分工修改建议

| 成员 | 修改建议 | 预期交付 | 验收标准 |
|---|---|---|---|
| 1号 | 为 Boundary 高频类别提供有序替代属性和字段覆盖率。 | 2–3 级 question fallback playbook | 每类至少两个可回答属性；来自 catalog，不使用 public target 特判。 |
| 2号 | 将 clarification policy 接入 Agent；收到 no-preference 后调用 neutral/asked 状态并换问或停止。 | end-to-end Boundary 状态 trace | 首问非空；neutral 属性不再问、不参与约束；不会无限连续追问。 |
| 3号 | neutral 后以剩余类别/state 重新召回，并输出合法 fallback 与 route evidence。 | neutral-aware retrieval trace | 候选非空、唯一；neutral 词不进入 query/filter；Agent 与诊断路径一致。 |
| 4号 | neutral 属性权重置零，接入 RRF 并评估 candidate Top 100 到 Top 10 的转化。 | neutral-aware score breakdown | final score 无 neutral/profile 冲突贡献；已有候选可稳定进入更高排名。 |
| 5号 | 对 10 条逐条记录首问、no-preference、下一动作、重复属性和候选变化。 | Boundary 行为矩阵、dev/holdout gate | no-preference 触发率 > 0；neutral 重复询问为 0；场景不再 0/10。 |

## 5. V2 观察指标

- 首次有效追问率、no-preference 触发率、neutral 重复询问次数。
- neutral 前后候选数、合法性、Candidate Recall@50/100 和 final rank。
- 换问次数及 MTTC，避免通过无限提问换取偶然命中。
- 3 条 holdout 必须逐条看 trace，不能只看小样本平均值。
