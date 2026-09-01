# V2.1 未命中归因报告

## 1. 结论

V2.1 正式结果有 97 个 miss。本报告用 `origin/dev@0eb12aa` 重放全部 miss 的有效轮次，并在生产过滤、融合和排序逻辑不变的前提下，额外保留每条 route 在统一 Top 100 截断前的目标位置。

| 主因 | 数量 | 占 97 miss | 判定 |
|---|---:|---:|---|
| R1 纯召回缺失 | 20 | 20.62% | 所有可计分轮次、所有启用 route 均无目标 |
| R3 前融合截断 | 28 | 28.87% | route 内有目标，但顺序合并 Top 100 后消失 |
| F1 Hard filter 误删 | 1 | 1.03% | 合并候选有目标，hard filter 后消失 |
| K1-near 排名 11–20 | 21 | 21.65% | filter 后存在，最佳完整排名为 11–20 |
| K1-deep 排名 21–100 | 27 | 27.84% | filter 后存在，最佳完整排名为 21–100 |
| 合计 | 97 | 100% | 每个 session 只计一个主因 |

原先的“候选缺失 49”现已拆成 R1 20、R3 28、F1 1；“候选内未进 Top 10 48”拆成 K1-near 21、K1-deep 27。因此当前最大的单一机制桶是 R3，不应再把全部候选缺失统称为纯召回失败。

28 个 R3 中有 13 个目标在至少一条 route 排名前 5，4 个达到 route rank 1；19 个 session 的最佳证据来自路由顺序第 5 位或更后。它们说明顺序截断既会丢后置 route，也会丢很强的 route 内候选。

## 2. 分场景归因

| 场景 | Miss | R1 | R3 | F1 | K1-near | K1-deep |
|---|---:|---:|---:|---:|---:|---:|
| Buying | 31 | 6 | 11 | 1 | 6 | 7 |
| Browsing | 43 | 6 | 12 | 0 | 10 | 15 |
| Intent Override | 18 | 7 | 3 | 0 | 4 | 4 |
| Boundary | 5 | 1 | 2 | 0 | 1 | 1 |
| Overall | 97 | 20 | 28 | 1 | 21 | 27 |

- Buying 的 18 个“候选缺失”中，11 个其实已被 route 找回但在融合前丢失，只有 6 个是纯召回缺失，另有 1 个 filter 误删。
- Browsing 的主桶为排序 25 个，其次是 R3 12 个；继续加 route 而不控制融合与高位质量会增加延迟和竞争噪声。
- Intent Override 的首要问题是 R1 7 个，说明 override 生效后的当前值仍不能稳定生成有效候选；另有 3 个 R3。
- Boundary 的 5 个 miss 中 2 个 R3、1 个 R1、2 个 K1，已能完整解释，不存在 O1 待定桶。

## 3. 判定顺序与证据边界

归因只检查 evaluator 允许计分的轮次。Intent Override 生效前即使出现目标，也不作为成功或 post-override 候选证据。每个 session 按以下顺序取一个主因：

1. 目标进入 filter 后集合：K1，按最佳完整 rank 再分 near/deep。
2. 未进入 filter 后集合，但曾在合并 Top 100 内且被 filter 移除：F1。
3. 未进入合并集合，但至少一条未截断 route 含目标：R3。
4. 所有未截断 route 均无目标：R1。

这里的 K1 表示目标没有进入官方 Top 10，不等于当前 Top 10 一定不相关；仓库没有逐商品人工相关性标签。R3 证明目标被工程性截断，也不证明目标必然应排进 Top 10。案例仅用于错误分析和通用回归，禁止转成 public ID、目标 ASIN 或商品文本特判。

## 4. 对话次因

对话问题不覆盖上述主因，而是解释为什么系统没有在后续轮次自我恢复。

| 次因观察 | Session 数 | 轮次/说明 |
|---|---:|---|
| 出现固定通用重试 | 97 | 共 636 轮，所有 miss 均发生 |
| 出现“无额外偏好” | 81 | 共 165 轮 |
| 从未得到具体约束回答 | 50 | clarification 没有为目标增加新证据 |
| 从未追问 | 12 | 直接进入重复推荐/重试循环 |
| Boundary neutral 回复 | 4 | neutral 处理已触发，但仍未命中 |

固定重试让 turn 6–10 不再产生新命中，因此 Q1/停止策略是横跨所有 97 个 miss 的次因；它不是 R1/R3/F1/K1 的替代归因。

## 5. 代表性证据

