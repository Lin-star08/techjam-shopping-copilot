# V3 99% Hit@10 数据规律与四人作战工作流

## 1. 目标定义与结论

V2.1 在 200 条 public 数据上命中 103 条，Hit@10 为 `0.515000`。达到 99% 意味着至少命中 198/200，即需要在当前 97 个 miss 中净恢复至少 95 个，同时最多允许 2 个失败。

这是一个 stretch goal，不是基于现有证据可以直接承诺的结果。正确的工程目标是建立一条能够验证是否可达 99% 的工作流：先证明数据在现有对话信息下可识别，再把候选召回、融合、过滤和排序的损失逐层降到接近零。禁止通过 public sample ID、目标 ASIN、商品标题或逐例规则实现表面上的 99%。

当前最重要的结论：

1. 97 个 miss 已拆为 R1 纯召回 20、R3 融合前截断 28、F1 过滤误删 1、K1 rank 11–20 为 21、K1 rank 21–100 为 27。
2. 先消灭 R3/F1、再把全 catalog 结构化召回做成接近无损，理论上可把 49 个候选链失败大幅压缩；剩余难点是精确 ASIN 的可识别性和排序。
3. 200 个目标的完整可观察 intent-card 签名互不重复，但放回 50,000 商品 catalog 后，25 个目标仍与其他商品共享相同签名，其中 2 个目标对应的同签名候选分别超过 10 个，最大为 47。因此 99% 必须有 Oracle 可识别性 Gate；若完整对话信息仍无法把至少 198 个目标放进 Top 10，需要增加可回答信号或重新审视 exact-ASIN 指标，而不能继续盲目调权。
4. Public 目标全部是数据质量 A 级商品，且有价格比例为 89%，远高于 catalog 的 19.89%。评测集存在明显完整度偏置；利用结构化字段是合理的，但不能宣称结果能代表整个 catalog。
5. 隐藏约束严重偏向 material 和 feature，而系统高频询问 use_case。V3 的问题策略必须改为 catalog/category 驱动的 material、feature、color 优先级。

## 2. 数据质量审计

### 2.1 Catalog 基本质量

| 项目 | 结果 | 对 V3 的影响 |
|---|---:|---|
| Catalog 行数 / 唯一 ASIN | 50,000 / 50,000 | 无 ASIN 重复，可稳定按商品建索引 |
| 空标题 | 2 | 进入最低质量层，不作为正常精确召回依据 |
| Features 非空 | 44,781（89.56%） | 主要属性召回来源，但需处理 10.44% 缺失 |
| Description 非空 | 26,113（52.23%） | 不能作为硬性必备字段 |
| Details 非空 | 48,330（96.66%） | 适合结构化属性抽取 |
| Store 非空 | 49,686（99.37%） | 可作弱 brand/store 证据 |
| Price 原始非空 | 10,527（21.05%） | 价格严重稀疏，缺失不能判为超预算 |
| 可解析数值价格 | 10,410（20.82%） | 另有 117 条为 `—`、`from 12.99` 等非标准值 |
| 价格 > 1000 | 22 | 标记异常/长尾，不应无依据删除 |
| 规范化标题重复行 | 751 | 不同 ASIN 可能同标题，不能只用标题确定 exact target |
| Leaf category 数 | 799 | 长尾明显，需要按支持度分层 |

价格中位数为 22.88，P95 为 138.924，P99 为 379.99，最大值为 4,119。Rating 全量存在，中位数 4.2；rating_number 中位数仅 12，但最大值 408,371，热门度高度长尾，必须使用 `log1p` 或分位数归一化，不能直接线性加权。

### 2.2 数据质量分层规律

定义只用于索引和缺失处理，不用于删除商品：

- A 级：title、categories、features、details 均非空。
- B 级：title、categories 非空，features/details 至少一个非空。
- C 级：不满足以上条件。

| 质量层 | Catalog | Public 目标 |
|---|---:|---:|
| A | 43,348（86.70%） | 200（100%） |
| B | 6,412（12.82%） | 0 |
| C | 240（0.48%） | 0 |
| A 且有价格 | 9,943（19.89%） | 178（89.00%） |

筛选规则：A/B/C 决定可用证据和 unknown 策略，不允许简单丢弃 B/C。否则在 public 上可能看起来变好，却会破坏真实 catalog 覆盖。

