# 1号成员：数据词典与商品知识修改建议

## 1. 本阶段目标

把 V1.1 的“候选缺失”转化为可复用的 catalog 词典、类别属性统计和追问知识，不直接修改排序权重。Public target 只用于评估问题分组，不能进入词典生成逻辑。

V1.1 证据：162 个 miss 中有 68 个目标在所有有效轮次都未进入 filter 后候选；分场景为 Buying 19、Browsing 37、Intent Override 10、Boundary 2。1号优先处理这 68 条背后的通用字段覆盖与词法问题。

## 2. 分阶段任务

### 阶段 A：字段与缺失统计（P0）

1. 按 category 统计 title、features、description、details、store、price 的非空率。
2. 对 material、color、size、style、feature、use_case 建立“值—别名—出现字段—覆盖商品数”表。
3. 区分安全强约束和弱信号：高精度 material/color/budget 可进入 filter 候选；`fabric`、`comfortable` 等泛词只提供召回/排序证据。
4. 对 68 个候选缺失案例只做聚合归因，例如 alias 缺失、category 过粗、字段稀疏；禁止添加 sample ID 或目标 ASIN 规则。

预期交付：更新 `artifacts/lexicon.json` 的生成源、字段覆盖报告、候选缺失 taxonomy。

验收：词典完全由 `data/catalog.jsonl` 可复现生成；每个新增 alias 有 catalog 证据和覆盖数；不存在 public target 专用映射。

### 阶段 B：类别—属性 playbook（P0）

1. 对 Browsing/Boundary 高频类别计算属性覆盖率与区分度。
2. 每类给出 2–3 个可回答属性及备选顺序，例如先问 material，再问 style/use_case。
3. 信息增益建议使用 catalog 候选分布计算，不能用 public ground truth 命中率选择问题。

推荐统计口径：对类别候选集合 (C)，属性 (a) 的离散度可用归一化熵；同时报告可回答覆盖率。优先选择“覆盖率高且分布不过度集中”的属性。

预期交付：`category -> [{attribute, coverage, entropy, top_values}]` 的机器可读文件及通俗版说明。

验收：重点类别至少两个备选属性；第一个属性无偏好时仍有下一选择；字段缺失不会被解释为用户无偏好。

### 阶段 C：联调与回归（P1）

1. 向2号提供可问属性与值规范；向3号提供 query expansion；向4号提供属性可靠度。
2. 对新词典运行 candidate recall ablation，只看 development，阶段候选再看 holdout。
3. 检查新 alias 是否扩大噪声候选，尤其 `fabric`、`accessories`、`men/women` 等高频词。

验收：68 个候选缺失类别的 Candidate Recall@100 提升；候选量和误扩张同时报告；四场景没有明显退化。

## 3. 典型案例对应

| 案例 | 现象 | 1号应提供的通用资产 |
|---|---|---|
| `public_0006` / Browsing | Basketball Men，目标始终未进候选/Top 10 | Basketball shorts 的 category alias、material/feature 覆盖和高价值问题，不写目标商品规则。 |
| `public_0002` / Intent | leather override 后仍 miss | Belts + leather 的联合类别词和字段覆盖，供3号建立联合 route。 |
| `public_0054` / Buying success | fabric 条件在 RRF 后 rank 5 | 说明泛 material 词可以提供弱证据，但不应自动定义为精确 hard filter。 |

## 4. 数据验收清单

- 词典可由脚本重新生成且顺序稳定。
- 所有统计注明分母、缺失值处理和 population/sample 口径。
- 不使用 public sample 的 target 频次选词或调参。
- 向5号提供前后 Candidate Recall、候选量均值/方差和极值。
- 交付版本带 Git commit、生成命令和 schema 说明。
