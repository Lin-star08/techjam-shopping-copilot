# V2.1 组内交接说明

## 1. 本轮完成内容

5号已对`origin/dev@0eb12aa`完成132项测试、默认`mild_evidence_light`正式评测、确定性复跑、200条全量trace、生产候选/evidence审计、固定dev/holdout统计、描述性统计、V0–V2.1横向比较及development-only配置消融。

正式结果：Hit@10 `0.515000`、MRR `0.246766`、MTTC `6.450000`、Technical `0.422530`。

注意：当前`feature/evaluation`代码HEAD仍为`5e4e8ae`；本轮评测远端V2.1隔离副本，没有合并代码。由于holdout Technical和Boundary回归，V2.1暂不替换V2 final baseline。

## 2. 文件位置

| 文件 | 用途 | 使用者 |
|---|---|---|
| `results/v2.1-evidence.json` | 200条正式结果 | 全员，5号维护 |
| `docs/reports/v2.1/README.md` | 总览、Gate、候选和消融 | 全员先读 |
| `docs/reports/v2.1/buying.md` | Buying分析 | 1–4号 |
| `docs/reports/v2.1/browsing.md` | Browsing分析 | 1–4号 |
| `docs/reports/v2.1/intent_override.md` | Override分析 | 2–4号 |
| `docs/reports/v2.1/boundary.md` | Boundary回归与截断证据 | 3号主责，全员关注 |
| `docs/reports/v2.1/turn_casebook.md` | turn1–10案例 | 全员回归 |
| `docs/reports/v2.1/miss_attribution.md` | 97个miss的R1/R3/F1/K1逐条归因 | 全员；3、4号重点 |
| `docs/reports/v2.1/V2.1_97_Misses_Scenario_Attribution_Report.docx` | 四场景完整ID、原因分析和97条证据的Word交付版 | 全员，可直接评审/汇报 |
| `docs/reports/v2.1/V3_Multidimensional_Improvement_Roadmap.docx` | V3九个改进维度、量化目标、五人分工和实验Gate | 全员，作为V3开发路线图 |
| `docs/reports/v2.1/V3_99_Hit10_Team_Workflow.md` | Catalog质量/分布规律、99%可行性Gate和四位成员任务 | 全员，作为V3冲刺主控文档 |
| `docs/reports/v2.1/version_comparison.md` | V0–V2.1比较 | 4、5号重点 |
| `docs/reports/v2.1/team/` | 1–4号专项任务 | 对应成员 |
| `experiments.md` | 正式实验台账 | 5号 |
| `docs/failure_cases.md` | 失败分类 | 全员 |
| `docs/internal_split.json` | 固定150/50切分 | 5号；不得重抽 |

## 3. 每位成员怎么用

### 1号

审计evidence term准确率、leaf类别alias和问题信息价值。交付catalog驱动的词表/覆盖统计，不读public目标生成规则。

### 2号

解释通用重试为何改变intent/route，保持session语义连续；补decision/state debug和三问后停止策略。

### 3号

最高优先级修复顺序Top100：采用全量证据聚合后裁剪或route quota/round-robin。恢复Boundary候选覆盖并做route级性能profiling。

### 4号

不要立即把medium开到holdout。先等3号冻结候选，再做light/medium单变量evidence实验和完整score breakdown。

### 5号

维持V2为final baseline、V2.1为实验候选。下一次只有holdout MRR/Technical、Boundary和延迟过gate才允许升级。

## 4. 推荐顺序

1. 3号修候选截断和route profiling。
2. 2号同步补intent/route reason，但不改变排序。
3. 1号审计evidence词质量。
4. 4号在冻结候选上评估medium。
5. 5号先development，候选过gate才打开一次holdout。

## 5. 交接清单

- commit和分支；
- 唯一主要改动；
- 配置、测试、依赖和复现命令；
- dev指标与是否看过holdout；
- 四场景、候选覆盖、gained/lost、rank churn；
- mean/P95/max延迟与route预算；
- 成功/失败案例及public防硬编码声明。

## 6. 复现命令

在包含`0eb12aa`且具有`data/catalog.jsonl`的工作树运行：

```bash
python3 -m unittest discover -s tests -v
env -u RANKING_CONFIG_NAME python3 -m evaluator.local_evaluator \
  --output results/v2.1-evidence.json
env -u RANKING_CONFIG_NAME python3 -m evaluator.debug_trace \
  --all --output /tmp/v2.1_all_traces.json
```

正式配置是未设置环境变量时的`mild_evidence_light`；其他配置只在development评估。