### 2.3 Category 长尾规律

- Public 目标覆盖 112 个 leaf category，说明不是少数类别问题。
- 目标 leaf 在 catalog 中的支持度中位数为 230，P75 为 503，P95 约为 1,037，最大为 2,807。
- 5 个目标位于支持度不超过 10 的超小类；45 个位于 11–100；132 个位于 101–1000；18 个位于超过 1000 的大类。
- Catalog 高频 leaf 中出现 `Casual`、`Westlake` 等可能属于 style、系列或污染标签的值，leaf category 不能未经置信度判断直接成为 hard filter。

建议的类别支持度策略：

| Leaf 支持度 | 候选策略 | 对话策略 |
|---|---|---|
| ≤10 | 类内全部保留，避免排序前裁剪 | 通常不需要类别追问 |
| 11–100 | 类内结构化召回，目标是 Recall@100=100% | 询问一个高区分属性 |
| 101–1000 | lexical + attribute + state 多路召回 | material/feature/color 中选择信息增益最高者 |
| >1000 | 类别本身区分度不足，不允许热门候选占满预算 | 必须先获得高区分属性或执行多样化探索 |

### 2.4 Public 分布规律与偏置

| 维度 | 分布 |
|---|---|
| Scenario | Buying 80、Browsing 80、Intent Override 30、Boundary 10 |
| Difficulty | Easy 80、Medium 90、Hard 30 |
| Scenario-Difficulty | Buying=Easy；Browsing/Boundary=Medium；Intent Override=Hard |
| Category bucket | 200 条全部为 clothing |
| Profile 高频标签 | fit 163、material 154、comfort 144、style 101 |

Scenario 与 difficulty 完全耦合，因此不能把“场景改善”和“难度改善”当成两个独立结论。全部样本都属于 clothing，99% 只能表示当前评测域，不代表跨品类泛化。

Public 目标与 catalog 的字段差异：

- 目标 features/details 均为 100% 非空，catalog 分别为 89.56% 和 96.66%。
- 目标 description 非空 44.5%，低于 catalog 的 52.23%。
- 目标 price 非空 89%，远高于 catalog 的 21.05%。

因此 V3 可以充分利用 features/details，但 description 只能是可选信号，price 必须使用 unknown 逻辑。评测集的价格偏置必须写入限制说明。

### 2.5 约束生成分布

200 个目标共生成 400 个 hard constraints 和 400 个 soft preferences。

| 约束类型 | Hard | Hard占比 | Soft | Soft占比 |
|---|---:|---:|---:|---:|
| Material | 258 | 64.50% | 44 | 11.00% |
| Feature | 90 | 22.50% | 314 | 78.50% |
| Color | 44 | 11.00% | 16 | 4.00% |
| Style | 5 | 1.25% | 14 | 3.50% |
| Size | 2 | 0.50% | 9 | 2.25% |
| Use case | 1 | 0.25% | 3 | 0.75% |

V2.1 却询问 use_case 141 次。Use case 在800个可披露约束中仅出现4次，这是问题策略与数据分布的明显错配。V3 必须优先选择 material、feature、color，并按 leaf category 的真实覆盖和熵动态排序。

## 3. Development / Holdout 使用规律

固定切分是按 scenario 做 SHA-256 分层，development 150、holdout 50，不使用 ground truth。Development/holdout 场景比例基本一致，但没有按 leaf 支持度、字段缺失或约束类型分层。

| 范围 | 当前 Hit | Miss | R1 | R3 | F1 | K1-near | K1-deep |
|---|---:|---:|---:|---:|---:|---:|---:|
| Development | 77/150 | 73 | 16 | 22 | 1 | 15 | 19 |
| Holdout | 26/50 | 24 | 4 | 6 | 0 | 6 | 8 |

99% 在 development 上意味着至少 149/150，在 holdout 上意味着至少 49/50。不得修改现有 `docs/internal_split.json`。开发期间应仅在 development 内建立按以下字段分层的 shadow folds：

- scenario；
- leaf support tier；
- hard constraint 主类型；
- A/B/C 质量层；
- price known/unknown；
- normalized-title duplicate family。

## 4. 99% 工作流总览

