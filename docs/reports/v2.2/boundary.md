# V2.2 Boundary 分析

Boundary 为 5 hit / 5 miss，Hit `0.500000`、MRR `0.364286`、MTTC `6.300000`，与 V2.1 完全一致；5 个 shared hit 的 rank 也全部不变。

全量 trace 记录 6 次 Boundary no-preference，说明 neutral 流程仍被端到端触发。未命中仍为 `public_0104`, `public_0112`, `public_0169`, `public_0180`, `public_0187`。

稳定不代表旧问题已解决：V2.1 已证明 `public_0104` 与 `public_0169` 存在前融合 Top-100 截断。本次只改变知识语料，没有触碰该机制，因此不能把 Boundary 不回归解读为截断已修复。
