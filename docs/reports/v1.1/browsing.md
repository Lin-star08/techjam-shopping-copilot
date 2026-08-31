# v1.1 Browsing 场景分析报告

## 1. 指标与命中分布

| 数据范围 | 样本数 | Hits | Misses | Hit@10 | MRR | MTTC |
|---|---:|---:|---:|---:|---:|---:|
| Full public | 80 | 6 | 74 | 0.075000 | 0.021161 | 10.250000 |
| Development | 60 | 4 | 56 | 0.066667 | 0.018214 | 10.333333 |
| Internal holdout | 20 | 2 | 18 | 0.100000 | 0.030000 | 10.000000 |

相对 V1 新增 4 个命中、无丢失；6 个命中全部发生在 turn 1，排名为 2、2、4、5、7、10。

描述性统计（population variance）：Hit 方差 0.069375；RR 方差 0.007464；完成轮次均值 10.250000、方差 6.937500、标准差 2.633913、极值 1–11；6 个命中的 rank 均值 5.000000、方差 8.000000、极值 2–10。

## 2. 未识别原因

### 已证实

1. 74 个 miss 的目标没有进入最终 Top 10；全部 Browsing 响应仍然没有提出问题。
2. 至少一个有效轮次中，43/80 个目标进入 filter 后候选，39 个进入完整 RRF Top 100、21 个进入 Top 50，最终只有 6 个进入 Top 10。
3. 剩余失败可拆为 37 个候选缺失和 37 个候选内排序失败；两类规模相同，不能只优化其中一端。
4. 666 个固定重试轮次形成 24 组不同 Top 10，而 V1 所有场景的重试只有 1 组。RRF 使保留类别/state 能影响后续结果，但 Browsing 没有新增 turn 2+ 命中。
5. V1 的两个命中均保留；`public_0081` 从 rank 9 升到 2，`public_0134` 保持 rank 4。
6. profile/category route 已参与融合，但 hidden material/style/feature 因零追问仍无法披露。

### 合理推断

1. RRF 已显著改善宽类别内部排序，但没有用户新信息时，上限仍低：Hit@10 只有 0.075。
2. 37 个候选缺失案例需要高价值追问或更广召回；37 个候选内 miss 可通过 category-aware 权重和多样性处理。
3. 重试列表变得与状态相关是必要进展，但如果第 2–10 轮没有新输入，重复同一会话列表仍不会继续收敛。

### 证据边界

当前候选漏斗可以定位目标是否进入实际 filtered pool，但没有属性信息增益、候选熵和非目标相关性标签。因此不能仅根据目标 rank 决定应问 material、style 还是其他属性。

## 3. 代表性 public 案例

以下案例只用于错误分析，不得转化为 public set 硬编码。

| Sample | V1 → V1.1 | 观察 |
|---|---|---|
| `public_0011` | miss → rank 5 | Underwear Undershirts；RRF 在宽类别内产生新增命中。 |
| `public_0164` | miss → rank 2 | Watches Watch Bands；多路线共同支持显著提升目标。 |
| `public_0081` | rank 9 → rank 2 | 已有边缘命中升到前列，证明融合能改善 MRR。 |

## 4. 5 人分工修改建议

| 成员 | 修改建议 | 预期交付 | 验收标准 |
|---|---|---|---|
| 1号 | 为宽类别估算候选规模、属性覆盖和信息增益。 | category question playbook | 每类至少 2–3 个可回答属性；规则来自 catalog。 |
| 2号 | 接入一次一个属性的 clarification，维护 asked/neutral。 | Browsing end-to-end trace | 首轮模糊可提问；不重复；回答后 state 更新。 |
| 3号 | 针对 37 个候选缺失类增加 category/attribute recall，并修正固定重试句的 generic 判定。 | recall 与 routing ablation | 重试不再仅靠相同文本；Candidate Recall 提升。 |
| 4号 | 对 37 个候选内 miss 调整 route weight、多样性和显式回复权重。 | Weighted RRF/diversity 实验 | Profile 不覆盖当前需求；Top 50→10 转化率提高。 |
| 5号 | 记录 ask rate、候选缩减、候选漏斗、重复列表和首次命中轮次。 | Browsing gate 表 | 新增 turn 2+ 命中；重复问题率 0；dev/holdout 均改善。 |

## 5. 下一版本观察项

- Clarification 前后 Candidate Recall、RRF rank 和候选熵。
- 候选缺失 37 条与候选内 miss 37 条分别改善多少。
- Turn 2+ 命中率；V1.1 仍为 0。
- Profile/category/clarification 三项必须分开 ablation。