- `public_0104`（Boundary，R3）：turn 3 的 `current_message` rank 1、`field_attribute` rank 2、`relaxed` rank 2 和 fallback rank 1 均有目标，但前序 route 已填满 100 个唯一 ASIN，目标未进入融合。
- `public_0200`（Buying，R3）：目标在 turn 3 的 `current_message` rank 1，仍被前融合截断；说明 R3 不只发生在 Boundary。
- `public_0156`（Buying，F1）：turn 1 目标在 `current_message`、`field_attribute`、`relaxed`、fallback 均为 rank 1，却被 `category=bag` 过滤。商品类别文本使用复数 `Bags`，当前 exact-token 判断没有处理单复数，是可复现的 category filter 误删。
- `public_0098`（Browsing，K1-near）：目标已进入 filter 后候选，最佳完整 rank 11，只差一个名次；适合冻结候选后的重排实验。
- `public_0040`（Browsing，K1-deep）：目标最佳完整 rank 100，不能和 rank 11 案例使用同一种“轻微调权”假设。
- `public_0003`（Intent Override，R1）：override 后 8 个有效轮次的所有启用 route 均无目标，且后续 7 轮为固定重试。

## 6. 负责人、修改方向与验收

| 桶 | 主责 | 修改方向 | 验收标准 |
|---|---|---|---|
| R1 | 3号，1号支持 | 补 leaf category/attribute 查询覆盖；用 catalog 统计完善 alias，不读 public 目标造规则 | development 的逐 route recall 上升；20 个 R1 下降且无类别泛化回归 |
| R3 | 3号 | 顺序 Top 100 改为 route quota、round-robin，或全 route 聚合后统一裁剪 | 后置 route 的 rank 1 不因 route 顺序丢失；28 个 R3 显著下降；P95 延迟有记录 |
| F1 | 3号，1号支持 | category filter 统一单复数/规范化；保留 filter reason | `bag`/`bags` 等 catalog 驱动形态测试通过；`public_0156`仅作通用回归样例 |
| K1-near | 4号 | 冻结候选，对 rank 11–20 做 evidence/显式需求单变量重排 | near 桶转化提高，shared MRR 和 holdout MRR 不降 |
| K1-deep | 4号，3号支持 | 审计竞争商品 score breakdown、route 重复证据和候选噪声 | 不用大幅 boost 硬推目标；deep 改善同时保护 Top 3 |
| 对话次因 | 2号 | 连续无新增信息/候选不变时停止或改变策略，输出 decision reason | turn 6–10 零收益调用显著下降；具体回答率和每问边际命中可追踪 |
| 全部 | 5号 | 保持主因互斥，报告 dev/holdout、场景、churn、延迟 | 先 development，过 gate 后只开一次 holdout；不得按 public ID 调参 |

## 7. 全量 session 归因

### R1：所有 route 均未召回（20）

- Buying：`public_0018`、`public_0027`、`public_0124`、`public_0149`、`public_0171`、`public_0193`
- Browsing：`public_0012`、`public_0048`、`public_0092`、`public_0099`、`public_0137`、`public_0195`
- Intent Override：`public_0003`、`public_0064`、`public_0071`、`public_0103`、`public_0144`、`public_0177`、`public_0198`
- Boundary：`public_0187`

### R3：route 命中但融合前截断（28）

“首次证据轮”是第一个出现 route 目标的有效轮次；“最佳 route@rank”取该 session 所有有效轮次中的最佳 route rank。

| Session | 场景 | 首次证据轮 | 最佳 route@rank | 有证据轮数 |
|---|---|---:|---|---:|
| `public_0013` | Intent | 4 | category_requirement@25 | 1 |
| `public_0030` | Buying | 1 | field_category@6 | 9 |
| `public_0031` | Buying | 1 | category_requirement@4 | 1 |
| `public_0039` | Browsing | 1 | same_category_popular@20 | 2 |
| `public_0043` | Browsing | 1 | same_category_popular@2 | 2 |
| `public_0047` | Browsing | 1 | same_category_popular@26 | 1 |
| `public_0049` | Browsing | 1 | title@2 | 1 |
| `public_0063` | Browsing | 3 | current_message@1 | 2 |
| `public_0066` | Buying | 1 | category_requirement@22 | 1 |
| `public_0072` | Intent | 3 | current_message@34 | 1 |
| `public_0076` | Browsing | 4 | current_message@17 | 1 |
| `public_0095` | Buying | 1 | category_requirement@6 | 1 |
| `public_0097` | Buying | 1 | category_requirement@5 | 1 |
| `public_0104` | Boundary | 3 | current_message@1 | 1 |
| `public_0105` | Browsing | 1 | same_category_popular@6 | 1 |
| `public_0109` | Buying | 1 | category_requirement@22 | 1 |
| `public_0122` | Browsing | 1 | same_category_popular@4 | 2 |
| `public_0134` | Browsing | 1 | field_attribute@2 | 1 |
| `public_0141` | Browsing | 1 | current_message@9 | 1 |
| `public_0150` | Browsing | 1 | current_message@3 | 1 |
| `public_0159` | Buying | 1 | field_category@8 | 1 |
| `public_0161` | Buying | 1 | category_requirement@12 | 2 |
| `public_0162` | Browsing | 1 | same_category_popular@18 | 1 |
| `public_0169` | Boundary | 4 | current_message@1 | 1 |
| `public_0174` | Buying | 1 | category@4 | 1 |
| `public_0178` | Buying | 4 | current_state@14 | 7 |
| `public_0186` | Intent | 3 | category@5 | 1 |
| `public_0200` | Buying | 3 | current_message@1 | 1 |