```text
Catalog质量审计
  → 全量商品结构化Intent Signature
  → Oracle可识别性上限
  → 状态与约束获取
  → 全catalog混合召回
  → 公平融合与三值过滤
  → 冻结候选排序
  → 重复/同签名商品消歧
  → Development分层回归
  → 一次Holdout Gate
```

### Gate 0：冻结基线与禁止项

- 固定 V2.1 正式结果、commit、配置、数据 SHA 和 internal split。
- 所有新模块不得读取 public ground truth 参与线上响应。
- Public ID/ASIN 仅能出现在 evaluator、错误报告和通用回归测试参数中。
- 每个实验只能有一个主要变量。

### Gate 1：数据质量与索引覆盖

- 50,000 个 ASIN 全部进入基础索引，包括 B/C 级商品。
- 为每个商品生成规范化 category、material、color、feature、size、style、brand/store、price-known、quality-tier。
- 所有解析字段保留 source field、normalized value、confidence 和 missing/unknown。
- 索引构建后 ASIN 数必须仍为 50,000，不能因缺字段静默丢商品。

### Gate 2：Oracle 可识别性

为每个 catalog 商品生成不依赖 public 的完整 catalog-intent signature，然后回答：如果系统拿到 evaluator 最多能够披露的 category + hard + soft + profile 信息，目标是否能进入 Top 10？

必须报告：

- Oracle Recall@10 / @100；
- 每个同签名组的商品数；
- 目标在同签名组中的可区分字段；
- full-information 仍无法 Top10 的数量。

99% 可行 Gate：Oracle Hit@10 至少 198/200。若未达到，不得继续宣称排序调参可以达到99%；必须新增 evaluator 可回答的品牌、尺寸、颜色或具体feature信号，或者调整 exact-ASIN 指标口径。

### Gate 3：约束获取和状态一致性

- 通用重试不能覆盖已有 Buying/Override 意图。
- Override 原子替换旧值，旧 query/filter/evidence 贡献归零。
- Neutral 只影响单个属性，不清除 category 和其他有效条件。
- 问题从 material、feature、color 中按候选熵下降量选择；use_case 只有在类别统计证明有信息量时才询问。
- 连续两轮候选不变、两次无额外偏好或三次有效追问后停止/切换策略。

Gate：具体约束回答率 ≥50%，有效约束披露覆盖 ≥95%，turn 6–10 零收益调用 <50。

### Gate 4：全量召回与公平融合

99% 不能依赖若干小 Top-K route 的偶然交集。V3 应使用预计算稀疏索引或可控的全 catalog 打分：

- structured exact/normalized attributes；
- title/category/feature/details BM25；
- current-message、current-state、override-recency；
- profile 仅作弱召回和tie-break；
- 全 route 聚合后裁剪，或按配额 round-robin；
- 每个启用 route 的 Top3 必须有保底。

Gate：

- Candidate Recall@500 = 100%；
- Candidate Recall@100 ≥99.5%；
- 四场景 Recall@100 均 ≥99%；
- R3=0；
- 改变 route 声明顺序不改变候选集合；
- 记录每条 route 的去重新增量和延迟。

### Gate 5：三值 Hard Filter

每个条件返回 `MATCH / MISMATCH / UNKNOWN`：

- MATCH 保留；
- 明确 MISMATCH 才过滤；
- UNKNOWN 保留并交给排序降权；
- price 缺失或 `—` 不得等于超预算；
- category 先经过 taxonomy confidence 和单复数/alias 归一化；
- filter 后必须输出 target-independent reason code。

Gate：Candidate Recall@100 到 filter 后的生存率=100%，F1=0；不能通过关闭全部过滤实现。

### Gate 6：冻结候选排序与消歧

排序优先级：

```text
当前轮明确hard
  > 当前轮明确soft
  > active session state
  > 独立字段证据
  > category
  > profile
  > popularity/fallback
```

规则：

- 同一 term 在相关 route 中重复出现只算一次或衰减累计。
- K1-near 和 K1-deep 分开实验；near 用轻量重排，deep 先清理噪声。
- normalized-title duplicate 作为 variant family；不能把多个真实 ASIN 粗暴合并成一个，也不能让一个 family 占满 Top10。
- 同 intent signature 商品使用 brand、具体feature、rating/popularity的校准 tie-break，并明确标注这是弱证据。
- Browsing 使用轻量多样性约束，避免同品牌/同标题变体占满 Top10。

