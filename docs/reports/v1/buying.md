# v1 Buying 场景分析报告

## 1. 场景与指标

Buying 首轮给出类别和一个明确条件。V1 已加入约束解析、安全过滤和多路线候选，但最终 Top 10 尚未使用独立融合排序。

| 数据范围 | 样本数 | Hits | Misses | Hit@10 | MRR | MTTC |
|---|---:|---:|---:|---:|---:|---:|
| Full public | 80 | 20 | 60 | 0.250000 | 0.126176 | 8.500000 |
| Development | 60 | 12 | 48 | 0.200000 | 0.104993 | 9.000000 |
| Internal holdout | 20 | 8 | 12 | 0.400000 | 0.189722 | 7.000000 |

相对 V0，Full 增加 1 个净命中（+0.0125），MRR 反而下降 0.000332。20 个命中全部发生在第 1 轮；rank 分布为：1×7、2×3、3×1、4×1、6×1、7×2、8×1、9×3、10×1。

## 2. 未识别原因

### 已证实

1. 60 个 miss 的目标均未进入任何有效轮次的最终 Top 10；失败后产生 540 个通用重试轮次，且没有一次追问。
2. V0→V1 有 2 个新增命中和 1 个回归：`public_0053` rank 6、`public_0065` rank 9；`public_0156` 从 rank 1 变为 miss。净命中增加并不代表排序整体稳定。
3. 重建的 100 个候选中，50/80 个 Buying 目标可被找到，而最终只命中 20/80。也就是说，至少 30 个最终 miss 的目标曾位于重建候选 Top 100，但没有进入最终 Top 10。
4. `Agent.respond` 调用 `merge_candidates`，而不是 `starter.ranking.rerank_candidates`。`merge_candidates` 只按路线顺序保留首次出现候选，不计算跨路线 RRF 分数。
5. 非 generic 首轮的路线顺序是 current-message → current-state → category → attribute/profile → fallback；前一条路线最多先占 50 位，合并到 100 位即停止，后置路线的证据不能提升已经出现候选的排序。
6. safe hard filter 只直接处理 budget、有限类别、color、material，并在过滤后不足 10 个时回填被过滤候选；长文本 feature 条件并不等价于严格硬约束。

### 合理推断

1. `public_0053` 和 `public_0065` 表明 material filter 对部分商品有效，但新增命中分别只有 rank 6 和 9，收益仍较脆弱。
2. V1 的多路召回能扩大候选覆盖，但没有融合分数时，后置 state/category 路线难以改变前十，是 candidate Top 100 与 final Top 10 差距的主要嫌疑。
3. `public_0156` 的明确要求是长 feature 文本，不在当前 safe filter 的受支持字段内；字段权重和顺序变化可能把原 rank-1 目标挤出前十。

### 证据边界

候选诊断为离线重建，并非正式响应保存的 route trace；它可以证明候选覆盖与最终命中之间存在明显差距，但尚不能对每个目标精确区分 K1 排序失败、filter 误删或 Agent 与诊断路径差异。尤其诊断 filter 未复现 Agent 的 `extract_basic_hard_constraints` fallback，`target_filtered_out=0` 不能作为过滤绝对安全的证明。

## 3. 代表性 public 案例

以下案例仅用于错误分析，不得转化为 public set 商品 ID 或文本特判。

| Sample | V0 → V1 | 观察 |
|---|---|---|
| `public_0053` | miss → rank 6 | Passport Covers + leather；材质约束使目标进入前十，是正向案例。 |
| `public_0065` | miss → rank 9 | Bibs + polyester；新增命中位于边缘，需要用稳定融合继续验证。 |
| `public_0156` | rank 1 → miss | Drawstring Bags + “Easy cinch opening…”；长 feature 不受当前 hard filter 支持，是必须保留的回归案例。 |

## 4. 5 人分工修改建议

| 成员 | 修改建议 | 预期交付 | 验收标准 |
|---|---|---|---|
| 1号 | 扩充 feature/material/category 的字段词典，标出哪些键值适合强过滤、哪些只能加权。 | Buying 属性覆盖表、feature 规范化建议 | 每项规则来自 catalog 统计；说明字段缺失率和误过滤风险，不使用 public target 定制。 |
| 2号 | 保留首轮类别和明确需求；只有缺失高价值槽位时追问，失败反馈不能覆盖现有状态。 | Buying 状态 trace、追问决策表 | 首轮条件跨轮存在；不重复问；状态可解释且不把模糊 feature 强制升级。 |
| 3号 | 统一 Agent 与诊断工具的 hard-constraint 来源；输出各 route 候选和 filter reason。 | 可观测 candidate pipeline、filter 对照测试 | Agent/diagnostic 同一输入得到相同 pre/post-filter 集合；目标误删可逐条定位。 |
| 4号 | 把现有 RRF 真正接入 Agent，保留多路线证据，并在其后加入显式需求加权。 | RRF 集成、score breakdown、路线权重 ablation | `public_0156` 不再回归；candidate Top 100 中的目标更常进入 Top 10；MRR 不低于 V0。 |
| 5号 | 将 filter、multi-route、RRF 分成独立实验，维护 Buying churn 表。 | dev/holdout 指标、gain/loss 列表、回归门禁 | Full/dev/holdout 齐全；新增命中、丢失命中和 rank 变化均可复现；不得只看净 Hit。 |

## 5. V2 观察指标

- Candidate Recall@50/100、post-filter target retention 和 final Hit@10 的漏斗。
- V0/V1/V2 的 gained hit、lost hit、rank 上下移动数量。
- 明确 material/color/budget 与长 feature 条件分别统计，避免平均值掩盖解析缺口。
- Development Buying MRR 必须重点监控：V1 从 0.116548 降至 0.104993。
