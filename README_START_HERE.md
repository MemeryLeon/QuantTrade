# QuantTrade 使用入口

## 当前仓库入口

本仓库按 `PROJECT_PLAN.md` 和 `TASKS/INDEX.md` 推进，当前只允许在任务文件指定的分支内按编号小步完成任务。

优先阅读：

1. `AGENTS.md`：Codex 工作规则和项目红线；
2. `PROJECT_PLAN.md`：总体范围、技术栈、目录和阶段定义；
3. `TASKS/INDEX.md`：分支任务包顺序和门禁；
4. `TASKS/A_ENVIRONMENT_BASELINE.md`：当前 A 阶段任务。

## 目录地图

- `backend/`：后端 Python 包、应用分层目录、迁移和测试；
- `frontend/`：前端源码和测试落点，实际构建脚本在 A3 建立；
- `lean/`：LEAN 配置、模板、解析器、兼容清单和 Golden Fixture；
- `infra/`：Compose 辅助文件、Nginx 和监控配置落点；
- `docs/`：ADR、架构说明、数据语义、决策、验收和运维文档；
- `TASKS/`：阶段任务文件和任务索引；
- `templates/`：分支任务和 PR 描述模板。

## 第一次使用流程

1. 将本任务包复制到 QuantTrade 仓库根目录。
2. 让 Codex 读取：
   - `AGENTS.md`
   - `PROJECT_PLAN.md`
   - `TASKS/INDEX.md`
   - `TASKS/A_ENVIRONMENT_BASELINE.md`
3. 首次只执行 `A-BR1`。
4. A0～A3 在同一个 `chore/A-environment-baseline` 分支完成。
5. 分支全部完成后只创建一个 PR。
6. 合并后由用户验收。
7. 用户回复“验收通过，继续”后，领取 B-BR1。

## 首次启动提示词

请读取 `AGENTS.md`、`PROJECT_PLAN.md`、`TASKS/INDEX.md` 和当前阶段任务文件。

只领取第一个依赖已完成且状态为 READY 的分支任务包。
从最新 main 创建任务文件指定的分支，在同一个分支内按编号完成全部任务。
每个任务完成后运行相关测试并创建一次 commit。
不要为每个任务新建分支或 PR。
分支任务包完成后运行完整检查、创建一个 PR，并按人工门禁处理。
合并后停止并提示我验收。
只有我回复“验收通过，继续”后，才将当前任务包标记 DONE 并领取下一项。
不得因为我长时间未回复而默认验收通过。
F5 进入 Paper 观察期后，必须等待系统真实累计至少 3 个实际交易日数据，不得伪造观察结果。
任何未在文档中明确的框架、字段、阈值或金融定义，不得自行决定，必须先提出问题。

## 用户回复

- 通过：`验收通过，继续`
- 不通过：`验收不通过：<问题>`
- 暂停：`暂停推进`
- 批准设计评审：`B 核心设计评审通过，继续`
