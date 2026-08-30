# 团队交付接口说明

这份文件用于开工前统一协作方式。大家先按这里约定交付，后续如果发现不合适，再由组长统一修改，不要每个人临时发不同格式。

## 1. 总原则

- 最终被评估器调用的入口只有 `starter/agent.py`，所有代码改动都要围绕它能稳定运行来做。
- 不直接修改 `evaluator/`、`data/public_set.jsonl`、`data/catalog.jsonl` 和官方 `docs/evaluation_config.json`。
- 非代码产出也必须能被下游使用：词典用 JSON，实验记录用 Markdown/JSON，失败分析用固定表格格式。
- 每次交付都要说明：改了什么、交给谁、怎么验证、是否影响其他人。
- 一个主要功能对应一个版本或 commit。没有跑分记录的改动，不进入最终候选。

## 2. 统一目录

| 路径 | 用途 | 负责人 | 说明 |
| --- | --- | --- | --- |
| `starter/agent.py` | 最终 Agent 入口 | 2/3/4 号共同接入，5 号验收 | `Agent.reset()` 和 `Agent.respond()` 必须符合官方接口 |
| `starter/state.py` | 对话状态管理 | 2 号 | 记录当前有效需求、已问属性、无偏好属性、失效旧需求 |
| `starter/constraints.py` | 需求解析与约束分类 | 2 号 | 负责把用户表达解析成统一 Constraint；区分硬条件、软偏好、不确定条件 |
| `starter/filtering.py` | 约束过滤 | 3 号 | 根据 2 号输出的 Constraint / SessionState 应用安全 hard filter；不确定条件不得硬过滤 |
| `starter/retrieval.py` | 多路召回 | 3 号 | 从不同路线召回候选商品 |
| `starter/ranking.py` | 融合排序 | 4 号 | 合并候选、归一化、RRF 或 rerank |
| `starter/resources.py` | 加载共享资源 | 1/3 号 | 统一读取 `artifacts/*.json` |
| `artifacts/lexicon.json` | 商品词典 | 1 号交付给 2/3/4 号 | 必须能被 Python `json.load()` 直接读取 |
| `artifacts/category_playbook.md` | 品类观察说明 | 1 号交付给全组 | 写给人读，用于理解重点品类 |
| `artifacts/failure_taxonomy.md` | 失败类型复盘 | 1/5 号维护 | 每次跑分后更新主要失败原因 |
| `artifacts/experiments.md` | 实验记录 | 5 号维护，全组填写 | 每个版本、改动、分数、结论都要写 |
| `artifacts/demo_script.md` | 演示脚本 | 5 号主写，全组补充 | 最终展示用 |
| `results.json` | 本地评估输出 | 5 号生成 | 由 `python -m evaluator.local_evaluator` 自动生成 |
| `tests/` | 自动测试 | 各模块负责人补充 | 新增状态、解析、过滤、排序逻辑时要补测试 |

如果某个文件暂时不存在，由对应负责人新建。文件名不要随意变化，否则其他人不好接。

## 3. 每个人交付什么

| 人员 | 主要交付文件 | 交付给谁 | 交付时间 | 验收方式 |
| --- | --- | --- | --- | --- |
| 1 号：数据洞察 | `artifacts/lexicon.json`、`artifacts/category_playbook.md`、`artifacts/failure_taxonomy.md` | 2/3/4/5 号 | Day 1 下午先交 v1，之后按失败案例更新 | `lexicon.json` 能被 Python 读取；词条来自 catalog，不来自 public 答案特判 |
| 2 号：对话状态 | `starter/state.py`、`starter/constraints.py`、状态/解析测试 | 3/4 号 | Day 1 下午先交可运行版本 | 能处理 no preference、intent override、asked_attributes；不会让旧条件污染当前状态；Constraint 输出符合统一格式 |
| 3 号：检索约束 | `starter/filtering.py`、`starter/retrieval.py`、过滤/检索测试 | 4 号 | Day 1 晚上先交候选接口 | 每轮能返回合法候选；不确定条件不会硬过滤；Candidate 输出符合统一格式 |
| 4 号：融合排序 | `starter/ranking.py`、排序参数说明、ablation 结论 | 5 号和最终 `agent.py` | Day 2 下午前交主版本 | Top 10 合法去重；分数变化有记录；不只看总分 |
| 5 号：评估交付 | `artifacts/experiments.md`、`results.json`、README/Devpost/demo 草稿 | 全组 | 每次合并后更新 | 记录总分和四类场景；能复现命令；最终无 API key 和无关大文件 |

## 4. 共享数据格式

### 4.1 商品候选 Candidate

所有检索路线交给排序模块时，都用同一种候选格式。

```json
{
  "parent_asin": "B07K34RX5J",
  "route": "current_state",
  "route_rank": 12,
  "route_score": 8.42,
  "matched_terms": ["blue", "running", "shoes"],
  "debug_reason": "matched category and color"
}
```

