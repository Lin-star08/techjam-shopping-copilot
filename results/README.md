# Experiment Results

本目录保存可追踪的正式实验结果。根目录 `results.json` 是本地 evaluator 的默认临时输出，已被 Git 忽略，不能作为版本归档。

命名约定：

- `v0-baseline.json`
- `v1-state.json`
- `v2-fusion.json`
- `v3-final.json`

正式结果必须能够映射到 `experiments.md` 中的 Git commit、配置和结论。不要手工修改指标；应直接保存 evaluator 输出。