Gate：冻结候选 Development Hit@10 ≥99%，MRR ≥0.60；25个同签名目标必须单独报告，不能隐藏在整体指标中。

### Gate 7：分层回归与一次 Holdout

按 scenario、leaf支持度、constraint主类型、价格缺失和duplicate family 报告：

- Hit@10、MRR、MTTC；
- candidate Recall@100；
- filter survival；
- R1/R3/F1/K1；
- gained/lost/shared rank churn；
- mean/P95/max latency；
- 问题的边际候选缩减和边际命中。

Development 达到 149/150 且所有机制 Gate 通过后，只打开一次 holdout。Full 99% 的最终条件是 198/200，同时 holdout 至少 49/50；任何未过 Oracle Gate 的样本必须单独披露。

## 5. 四位成员工作分配

## 1号：数据质量、Taxonomy 与 Intent Signature

### 任务

1. 生成50,000商品质量画像和A/B/C分层。
2. 规范category、material、color、feature、size、style、brand/store和price。
3. 识别taxonomy污染：style/系列词伪装成leaf category、过宽父类、单复数和alias断裂。
4. 为全 catalog 生成结构化 intent signature，不使用 public ground truth 建规则。
5. 计算每个属性在每个leaf category内的覆盖率、熵和候选缩减能力，提供给2号。
6. 标记normalized-title duplicate family和同intent-signature family，提供给4号。

### 交付物

- `catalog_quality_profile.json`
- `catalog_field_coverage.md`
- `taxonomy_aliases.json`
- `attribute_information_value.json`
- `catalog_intent_signatures.jsonl`
- `duplicate_and_ambiguity_groups.json`
- 构建脚本、单元测试和数据SHA

### 验收

- 索引ASIN保持50,000；无静默丢失。
- 所有规范化值可追溯到原字段和confidence。
- Oracle报告覆盖全部200目标，并明确25个同签名目标。
- 不包含public ID/ASIN特判规则。

### 交接

- 给2号：category→高信息价值问题优先级。
- 给3号：结构化字段、taxonomy confidence、质量层。
- 给4号：duplicate/ambiguity family和字段置信度。

## 2号：State、Intent、Clarification 与可识别性补全

### 任务

1. 修复通用重试导致的intent漂移。
2. 实现override原子状态更新和neutral单属性屏蔽。
3. 使用1号的属性信息价值选择material/feature/color问题，降低无效use_case询问。
4. 保存已问、已neutral、已展示、已拒绝和候选变化状态。
5. 当候选同签名组超过10时，优先询问真正能够分裂该组的属性；若无可回答信号，输出不可识别reason。
6. 实现候选不变、无新增信息和最大三问的停止/策略切换。

### 交付物

- State transition spec
- `intent_before/after`、active/invalidated/neutral debug trace
- Information-gain question policy
- Stop/fallback policy
- Override、Boundary、重复重试回归测试

### 验收

- 旧override值的query/filter/evidence贡献为0。
- Neutral属性不再重复询问。
- 具体约束回答率≥50%。
- 有效约束披露覆盖≥95%。
- turn6–10零收益调用<50。

### 交接

- 给3号：active约束、intent mode和检索计划。
- 给4号：current-turn/recency/neutral/invalidated标记。

## 3号：全 Catalog 召回、公平融合与安全过滤

### 任务

1. 接入结构化field index和BM25/lexical index。
2. 为每种scenario制定route配额，但保证各启用route Top3进入融合。
3. 删除顺序收满Top100提前返回机制，采用全route聚合或round-robin。
4. 实现Candidate@500→@100两级漏斗和逐route trace。
5. 实现MATCH/MISMATCH/UNKNOWN三值filter以及filter reason。
6. 对price missing、非标准价格、taxonomy低置信度保持保守。
7. 做route缓存、并行和性能profiling，防止以无界扩容换覆盖。

### 交付物

- Structured + lexical hybrid retriever
- Fair fusion / route quota实现
- Candidate funnel trace
- Tri-state hard filter
- Route order invariance tests
- Recall@100/500与latency报告

### 验收

