# V3.1 Boundary 类别信息追问

V3.1 是 V3 上的 development-only 单变量实验。它把 Boundary 在开放问题收到 no-preference 后的固定 `material` 问题，替换为完整 catalog 驱动的类别决策：按每个 coarse category 中商品签名第一项的 `rating_number` 加权分布，在 `material`、`feature`、`color` 中选择最可能披露第一条 hard signal 的属性。

该规则只读取 catalog、当前消息和 profile，不读取 public sample ID、ground truth 或目标 ASIN。若选定属性无额外偏好，下一轮切换 material/feature；若获得证据但同签名组仍超过 Top 10，下一轮复问相同属性以继续消歧。

## Development 结果

| 版本 | Hit@10 | MRR | MTTC | Boundary MTTC | Technical |
|---|---:|---:|---:|---:|---:|
| V3 | 1.000000 | 0.977222 | 2.166667 | 3.142857 | 0.969833 |
| V3.1 | 1.000000 | 0.977222 | 2.153333 | 2.857143 | 0.970100 |
| Delta | 0 | 0 | -0.013334 | -0.285714 | +0.000267 |

7 个 development Boundary 样例已经达到当前对话协议的乐观信息下界：一个类别热门商品在 turn 1 命中，其余 6 个在第一次 no-preference 后于 turn 3 命中。整体目标仍为 2/3 通过，MTTC 距 `<2` 尚差 `0.153333`。

## Gate

- 143/143 tests passed。
- Public-label literal audit passed。
- 因 development 的 MTTC Gate 未通过，本改动没有再次打开 holdout；避免用已经查看过的保留集继续选择策略。
- 目录先验实验中，评论速度、上架时间、价格/字段完整度、average rating 和 profile IDF 的 Buying 首轮 Top-1 最好只从 36/60 提升到 38/60，仍不足以承担剩余差距，因此未把过拟合权重加入线上排序。
- 进一步使用固定SHA五折做了不含任何ID特征的listwise线性排序 OOF：Top-1 `37/60`、Top-10 `57/60`、MRR `0.741483`，各折Top-1为`5/8、8/14、7/13、10/13、7/12`。相对catalog popularity仅多1个首轮命中，无法接近整体MTTC在其他场景均达到乐观下界后仍需从Buying节省的至少13个轮次；训练权重没有进入线上代码。

复现：

```bash
python3 -m unittest discover -s tests -q
python3 -m tools.run_goal_workflow \
  --split development \
  --output results/v3.1-boundary-development.json \
  --skip-tests
```

证据摘要见 `results/v3.1-boundary-evidence.json`，逐 session 结果见 `results/v3.1-boundary-development.json`。
