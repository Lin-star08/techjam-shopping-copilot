# V2.2 Buying 分析

Buying 为 48 hit / 32 miss，Hit `0.600000`、MRR `0.277693`、MTTC `5.487500`。相对 V2.1 分别变化 `-0.012500`、`-0.000397`、`+0.075000`。

新增 `public_0031`（turn 2 rank 9）、`public_0097`（turn 1 rank 3）；丢失 `public_0020`、`public_0061`、`public_0155`。Development Buying 从 38/60 降为 36/60，holdout 从 11/20 升为 12/20，说明 overall 小幅回落由 development 驱动。

shared rank 中 3 个改善、42 个不变、1 个下降。下一步先审计三个 development lost 的问题路径和候选位置，不应因 holdout Buying 改善而忽略 development 回归。