- Candidate Recall@500=100%。
- Candidate Recall@100≥99.5%，四场景均≥99%。
- R3=0、F1=0、route rank1丢失=0。
- Route顺序不影响候选集合。
- 平均延迟≤100ms、P95≤250ms；若为99%牺牲性能，必须量化披露。

### 交接

- 给4号：冻结的development候选、全部route evidence、filter reason和quality tier。

## 4号：排序、Duplicate消歧、多样性与指标转化

### 任务

1. 在3号冻结候选后做排序，禁止同时改召回。
2. 当前hard/soft/state证据优先，profile和popular只能弱加权。
3. 对同族route和重复matched term去重或衰减。
4. 为normalized-title duplicate和同intent-signature family设计variant-aware排序。
5. K1-near与K1-deep分别调试并输出完整score breakdown。
6. Browsing加入轻量MMR/brand/leaf多样性，不让单family占满Top10。
7. 对25个可识别性模糊目标单独报告rank，不得用整体均值掩盖。

### 交付物

- Frozen-candidate ranking配置
- Score breakdown和route-family校准
- Duplicate/ambiguity ranking策略
- K1-near/deep转化报告
- 四场景Hit/MRR/churn报告

### 验收

- Oracle候选上的Development Hit@10≥99%。
- 正式候选上的Development至少149/150后才申请holdout。
- MRR≥0.60，shared Top3不发生大规模回归。
- 同一variant family不能占据超过约定Top10配额。
- 25个同签名目标有独立结果和失败原因。

## 6. 团队依赖与合并顺序

```text
1号数据规范与signature
   ├─→ 2号问题信息价值与消歧属性
   ├─→ 3号结构化索引与filter confidence
   └─→ 4号duplicate/ambiguity family

2号active state/query plan ─→ 3号召回 ─→ 4号冻结候选排序

主分支合并顺序：Data → State → Retrieval/Filter → Ranking
```

禁止四个人同时在同一版本修改召回、状态和排序。每次交接必须包括commit、唯一主要改动、配置、测试、development指标、候选漏斗、失败归因和已知风险。

## 7. 里程碑

| 里程碑 | 目标 | 必须通过的Gate |
|---|---|---|
| M0 | 复现V2.1 | 结果hash、97个miss归因一致 |
| M1 | Hit@10 ≥0.70 | R3/F1基本消除，Recall@100≥90% |
| M2 | Hit@10 ≥0.85 | 结构化召回、状态和高信息追问接入 |
| M3 | Hit@10 ≥0.95 | Candidate Recall@100≥99%，排序与duplicate消歧稳定 |
| M4 | Development 149/150 | Oracle≥99%，所有分层回归通过 |
| M5 | Full 198/200 | 一次holdout至少49/50，无public硬编码 |

若M4前Oracle低于99%，停止继续调生产权重，回到可识别性设计；若Oracle通过但正式系统未通过，按候选漏斗定位State、Recall、Filter或Ranking的第一个损失层。

## 8. 每日主控看板

团队负责人每天只看以下指标，禁止只报Overall Hit：

1. 50,000 ASIN索引完整率。
2. Full-information Oracle Hit@10。
3. Candidate Recall@500 / @100。
4. Filter survival和F1数量。
5. R1/R3/K1-near/K1-deep数量。
6. 四场景Hit@10/MRR/MTTC。
7. Leaf支持度分层Hit@10。
8. Material/feature/color约束披露率和问题边际收益。
9. Duplicate/同签名family Hit@10。
10. gained/lost/shared rank churn。
11. mean/P95/max latency。
12. 是否查看过holdout及查看次数。

## 9. 最终验收与证据边界

99%通过条件：

- Full public 至少198/200；
- Development至少149/150，holdout至少49/50；
- Candidate Recall@100≥99.5%，R3=0、F1=0；
- 四场景均有结果，不能用Buying提升掩盖Intent/Boundary失败；
- Oracle、duplicate family和同签名目标结果公开；
- 无public ID、ASIN、标题或目标文本特判；
- 所有规则来源为catalog、通用语义或development聚合；
- holdout仅在预注册Gate后打开一次；
- 延迟、token、成本、fallback和失败边界全部披露。

如果完整可观察信息仍无法唯一识别超过2个目标，99% exact-ASIN不是单纯工程实现问题。此时应向评审明确说明信息不足，并提出增加可回答属性或采用相关商品集合标签的指标方案，而不是伪造99%。
