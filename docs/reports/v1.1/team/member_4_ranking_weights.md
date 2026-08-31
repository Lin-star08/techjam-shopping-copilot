# 4号成员：融合、重排与权重实验修改建议

## 1. 本阶段目标

处理 V1.1 的 94 个“目标已进入 filter 后候选、但未进入最终 Top 10”的 miss，同时控制已有命中的 rank churn。不要在同一次实验里扩词典、加 route 或接追问。

排序型 miss 分布：Buying 37、Browsing 37、Intent Override 15、Boundary 5。V1→V1.1 虽新增 13 个 hit，但丢失 `public_0053`；shared Buying hits 中 4 条上升、6 条下降、9 条不变。

## 2. 两类权重必须分开

### 评测权重：固定，不可调

官方 Technical Score：

`0.50 × Hit@10 + 0.30 × MRR + 0.20 × Efficiency`

其中 `Efficiency = clip((11 - MTTC) / 10, 0, 1)`。V1.1 三项贡献为 0.095000、0.028037、0.036400，总计 0.159437。不得修改 evaluator 或用自定义分数替代正式结果。

### 产品排序权重：可实验

当前等权 RRF：

`RRF(d) = Σ_r 1 / (k + rank_r(d))`，当前 `k=60`。

原始 SIGIR 2009 RRF 论文将 `k=60` 在 pilot 中固定，并说明该常数用于减弱异常系统高排名的影响；论文同时强调 RRF 的优点是不需要校准不同检索器的原始 score。这里提出的 route weight 和显式 bonus 是本项目的待验证扩展，不是论文给出的通用最优参数。参考：[Cormack, Clarke & Büttcher, 2009](https://research.google/pubs/reciprocal-rank-fusion-outperforms-condorcet-and-individual-rank-learning-methods/)。

建议第一步只做 Weighted RRF：

`WRRF(d) = Σ_r w_r / (k + rank_r(d))`

第二步再单独加入与 RRF 同量纲的显式信号：

`Final(d) = WRRF(d) + [λ_exp E(d) + λ_rec R(d) - λ_bad V(d)] / (k + 1)`

- `E(d)`：当前轮明确需求匹配度，归一到 0–1。
- `R(d)`：override 新值/近期明确值匹配度，归一到 0–1。
- `V(d)`：明确约束违反度，归一到 0–1；高置信违反项优先由 filter 处理。

这种写法让 bonus 与“一条 rank-1 route”的贡献处于同一量级，避免直接加 0.1 等大常数压倒 RRF。

## 3. 分阶段实验

### 阶段 A：Weighted RRF（P0）

权重初始假设，不是最终答案：

| Route | 初始中心 | Development 搜索范围 | 原因 |
|---|---:|---:|---|
| current_message | 1.40 | 1.0–1.8 | 当前明确表达优先，保护单路线强匹配。 |
| current_state | 1.20 | 0.9–1.5 | 保留跨轮有效需求。 |
| category | 1.00 | 固定 1.0 | 作为尺度基准。 |
| attribute_profile | 0.50 | 0.2–0.8 | 画像/软偏好不能覆盖明确需求。 |
| browsing_profile | 0.35 | 0.1–0.6 | 只用于模糊场景弱加分。 |
| popular_category | 0.20 | 0–0.4 | 主要是 fallback，不应主导。 |
| fallback_bm25 | 0.50 | 0.2–0.8 | 保证覆盖但控制泛查询噪声。 |

同时仅搜索 `k ∈ {20, 40, 60, 80}`。先固定 k 调 route weight，再固定最佳权重调 k，避免组合爆炸和无法归因。

验收：development Hit/MRR 不低于 V1.1；`public_0053` 类型的单路线强匹配回归减少；holdout 只在候选配置确定后查看。

### 阶段 B：Explicit/Recency 信号（P0）

1. 固定阶段 A 权重，再搜索 `λ_exp, λ_rec ∈ {0, 0.25, 0.5, 1.0}`。
2. `invalidated`、`neutral` 值贡献必须为 0。
3. Intent Override 单独检查 MRR，当前从 V1 的 0.111111 降到 0.097778。

验收：Intent MRR 恢复；Buying development MRR 不再下降；score breakdown 能解释每个 Top 10。

### 阶段 C：多样性（P1）

只在 Weighted RRF 稳定后，针对 Browsing 加轻量去同质化。多样性不得把明确匹配商品移出前十，也不得与 profile 权重同时改变。

## 4. 典型案例对应

| 案例 | 排序证据 | 修改方向 |
|---|---|---|
| `public_0053` / Buying regression | 候选存在，最佳 RRF rank 13；只来自 current-message/fallback | 提高当前明确路线相对弱重复 route 的权重。 |
| `public_0065` / Buying success | rank 9→3 | 保留多 route 共识带来的收益。 |
| `public_0125` / Intent success | 新增 hit 但仅 rank 10 | 增加 override 新值 recency 信号，不通过 sample 特判。 |
| `public_0166` / Intent rank-down | rank 1→3 | 检查等权 route 是否稀释新明确值。 |

## 5. 排序验收清单

- 每个实验只改一组参数并绑定 commit。
- 同时报 Hit、MRR、MTTC、Technical Score 和 gained/lost/rank up/down。
- 分别报告 micro（样本加权）与 macro（四场景等权），防止 80 条大场景掩盖 10 条 Boundary。
- Development 用于选择权重，holdout 用于阶段确认，不能反复查看后回调参数。
- 所有权重、k、score 分量和 tie-break 可复现。
