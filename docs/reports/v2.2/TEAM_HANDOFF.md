# V2.2 组内交接说明

## 一页结论

| 项目 | 内容 |
|---|---|
| 唯一主要变量 | 用 `data/public_set1.jsonl` 的 3,021 条商品重建 lexicon/playbook |
| 正式检索与评分 | 50k `data/catalog.jsonl` + 200 会话 `data/public_set.jsonl` |
| 正式结果 | Hit 0.535000 / MRR 0.251399 / MTTC 6.305000 / Technical 0.436820 |
| 相对 V2.1 | +4 net hits；Technical +0.014290；holdout MRR +0.030834 |
| Gate | 保留实验候选；暂不替换 V2 final baseline |

## 文件位置

| 文件 | 用途 |
|---|---|
| `results/v2.2-public-set1-knowledge.json` | 正式指标与逐 session 结果 |
| `docs/reports/v2.2/README.md` | 总览、gate、数据口径与复现 |
| `docs/reports/v2.2/version_comparison.md` | V0–V2.2 横向比较 |
| `docs/reports/v2.2/turn_casebook.md` | 逐轮、追问与性能 |
| `docs/reports/v2.2/miss_attribution.md` | 93 miss 与 18 个 churn 案例 |
| `docs/reports/v2.2/{buying,browsing,intent_override,boundary}.md` | 四场景报告 |
| `docs/reports/v2.2/team/` | 1–4号后续任务 |
| `artifacts/lexicon.json` | public_set1 驱动的机器可读知识资产 |
| `artifacts/category_playbook.md` | public_set1 驱动的问题 playbook |

## 复现

```bash
python3 -m artifacts.build_lexicon \
  --catalog data/public_set1.jsonl \
  --output artifacts/lexicon.json \
  --playbook-output artifacts/category_playbook.md
python3 -m unittest discover -s tests -v
env -u RANKING_CONFIG_NAME python3 -m evaluator.local_evaluator \
  --catalog data/catalog.jsonl \
  --dataset data/public_set.jsonl \
  --output results/v2.2-public-set1-knowledge.json
```

## 风险与下一步

1. `public_set1` 与 public target 的 ASIN 交集为 0，避免了直接目标泄漏；但仍需团队确认它的来源、许可和最终提交可用性。
2. 先在 development 审计 Buying lost、Intent rank 回落和 Browsing holdout 替换，不再次查看 holdout 调参。
3. 补生产候选漏斗后再做 R1/R3/F1/K1 归因。
4. V2.2 holdout Technical `0.444233` 仍低于 V2 的 `0.452600`，final gate 未过。