### F1：Hard filter 误删（1）

| Session | 场景 | 证据 |
|---|---|---|
| `public_0156` | Buying | turn 1 合并前后均有目标，`category=bag` hard filter 后消失；目标商品类别含 `Gym Bags` / `Drawstring Bags` |

### K1-near：最佳完整 rank 11–20（21）

| Session | 场景 | 最佳 rank@turn | filter 后出现轮数 |
|---|---|---:|---:|
| `public_0006` | Browsing | 13@2 | 10 |
| `public_0007` | Browsing | 18@3 | 10 |
| `public_0016` | Browsing | 20@3 | 2 |
| `public_0021` | Browsing | 17@1 | 7 |
| `public_0023` | Intent | 17@4 | 7 |
| `public_0026` | Buying | 17@3 | 9 |
| `public_0038` | Intent | 15@4 | 1 |
| `public_0052` | Intent | 15@5 | 7 |
| `public_0054` | Buying | 14@1 | 1 |
| `public_0058` | Buying | 18@1 | 2 |
| `public_0073` | Browsing | 16@2 | 10 |
| `public_0086` | Browsing | 13@1 | 1 |
| `public_0098` | Browsing | 11@1 | 1 |
| `public_0107` | Buying | 15@1 | 8 |
| `public_0123` | Intent | 18@5 | 8 |
| `public_0132` | Buying | 13@2 | 8 |
| `public_0138` | Browsing | 13@4 | 9 |
| `public_0158` | Browsing | 14@1 | 1 |
| `public_0172` | Browsing | 15@4 | 2 |
| `public_0179` | Buying | 13@2 | 10 |
| `public_0180` | Boundary | 19@3 | 2 |

K1-near 的最佳 rank 均值 15.43、中位数 15、范围 11–20。

### K1-deep：最佳完整 rank 21–100（27）

| Session | 场景 | 最佳 rank@turn | filter 后出现轮数 |
|---|---|---:|---:|
| `public_0008` | Buying | 22@2 | 9 |
| `public_0032` | Buying | 51@2 | 9 |
| `public_0034` | Intent | 39@4 | 1 |
| `public_0040` | Browsing | 100@1 | 1 |
| `public_0051` | Browsing | 57@2 | 10 |
| `public_0060` | Browsing | 34@1 | 1 |
| `public_0068` | Intent | 22@4 | 7 |
| `public_0074` | Browsing | 88@2 | 9 |
| `public_0075` | Browsing | 28@4 | 8 |
| `public_0081` | Browsing | 23@1 | 2 |
| `public_0083` | Buying | 86@4 | 1 |
| `public_0087` | Browsing | 56@3 | 9 |
| `public_0091` | Browsing | 87@1 | 1 |
| `public_0093` | Buying | 46@2 | 8 |
| `public_0096` | Intent | 22@5 | 6 |
| `public_0100` | Browsing | 31@1 | 9 |
| `public_0106` | Buying | 50@1 | 3 |
| `public_0112` | Boundary | 47@1 | 10 |
| `public_0121` | Browsing | 23@3 | 9 |
| `public_0127` | Browsing | 82@1 | 1 |
| `public_0133` | Buying | 32@4 | 2 |
| `public_0143` | Buying | 21@2 | 9 |
| `public_0151` | Browsing | 85@1 | 1 |
| `public_0170` | Browsing | 27@1 | 1 |
| `public_0175` | Browsing | 59@1 | 7 |
| `public_0181` | Browsing | 27@4 | 2 |
| `public_0183` | Intent | 21@4 | 1 |

K1-deep 的最佳 rank 均值 46.89、中位数 39、范围 21–100。
