# 4号成员：V2.1 Evidence-aware Ranking建议

## 1. 先读

1. `docs/reports/v2.1/version_comparison.md`
2. `docs/reports/v2.1/intent_override.md`
3. `docs/reports/v2.1/browsing.md`
4. `starter/ranking.py`

## 2. 直接证据

- 候选内miss从V2的70降到48，是V2.1最大正向变化。
- 但shared 67个hit中23个rank下降；holdout MRR从0.334降到0.269944。
- Development配置均有相同77个hit。MRR：equal 0.236183、mild 0.236976、tiny 0.238587、light 0.239040、medium 0.243577。
- Medium相对light有3个shared rank提升、74不变、0下降，Technical也最高；但holdout未打开。
- 15个V2 hit回归中部分是候选截断，不能归因给ranking。

## 3. 分阶段任务

### A. 冻结候选集

等待3号修复Top100并导出固定development候选及route evidence。所有evidence强度实验使用同一候选，避免召回变化混入归因。

### B. 完整score breakdown

记录RRF route贡献、hard/soft evidence count、multiplier、neutral/invalidated过滤及最终score；加入竞争商品对比。

验收：分量之和严格等于生产分数；neutral/invalidated boost为0；正式响应不泄漏debug字段。

### C. Medium候选

在修复后的development重新比较light/medium。只有medium继续提高MRR、无lost且性能可接受，才向5号申请一次holdout。

验收：holdout Hit不降，MRR/Technical不低于V2；Boundary恢复；shared rank下降受控。

## 4. 风险

151个已覆盖目标全部有正boost，说明boost并不稀缺；若竞争商品也普遍boost，强度增加可能只是改变tie而非提高相关性。必须报告boost覆盖分布和人工抽样，不能只看目标。

## 5. 交接

向1号索取evidence误匹配率；向2号索取state时效；向3号索取冻结候选；向5号交付配置、commit、dev churn、延迟与holdout申请理由。
