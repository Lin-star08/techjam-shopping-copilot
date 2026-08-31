# 3号成员：V2 检索、Hard Filter 与 Fallback 建议

## 1. 你先看哪些文件

1. `docs/reports/v2/README.md` 的候选漏斗
2. 四个场景报告中的“已证实失败结构”
3. `docs/failure_cases.md`
4. `starter/retrieval.py`、`starter/constraints.py`、`starter/agent.py`

## 2. V2 候选漏斗

| 场景 | filter后候选覆盖 | miss：候选缺失 | miss：候选内rank>10 |
|---|---:|---:|---:|
| Buying | 63/80 | 17 | 25 |
| Browsing | 58/80 | 22 | 28 |
| Intent Override | 23/30 | 7 | 15 |
| Boundary | 8/10 | 2 | 2 |
| Overall | 152/200 | 48 | 70 |

相对V1.1，候选缺失从68降至48，证明追问回答与状态确实扩大了有效覆盖；但48条仍是必须单独解决的R1/F1桶。

## 3. 已知风险

- `public_0156` 是唯一观察到目标在某个可计分轮次由filter前存在变为filter后消失的样本；下一轮又恢复且最佳rank 96，因此它是C1/F1风险，不是纯filter根因结论。
- 现有runtime audit只记录目标是否存在、完整rank和hard constraints，没有保存每条route的目标rank及filter reason。
- 22个Browsing候选缺失表明具体回答未必形成有效的category+attribute联合检索。
- 7个Intent候选缺失必须只看override生效轮，不能把旧意图轮的候选覆盖算进去。

## 4. 分阶段任务

### 阶段 A：原生可观测性

在debug路径输出每route候选数、目标route rank、matched terms、filter前后状态和filter reason；正式响应不增加debug字段。

验收：每个miss可按第一个失败环节稳定归入R1、R2或F1；审计重放与正式hit/turn/rank一致。

### 阶段 B：联合召回

对追问得到的规范值构造`category + active attribute`查询；override只使用新值，neutral值完全排除。保留current message、state、profile与fallback为独立route，禁止提前全局截断。

验收：development候选覆盖提高；四场景分别报告；候选增长不能导致超时或大规模K1回归。

### 阶段 C：安全filter

仅对高置信、可验证字段应用硬过滤；缺字段商品应保守保留。解析出的粗category需要和商品类别层级兼容，避免子串误判。

验收：`target_filtered_out`逐轮可查；不确定值不误删；filter前后候选数与回退原因均记录。

## 5. 给其他成员的交接

- 给1号：缺失route最多的规范类别/属性组合和字段空洞。
- 给2号：state中哪些值实际进入query、哪些因neutral/invalidated被排除。
- 给4号：不丢失route evidence的完整候选及每route rank。
- 给5号：候选覆盖、R1/R2/F1数量、延迟、内存和失败案例。

## 6. Gate

下一版本至少同时满足：候选覆盖高于152/200；Intent只按eligible轮统计；F1无新增；正式Top 10合同合法；P95延迟和候选规模有上界；不对public ASIN或sample做特判。
