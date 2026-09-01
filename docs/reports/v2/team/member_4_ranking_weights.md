# 4号成员：V2 融合、重排与权重实验建议

## 1. 你先看哪些文件

1. `docs/reports/v2/version_comparison.md`
2. `docs/reports/v2/buying.md`
3. `docs/reports/v2/intent_override.md`
4. `starter/ranking.py` 与 `experiments.md`

## 2. V2 给你的直接证据

- 118个miss中70个目标曾进入生产filter后候选，但完整rank始终大于10，是当前最大失败桶。
- 候选内miss：Buying 25、Browsing 28、Intent 15、Boundary 2。
- V1.1→V2有2个lost hit：`public_0054`最佳完整rank 23，`public_0125`最佳完整rank 13。
- 共享36个hit中3个rank改善、30个不变、3个变差。
- Development-only消融：equal MRR 0.181717；mild 0.180616；stronger 0.180124。三者Hit和MTTC相同，两个加权预设均未过gate。

## 3. 对当前权重实验的解释

`mild/stronger`只改变固定route权重。它们不能区分当前轮显式值、历史soft值、profile信号和override新值的时效性。因此结果只能否定这两组预设，不能否定“显式需求重排”方向。

不要继续在full public上网格搜索权重。先在development上用少量、有机制解释的配置；只有候选配置才打开一次holdout。

## 4. 分阶段任务

### 阶段 A：贡献可解释

为每个候选输出内部score breakdown：各route RRF贡献、current-turn exact/normalized match、active hard/soft match、profile match、override recency、缺字段状态。正式响应仍只返回最终score。

验收：所有分量之和等于生产final score；重复运行顺序一致；不使用ground truth计算分数。

### 阶段 B：显式与时效重排

保持RRF为候选共识底分，再增加小幅、封顶的显式匹配和current-turn/override recency分。Hard constraint仍由3号filter负责，排序层不得用未知字段做绝对淘汰。

验收：development Hit或MRR至少一项实质提高，另一项不显著下降；lost hit和rank churn完整披露；Intent old-value contribution为0。

### 阶段 C：近边界审计

优先看完整rank 11–20的miss，但规则必须基于通用匹配特征。对rank 1–3 shared hits设保护性回归门槛。

验收：报告`11–20→Top10`数量、`Top10→miss`数量、shared rank ↑/=/↓；不能只报净Hit。

## 5. 建议实验矩阵

| 实验 | 唯一变量 | 主要指标 | 风险指标 |
|---|---|---|---|
| K2.1 | current-turn exact match小幅加分 | Buying/Browsing MRR | lost hit、rank1回退 |
| K2.2 | override新值recency加分 | Intent eligible MRR | pre-override污染、shared rank下降 |
| K2.3 | profile弱信号降权 | Browsing Hit/MRR | cold-start与Boundary |

一次只运行一个。不要把新召回、filter和权重同时合并后声称排序收益。

## 6. 给其他成员的交接

- 向1号索取属性强弱和规范值，不从public目标反推权重。
- 向2号索取current/invalidated/neutral/override状态。
- 向3号索取完整route evidence和filter后候选。
- 向5号提供配置名、参数、commit、development结果、churn和是否申请打开holdout。
