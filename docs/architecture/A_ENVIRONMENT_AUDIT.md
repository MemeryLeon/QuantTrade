# A 阶段环境审计

审计日期：2026-07-02

任务包：A-BR1  
分支：`chore/A-environment-baseline`

## 结论

当前仓库已经进入 Git 管理，并已有项目级 Codex MCP 配置和项目虚拟环境。基础开发工具中，Git、Python 3.11、Node.js、npm、Docker CLI、Docker Compose 独立命令和 ripgrep 可用。Docker daemon 当前未运行或不可连接；PostgreSQL、Redis、MinIO、LEAN CLI、IBKR/TWS 本地命令入口尚未就绪。A1 需要补齐 Compose 服务、`.env.example`、后端依赖和统一安装命令。

## 审计结果

| 项目 | 状态 | 当前结果 | 说明 |
|---|---|---|---|
| Git | PASS | `git version 2.50.1.windows.1` | 仓库已初始化，当前分支为 `chore/A-environment-baseline`。 |
| Git 工作区 | WARN | 存在 `README_START_HERE.md` 未提交删除 | 该删除早于本轮 A0，未纳入 A0 提交；A2 前需要人工确认是否恢复。 |
| ripgrep | PASS | `ripgrep 15.0.0` | 全局用户入口为 `C:\Users\Saber_WrokStation02\AppData\Roaming\npm\rg.cmd`。普通沙箱中仍可能先解析到 Codex WindowsApps 占位入口。 |
| Python | PASS | `Python 3.11.9` | 符合后端 Python 3.11 基线。 |
| 项目虚拟环境 | PASS | `.venv`，`Python 3.11.9`，`pip 24.0` | 已在项目根目录创建，并被 `.gitignore` 排除。 |
| Node.js | PASS | `v22.18.0` | 满足现代前端工具链要求。 |
| npm | PASS | `10.9.3` | 当前项目 `.npmrc` 使用 `https://registry.npmmirror.com`。 |
| Docker CLI | WARN | `Docker version 29.6.1` | CLI 存在，但读取用户 Docker 配置时报 `Access is denied`。 |
| Docker daemon | FAIL | 无法连接 `npipe:////./pipe/docker_engine` | Docker Desktop/daemon 当前未运行或当前会话无法访问。 |
| Docker Compose | WARN | `docker-compose version v5.1.4` | 独立 `docker-compose` 可用；`docker compose version` 在当前环境返回 `unknown command`。后续命令需兼容此差异。 |
| PostgreSQL 客户端 | FAIL | `psql`、`pg_isready` 未找到 | A1 通过 Docker Compose 服务和健康检查补齐运行基线。 |
| Redis 客户端 | FAIL | `redis-cli` 未找到 | A1 通过 Docker Compose 服务和健康检查补齐运行基线。 |
| MinIO 客户端 | FAIL | `mc` 未找到 | A1 通过 Docker Compose 服务和健康检查补齐运行基线。 |
| LEAN CLI | FAIL | `lean` 未找到 | 后续 D 阶段前必须补齐正式 LEAN 运行链路；A 阶段只记录缺口。 |
| IBKR/TWS 本地入口 | FAIL | `ibkr`、`tws` 未找到 | F 阶段前补齐 Paper 连接环境；A 阶段只记录缺口。 |
| Make | FAIL | `make` 未找到 | A3 需要提供 Windows 可执行的统一命令入口或兼容方案。 |

## 关键缺口

1. Docker daemon 当前不可用，导致 PostgreSQL、Redis、MinIO 等服务无法启动验证。
2. 当前 Docker Compose 只能确认 `docker-compose` 独立命令可用，不能依赖 `docker compose` 子命令。
3. 仓库还没有 `backend/`、`frontend/`、`infra/`、`.env.example`、`Makefile` 和服务编排文件。
4. 后端生产依赖尚未声明 `pyarrow`，也没有 Parquet 往返测试。
5. 根目录 `README_START_HERE.md` 当前处于未提交删除状态，A2 根目录入口落位前需要处理。

## A1 建议处理

- 建立 `docker-compose.dev.yml`，优先提供 PostgreSQL、Redis、MinIO 健康检查。
- 新增 `.env.example`，只放示例值，不写真实密钥。
- 建立后端最小 Python 包和依赖声明，将 `pyarrow` 放入生产依赖。
- 添加 Parquet 往返测试，覆盖带时区时间、价格精度、成交量整数、空值和列类型。
- 在统一命令脚本里兼容 Windows 当前缺少 `make` 的现状。
