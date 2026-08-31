# V2.2 Intent Override 分析

Intent Override 为 13 hit / 17 miss，Hit `0.433333`、MRR `0.245556`、MTTC `7.933333`。相对 V2.1 Hit 提高 `0.033333`、MTTC 改善 `0.233334`，但 MRR 下降 `0.015277`。

新增 `public_0177`（development，turn 4 rank 4）与 `public_0183`（holdout，turn 4 rank 2）；丢失 `public_0125`（holdout，原 turn 4 rank 3）。`public_0004` 仍在 turn 3 命中，但 rank 1→8，是 MRR 回落的重要案例。

override 前的推荐不计分语义由 trace 测试覆盖。下一步应对这两个 rank 回落案例检查旧偏好失效、问题顺序与候选融合，不能只看净增 1 个 hit。
