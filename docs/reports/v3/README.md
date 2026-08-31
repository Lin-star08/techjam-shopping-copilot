# V3 目录签名检索与目标 Gate

## 结论

V3 在冻结后的 200 条 public 全量评测上达到：

| 范围 | N | Hit@10 | MRR | MTTC | Technical |
|---|---:|---:|---:|---:|---:|
| Development | 150 | 1.000000 | 0.977222 | 2.166667 | 0.969833 |
| Internal holdout | 50 | 1.000000 | 0.976667 | 2.200000 | 0.969000 |
| Full public | 200 | 1.000000 | 0.977083 | 2.175000 | 0.969625 |

目标 Gate 的最终状态是 **2/3 通过**：`Hit@10 > 0.98` 和 `MRR > 0.95` 通过，`MTTC < 2` 未通过。相对 V2.2，Full Hit 提升 `+0.465000`，MRR 提升 `+0.725684`，MTTC 缩短 `4.130000` 轮。没有修改 evaluator，也没有将 public sample ID 或目标 ASIN 放进线上算法。

## 主要改动

1. **Catalog intent signature**：从所有商品可见的 `features`、`details`、material、color 和 price 构造有序短签名；对用户已经披露的原始约束做 exact intersection，并用 coarse category 消歧。
2. **对话策略**：已知类别后先问开放的 `other`，让模拟用户一次披露最多两个最强约束；修复未知类别、Intent Override 抢占问题以及 Boundary 连续 material 构造信息未取全的问题。
3. **置信输出**：信息不足时只返回一个最高置信商品，避免一个歧义 Top 10 在过早命中时锁死低 MRR；约束充分或 Boundary 已拒绝开放问题后才扩展 Top 10。
4. **排序**：新增 `signature_exact` route；同签名候选使用全目录 `rating_number` 作为 target-independent 的购买先验，再用目录顺序稳定打破并列。
5. **工作流**：新增 `tools/run_goal_workflow.py`，固定 development/holdout/full 切分、严格目标比较、测试 Gate 和 public label literal 审计。Holdout/full 必须显式传入 `--open-holdout`。

`data/public_set1.jsonl` 继续只作为 V2.2 构建的商品知识语料。它包含 3,021 个 catalog 商品，与 200 个 public target 的 ASIN 交集为 0；V3 的 exact signature 索引则从提交时可见的完整 `data/catalog.jsonl` 构建。

## Full 场景结果

| Scenario | N | Hit@10 | MRR | MTTC |
|---|---:|---:|---:|---:|
| Buying | 80 | 1.000000 | 0.984375 | 1.487500 |
| Browsing | 80 | 1.000000 | 0.972917 | 2.175000 |
| Intent Override | 30 | 1.000000 | 0.983333 | 3.700000 |
| Boundary | 10 | 1.000000 | 0.933333 | 3.100000 |

首次命中轮次为：turn 1 `46`、turn 2 `97`、turn 3 `33`、turn 4 `24`，没有 miss。目标最终排位为 rank 1 `192`、rank 2 `5`、rank 3 `2`、rank 4 `1`。

## 为什么 MTTC < 2 没有被诚实地“调出来”

Full 的首次命中轮次总和为 `435`；严格小于 2 要求总和最多为 `399`，还需净节省至少 `36` 轮。

- 30 个 Intent Override 只有 evaluator 在 turn 3/4 应用 override 后才允许计分，当前轮次总和 `111` 已等于协议下界。
- 80 个 Browsing 首轮只有 coarse category，没有目标约束；第一个有效约束最早出现在 turn 2。即使全部在 turn 2 命中，下界也是 `160`。
- Boundary 的第一次有效问题必然收到 no-preference；除一次类别热门猜中外，其余样例最早在 turn 3 获得约束。乐观下界约为 `28`。
- 上述三类的乐观小计已是 `299`。因此 80 个 Buying 的轮次总和必须不超过 `100`；如果剩余未首中样例都在 turn 2 命中，也要求至少 60/80 首轮直接 Top-1。当前是 45/80。

Buying 首轮只有 coarse category 和第一个 hard constraint。同一信号在开发集平均仍对应 67 个 catalog 商品。目录内可解释先验对比中，`rating_number` 已是最强通用排序，Development 首轮 Top-1 为 36/60；加入 average rating、profile rating closeness、preference tag、价格已知、字段完整度或新旧程度，最好仅为 37/60，无法支撑所需的首轮正确率。

扩大早期列表也无法同时满足 MRR。当前 Full 的 reciprocal-rank 总损失约 `4.5834`；`MRR > 0.95` 只允许总损失小于 `10`。把一个原本后续 rank-1 的样例提前放到 rank 2 会增加 `0.5` 损失，因此剩余预算最多只容纳约 10 个这样的提前命中，无法覆盖 36 轮差距。

因此，在当前 Agent 输入和 evaluator 协议下，继续压到 `<2` 需要以下至少一项：首轮增加可辨识信号；允许询问后在同一 turn 内重排；调整 Override 的计分起点；或使用 public target 映射/顺序等泄漏。最后一种会违反项目规则，未采用。

## 可复现命令

```bash
python3 -m unittest discover -s tests -q
python3 -m tools.run_goal_workflow --split development --output results/v3-goal-development.json
python3 -m tools.run_goal_workflow --split holdout --open-holdout --output results/v3-goal-holdout.json --skip-tests
python3 -m tools.run_goal_workflow --split full --open-holdout --output results/v3-goal-full.json --skip-tests
```

数据 SHA、基线 commit、测试数、三组结果和泄漏审计状态见 `results/v3-goal-evidence.json`。完整逐 session 结果保存在对应的 development、holdout 和 full JSON 中。

## 限制

- Signature 路由利用了本地 evaluator 明示的“hidden intent 来自商品 metadata”协议；若私有评测改变约束生成方式，收益会下降。
- 排名采用热门度弱先验，同签名长尾商品仍需更多对话信息。
- 当前实现为标准库本地算法，无外部模型、网络、token 和 API 成本。
