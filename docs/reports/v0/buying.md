# v0 Buying 场景分析报告

## 1. 场景与指标

Buying 会在首轮透露一个目标商品的硬条件。理想系统应将类别和明确条件作为当前有效需求，先排除明显不符合的商品，再对候选排序。

| 数据范围 | 样本数 | Hits | Misses | Hit@10 | MRR | MTTC |
|---|---:|---:|---:|---:|---:|---:|
| Full public | 80 | 19 | 61 | 0.237500 | 0.126508 | 8.625000 |
| Development | 60 | 11 | 49 | 0.183333 | 0.116548 | 9.166667 |
| Internal holdout | 20 | 8 | 12 | 0.400000 | 0.156389 | 7.000000 |

19 个命中全部发生在第 1 轮。命中排名分布为：rank 1 共 7 条、rank 2 共 3 条、rank 3 共 2 条，其余 7 条分布在 rank 4、7、8、9、10。

## 2. 目标未识别的原因

### Trace 已证实

1. 61 个 miss 的目标商品在全部有效轮次中都没有进入 Agent 返回的 Top 10。
2. Agent 没有提出任何追问。首轮失败后，61 条会话累计产生 549 个通用重试轮次。
3. 通用回复为固定文本，之后的 BM25 查询也固定，因而反复返回相同 Top 10；第 2–10 轮不能补充新条件或恢复首轮类别与硬条件。
4. 全部响应结构合法且无异常，所以主要问题是检索策略质量，不是接口或运行稳定性。
5. 61 个 miss 中，28 个目标缺少 description，但所有目标都有 features。字段稀疏会降低文本覆盖，却不能单独解释全部失败。

### 结合实现的合理推断

1. `starter/agent.py` 将类别和硬条件拆成多个 token，再通过 OR 连接；“满足类别”或“出现常见材质词”都可能获得分数，硬条件没有必须满足的语义。
2. 没有 hard filter，导致与类别相关但不满足明确约束的商品仍可占据 Top 10。
3. 只有单一 BM25 路线，没有 current-message、category、attribute、profile 等互补召回，某一字段词法不匹配时没有补救路线。
4. BM25 直接输出最终 Top 10，没有独立候选融合和重排，无法显式提高同时满足类别与硬条件的商品。

### 当前不能确认

61 个目标可能完全没有被 FTS 找回，也可能位于第 11 名以后。由于 v0 不记录 Top 10 外候选和 pre-rerank rank，不能在现有证据下进一步拆分为 R1 召回缺失或 K1 排序失败。

## 3. 代表性案例

以下案例只用于错误分析，不得写入 Agent 规则。

| Sample | 首轮需求 | 目标 | 观察 |
|---|---|---|---|
| `public_0001` | Jewelry Necklaces；硬条件 `Material:alloy` | Celtic knot pendant necklace | 目标未进 Top 10。宽泛类别和常见 material 词没有形成必须同时满足的约束。 |
| `public_0005` | Snow & Cold Weather；硬条件 `leather` | GLOBALWIN waterproof winter boots | 目标未进 Top 10。单独的 leather 词覆盖面过大，缺少冬季用途与类别联合约束。 |
| `public_0044` | Men Jammers；硬条件 `fabric` | K898 swimming jammer shorts | 第 1 轮 rank 1 命中，说明类别词非常具体时 BM25 可以成功，但不代表硬约束机制有效。 |

## 4. 按团队分工的修改意见

| 成员 | 修改建议 | 预期交付 | 验收标准 |
|---|---|---|---|
| 1号：数据洞察与商品知识 | 统一材质、类别、品牌/store 和常见 details 键值；统计字段覆盖率与歧义词。 | `lexicon.json`、Buying 类别/约束 playbook、字段缺失说明 | 词典可由 Python 加载；每条规则说明数据覆盖率，不能依据 public target 频次硬编码。 |
| 2号：对话状态与策略 | 将首轮明确类别和约束写入 `current_slots`/`hard_constraints`；失败后只询问最有价值的缺失属性。 | Buying 状态样例、hard/soft 判定规则、追问策略 | 明确条件能跨轮保留；同一属性不重复问；模糊解析不进入强过滤。 |
| 3号：检索与约束工程 | 为高置信约束增加边界保护的 hard filter；同时建立 current-message、category、attribute 多路召回。 | filter/retrieval 函数、统一候选结构、fallback | 高置信条件生效；字段缺失或解析不确定时不误删；每条候选可说明 route 和 matched terms。 |
| 4号：融合排序与调参 | 使用 RRF 或归一化融合；显式类别和硬条件权重高于软偏好/profile。 | fusion/rerank 代码、score 分解、单变量权重实验 | 目标已召回时能看到 pre/post rank；硬条件违反项不能仅靠其他词堆分进入前列。 |
| 5号：评估实验与交付 | 分别测试 hard filter、multi-route、rerank，不把三项合成一次实验。 | Buying ablation、代表性 trace、dev/holdout 对比 | Full/dev/holdout 均记录 Hit@10、MRR、MTTC；改善不能依赖 public case 特判，其他场景无明显退化。 |

## 5. 下一版本观察项

- 目标进入统一候选池的比例，而不仅是最终 Hit@10。
- hard filter 前后候选量和目标保留率。
- 首轮 Hit@10、MRR，以及失败后有效追问带来的首次命中轮次。
- Development 与 holdout 的差异；当前 Buying holdout 基线明显高于 development，样本较少，不能只看单次绝对增幅。
