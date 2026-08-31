# V2.2 逐轮案例册

## 逐轮汇总

| Turn | 活跃会话 | 首次命中 | 累计命中 |
|---:|---:|---:|---:|
| 1 | 200 | 45 | 45 |
| 2 | 155 | 17 | 62 |
| 3 | 138 | 23 | 85 |
| 4 | 115 | 20 | 105 |
| 5 | 95 | 2 | 107 |
| 6 | 93 | 0 | 107 |
| 7 | 93 | 0 | 107 |
| 8 | 93 | 0 | 107 |
| 9 | 93 | 0 | 107 |
| 10 | 93 | 0 | 107 |

V2.1 的 turn 1–5 为 46/17/19/19/2。V2.2 少 1 个首轮命中，但 turn 3–4 多 5 个，说明净增来自对话后的知识/问题路径，而不是首轮检索全面变强。

## 新增与丢失案例

- 新增 11：`public_0031`, `public_0039`, `public_0043`, `public_0063`, `public_0086`, `public_0097`, `public_0105`, `public_0122`, `public_0127`, `public_0177`, `public_0183`。
- 丢失 7：`public_0019`, `public_0020`, `public_0061`, `public_0077`, `public_0125`, `public_0153`, `public_0155`。
- `public_0097` 从 miss 变为 turn 1 rank 3；它不是追问收益。
- `public_0086`、`public_0183` 是 holdout 后置新增命中；`public_0077`、`public_0125`、`public_0153` 是对应 holdout lost。
- `public_0004` 仍命中但 rank 1→8，是最大 shared-rank 回落；`public_0129` rank 2→1，是 holdout shared-rank 改善。

## 对话与性能

全量 trace 有 1,168 次 respond，409 次追问；问询分布为 use_case 142、style 94、material 57、size 51、feature 37、category 18、color 10。具体约束回答 67 次，无额外偏好 246 次，Boundary no-preference 6 次。

turn 6–10 的 465 次调用没有新增命中，相邻 Top 10 完全重复 518 次。应继续实施“三问后或候选稳定后停止”的成本优化，但这属于独立策略实验，不能混入本次知识语料归因。
