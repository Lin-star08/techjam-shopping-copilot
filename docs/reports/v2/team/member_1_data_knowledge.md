# 1号成员：V2 数据词典与商品知识修改建议

## 1. 你先看哪些文件

1. `docs/reports/v2/browsing.md`：追问收益最大，适合优化 question playbook。
2. `docs/reports/v2/buying.md`：已有硬条件后的第二属性选择仍低效。
3. `docs/reports/v2/turn_casebook.md`：查看问题在哪一轮带来具体回答和新命中。
4. `artifacts/lexicon.json`、`artifacts/category_playbook.md`：你的实际交付资产。

不要从 public 目标商品反推词条或写 session 特判；案例只能用于发现可泛化的数据覆盖问题。

## 2. V2 给你的直接证据

- 438 次追问中，use_case 142 次最多；全场共有273次“没有额外偏好”，说明高频问题不等于高信息价值。
- Browsing 198次追问得到57次具体回答；Buying 147次只得到18次具体回答。
- Browsing 的24个新增 hit 全在追问后发生；`material` 在多个成功案例中直接把目标推到前列。
- 36次 category 问题仍会出现，说明粗类别解析与 playbook 名称未完全对齐。
- Boundary 中 `public_0035`、`public_0112` 从未提问，需检查 Walking 等类别的匹配覆盖，但不能针对这两个 ID 加规则。

## 3. 分阶段任务

### 阶段 A：覆盖率审计

按规范化类别统计：可匹配 playbook 比例、每个候选属性的字段覆盖率、值分布、缺失率和信息熵。明确 exact match、token overlap 与 fallback 各自覆盖多少类别。

交付物：`artifacts/category_playbook.md` 的覆盖表，以及从 catalog 可重复生成的统计命令。

验收：不读取 public ground truth；同一 catalog 重跑结果确定；每个低覆盖类别有“补规则”或“安全 fallback”的明确选择。

### 阶段 B：重排问题优先级

将类别问题按“覆盖率 × 区分度 × 可回答性”排序。已有 hard/soft 值的属性必须排除；优先能形成稳定检索词的 material、size、style、feature，避免所有类别一律 use_case 优先。

交付物：每类最多3个高价值问题，包含 `ask_attribute`、question、coverage、information_value 和数据来源。

验收：development 上首问具体回答率上升；每问后的候选缩减率可测；Browsing Hit/MRR 不下降。

### 阶段 C：规范化与回归

补齐复合类别、材质同义词、属性名和取值规范化，特别检查 override 新旧值是否落入同一 slot。

交付物：词典 diff、构建脚本、schema 校验和抽样审计。

验收：84项现有测试继续通过；新增词条来自 catalog 统计或通用知识，不来自 public target；2号、3号可直接消费规范值。

## 4. 给其他成员的交接

- 给2号：类别→问题优先级、coverage、information_value、fallback reason。
- 给3号：规范化类别和值、字段缺失率、可用于联合 route 的高置信词。
- 给4号：哪些属性是显式/高价值信号，哪些只适合弱加分。
- 给5号：资产版本、构建命令、预期影响场景、已知覆盖空洞。

## 5. 不建议做的事

- 不把 `sample_id`、ASIN 或隐藏 intent card 写入词典。
- 不凭单个成功案例全局提高某属性优先级。
- 不修改 evaluator 或固定 split。
- 不把 coverage 当作 information value；高覆盖但所有商品值相同的问题没有区分度。
