# V2 组内交接说明

## 1. 这一步完成了什么

5号已对 `origin/dev@964072b` 的V2默认等权配置完成：84项测试、200条正式评测、确定性复跑、全量逐轮trace、生产候选漏斗审计、固定development/holdout统计、描述性统计、V0–V2横向比较，以及development-only的`mild/stronger`权重消融。

正式V2结果为：Hit@10 `0.410000`、MRR `0.219788`、MTTC `7.430000`、Technical Score `0.342336`。

注意：当前 `feature/evaluation` 代码HEAD仍是`5e4e8ae`；V2代码来自已获取的`origin/dev@964072b`隔离副本。本说明和结果记录该来源，但没有替组员合并V2代码。

## 2. 文件位置与用途

| 文件 | 作用 | 谁使用 |
|---|---|---|
| `results/v2-dialogue.json` | 200条正式结果与session指标 | 全员；5号维护 |
| `docs/reports/v2/README.md` | 总体、分割集、统计、候选漏斗、Gate | 全员先读 |
| `docs/reports/v2/buying.md` | Buying成功/失败与分工 | 1、2、3、4号 |
| `docs/reports/v2/browsing.md` | Browsing追问收益与剩余问题 | 1、2、3、4号 |
| `docs/reports/v2/intent_override.md` | override有效轮、状态和排序问题 | 2、3、4号 |
| `docs/reports/v2/boundary.md` | neutral/no-preference端到端行为 | 2号主责，1/3/4号配合 |
| `docs/reports/v2/turn_casebook.md` | turn 1–10逐轮成功/失败案例 | 全员回归参考 |
| `docs/reports/v2/version_comparison.md` | V0/V1/V1.1/V2横向比较与权重解释 | 全员；4、5号重点 |
| `docs/reports/v2/team/member_1_data_knowledge.md` | 1号专属任务与验收 | 1号 |
| `docs/reports/v2/team/member_2_state_policy.md` | 2号专属任务与验收 | 2号 |
| `docs/reports/v2/team/member_3_retrieval_filter.md` | 3号专属任务与验收 | 3号 |
| `docs/reports/v2/team/member_4_ranking_weights.md` | 4号专属任务与验收 | 4号 |
| `experiments.md` | 正式实验台账 | 5号维护 |
| `docs/failure_cases.md` | 跨版本失败分类与证据口径 | 全员使用，5号维护 |
| `docs/internal_split.json` | 固定development 150 / holdout 50 | 5号执行；任何人不得重抽 |

临时全量trace和候选审计位于`/tmp`，不纳入Git。需要案例复现时应从同一V2 commit重新运行，不依赖临时文件长期存在。

## 3. 每个成员怎么用

### 1号：产品知识与问题playbook

先读自己的专项报告，再读Browsing和Buying。重点解决use_case高频但neutral多、低覆盖类别无问题、category映射不完整。交付词典/问题表时把coverage、information value、构建来源一起交给2号和5号。

### 2号：State、Intent和Clarification

先读Intent、Boundary和逐轮案例。补齐state before/after、neutral、invalidated、decision reason；优化第一问和三问后的停止行为。交给3号的是“当前有效值”，交给4号的是“当前轮/override时效标记”。

### 3号：Retrieval与Filter

先读总览候选漏斗和四场景失败结构。为48个候选缺失补逐route证据，区分R1/R2/F1；把完整route evidence交给4号，禁止融合前提前截断。

### 4号：Fusion与Rerank

先读横向对比和自己的专项报告。当前两组固定权重已在development失败，不要直接打开holdout。下一实验应加入可解释的显式/recency分量，目标是70个候选内miss，同时保护已有高位hit。

### 5号：Evaluation与Gate

维护结果、实验台账、失败分类和固定split。每次只允许一个主要变量；先development，候选过gate才看holdout。必须报告micro/macro、四场景、方差、极值、候选漏斗、逐轮、gained/lost和rank churn。

## 4. 推荐工作顺序

1. 1号完成类别覆盖和问题信息价值表。
2. 2号接入可审计decision/state，并单独评测问题顺序与停止策略。
3. 3号在冻结2号策略后补联合route和filter reason。
4. 4号在冻结候选集后做显式/recency单变量重排。
5. 5号分别gate，禁止把三项合成一个无法归因的版本。

1号的数据统计可与2号debug可观测性并行；3号的trace框架可与4号score breakdown并行，但任何正式指标必须在依赖版本冻结后重跑。

## 5. 每次交接必须包含

- Git commit SHA和分支；
- 唯一主要改动及明确未改内容；
- 配置、参数、依赖和新增测试；
- 预期改善场景、指标与风险；
- 最小复现命令；
- development结果及是否看过holdout；
- gained/lost与至少一个成功、失败案例；
- 是否需要模型、网络、密钥或新增成本。

## 6. V2复现命令

以下命令应在包含`964072b`代码且具有`data/catalog.jsonl`的工作树运行：

```bash
python3 -m unittest discover -s tests -v
env -u RANKING_CONFIG_NAME python3 -m evaluator.local_evaluator \
  --output results/v2-dialogue.json
env -u RANKING_CONFIG_NAME python3 -m evaluator.debug_trace \
  --all --output /tmp/v2_all_traces.json
```

`mild/stronger`只完成了development筛选，均未过gate；不要把它们描述成V2正式结果。
