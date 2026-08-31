# 3号：V2.2 检索与过滤后续

- 本次未修改、也未修复 V2.1 已证实的顺序 Top-100 截断。
- 对 7 个 lost 保存未截断 route、merge 前后、filter 前后和目标完整 rank。
- 区分“问题改变导致 query 改变”和“同 query 下候选/排序改变”；前者交给 2号，后者进入 R3/F1/K1。
- 输出 93 miss 的互斥漏斗后再更新 `miss_attribution.md`。
