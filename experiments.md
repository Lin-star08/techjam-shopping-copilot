# TechJam 实验记录

本文档由 5 号维护，是所有功能是否进入最终版本的唯一实验台账。每个主要实验必须绑定 Git commit，并同时记录总体与四类场景指标。

## 实验规则

1. 一次实验只改变一个主要因素；混合改动必须拆开或明确标记为不可归因。
2. 日常调参只看固定 development split；阶段性候选才查看 internal holdout。
3. Public ground truth 仅用于评分和错误分析，不得进入 Agent、检索索引、规则或切分逻辑。
4. 不修改 `evaluator/local_evaluator.py` 或 `data/public_set.jsonl` 来获得报告分数。
5. 每次运行前执行测试，并记录 Git commit、配置、模型/API、token、成本和延迟。
6. 总分之外必须检查 Buying、Browsing、Intent Override、Boundary，显著场景退化必须解释。
7. 不能稳定复现、无法解释或只改善 development 而伤害 holdout 的功能，默认不进入 final。

## 固定数据切分

- 文件：`docs/internal_split.json`
- 方法：按 `scenario_type` 分层，再以固定 seed 对 `sample_id` 做 SHA-256 排序。
- Development：150 条。
- Internal holdout：50 条，包含 Buying 20、Browsing 20、Intent Override 7、Boundary 3。
- 切分不读取目标商品进行选择；中途不得重抽。

## v0-baseline

- 状态：已复现并锁定
- Git commit：`3407835`
- Agent：标准库 SQLite FTS5 BM25，无状态、无 LLM、无网络依赖
- 主要能力：仅根据当前一轮消息检索；无 State、Filter、Profile、Multi-route、Clarification、Rerank
- 运行命令：`python3 -m evaluator.local_evaluator --output results/v0-baseline.json`
- 单元测试：5/5 通过（含固定切分与 Intent Override trace 语义测试）
- Token：prompt 0 / completion 0 / total 0
- 模型/API 成本：0

| 数据范围 | 样本数 | Hit@10 | MRR | MTTC |
|---|---:|---:|---:|---:|
| Overall | 200 | 0.125000 | 0.068034 | 9.810000 |
| Buying | 80 | 0.237500 | 0.126508 | 8.625000 |
| Browsing | 80 | 0.025000 | 0.004514 | 10.750000 |
| Intent Override | 30 | 0.133333 | 0.104167 | 10.066667 |
| Boundary | 10 | 0.000000 | 0.000000 | 11.000000 |

补充观察：共命中 25 条，其中 21 条在第 1 轮命中，4 条在第 4 轮命中。Browsing 仅命中 2/80，Boundary 为 0/10，是后续实验的重点监控场景。

Trace 冒烟验证：`public_0002` 成功重放 10 轮，无 Agent 异常；override 在第 3 轮生效，v0 最终 miss。逐轮 trace 只写入临时目录，不作为正式指标来源。

完整结果：`results/v0-baseline.json`

## 功能交接要求

2、3、4 号交付待评估版本时，必须同时提供：

- Git commit SHA；
- 唯一主要改动；
- 预期改善的场景和指标；
- 新增或变化的参数；
- 已知风险及可能退化的场景；
- 最小复现命令；
- 是否需要模型、网络、密钥或新增依赖。

资料不完整时可以跑冒烟测试，但不得把结果标记为正式 ablation。

## 实验模板

复制本节，为每个版本建立独立条目。

### vX-名称

- 日期/负责人：
- Git commit：
- 对比基线：
- 唯一主要改动：
- 预期改善场景/指标：
- 配置和参数：
- 模型/API/网络依赖：
- 测试结果：
- 运行命令：
- 总运行时间与单轮延迟：
- Prompt / completion tokens：
- 估算成本：

| 数据范围 | 样本数 | Hit@10 | MRR | MTTC | 相对基线变化 |
|---|---:|---:|---:|---:|---|
| Development | 150 |  |  |  |  |
| Internal holdout | 50 |  |  |  |  |
| Buying |  |  |  |  |  |
| Browsing |  |  |  |  |  |
| Intent Override |  |  |  |  |  |
| Boundary |  |  |  |  |  |

- 主要改善案例：
- 主要退化案例：
- Failure taxonomy 变化：
- 可复现性检查：
- 结论：保留 / 回退 / 待验证
- 下一步：

## Final Gate

最终候选必须满足：

- 官方 evaluator 可完整运行；
- 全部测试通过；
- 输出接口合法，商品 ID 有效且唯一；
- development 与 internal holdout 均有记录；
- 四类场景指标齐全；
- Intent Override 和 no-preference 有 trace 证据；
- 模型、成本、token、延迟、限制和 fallback 已披露；
- 仓库不包含 API key、私有数据或无关大文件。
