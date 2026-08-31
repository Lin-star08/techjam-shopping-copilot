# Artifacts 交付说明

本目录保存团队共享的知识资产和交付说明。文件用途及负责人以[团队交付接口说明](<../team_delivery_contract(1).md>)为准。

## 1号正式交付

| 文件 | 内容 | 交给谁 | 验收方式 |
| --- | --- | --- | --- |
| `lexicon.json` | 机器可读的商品词典、alias、类目规则、覆盖统计和追问顺序 | 2/3/4号 | 能被 Python `json.load()` 直接读取；词条和统计来自catalog |
| `category_playbook.md` | 给人阅读的类目观察、追问顺序和交接要点 | 全组 | 与 `lexicon.json` 中的 `category_playbook` 一致 |
| `failure_taxonomy.md` | 已确认的问题、处理原则、责任模块和回归检查项 | 2/3/4/5号 | 每条结论有数据依据，不包含针对public答案的特判 |

`build_lexicon.py` 是配套生成器，用于重建 `lexicon.json` 和 `category_playbook.md`。它不是额外的业务接口，但需要与生成结果一起维护，否则下次重建会覆盖人工修改。

## 当前版本

- 资产版本：V3
- Schema：`1.3`
- Catalog：`data/catalog.jsonl`
- 商品数：50,000
- Evidence词：202
- 类目alias：171
- 质量标记：accurate 36、broad 165、ambiguous 13、noise 0；标记可以重叠
- Public ground truth：未用于生成词典、alias或分类规则

## 下游怎么使用

- 2号从 `lexicon.json` 读取属性词表和 `category_playbook[*].question_order`。已经问过、用户表示无所谓或当前状态已有答案的属性要跳过。
- 3号使用alias、字段覆盖率和不可靠类目规则。歧义词只作软证据，不能仅凭alias或宽泛叶子类目执行hard filter。
- 4号可参考evidence质量标记设置强弱：准确且明确的匹配可以使用较强证据；broad需要限幅或降权；ambiguous需要结合route判断。
- 5号在合并后运行完整评测，并根据新失败更新 `failure_taxonomy.md` 和正式实验台账。

## 不可靠类目的统一处理

- `Casual`：父类目作为商品类型，`casual`保留为style。
- `Sets`：与最近的有效父类目组合，例如 `Sleepwear Sets`、`Bikini Sets`。
- `Women`、`Men`：只表示audience，不是商品类型。
- `Westlake`、`Clothing`：叶子标签本身不能作为商品类型；标题只能提供软推断，不能确定时继续追问。
- 所有推断都保留原始catalog路径，便于复盘。

## 重建与检查

在仓库根目录运行：

```bash
python artifacts/build_lexicon.py
python -m unittest discover -s tests -p "test_lexicon.py" -v
```

也可以单独确认JSON是否合法：

```bash
python -c "import json; json.load(open('artifacts/lexicon.json', encoding='utf-8')); print('lexicon ok')"
```

提交前至少确认：

1. `lexicon.json` 可以正常读取，`version`和`updated_at`已更新。
2. `category_playbook.md` 与生成器输出一致。
3. 没有修改 `evaluator/`、`data/public_set.jsonl`、`data/catalog.jsonl` 或官方评测配置。
4. 没有API key、私有数据、public目标ASIN或单案例查表规则。
5. 如果字段结构发生变化，先通知依赖该结构的2/3/4号。

## 目录中的其他文件

- `experiments.md`：实验入口，按契约由5号维护、全组补充。
- `demo_script.md`：演示提纲，按契约由5号主写。

这两个文件不是1号的正式交付物，不应与词典版本一起随意改动。

## 本次README更新的影响

本次只补充交付说明，没有修改 `lexicon.json` 或 `starter/` 运行代码，因此不会改变检索、排序、追问逻辑和评测结果。
