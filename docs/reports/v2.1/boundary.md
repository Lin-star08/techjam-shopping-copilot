# V2.1 Boundary 场景分析

## 1. 指标与分布

| 指标 | V2 | V2.1 | Δ |
|---|---:|---:|---:|
| Hits / 10 | 6 | 5 | -1 net |
| Hit@10 | 0.600000 | 0.500000 | -0.100000 |
| MRR | 0.470000 | 0.364286 | -0.105714 |
| MTTC | 5.900000 | 6.300000 | +0.400000 |

首次命中turn 1/2/3分别为3/1/1；命中rank均值2.4、范围1–7。相对V2新增`public_0035`，丢失`public_0104`和`public_0169`。

## 2. 已证实行为与回归机制

- 仍有6次标准no-preference进入Agent，未发现同一neutral属性被重复问。
- 候选覆盖从V2的8/10降至7/10；5个miss可归为R1纯召回1、R3融合前截断2、K1-near 1、K1-deep 1。
- `public_0035`由V2最佳完整rank17改善为turn1 rank1；目标得到0.105 evidence boost并由多个category/field/profile route支持。
- `public_0104`在fabric回答轮位于current-message rank1、field-attribute rank2、relaxed rank2、fallback rank1；`public_0169`在cotton回答轮位于current-message rank1、field-attribute rank4、relaxed rank6、fallback rank1。但两者均未进入合并后的前100候选。
- 根因是`merge_candidates`按route顺序收集，前序route达到100个唯一ASIN即返回，后置route即使rank1也无法参与融合。这是已证实的前融合截断。

## 3. 合理推断与证据边界

Boundary route在neutral后扩大类别/热门候选，容易让前序category route占满预算。Round-robin或每route保底配额应能修复机制，但在全量评测前不能保证恢复两个具体case且无其他回归。

本报告证明目标在个别route中存在并被截断；不证明它必然比当前Top10更相关。完整清单见[未命中归因](miss_attribution.md)，public案例不得转化为ID特判。

## 4. 代表案例

- 成功：`public_0035`，V2从未命中，V2.1 turn1 rank1。
- 失败：`public_0104`，no-preference后获得fabric回答，目标在多个route高位却被Top100顺序截断。
- 失败：`public_0169`，cotton回答后目标位于current-message rank1，仍未进入融合候选。

## 5. 1–5号建议

| 成员 | 修改建议 | 交付物 | 验收标准 |
|---|---|---|---|
| 1号 | 保持类别alias/evidence准确，避免热门大类过宽 | category evidence审计 | 泛化类别不吞噬leaf类别信号 |
| 2号 | neutral后保留有效类别与新回答，输出intent/route reason | state/decision trace | no-preference不污染，问法不重复 |
| 3号 | 用round-robin/route quota替代顺序Top100 | 合并算法与回归测试 | 任一启用route的rank1候选不得因route顺序丢失 |
| 4号 | 截断修复后再评估evidence，禁止把召回缺失归为重排 | frozen-candidate ablation | Boundary至少恢复V2的6/10且MRR不降 |
| 5号 | Boundary设硬gate，记录候选截断率 | 场景验收表 | Hit/MRR/MTTC均不低于V2后才升级 |

## 6. 下一版指标

No-preference触发率、重复问率、每route配额使用、截断前后候选覆盖、Boundary Hit/MRR、P95延迟与route级耗时。
