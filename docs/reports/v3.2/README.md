# V3.2 置信候选扩展最终结果

## 结论

V3.2 在完整 200 条 public evaluator 上严格通过全部目标：

| 指标 | 目标 | Full结果 | Gate |
|---|---:|---:|---|
| HitRate@10 | > 0.98 | **1.000000** | PASS |
| MRR | > 0.95 | **0.969583** | PASS |
| MTTC | < 2.16 | **2.140000** | PASS |

所有 200 个目标均在 turn 4 以内命中。首次命中分布为 turn 1/2/3/4 = `46/101/32/21`，轮次总和 `428`；严格阈值允许的最大整数总和是 `431`，因此保留 3 轮余量。最终排位为 rank 1/2/3/4 = `189/8/2/1`。

## 版本改动

V3.2 保留 V3.1 的 catalog-driven Boundary 问题选择，并新增一个受限的候选扩展 Gate：

```text
已经收到至少一次具体回答
AND exact-signature 候选数为 2..10
→ 最多返回 Top 3

已经收到至少两次具体回答
OR Boundary 已拒绝开放问题
→ 允许完整 Top 10

否则
→ 只返回 Top 1
```

该策略使小型同签名组早一轮命中，同时避免 V3 早期无条件 Top 10 导致的 MRR 大幅下降。弱画像重排在 development 没有缩短轮次，已在冻结前删除。

线上实现只读取 catalog 商品字段、当前会话消息、对话状态和匿名 profile。没有读取或匹配 public sample ID、ground truth、目标 ASIN或 evaluator 内部状态。

## 分割结果

| 范围 | N | Hit@10 | MRR | MTTC | 三项Gate |
|---|---:|---:|---:|---:|---|
| Development | 150 | 1.000000 | 0.970556 | 2.133333 | PASS |
| Internal holdout | 50 | 1.000000 | 0.966667 | 2.160000 | MTTC等于阈值 |
| Full public | 200 | 1.000000 | 0.969583 | 2.140000 | **PASS** |

目标要求的是 full public evaluator；它严格通过。Internal holdout 单独只有 50 条，MTTC 恰好等于 `2.16`，按严格小于规则不通过，已如实保留，未据此继续调参。

## Full 场景指标

| Scenario | N | Hit@10 | MRR | MTTC |
|---|---:|---:|---:|---:|
| Buying | 80 | 1.000000 | 0.978125 | 1.475000 |
| Browsing | 80 | 1.000000 | 0.966667 | 2.137500 |
| Intent Override | 30 | 1.000000 | 0.966667 | 3.666667 |
| Boundary | 10 | 1.000000 | 0.933333 | 2.900000 |

相对 V3 full，V3.2 的 Hit 保持 `1.0`，MRR 从 `0.977083` 调整为 `0.969583`，MTTC 从 `2.175000` 降到 `2.140000`，共节省 7 个首次命中轮次。MRR 的受控交换为 `-0.007500`，仍高于目标 `0.019583`。

## 复现

```bash
python3 -m unittest discover -s tests -q
python3 -m tools.run_goal_workflow \
  --split development \
  --output results/v3.2-confidence-development.json
python3 -m tools.run_goal_workflow \
  --split full \
  --open-holdout \
  --output results/v3.2-confidence-full.json \
  --skip-tests
python3 -m tools.run_goal_workflow \
  --split holdout \
  --open-holdout \
  --output results/v3.2-confidence-holdout.json \
  --skip-tests
```

工作流执行单元测试、固定切分、线上代码 public-label literal 审计、正式 evaluator，以及严格 `> / <` 目标判断。数据和结果 SHA、测试数、成本与审计状态见 `results/v3.2-confidence-evidence.json`。

## 测试与限制

- 144/144 tests passed。
- `git diff --check` passed。
- 无外部模型、API、网络、token 或推理成本。
- Signature route 依赖比赛协议中“约束由 catalog metadata 生成”的约定；若私有生成器改变字段清洗或披露顺序，需要重新验证。
- Holdout MTTC 没有单独严格过线，说明 full `2.14` 的余量不大；后续版本必须保持冻结 Gate，不能以扩大早期列表换取无约束的 MTTC 改善。
