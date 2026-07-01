# 阶段 A：环境与仓库基线

## 阶段目标

检查并补齐开发环境、依赖、基础服务、目录、文档和统一命令。

## 去歧义执行规则

- 本文件中的“必须”表示不可跳过。
- 本文件中的“不得”表示禁止实现。
- 未写明的框架、字段、阈值或算法不得由 Codex 自行新增；需要时先记录问题并请求人工决定。
- 简单阶段使用一个分支；复杂阶段仅按本文件列出的分支任务包拆分。

## A-BR1 分支任务包

- **工作分支**：`chore/A-environment-baseline`
- **人工门禁**：普通；更换语言、框架、数据库、包管理器或核心依赖时必须先人工批准
- **状态来源**：`TASKS/INDEX.md`

## 分支级 Loop Engineering

1. 同步最新 `main`，创建本任务包指定分支。
2. 只按本文件中的任务顺序执行。
3. 每完成一个任务：
   - 运行相关测试；
   - 修复全部失败；
   - 更新任务状态；
   - 创建一次清晰 commit。
4. 不为分支内每个任务创建新分支或新 PR。
5. 分支全部任务完成后运行：
   - `make check`；
   - 需要时运行 `make test-integration`；
   - 需要时运行 `make e2e`。
6. 创建一个 PR。CI 失败时继续在原分支修复。
7. 按人工门禁规则合并。
8. 合并后停止，提示用户验收。
9. 只有用户回复“验收通过，继续”后，才将任务包标记 DONE 并领取下一项 READY。
10. 不允许因用户长时间未回复而自动视为验收通过。


### A0：现状审计与版本检查

**状态**：DONE

#### 工作内容

- 盘点 Git、Docker、Docker Compose、Python、Node、当前包管理器、PostgreSQL、Redis、MinIO、LEAN 与 IBKR 状态。
- 输出 `docs/architecture/A_ENVIRONMENT_AUDIT.md`，逐项标记 PASS、WARN、FAIL。
- 只审计和记录，不在 A0 大规模修改业务代码。

#### 任务验收

- 技术栈、版本和缺失项明确。
- 未确认的版本不得由 Codex自行选择。
- 相关测试通过后创建一次 commit。

### A1：补齐工具链与基础服务

**状态**：DONE

**完成记录**：已补齐 Compose 配置、`.env.example`、后端 `pyarrow`/`tzdata` 依赖和 Parquet 往返测试。WSL 启用后，`docker compose config` 通过，PostgreSQL、Redis、MinIO 基础服务均启动并通过健康检查；PyArrow 可导入，Parquet 往返测试通过。`make doctor` 和 `make bootstrap` 的统一命令入口按 A3 范围落位。

#### 工作内容

- 按 PROJECT_PLAN.md 修复不兼容版本并补齐 PostgreSQL、Redis、MinIO、Compose 健康检查。
- 补齐 `.env.example`，不得写入真实密钥。
- 保留现有包管理器；确需更换时停止并请求人工批准。
- 将 `pyarrow` 加入后端生产依赖；不得同时引入 fastparquet。
- `make bootstrap` 必须能够安装 PyArrow。

#### 任务验收

- `docker compose config` 通过。
- 基础服务健康检查通过。
- `make doctor` 验证 PyArrow 可导入。
- Parquet 往返测试保持时区、价格精度、成交量整数、空值和列类型。
- 相关测试通过后创建一次 commit。

### A2：目录与文档落位

**状态**：DONE

**完成记录**：已按项目规划补齐 `backend`、`frontend`、`lean`、`infra`、`docs`、`TASKS` 的目录落点和说明入口；根目录 `README_START_HERE.md` 已补充仓库入口与目录地图；新增 `docs/architecture/A_DIRECTORY_BASELINE.md` 记录 A2 目录基线。未创建业务接口、页面、数据库表、LEAN Parser 或统一命令，A3 范围保持独立。

#### 工作内容

- 对齐 backend、frontend、lean、infra、docs、TASKS 等目录。
- 放置 AGENTS.md、PROJECT_PLAN.md、任务索引、ADR、决策和验收记录。
- 已有代码采用小步迁移；不得同时搬迁目录和重写业务。

#### 任务验收

- 根目录入口完整。
- 现有应用仍可启动。
- 相关测试通过后创建一次 commit。

### A3：统一命令与基线冒烟

**状态**：DONE

**完成记录**：已建立 `Makefile`、Windows `make.cmd` 和 `scripts/dev.py`，提供 `doctor`、`bootstrap`、`dev`、`check`、`test`、`test-integration`、`e2e`、`down` 统一命令；补齐最小 FastAPI 健康接口、后端格式/类型/单元测试、前端 React TypeScript Vite 构建冒烟，以及 PostgreSQL、Redis、MinIO 健康冒烟；生成 `docs/acceptance/A_BASELINE.md`。

#### 工作内容

- 建立 make doctor/bootstrap/dev/check/test/test-integration/e2e/down。
- 完成 API、数据库、Redis、MinIO 和前端构建冒烟测试。
- 生成 `docs/acceptance/A_BASELINE.md`。

#### 任务验收

- `make doctor` 无关键 FAIL。
- `make check` 通过。
- 相关测试通过后创建一次 commit。

### 分支任务包完成条件

- 本任务包内全部任务完成。
- 完整检查通过。
- PR 描述包含范围、测试、风险、迁移、回滚和未完成项。
- 按门禁规则完成合并。
- 用户验收通过后才能领取下一任务包。
