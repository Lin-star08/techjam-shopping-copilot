# v1.1 Buying 场景分析报告

## 1. 指标与命中分布

| 数据范围 | 样本数 | Hits | Misses | Hit@10 | MRR | MTTC |
|---|---:|---:|---:|---:|---:|---:|
| Full public | 80 | 24 | 56 | 0.300000 | 0.154563 | 8.000000 |
| Development | 60 | 14 | 46 | 0.233333 | 0.098862 | 8.666667 |
| Internal holdout | 20 | 10 | 10 | 0.500000 | 0.321667 | 6.000000 |

相对 V1，Full 新增 5 个、丢失 1 个，净增 4 个命中。24 个命中全部发生在 turn 1，rank 分布为 1×9、2×1、3×3、4×3、5×2、7×1、8×2、9×2、10×1。

值得注意：Development Buying MRR 从 0.104993 降至 0.098862，而 holdout MRR 从 0.189722 升至 0.321667，收益分布不均。

描述性统计（population variance）：Hit 方差 0.210000；RR 方差 0.100325；完成轮次均值 8.000000、方差 21.000000、标准差 4.582576、极值 1–11；24 个命中的 rank 均值 3.875000、方差 9.026042、极值 1–10。高完成轮次方差来自 turn-1 hit 与 turn-11 miss 的两端分化。

## 2. 未识别原因

### 已证实

1. 56 个 miss 的目标未进入最终 Top 10；失败会话产生 504 个固定重试轮次，Agent 没有追问。
2. 至少一个有效轮次中，61/80 个目标进入 filter 后候选；其中 24 个进 Top 10，37 个目标已召回但排在前十之外，19 个从未进入 filter 后候选。
3. 候选完整 RRF rank 中，59/80 个目标位于 Top 100，51/80 位于 Top 50，说明剩余损失同时包含召回缺失和 K1 排序问题。
4. V1→V1.1 的 shared hits 中 4 条排名提高、6 条降低、9 条不变；净指标改善掩盖了明显的 rank churn。
5. 唯一 lost hit `public_0053` 仍由 current-message 和 fallback route 找回，但最佳 RRF rank 为 13；这是已证实的等权融合排序回归，不是召回缺失。
6. `public_0156` 在某个有效轮次发生目标被 filter 排除，但在其他轮次仍进入 filter 后候选，最佳 RRF rank 108。它说明 filter 风险存在，但不能把整条 miss 只归因于过滤。

### 合理推断

1. 多 route 重复出现奖励带来 5 个新增命中，但等权 RRF 可能让多个弱证据压过单个高质量显式需求证据。
2. 19 个候选缺失目标需要改进 current-message/category/attribute route；37 个候选内 miss 更适合通过显式条件匹配和 route weight 调整处理。
3. Development MRR 下降表明不能只根据 holdout 的大幅提升直接固定当前 RRF 参数。

### 证据边界

当前完整 RRF rank 可确认候选是否存在，但没有每个商品的 hard/soft match score。对排在目标前面的商品，尚不能逐一断言其相关性更差；需要 score breakdown 和约束违反记录。

## 3. 代表性 public 案例

以下案例只用于错误分析，不得转化为 public set 硬编码。

| Sample | V1 → V1.1 | 观察 |
|---|---|---|
| `public_0054` | miss → rank 5 | Hoodies & Sweatshirts + fabric；多路线融合带来新增命中。 |
| `public_0065` | rank 9 → rank 3 | Bibs + polyester；RRF 显著提升已有边缘命中。 |
| `public_0053` | rank 6 → miss（RRF rank 13） | Passport Covers + leather；目标只获得 current-message/fallback 支持，被等权融合挤出前十。 |

## 4. 5 人分工修改建议

| 成员 | 修改建议 | 预期交付 | 验收标准 |
|---|---|---|---|
| 1号 | 统计 material/category/feature 在各字段和路线中的可靠度。 | route × attribute 覆盖表 | 数据来自 catalog；能区分高质量单路线证据与泛化重复证据。 |
| 2号 | 保持当前状态合同，补充失败后高价值追问；不要用重复反馈覆盖明确条件。 | Buying clarification trace | 首轮 miss 后能获得新属性；asked/neutral 行为正确。 |
| 3号 | 针对 19 个候选缺失类提升 query/route 覆盖，逐轮记录 filter reason。 | recall ablation、filter audit | Candidate Recall 提升；目标误删逐轮可见且不会靠放松所有过滤解决。 |
| 4号 | 给 current-message、current-state、category、profile 设置可解释权重，并加入显式条件 match boost。 | Weighted RRF、score breakdown | `public_0053` 回归恢复；development MRR 不下降；不得使用 sample 特判。 |
| 5号 | 将 gained/lost hit、rank up/down 和候选漏斗纳入 gate。 | Buying churn 报告、dev/holdout 对比 | 不能只看净 Hit；任何原 Top-3 丢失或明显降级必须解释。 |

## 5. 下一版本观察项

- Candidate Recall → post-filter retention → RRF Top 50/10 的漏斗。
- 单路线强匹配与多路线弱匹配的分组表现。
- Development MRR 和 holdout MRR 同时改善，缩小当前分化。
- 1 个 lost hit、6 个 shared rank-down 的逐条回归结果。
