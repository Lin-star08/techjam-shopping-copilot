# V2 Intent Override 场景分析

## 1. 指标与分布

Intent Override 要求旧偏好失效后，只在 override 生效轮及之后计分。

| 指标 | V1.1 | V2 | Δ |
|---|---:|---:|---:|
| Hits / 30 | 5 | 8 | +3 net |
| Hit@10 | 0.166667 | 0.266667 | +0.100000 |
| MRR | 0.097778 | 0.163333 | +0.065555 |
| MTTC | 9.833333 | 9.100000 | -0.733333 |

V2 有 8 hit、22 miss；1 个首次命中在 turn 3，7 个在 turn 4。命中 rank 均值 2.375000、方差 2.484375、范围 1–5。

相对 V1.1 新增 4 个 hit、丢失 1 个，净增 3 个。shared hit 中 3 个 rank 不变、1 个下降。

## 2. 已证实的失败结构

- 30 个 session 中有 20 个在 override 生效前至少一次出现目标；共出现 26 个 pre-override target turn，这些按 evaluator 规则均不计分。
- override 生效后候选覆盖 23/30。22 个 miss 中，7 个目标从未进入 filter 后候选，15 个目标已进入但完整 rank > 10。
- `public_0004` 在 turn 1–2 rank 3 但不可计分；polyester override 生效后 turn 3 升至 rank 1，证明新值能改变有效排序。
- `public_0125` 是 V1.1 hit→V2 miss 的回归：override 前 rank 3，生效后候选仍存在但最佳完整 rank 13。

## 3. 合理推断

V2 已能保存多轮上下文并处理部分 override，但 20/30 的 pre-override 出现率说明旧需求下的高排名很常见。下一步不应追求“提前看到目标”，而应验证 override 后旧值完全退出 state、route query 和 score contribution。

15 个候选内 miss 表明 recency/explicit override 需要独立于等权 RRF 的加分或门控。当前 `mild/stronger` 只是固定 route 权重，不能表达“本轮新值高于历史值”。

## 4. 证据边界

Trace 记录 eligibility、目标 rank 和用户消息，但未保存每轮完整 state、invalidated slots、route matched terms 与 score contribution。目标在 override 后下降不能自动证明旧偏好污染；也可能是新值召回竞争更强。需要 state/route/score 三联证据后才能判为 S2。

## 5. 代表案例

- 成功：`public_0004`，override 前目标 rank 3 不计分；polyester 生效后 rank 1，体现正确的有效轮语义。
- 成功：`public_0080`，turn 3 目标 rank 8 但仍不可计分；cotton override 后 turn 4 到 rank 2。
- 失败：`public_0125`，V1.1 的 rank-10 hit 在 V2 回归；V2 override 后最佳完整 rank 13，是 K1 边界案例。

## 6. 1–5号修改建议

| 成员 | 建议 | 预期交付物 | 验收标准 |
|---|---|---|---|
| 1号 | 标注同属性值的规范化与类别适用范围 | override value normalization 表 | 新旧值可稳定映射到同一 slot，不依赖 public ID |
| 2号 | 输出 before/after state、invalidated 和 neutral；保证新值覆盖旧值 | override state trace 与单测 | 旧值不再出现在 active query/filter；30条均可审计 |
| 3号 | 建立 override 后 category+new-value 联合 route | eligible-turn route trace | override 后候选覆盖高于23/30 |
| 4号 | 增加 current-turn/override recency 分量，不用固定 route 权重代替 | contribution breakdown | 候选内15个 miss改善且 shared high-rank 不回退 |
| 5号 | 分开统计 pre-only、post-candidate-miss、post-rank-miss | override gate 表 | 只用生效轮计分；gained/lost/rank churn 全量记录 |

## 7. 下一版观察指标

override 后候选覆盖、旧值残留率、current-turn contribution、pre-only session 数、eligible-turn Hit/MRR、shared-rank churn 与 lost hits。
