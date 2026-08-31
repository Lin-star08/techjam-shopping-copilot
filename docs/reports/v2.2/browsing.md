# V2.2 Browsing 分析

Browsing 为 41 hit / 39 miss，Hit `0.512500`、MRR `0.213185`、MTTC `6.512500`。相对 V2.1 分别改善 `+0.050000`、`+0.017709`、`-0.350000`，是 V2.2 的主要净收益来源。

新增 7：`public_0039`, `public_0043`, `public_0063`, `public_0086`, `public_0105`, `public_0122`, `public_0127`；丢失 3：`public_0019`, `public_0077`, `public_0153`。Development Browsing Hit 从 `0.433333` 升至 `0.516667`，但 holdout 从 `0.550000` 降至 `0.500000`，同时 holdout MRR 从 `0.255972` 升至 `0.283056`。

结论是“更多后置命中且平均排名改善”，不是全面无回归；两个 holdout lost 与一个 holdout gained 的替换需要候选漏斗证据。
