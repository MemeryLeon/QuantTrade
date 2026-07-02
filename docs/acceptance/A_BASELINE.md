# A 阶段基线验收

验收日期：2026-07-02

任务包：A-BR1
分支：`chore/A-environment-baseline`

## 范围

A3 建立统一命令和基线冒烟测试，覆盖：

- 后端最小 API 健康接口；
- PyArrow Parquet 往返测试；
- PostgreSQL、Redis、MinIO Docker Compose 健康检查；
- 前端 React、TypeScript、Vite 生产构建；
- Windows `make.cmd` 和通用 `Makefile` 命令入口。

## 统一命令

| 命令 | 当前实现 |
|---|---|
| `make doctor` | 检查 Python、PyArrow、Node、npm、Docker、Compose 配置和三项基础服务健康状态 |
| `make bootstrap` | 安装后端开发依赖和前端 npm 依赖，优先使用国内镜像 |
| `make dev` | 启动 PostgreSQL、Redis、MinIO |
| `make check` | 运行 doctor、后端格式检查、后端类型检查、后端测试、前端构建、基础服务冒烟 |
| `make test` | 运行后端格式检查、类型检查和 pytest |
| `make test-integration` | 校验 Compose 配置和 PostgreSQL、Redis、MinIO 健康状态 |
| `make e2e` | 当前 A 阶段以前端生产构建作为 e2e 基线冒烟 |
| `make down` | 停止本地 Compose 开发服务，默认保留数据卷 |

Windows PowerShell 当前未安装 GNU Make。可使用 `.\make.cmd check`；在 `cmd.exe` 中可直接运行 `make check` 调用仓库内 `make.cmd`。

## 验证结果

| 项目 | 结果 |
|---|---|
| `.\make.cmd doctor` | PASS |
| `.\make.cmd check` | PASS |
| `.\make.cmd test-integration` | PASS |
| `.\make.cmd e2e` | PASS |
| `cmd /c make check` | PASS |

## 冒烟覆盖

- API：`GET /health` 返回 `{"status": "ok"}`；
- 后端测试：2 个 pytest 用例通过；
- 后端格式：Ruff 通过；
- 后端类型：Mypy 通过；
- Parquet：保留时区、价格精度、成交量整数、空值和列类型；
- 数据库：PostgreSQL 容器健康状态为 `healthy`；
- 缓存：Redis 容器健康状态为 `healthy`；
- 对象存储：MinIO 容器健康状态为 `healthy`；
- 前端：`npm run build` 成功生成生产构建。

## 已知提示

当前 pytest 输出中存在一条第三方测试客户端弃用提示，来源于 FastAPI/Starlette 的 TestClient 依赖链，不影响 A 阶段基线通过。后续升级 FastAPI/Starlette 测试客户端方案时应一并消除该提示。

## 未纳入 A 阶段的内容

- 未创建业务数据库迁移；
- 未实现行情、策略、回测、交易或风控业务接口；
- 未生成 OpenAPI 前端客户端；
- 未接入 LEAN 正式运行链路；
- 未配置 CI，后续阶段按任务文件推进。
