# V2.2 Public-set1 Knowledge 四场景分析总览

## 1. 版本范围

V2.2 以工作树基线 commit `2e0d0b6` 为代码基础，保持 V2.1 的检索、状态、对话和 `mild_evidence_light` 排序配置不变。唯一主要变量是用 `data/public_set1.jsonl` 的 3,021 条商品记录重建 `artifacts/lexicon.json` 和 `artifacts/category_playbook.md`。

`public_set1.jsonl` 是商品语料，不是评分会话：它有 3,021 个唯一 ASIN，全部属于完整 50,000 商品目录，与 200 个 public ground-truth ASIN 的交集为 0。因此本实验只把它用于产品知识构建；正式评分仍使用 `data/public_set.jsonl`，正式检索库仍使用 `data/catalog.jsonl`。没有伪造 scenario、profile 或 ground truth。

## 2. 数据与复现

- 正式结果：`results/v2.2-public-set1-knowledge.json`
- 对比基线：`results/v2.1-evidence.json`
- 固定切分：`docs/internal_split.json`（development 150 / internal holdout 50）
- 知识构建：`python3 -m artifacts.build_lexicon --catalog data/public_set1.jsonl --output artifacts/lexicon.json --playbook-output artifacts/category_playbook.md`
- 测试：`python3 -m unittest discover -s tests -v`，132/132 通过
- 正式评测：`env -u RANKING_CONFIG_NAME python3 -m evaluator.local_evaluator --catalog data/catalog.jsonl --dataset data/public_set.jsonl --output results/v2.2-public-set1-knowledge.json`
- 全量 trace：`env -u RANKING_CONFIG_NAME python3 -m evaluator.debug_trace --catalog data/catalog.jsonl --dataset data/public_set.jsonl --all --output /tmp/v2.2_all_traces.json`
- 首轮运行：102.10 秒；确定性复跑指标与逐 session 完全一致
- 两份结果 SHA-256：`adb8b29ca3e9dd6e1345ad1eab0bc3107ecad7c4c7725e5f8b9c05c769bb03c3`
- 模型、API、网络和 token 成本：均为 0

## 3. 总体结果

| 数据范围 | 样本数 | V2.2 Hit@10 | Δ vs V2.1 | V2.2 MRR | Δ vs V2.1 | V2.2 MTTC | Δ vs V2.1 | Technical Δ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Full public | 200 | 0.535000 | +0.020000 | 0.251399 | +0.004633 | 6.305000 | -0.145000 | +0.014290 |
| Development | 150 | 0.540000 | +0.026667 | 0.234939 | -0.004101 | 6.306667 | -0.193333 | +0.015969 |
| Internal holdout | 50 | 0.520000 | 0 | 0.300778 | +0.030834 | 6.300000 | 0 | +0.009250 |

| 场景 | Hits / Misses | Hit@10 | Δ | MRR | Δ | MTTC | Δ | 报告 |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Buying | 48 / 32 | 0.600000 | -0.012500 | 0.277693 | -0.000397 | 5.487500 | +0.075000 | [查看](buying.md) |
| Browsing | 41 / 39 | 0.512500 | +0.050000 | 0.213185 | +0.017709 | 6.512500 | -0.350000 | [查看](browsing.md) |
| Intent Override | 13 / 17 | 0.433333 | +0.033333 | 0.245556 | -0.015277 | 7.933333 | -0.233334 | [查看](intent_override.md) |
| Boundary | 5 / 5 | 0.500000 | 0 | 0.364286 | 0 | 6.300000 | 0 | [查看](boundary.md) |

V2.2 共命中 107 条。相对 V2.1 新增 11 条、丢失 7 条、共有 96 条，净增 4 条；shared hit 中 3 个 rank 提升、89 个不变、4 个下降。Technical Score 从 `0.422530` 提高到 `0.436820`。

## 4. Development / Holdout Gate

Development 新增 8、丢失 4，净增 4；Hit 和 MTTC 改善，但 MRR 下降 `0.004101`。Holdout 新增 3、丢失 3，Hit/MTTC 不变，MRR 提高 `0.030834`，Technical 提高 `0.009250`；23 个 shared hit 中 1 个 rank 提升、22 个不变、0 个下降。

