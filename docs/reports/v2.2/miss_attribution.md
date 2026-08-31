# V2.2 未命中与 Churn 清单

## 口径

V2.2 正式结果有 93 个 miss。本版完成正式 evaluator、确定性复跑和全量响应 trace，但没有运行 V2.1 报告所用的临时生产候选漏斗 hook，因此这里只报告可直接验证的结果状态，不把 miss 强行归类为 R1、R3、F1 或 K1。

V2.1 已证实的顺序 Top-100 截断仍存在，因为本次没有修改检索实现。后续补齐 filter 前后候选、未截断 route 列表和完整 rank 后，再对 93 条做互斥主因归类。

## V2.1→V2.2 Churn

| 场景 | Sample | Split | V2.1 | V2.2 |
|---|---|---|---|---|
| Buying | `public_0020` | development | T1/R2 | miss |
| Buying | `public_0031` | development | miss | T2/R9 |
| Buying | `public_0061` | development | T5/R3 | miss |
| Buying | `public_0097` | holdout | miss | T1/R3 |
| Buying | `public_0155` | development | T2/R7 | miss |
| Browsing | `public_0019` | development | T2/R1 | miss |
| Browsing | `public_0039` | development | miss | T3/R3 |
| Browsing | `public_0043` | development | miss | T2/R8 |
| Browsing | `public_0063` | development | miss | T2/R2 |
| Browsing | `public_0077` | holdout | T1/R3 | miss |
| Browsing | `public_0086` | holdout | miss | T3/R1 |
| Browsing | `public_0105` | development | miss | T4/R1 |
| Browsing | `public_0122` | development | miss | T4/R4 |
| Browsing | `public_0127` | development | miss | T5/R5 |
| Browsing | `public_0153` | holdout | T3/R8 | miss |
| Intent Override | `public_0125` | holdout | T4/R3 | miss |
| Intent Override | `public_0177` | development | miss | T4/R4 |
| Intent Override | `public_0183` | holdout | miss | T4/R2 |

## 93 个 miss

### Buying（32）

`public_0008`, `public_0018`, `public_0020`, `public_0026`, `public_0027`, `public_0030`, `public_0032`, `public_0054`, `public_0058`, `public_0061`, `public_0066`, `public_0083`, `public_0093`, `public_0095`, `public_0106`, `public_0107`, `public_0109`, `public_0124`, `public_0132`, `public_0133`, `public_0143`, `public_0149`, `public_0155`, `public_0156`, `public_0159`, `public_0161`, `public_0171`, `public_0174`, `public_0178`, `public_0179`, `public_0193`, `public_0200`

### Browsing（39）

`public_0006`, `public_0007`, `public_0012`, `public_0016`, `public_0019`, `public_0021`, `public_0040`, `public_0047`, `public_0048`, `public_0049`, `public_0051`, `public_0060`, `public_0073`, `public_0074`, `public_0075`, `public_0076`, `public_0077`, `public_0081`, `public_0087`, `public_0091`, `public_0092`, `public_0098`, `public_0099`, `public_0100`, `public_0121`, `public_0134`, `public_0137`, `public_0138`, `public_0141`, `public_0150`, `public_0151`, `public_0153`, `public_0158`, `public_0162`, `public_0170`, `public_0172`, `public_0175`, `public_0181`, `public_0195`

### Intent Override（17）

`public_0003`, `public_0013`, `public_0023`, `public_0034`, `public_0038`, `public_0052`, `public_0064`, `public_0068`, `public_0071`, `public_0072`, `public_0096`, `public_0103`, `public_0123`, `public_0125`, `public_0144`, `public_0186`, `public_0198`

### Boundary（5）

`public_0104`, `public_0112`, `public_0169`, `public_0180`, `public_0187`

## 下一步证据要求

对 7 个 lost 优先保存：每轮问题与回复、全部 route 的目标 rank、顺序裁剪前后集合、hard filter reason、完整 RRF/evidence score。只有这些证据齐全，才能判断是知识导致的对话路径变化、R3 截断、filter 误删还是最终排序失败。
