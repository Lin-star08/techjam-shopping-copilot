# 3号成员：检索、Hard Filter 与 Fallback 修改建议

## 1. 本阶段目标

优先解决 V1.1 中 68 个“有效轮次从未进入 filter 后候选”的 miss，并把 filter 前后证据变成正式可观测数据。不要同时调整 RRF 权重，以保持实验可归因。

候选缺失分布：Buying 19/80、Browsing 37/80、Intent Override 10/30、Boundary 2/10。另有 94 个 miss 已在候选中，应交给4号排序，不应通过无限扩大召回池解决。

## 2. 分阶段任务

### 阶段 A：统一可观测 Pipeline（P0）

1. Agent 与诊断工具共享同一个候选构造函数，避免 V1 诊断仍使用旧 `merge_candidates(limit=100)` 的漂移。
2. 开发 trace 至少记录：route、route_rank、matched_terms、filter 前后候选数、filter reason、目标是否保留。
3. 将 per-turn 和 per-session 分开：某轮被过滤、另一轮重新出现不能合并成“整条被过滤”。

预期交付：统一 `build_candidates`/debug hook、结构化候选漏斗、逐轮 filter audit。

验收：正式 Agent 与诊断同输入的候选集合一致；不再靠临时 runtime patch 才能定位 R1/F1/K1。

### 阶段 B：召回补强（P0）

1. 对候选缺失按路线分组：category alias 缺失、current-message 词法不匹配、state 未进入 query、profile 无覆盖。
2. 建立“类别 + 当前明确属性”的联合 route，尤其 Intent Override 的保留类别 + 新值。
3. Browsing 回答后生成 attribute route；没有新回答时不得把固定反馈句当商品查询。
4. route limit 和总候选上限必须参数化，报告候选量均值、方差、P95 和最大值。

预期交付：单路线 recall ablation、联合 route、参数说明。

验收：68 个候选缺失类的 Recall@100 改善；延迟和候选量受控；不得通过 catalog 全量 fallback 虚增 recall。

### 阶段 C：Hard Filter 安全性（P0）

1. 只对高置信、字段可验证的 material/color/category/budget 执行强过滤。
2. 长 feature、`fabric` 等泛词默认作为排序信号；字段缺失时保持候选而非判定不满足。
3. 回填逻辑必须标记 `fallback after strict filter`，并统计回填比例。

预期交付：filter truth table、误删回归集、字段缺失策略。

验收：目标逐轮误删可见；`public_0156` 的 filter 行为有明确解释；新增过滤不能损害 Boundary/Browsing 候选非空性。

## 3. 典型案例对应

| 案例 | 证据 | 3号动作 |
|---|---|---|
| `public_0002` / Intent failure | leather 生效后目标不在最终 Top 10，属于需检查的联合类别 route | 建立 Belts + leather 组合路线并记录 target route rank。 |
| `public_0006` / Browsing failure | Basketball 类别下目标未进入有效候选 | 检查 category alias、shorts 词法覆盖及回答后 attribute route。 |
| `public_0156` / Buying failure | 某有效轮次目标被 filter 排除，其他轮次又出现，最佳 RRF rank 108 | 按轮输出 filter reason，区分 F1 与 K1，不做会话级误判。 |

## 4. 检索验收清单

- Candidate Recall@50/100 分场景、development/holdout 齐全。
- filter 前后目标保留率和候选量统计齐全。
- route limit、总候选数、fallback 比例及延迟极值可复现。
- 无效/重复 ASIN 不进入输出。
- 不修改 evaluator，不读取 public target 构造查询。