字段说明：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `parent_asin` | string | 是 | 商品 ID，必须存在于 `data/catalog.jsonl` |
| `route` | string | 是 | 候选来自哪条路线，例如 `current_message`、`current_state`、`category`、`attribute_profile` |
| `route_rank` | integer/null | 否 | 在本路线里的排名，从 1 开始 |
| `route_score` | number/null | 否 | 本路线原始分数，不同路线之间不要直接比较 |
| `matched_terms` | array[string] | 否 | 命中的关键词，方便复盘 |
| `debug_reason` | string | 否 | 给人看的简短原因，不返回 evaluator 也可以 |

Candidate 聚合规则：

- 同一个 `parent_asin` 在不同 retrieval route 中允许重复出现，3 号不要为了“去重”提前丢掉路线信息。
- 4 号在 `starter/ranking.py` 中负责按 `parent_asin` 聚合这些重复候选，并利用 `route_rank` / `route_score` 等信息做 fusion。
- fusion 完成后再按 `parent_asin` 去重，最终交给 `Agent.respond()` 的 Top 10 必须唯一。

### 4.2 当前状态 SessionState

2 号维护状态对象，其他模块只读它，不自己拼历史对话。

```json
{
  "session_id": "public_xxx",
  "turn": 3,
  "current_slots": {
    "category": "shoes",
    "color": "brown"
  },
  "hard_constraints": {
    "budget_max": 50
  },
  "soft_preferences": {
    "use_case": ["walking"],
    "style": ["casual"]
  },
  "asked_attributes": ["color"],
  "neutral_attributes": ["brand"],
  "invalidated_slots": {
    "color": ["black"]
  },
  "profile_signals": ["comfort", "fit"]
}
```

统一规则：

- `current_slots` 只放当前仍然有效的明确需求。
- `hard_constraints` 只放可以安全过滤的条件。
- `soft_preferences` 只影响排序，不直接删除候选。
- `asked_attributes` 用于避免重复追问。
- `neutral_attributes` 记录用户明确说“不在意”的属性。
- `invalidated_slots` 记录被新需求覆盖的旧条件，不能再进入 current-state retrieval。
- `profile_signals` 是弱信号，权重低于用户当前明确表达。

### 4.3 约束解析 Constraint

解析用户表达时，每个条件统一成下面格式。

```json
{
  "attribute": "color",
  "value": "brown",
  "kind": "hard",
  "confidence": 0.92,
  "source": "current_message",
  "raw_text": "make them brown"
}
```

字段规则：

| 字段 | 可选值/类型 | 说明 |
| --- | --- | --- |
| `attribute` | `category`、`material`、`color`、`size`、`style`、`brand`、`budget`、`feature`、`use_case`、`other` | 必须和官方 `ask_attribute` 取值保持一致 |
| `value` | string/number | 解析出的具体值 |
| `kind` | `hard`、`soft`、`neutral`、`override`、`unknown` | 决定后续是过滤、排序、跳过还是覆盖旧状态 |
| `confidence` | 0 到 1 | 低置信度不要硬过滤 |
| `source` | `current_message`、`state`、`profile` | 信息来源 |
| `raw_text` | string | 原始文本片段，方便复盘 |

### 4.4 Agent 最终返回

最终 `Agent.respond()` 只能返回官方允许的字段。

```json
{
  "message": "Here are the closest matches I found.",
  "ask_attribute": null,
  "recommendations": [
    {"parent_asin": "B07K34RX5J"}
  ],
  "usage": {
    "prompt_tokens": 0,
    "completion_tokens": 0
  }
}
```

注意：

- `ask_attribute` 只能是官方允许值或 `null`。
- `recommendations` 里必须是合法、唯一的 `parent_asin`。
- 实际评分只看 Top 10，所以我们最终返回时最多保留 10 个。
- 默认只返回 `parent_asin`，把 fusion/rerank 的内部得分留在模块内部；除非官方接口明确需要，否则不要额外返回 `score`。
- 不要把 `route`、`route_rank`、`route_score`、`debug_reason` 等内部调试字段返回给 evaluator。

## 5. 共享文件格式

### 5.1 `artifacts/lexicon.json`

建议结构：

```json
{
  "version": "v1",
  "source": "catalog_only",
  "updated_at": "2026-08-29",
  "categories": {
    "shoes": {
      "aliases": ["shoe", "sneaker", "running shoe"],
      "high_value_attributes": ["size", "color", "use_case"],
      "common_terms": ["walking", "running", "comfortable"]
    }
  },
  "materials": ["cotton", "polyester", "leather"],
  "colors": ["black", "white", "blue", "brown"],
  "brands_or_stores": {
    "Nike": ["nike"]
  }
}
```

要求：

- 必须是合法 JSON，不能有注释。
- 只使用 catalog 可见字段统计，不使用 public 正确答案做特判。
- 每次改动更新 `version` 和 `updated_at`。

### 5.2 `artifacts/experiments.md`

