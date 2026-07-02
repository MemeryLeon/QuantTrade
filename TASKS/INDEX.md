# QuantTrade 最终任务索引

## 状态

分支任务包：`BACKLOG → READY → IN_PROGRESS → DESIGN_REVIEW（可选） → OBSERVATION_RUNNING（F-BR3） → PR_OPEN → MERGED → USER_ACCEPTANCE → DONE`

分支内任务：`TODO → DOING → DONE`

- 初始只有 `A-BR1` 为 READY。
- B-BR1 在完成 B0、B1 草案后进入 DESIGN_REVIEW；人工确认后继续同一分支。
- 用户未回复“验收通过，继续”前，不得领取下一任务包。
- 不允许超时默认验收。

## 任务包

| 任务包 | 阶段 | 分支 | 包含任务 | 依赖 | 人工门禁 | 当前状态 |
|---|---|---|---|---|---|---|
| A-BR1 | A：环境与仓库基线 | `chore/A-environment-baseline` | A0, A1, A2, A3 | - | 普通；更换语言、框架、数据库、包管理器或核心依赖时必须先人工批准 | DONE |
| B-BR1 | B：架构与契约基线 | `feature/B-core-foundation` | B0, B1, B2, B3 | A-BR1 | 先设计评审，后实现；完成 B0、B1 草案后必须暂停并请求人工确认 | DONE |
| B-BR2 | B：架构与契约基线 | `feature/B-frontend-ci` | B4, B5 | B-BR1 | 普通；OpenAPI 破坏性变化必须人工批准 | DONE |
| C-BR1 | C：行情与基础看盘 | `feature/C-market-backend` | C0, C1, C2 | B-BR2 | 高风险：数据、时区、复权、快照和指标定义必须人工确认 | BACKLOG |
| C-BR2 | C：行情与基础看盘 | `feature/C-market-ui` | C3, C4 | C-BR1 | 普通；页面、数据警告和自选体验由用户验收 | BACKLOG |
| D-BR1 | D：LEAN 回测 MVP | `feature/D-lean-runtime` | D0, D1, D2 | C-BR2 | 高风险：LEAN Digest、资源限制、回测 Contract、费用和滑点需人工批准 | BACKLOG |
| D-BR2 | D：LEAN 回测 MVP | `feature/D-result-pipeline` | D3, D4 | D-BR1 | 高风险：Parser、Schema、Fixture 和金融结果语义必须人工确认 | BACKLOG |
| D-BR3 | D：LEAN 回测 MVP | `feature/D-backtest-ui` | D5, D6 | D-BR2 | 普通；最终复权、费用、滑点和交易结果由用户验收 | BACKLOG |
| E-BR1 | E：策略与组合工作台 | `feature/E-strategy-workbench` | E0, E1 | D-BR3 | 高风险：策略模板和报告金融语义需人工确认 | BACKLOG |
| E-BR2 | E：策略与组合工作台 | `feature/E-portfolio-experiments` | E2, E3 | E-BR1 | 高风险：组合估值、目标权重和实验语义需人工确认 | BACKLOG |
| F-BR1 | F：IBKR Paper、风控与对账 | `feature/F-ibkr-read-model` | F0, F1 | E-BR2 | 高风险：IBKR 字段映射、状态和时效定义需人工确认 | BACKLOG |
| F-BR2 | F：IBKR Paper、风控与对账 | `feature/F-risk-execution` | F2, F3 | F-BR1 | 高风险：下单、Fail Closed、风控、对账和 Kill Switch 必须人工批准 | BACKLOG |
| F-BR3 | F：IBKR Paper、风控与对账 | `feature/F-trading-ui-stability` | F4, F5 | F-BR2 | 高风险：阶段完成前必须人工验收 | BACKLOG |
| G-BR1 | G：受控实盘准备 | `feature/G-live-isolation-risk` | G0, G1 | F-BR3 | 最高风险：必须人工批准后合并 | BACKLOG |
| G-BR2 | G：受控实盘准备 | `feature/G-live-readiness` | G2, G3 | G-BR1 | 最高风险：Codex 不得自行给出 Go 决策 | BACKLOG |
| H-BR1 | H：因子研究 | `feature/H-factor-research-core` | H0, H1 | G-BR2 | 高风险：时间语义和未来数据防护需人工确认 | BACKLOG |
| H-BR2 | H：因子研究 | `feature/H-factor-lean-ui` | H2, H3 | H-BR1 | 高风险：目标权重和 LEAN 接入需人工确认 | BACKLOG |
| I-BR1 | I：机器学习研究 | `feature/I-ml-research-core` | I0, I1 | H-BR2 | 高风险：数据泄漏和时间切分需人工确认 | BACKLOG |
| I-BR2 | I：机器学习研究 | `feature/I-model-registry-lean` | I2, I3 | I-BR1 | 高风险：模型准入和 LEAN 推理需人工确认 | BACKLOG |
