# 2号：V2.2 状态与对话后续

- 对 11 gained、7 lost 逐条比较问题顺序和用户回复，重点检查 turn 2–4 的路径差异。
- Intent `public_0004` rank 1→8、`public_0125` hit→miss 是优先回归案例。
- 保持 override、neutral、asked 语义不变；停止策略作为单独实验。
- 为 category playbook 匹配记录 selected category、question source 与 fallback reason。
