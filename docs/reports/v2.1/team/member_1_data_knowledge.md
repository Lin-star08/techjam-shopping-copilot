# 1号成员：V2.1 数据词典与Evidence建议

## 1. 先读

1. `docs/reports/v2.1/browsing.md`
2. `docs/reports/v2.1/boundary.md`
3. `docs/reports/v2.1/README.md` 的候选/evidence部分
4. `starter/retrieval.py` 中 evidence term分类与类别alias

## 2. 直接证据

- 151个进入filter后候选的目标全部获得显式evidence和正boost，说明覆盖充分，但也提示evidence分类可能过宽。
- `category`、`feature`等matched attribute由词表和route共同推断；过宽类别词可能让大量商品同时boost，降低区分度。
- Browsing新增长尾类别首轮命中，但7个V2 hit回归；Boundary一个Walking案例大幅改善，两个headband/jeans案例被候选截断。
- use_case仍问141次，是最高频属性；全场234次无额外偏好。

## 3. 分阶段任务

### A. Evidence准确率审计

按属性抽样matched terms，区分真正商品字段匹配、类别同义词、泛化feature和噪声。特别检查一个term被同时标category与use_case的情况。

交付：route×attribute×term覆盖/频率表、误匹配样本、可重复catalog统计命令。

验收：不读取public ground truth生成词；每个boost term能追溯到商品字段；泛化词有上限或降权。

### B. Leaf类别与问题playbook

为长尾leaf类别提供规范alias和高区分问题，避免宽父类占据大量候选预算。将coverage与information value分开。

交付：更新的category playbook与alias diff。

验收：类别映射不成为hard filter；低区分问题降权；2号能直接消费属性优先级。

### C. 交接

- 给2号：类别→问题优先级与fallback reason。
- 给3号：leaf alias、字段覆盖和泛化词名单。
- 给4号：hard/soft evidence强度与误匹配率。
- 给5号：资产commit、构建命令、覆盖变化与风险。

## 4. 禁止事项

不得将public sample、ASIN、目标标题或隐藏intent写入词典；不得凭单个成功案例提高全局权重；不得用高覆盖代替真实区分度。