每次实验按固定格式写：

```markdown
## v1-state-2026-08-29

- 改动：加入 SessionState、no preference、intent override 基础处理
- 负责人：2号
- 运行命令：python -m evaluator.local_evaluator
- 总分：
  - HitRate@10:
  - MRR:
  - MTTC:
  - TechnicalScore:
- 分场景：
  - Buying:
  - Browsing:
  - Intent Override:
  - Boundary:
- 结论：保留 / 回退 / 继续观察
- 失败案例：列 3 个 sample_id 和原因
```

### 5.3 `artifacts/failure_taxonomy.md`

失败分析统一用这几类：

| 类型 | 判断方式 | 交给谁处理 |
| --- | --- | --- |
| 召回不到 | 目标商品完全没进入候选池 | 3 号 |
| 状态错误 | 当前需求记错、旧需求没移除、no preference 重复问 | 2 号 |
| hard filter 错 | 正确候选被过滤掉 | 3 号 |
| rerank 错 | 候选里有目标，但排不进 Top 10 或排名太低 | 4 号 |
| 追问无价值 | 问题没有缩小候选，或重复问 | 2/5 号 |
| 数据词典缺口 | 类别、材质、功能词没有覆盖 | 1 号 |

每条失败案例建议写成：

```markdown
- sample_id:
- scenario_type:
- target_parent_asin:
- 现象：
- 判断类型：
- 可能原因：
- 建议交给：
- 是否已修：
```

## 6. 合并前检查

每个人交付前至少完成下面检查：

- 能运行 `python -m evaluator.local_evaluator`，不会报错。
- 如果改了 Python 文件，至少运行相关测试：`python -m unittest`。
- 没有改官方 evaluator 来“提高分数”。
- 没有提交 API key、私有数据、无关大文件。
- 新增 JSON 文件能被 `json.load()` 读取。
- 新增函数有清楚输入输出，不让下游猜格式。


## 7. Git 分支与同步规则

为了避免多人同时改坏 `dev` 或互相覆盖，所有人统一执行下面规则：

1. `main` 只保存稳定版本/最终提交候选，不直接开发。
2. `dev` 是全组公共整合分支，不直接在上面写功能代码。
3. 每个人都从最新 `dev` 创建自己的 feature 分支：
   - 1 号：`feature/data-knowledge`
   - 2 号：`feature/state-manager`
   - 3 号：`feature/retrieval`
   - 4 号：`feature/rerank`
   - 5 号：`feature/evaluation`
4. 自己完成一个可验证的小阶段后，在自己的 feature 分支 `commit` 并 `push`。
5. 功能需要进入公共版本时，在 GitHub 创建 Pull Request：`feature/...` → `dev`。
6. 不直接把一个人的 feature 分支 merge 到另一个人的 feature 分支；共享更新统一经过 `dev`。
7. 需要获取队友已经合入 `dev` 的代码时，先更新本地 `dev`，再把 `dev` merge 到自己的 feature 分支：

```bash
git status
git switch dev
git pull origin dev
git switch feature/<自己的分支名>
git merge dev
```

8. 如果 `git status` 显示自己有尚未 commit 的重要修改，先保存并 commit，再切换分支/同步，避免丢失工作。
9. feature 分支第一次上传 GitHub 使用 `git push -u origin feature/<分支名>`；之后正常使用 `git push` 即可。
10. 每次 PR 合并进 `dev` 后，由 5 号或指定人员跑 evaluator 并记录结果；不是每次别人 `push`，所有人都要立刻同步。

## 8. 接口冻结规则

- 本文档作为 v1 协作契约。Day 1 开工后，`Candidate`、`SessionState`、`Constraint` 的字段名不要个人私自修改。
- 如果确实需要改共享字段或函数接口，先在群里说明原因和影响，由组长确认后统一修改本文档，再通知依赖方同步。
- 2/3/4 号优先保持 `starter/agent.py` 精简，只在接线时修改；核心逻辑分别放在 `state.py` / `constraints.py`、`filtering.py` / `retrieval.py`、`ranking.py`。

## 9. 开工顺序建议

1. 5 号先跑官方 baseline，保存 `results.json`，在 `artifacts/experiments.md` 记录 v0。
2. 1 号交 `lexicon.json` v1，先覆盖高频类别、材质、颜色、功能词。
3. 2 号交 `SessionState` 和 no preference / intent override 基础逻辑。
4. 3 号接入 hard filter 和多路召回，输出统一 Candidate。
5. 4 号接入 fusion/rerank，保证最终 Top 10 合法去重。
6. 5 号每次合并后跑分，记录总分、分场景、失败案例。
7. Day 3 下午只修 bug，不再重构架构。

## 10. 一句话对齐

所有人都记住这条线：用户说话 → 状态更新 → 区分硬条件和偏好 → 多路找候选 → 合并排序 → 推荐或追问 → 跑分复盘。

只要每个人的交付都能接上这条线，团队就不会散。
