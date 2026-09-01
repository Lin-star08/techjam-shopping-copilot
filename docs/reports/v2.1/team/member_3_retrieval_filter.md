# 3号成员：V2.1 Retrieval、候选预算与Filter建议

## 1. 先读

1. `docs/reports/v2.1/README.md` 的候选漏斗
2. `docs/reports/v2.1/boundary.md`
3. 四场景报告的lost案例
4. `starter/retrieval.py` 的`retrieve_route_candidates`与`merge_candidates`

## 2. 核心结论

V2.1 filter后覆盖151/200，低于V2的152；97个miss分为49个候选缺失、48个候选内。净收益不是总体覆盖扩大，而是候选替换与排序转化。

已确认顺序Top100问题：`merge_candidates`处理前序route达到100个唯一ASIN即返回。Boundary两个lost目标在关键轮次位于current-message rank1，也在多个后置route高位，但完全未进入融合。

## 3. 分阶段任务

### A. 修复合并公平性

先聚合所有启用route的证据，再统一裁剪；或采用每route保底配额/round-robin后填充。不得让route列表顺序决定候选生死。

验收：每个启用route的rank1都有保底；重复ASIN合并全部route evidence；改变route声明顺序不改变候选集合。

### B. 候选预算与性能

记录每route调用耗时、原始数、去重贡献数、最终保留数、目标rank。根据intent设置总预算，但先保留多样性再裁剪。

验收：coverage至少恢复V2的152/200；Boundary至少8/10；P95显著低于166.539 ms；max不再出现1.3秒级极值。

### C. Filter边界

当前仅1个session在有效轮观察到filter移除目标；继续输出filter reason，缺字段保持保守。候选截断发生在filter前，不得误标F1。

## 4. 交接

- 给1号：缺失最多的类别/属性和route词表问题。
- 给2号：每种intent实际启用route及budget。
- 给4号：未提前截断的完整route evidence候选。
- 给5号：R1/R2/F1数量、顺序不变性测试、route延迟和内存。

## 5. Gate

先修截断再调权重；候选集合冻结后才允许4号做evidence ablation。禁止针对public ASIN或sample补候选。
