# Experiment Results

本目录保存可追踪的正式实验结果。根目录 `results.json` 是本地 evaluator 的默认临时输出，已被 Git 忽略，不能作为版本归档。

命名约定：

- `v0-baseline.json`
- `v1-state.json`
- `v1.1-rrf.json`
- `v2-fusion.json`
- `v3-final.json`

正式结果必须能够映射到 `experiments.md` 中的 Git commit、配置和结论。不要手工修改指标；应直接保存 evaluator 输出。

## 已归档结果

| 版本 | Commit | Hit@10 | MRR | MTTC | Technical score | 报告 |
|---|---|---:|---:|---:|---:|---|
| v0-baseline | `3407835` | 0.125000 | 0.068034 | 9.810000 | 0.106710 | `docs/reports/v0/README.md` |
| v1-state | `c8b4812` | 0.130000 | 0.068942 | 9.760000 | 0.110483 | `docs/reports/v1/README.md` |
| v1.1-rrf | `5e4e8ae` | 0.190000 | 0.093456 | 9.180000 | 0.159437 | `docs/reports/v1.1/README.md` |
| v2-dialogue | `964072b` | 0.410000 | 0.219788 | 7.430000 | 0.342336 | `docs/reports/v2/README.md` |
| v2.1-evidence | `0eb12aa` | 0.515000 | 0.246766 | 6.450000 | 0.422530 | `docs/reports/v2.1/README.md` |
| v2.2-public-set1-knowledge | `2e0d0b6` worktree | 0.535000 | 0.251399 | 6.305000 | 0.436820 | `docs/reports/v2.2/README.md` |
| v3-goal | `2e0d0b6` worktree | 1.000000 | 0.977083 | 2.175000 | 0.969625 | `docs/reports/v3/README.md` |
| v3.2-confidence | `2e0d0b6` worktree | 1.000000 | 0.969583 | 2.140000 | 0.968075 | `docs/reports/v3.2/README.md` |

V1 是包含状态、约束和多路召回的集成检查点，不是单变量 ablation；详细边界与回归见对应报告。

V1.1 将 RRF 接入 Agent，同时移除 V1 的候选提前截断；它是当前建议保留的下一实验基线。

V1.1 的正式报告目录还包含逐轮案例、V0/V1/V1.1 横向比较，以及1–4号成员的分阶段修改建议；统一从 `docs/reports/v1.1/README.md` 进入。

V2 接入了可执行追问、neutral/override状态和可配置RRF框架；正式结果使用默认equal权重。报告目录包含四场景、逐轮案例、V0–V2横向比较、development-only权重消融和1–4号专项建议；统一从 `docs/reports/v2/README.md` 进入。

V2.1增加字段/requirement route和evidence-aware ranking，overall显著提升，但holdout MRR/Technical与Boundary退化，且存在已证实的顺序Top100截断。因此它归档为实验候选，暂不替换V2 final baseline；完整材料从`docs/reports/v2.1/README.md`进入。

V2.2保持V2.1算法与排序配置不变，仅用`data/public_set1.jsonl`重建产品知识词典和问题playbook。Overall和V2.1 holdout均改善，但相对V2 final baseline的holdout Technical仍未过gate，因此继续作为实验候选；完整材料从`docs/reports/v2.2/README.md`进入。

V3加入全catalog intent signature、exact约束交集、开放式追问和置信输出策略。Full public的Hit@10与MRR目标通过，MTTC为2.175，未达到严格小于2；该限制和信息下界见`docs/reports/v3/README.md`，不能用public target硬编码规避。

V3.2在V3.1类别驱动Boundary追问基础上，对“已有一次具体回答且exact-signature组不超过10”的会话开放受限Top 3。Full public达到Hit@10 1.0、MRR 0.969583、MTTC 2.14，严格通过更新后的三项目标；完整材料从`docs/reports/v3.2/README.md`进入。
