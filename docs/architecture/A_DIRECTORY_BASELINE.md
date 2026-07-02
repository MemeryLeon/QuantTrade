# A 阶段目录基线

记录日期：2026-07-02

任务包：A-BR1
分支：`chore/A-environment-baseline`

## 目标

A2 只建立后续阶段需要的目录落点和文档入口，不创建业务接口、页面、数据库表、交易逻辑或回测逻辑。

## 根目录入口

| 路径 | 用途 | 当前状态 |
|---|---|---|
| `AGENTS.md` | Codex 工作规则和项目红线 | 已落位 |
| `PROJECT_PLAN.md` | 项目计划、技术栈、目录和阶段定义 | 已落位 |
| `README_START_HERE.md` | 仓库使用入口和目录地图 | 已落位 |
| `TASKS/INDEX.md` | 分支任务包顺序和门禁 | 已落位 |
| `.env.example` | 本地开发示例配置，不包含真实密钥 | 已落位 |
| `docker-compose.dev.yml` | 本地 PostgreSQL、Redis、MinIO 基础服务 | 已落位 |

## 代码与运行目录

| 路径 | 用途 | A2 处理 |
|---|---|---|
| `backend/app/api/v1/` | 后端 API 路由落点 | 新增说明入口 |
| `backend/app/application/` | 应用服务和用例编排落点 | 新增说明入口 |
| `backend/app/domains/` | 纯领域模型、规则和端口落点 | 新增说明入口 |
| `backend/app/infrastructure/` | 数据库、存储、外部服务和引擎适配器落点 | 新增说明入口 |
| `backend/app/contracts/` | 稳定请求、响应和集成契约落点 | 新增说明入口 |
| `backend/app/workers/` | Celery 和长任务入口落点 | 新增说明入口 |
| `backend/app/core/` | 配置、日志和进程级工具落点 | 新增说明入口 |
| `backend/alembic/` | 数据库迁移落点 | 新增说明入口 |
| `frontend/src/` | 前端源码落点 | 新增说明入口 |
| `frontend/tests/` | 前端测试落点 | 新增说明入口 |
| `lean/config/` | LEAN 运行配置落点 | 新增说明入口 |
| `lean/templates/` | LEAN 模板落点 | 新增说明入口 |
| `lean/parsers/` | LEAN 结果解析器落点 | 新增说明入口 |
| `lean/compatibility/` | LEAN 兼容清单落点 | 已存在示例清单 |
| `lean/golden-fixtures/` | Golden Fixture 落点 | 新增说明入口 |
| `infra/compose/` | Compose 辅助配置落点 | 新增说明入口 |
| `infra/nginx/` | Nginx 配置落点 | 新增说明入口 |
| `infra/monitoring/` | 监控配置落点 | 新增说明入口 |

## 文档目录

| 路径 | 用途 | 当前状态 |
|---|---|---|
| `docs/adr/` | 重大架构和依赖决策 | 已落位 |
| `docs/architecture/` | 架构审计、设计评审和目录基线 | 已落位 |
| `docs/data/` | 数据语义、日历、快照和质量规则 | 已落位 |
| `docs/decisions/` | 轻量决策记录 | 已落位 |
| `docs/acceptance/` | 阶段验收记录 | 已落位 |
| `docs/runbooks/` | 运维和本地环境操作说明 | 已落位 |

## 范围边界

- 未创建前端业务页面或 API 调用；
- 未创建数据库表或迁移脚本；
- 未创建 LEAN Parser、策略模板或兼容正式清单；
- 未新增运行命令，统一命令由 A3 完成；
- 未更换语言、框架、数据库、包管理器或核心依赖。