相对 V2.1，V2.2 修复了 holdout MRR/Technical 的方向性回归。但现有 final baseline V2 的 holdout Technical 为 `0.452600`，V2.2 仍低 `0.008367`；同时 development MRR、Buying overall、Browsing holdout Hit 和 Intent overall MRR 各有局部退化。因此 V2.2 可保留为更强的实验候选，尚不足以替换 V2 final baseline。

## 5. 描述性统计与加权口径

以下均为 population variance；miss 的完成轮次按 11 计。

| 范围 | Hit 方差 | RR 方差 | 完成轮次方差 | 完成轮次极值 | 命中 rank 均值 | rank 方差 | rank 极值 |
|---|---:|---:|---:|---|---:|---:|---|
| Overall | 0.248775 | 0.126074 | 19.961975 | 1–11 | 4.065421 | 8.304131 | 1–10 |
| Buying | 0.240000 | 0.135157 | 20.924844 | 1–11 | 4.229167 | 8.718316 | 1–10 |
| Browsing | 0.249844 | 0.100695 | 19.849844 | 1–11 | 4.341463 | 8.029744 | 1–10 |
| Intent Override | 0.245556 | 0.136753 | 12.328889 | 3–11 | 3.230769 | 6.639053 | 1–8 |
| Boundary | 0.250000 | 0.194337 | 22.410000 | 1–11 | 2.400000 | 5.440000 | 1–7 |

四场景等权 macro 为 Hit `0.511458`、MRR `0.275180`、MTTC `6.558333`、Technical-like `0.427116`。正式 Technical 的 Hit、MRR、Efficiency 分量分别为 `0.267500`、`0.075420`、`0.093900`，合计 `0.436820`。

## 6. 逐轮与运行性能

| Turn | 活跃会话 | 首次命中 | 累计命中 |
|---:|---:|---:|---:|
| 1 | 200 | 45 | 45 |
| 2 | 155 | 17 | 62 |
| 3 | 138 | 23 | 85 |
| 4 | 115 | 20 | 105 |
| 5 | 95 | 2 | 107 |
| 6–10 | 每轮 93 | 0 | 107 |

- 全量 trace 共 1,168 次调用，全部响应合法、无异常。
- `ask_attribute` 共 409 次；具体约束回答 67 次、无额外偏好 246 次、Boundary no-preference 6 次。
- turn 6–10 仍有 465 次零收益调用；相邻 Top 10 完全重复 518 次。
- 单轮平均 61.431 ms、P95 160.916 ms、最大 1095.221 ms；与 V2.1 的 60.844 / 166.539 / 1296.558 ms 同一量级。

详细逐轮与案例见[逐轮案例册](turn_casebook.md)。

## 7. 产品知识变化与证据边界

V2.1 词典由完整 50,000 商品生成；V2.2 改为 3,021 条 `public_set1` 商品。六类 vocabulary 的规范值集合没有增删，主要变化来自 top store、top leaf category、category coverage/information value 和 playbook 覆盖。60 个 playbook 类别中有 10 个替换，另外 50 个共有类别的统计值发生变化。

这解释了“多数 shared rank 不变，但部分会话因追问路径变化发生 gained/lost”的现象；它不证明所有净增都由某个单独类别或问题引起。正式 trace 没有生产候选漏斗 hook，本版不把 93 个 miss 强行标成 R1/R3/F1/K1，详见[未命中与 churn 清单](miss_attribution.md)。

## 8. 交付索引与 Gate

- [组内交接说明](TEAM_HANDOFF.md)
- [93 个 miss 与 18 个 churn 案例](miss_attribution.md)
- [逐轮案例册](turn_casebook.md)
- [V0–V2.2 横向对比](version_comparison.md)
- [Buying](buying.md) / [Browsing](browsing.md) / [Intent Override](intent_override.md) / [Boundary](boundary.md)
- [1号专项](team/member_1_data_knowledge.md)
- [2号专项](team/member_2_state_policy.md)
- [3号专项](team/member_3_retrieval_filter.md)
- [4号专项](team/member_4_ranking_weights.md)

Gate 结论：保留 V2.2 为 V2.1 线上的更强实验候选，但暂不替换 V2 final baseline。下一步应在 development 上审计 Buying lost 与 Intent rank 回落，补生产候选漏斗，并验证 `public_set1` 的来源与最终提交可用性；冻结后才能再次打开 holdout。
