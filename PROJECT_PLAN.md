# QuantTrade Platform 开发规划书

## 1. 项目定位

QuantTrade Platform 是一个面向个人使用的中文量化投研交易工作台，目标是建立：

- 数据来源和时间语义清楚；
- 回测可以复现；
- 策略版本不可随意覆盖；
- Paper 与 Live 严格隔离；
- 交易流程可审计；
- 后续可扩展因子研究和机器学习；
- 代码由 Codex 按阶段、分支任务包和人工门禁持续开发。

当前项目是**单用户、私有部署**。当前阶段不建设注册、组织、角色、多租户和多设备同步系统。

## 2. 当前范围与明确排除项

### 2.1 当前建设范围

1. A 股行情和基础看盘；
2. 参数化策略模板和版本管理；
3. LEAN 标准回测；
4. 回测分析和组合管理；
5. IBKR Paper；
6. 基础风控、对账、审计；
7. 受控实盘准备；
8. 系统稳定后扩展因子和机器学习。

### 2.2 当前明确不做

以下内容在对应阶段前不得创建空接口、空页面、空表或占位业务代码：

- 多用户、组织、权限中心；
- 多数据源自动切换；
- 通用可视化策略编辑器；
- Agent 自动交易；
- 自研回测、撮合或交易执行内核；
- 因子研究和机器学习业务表；
- 未经准入的 Live 自动交易；
- 用 JSONB 长期代替正式领域关系。

## 3. 核心架构决策

### 3.1 LEAN 是唯一正式量化引擎

LEAN 负责：

- 历史时间推进；
- 回测；
- Universe 和证券订阅；
- 手续费、滑点和成交模拟；
- 现金、持仓和组合；
- 参数实验；
- Paper 和 Live 接入。

QuantTrade 不开发第二套正式回测引擎。

### 3.2 LEAN 防腐层

LEAN 必须通过以下边界接入：

```text
Application
→ IBacktestEngine
→ LeanBacktestAdapter
→ LeanWorker
→ LEAN Docker
→ LeanResultParser
→ QuantTrade Domain Model
```

禁止以下层直接依赖 LEAN 原始路径、字段、类型或 JSON：

- FastAPI Router；
- React 组件；
- Domain；
- 通用数据库业务表。

### 3.3 模块化单体

当前后端采用模块化单体。独立运行单元只有：

- FastAPI；
- 普通 Celery Worker；
- LEAN 专用 Celery Worker；
- PostgreSQL；
- Redis；
- MinIO；
- LEAN Docker 容器。

不提前拆微服务。

### 3.4 依赖方向

```text
API → Application → Domain ← Infrastructure
```

硬性规则：

- Domain 不导入 FastAPI、SQLAlchemy、Redis、AKShare、LEAN 或 IBKR SDK；
- Router 只调用 Application Service；
- Application 只依赖 Domain Port；
- Infrastructure 实现 Domain Port；
- 前端只调用生成的 API Client、Service 或业务 Hook。

## 4. 技术栈

### 4.1 前端

- React 18+；
- TypeScript 5.x；
- Vite；
- React Router；
- TanStack Query；
- Zustand，仅用于 UI 和本地偏好；
- Lightweight Charts；
- ECharts；
- openapi-typescript；
- openapi-fetch；
- Vitest；
- React Testing Library；
- Playwright。

### 4.2 后端

- Python 3.11；
- FastAPI；
- Pydantic v2；
- SQLAlchemy 2.x；
- Alembic；
- PostgreSQL；
- Redis；
- Celery；
- MinIO；
- PyArrow，唯一 Parquet 读写实现；
- Pytest；
- Ruff；
- MyPy 或 Pyright；
- JSON 结构化日志。

### 4.3 核心与交易

- QuantConnect LEAN；
- LEAN Docker；
- AKShare，初期唯一行情源；
- IBKR Paper；
- IBKR Live，仅通过准入后启用。

### 4.4 运维

- Docker Compose；
- GitHub Actions；
- Nginx；
- Prometheus + Grafana；
- OpenTelemetry 或 Sentry。

不得在未创建 ADR 并获得人工批准前更换核心框架、语言或依赖管理器。

## 5. 总体目录

```text
quanttrade-platform/
├─ AGENTS.md
├─ PROJECT_PLAN.md
├─ README_START_HERE.md
├─ TASKS/
├─ backend/
│  ├─ app/
│  │  ├─ api/v1/
│  │  ├─ application/
│  │  ├─ domains/
│  │  ├─ infrastructure/
│  │  ├─ contracts/
│  │  ├─ workers/
│  │  └─ core/
│  ├─ tests/
│  ├─ alembic/
│  └─ pyproject.toml
├─ frontend/
│  ├─ src/
│  ├─ tests/
│  └─ package.json
├─ lean/
│  ├─ templates/
│  ├─ config/
│  ├─ parsers/
│  ├─ compatibility/
│  └─ golden-fixtures/
├─ infra/
│  ├─ compose/
│  ├─ nginx/
│  └─ monitoring/
├─ docs/
│  ├─ adr/
│  ├─ architecture/
│  ├─ data/
│  ├─ decisions/
│  ├─ acceptance/
│  └─ runbooks/
├─ docker-compose.dev.yml
├─ docker-compose.prod.yml
├─ .env.example
└─ Makefile
```

已有项目结构不一致时，先建立迁移计划。不得一次性搬迁大量代码并同时修改业务逻辑。

## 6. 环境与统一命令

项目必须提供：

```text
make doctor
make bootstrap
make dev
make check
make test
make test-integration
make e2e
make down
```

含义：

- `doctor`：检查版本、端口、Docker、配置和依赖；
- `bootstrap`：安装依赖、创建必要目录和初始化开发环境；
- `dev`：启动开发环境；
- `check`：格式、静态类型、单元测试、迁移、OpenAPI 漂移和前端构建；
- `test-integration`：PostgreSQL、Redis、MinIO、Celery、LEAN、AKShare、IBKR Paper 集成测试；
- `e2e`：关键用户流程；
- `down`：安全停止开发环境。

命令内部适配仓库当前包管理方式。不得为了实现统一命令擅自更换包管理器。

Parquet 规则：

- 后端生产依赖必须包含 `pyarrow`；
- 不得同时引入 `fastparquet` 作为第二实现；
- `make bootstrap` 必须安装 PyArrow；
- `make doctor` 必须验证 PyArrow 可导入；
- 环境基线必须完成一次 Parquet 写入、读取和 Schema 保真测试；
- 测试至少覆盖带时区时间戳、价格精度、成交量整数、空值和列类型。

## 7. 行情数据与 AKShare 健康治理

### 7.1 数据接口

```python
class IDataProvider(Protocol):
    async def search_instruments(self, query: str) -> list[Instrument]: ...
    async def get_bars(self, request: BarsRequest) -> BarsResult: ...
    async def get_quote(self, instrument_id: str) -> Quote: ...
    async def get_calendar(
        self,
        market: str,
        start: date,
        end: date,
    ) -> TradingCalendar: ...

class IDataProviderHealth(Protocol):
    async def get_health(self, provider: str) -> DataSourceHealth: ...
```

`IDataProviderHealth` 与 `IDataProvider` 分离，避免行情接口承担熔断状态管理。

### 7.2 健康状态

```text
healthy
degraded
unavailable
recovering
```

健康模型至少包含：

- provider；
- status；
- checked_at；
- consecutive_failures；
- last_success_at；
- last_error_code；
- stale_cache_available；
- stale_age_seconds。

阈值必须通过配置定义，不得散落在业务代码中。

### 7.3 降级规则

仅**行情展示页面**允许在数据源异常时返回旧缓存，并必须同时返回：

```text
is_delayed = true
quality_flags 包含 STALE_CACHE 和 PROVIDER_DEGRADED
as_of = 实际数据时间
stale_age_seconds = 缓存年龄
```

以下场景禁止使用未明确确认的新鲜数据：

- 创建新的正式数据快照；
- 生成新的正式回测；
- Paper 或 Live 风控；
- 交易下单判断。

数据源异常时，前端必须显示全局警告横幅。不得仅显示角落图标。

当正式回测因数据源状态被拒绝时，API 使用 `DATA_SOURCE_DEGRADED` 或 `DATA_SOURCE_UNAVAILABLE`，`details` 至少包含：

- provider；
- provider_status；
- last_success_at；
- stale_age_seconds；
- data_snapshot_creation_allowed；
- formal_backtest_allowed。

前端回测提交页必须：

- 在已知数据源为 degraded 或 unavailable 时禁用正式回测提交；
- 显示数据源状态、最后成功时间和缓存年龄；
- 即使前端状态过期，仍以服务端拒绝结果为最终门禁。

### 7.4 数据质量标记

最少支持：

```text
MISSING_BARS
DUPLICATE_BARS
OUT_OF_ORDER
STALE_CACHE
PROVIDER_DEGRADED
PROVIDER_UNAVAILABLE
ADJUSTMENT_FACTOR_MISSING
CALENDAR_MISMATCH
TIMEZONE_AMBIGUOUS
```

禁止静默填补缺失数据。

## 8. 数据快照与复权因子

### 8.1 data_snapshots

PostgreSQL 必须创建 `data_snapshots` 元数据表，至少包含：

- id；
- source_id；
- market；
- instrument_scope；
- resolution；
- adjustment；
- start_time；
- end_time；
- timezone；
- calendar_version；
- schema_version；
- object_uri；
- checksum；
- row_count；
- created_at。

实际 OHLCV、公司行动和复权因子文件存 MinIO，优先使用 Parquet。不得将大规模行情写入 PostgreSQL。

### 8.2 复权因子

复权因子处理路径：

```text
数据源原始因子
→ MinIO 持久快照
→ data_snapshots 元数据与校验值
→ Redis 性能缓存
→ 内存批量应用
```

Redis 不是复现依据。Redis 丢失后必须能从 MinIO 和元数据恢复。

Phase 1 先支持首次请求加载和缓存。每日收盘预热属于后续性能增强，不是首次验收前置条件。

## 9. 时间和未来数据规则

- 内部统一 UTC；
- 证券保留交易所时区；
- API 返回带时区 ISO 8601；
- 禁止无时区 datetime；
- 数据必须区分观察时间、发布时间、系统可用时间和策略生效时间；
- 因子和机器学习必须使用系统可用时间防止未来数据；
- 数据时间语义不明确时，任务必须失败，不得猜测。

## 10. 指标模块

正式指标由后端或 LEAN 计算。前端只渲染。

首批指标：

- SMA；
- EMA；
- MACD；
- RSI；
- 布林带；
- ADX。

每个指标必须固定：

- 数学定义；
- 默认参数；
- 输入价格；
- 起始值规则；
- 缺失值规则；
- 输出单位；
- Golden 样本。

不得直接依赖第三方库默认参数而不做封装。

## 11. 策略版本

```text
draft
→ validated
→ backtested
→ paper_approved
→ live_approved
→ archived
```

规则：

- Strategy 是逻辑身份；
- StrategyVersion 是不可变执行版本；
- 源码、依赖、参数 Schema 随版本固化；
- 已参与回测、Paper 或 Live 的版本不得覆盖修改；
- 修改只能创建新版本。

## 12. 回测请求与复现

BacktestRequest 必须包含：

- strategy_version_id；
- instruments；
- start_date；
- end_date；
- resolution；
- adjustment；
- initial_capital；
- base_currency；
- benchmark；
- parameters；
- commission_model；
- slippage_model；
- data_snapshot_id。

每次回测必须保存：

- 策略版本；
- 策略产物 Digest；
- 参数快照；
- 数据快照；
- 数据源；
- 复权；
- 日历版本；
- LEAN 版本；
- LEAN 镜像 Digest；
- Parser 版本；
- Parser Artifact Digest；
- 原始输出 Schema 版本；
- Fixture 版本；
- 平台 Git SHA；
- 平台 Source Tree Digest；
- 后端镜像 Digest；
- 手续费；
- 滑点；
- 开始和结束时间。

缺少适用环境中的任一必需字段时，不得标记为“可复现”。

### 12.1 源代码身份与 Dirty Workspace

本地开发环境中的正式 LEAN 回测必须在创建任务前检查 Git 工作区：

```text
tracked 文件有未提交修改
或存在未纳入明确忽略规则的 untracked 文件
→ 拒绝创建正式回测
→ code = WORKSPACE_DIRTY
```

前端提示：

```text
当前代码存在未提交修改，无法创建可复现回测。请先提交代码变更。
```

本地身份至少保存：

- platform_git_sha；
- platform_source_tree_digest；
- git_workspace_clean = true。

部署或 CI 环境可能不包含 `.git`，此时不得执行运行时 `git status`。必须使用不可变构建身份：

- backend_image_digest；
- build_git_sha；
- platform_source_tree_digest；
- source_identity_mode = immutable_build。

无法证明本地工作区干净，或无法取得不可变构建身份时，使用 `SOURCE_IDENTITY_UNAVAILABLE` 拒绝正式回测。

`MockBacktestEngine` 的开发测试不受 Dirty Workspace 门禁限制，但不得将其结果标记为正式 LEAN 回测。

## 13. LEAN Parser 兼容绑定

必须存在：

```text
lean/compatibility/manifest.yaml
```

每条兼容记录至少绑定：

```text
lean_image_digest
parser_version
parser_artifact_digest
raw_output_schema_version
fixture_version
```

`parser_artifact_digest` 是 Parser 可执行代码或构建产物的 SHA-256，不依赖运行环境中是否存在 `.git`。

版本规则：

- LEAN 原始输出字段或结构变化时，升级 `raw_output_schema_version`；
- Parser 代码发生任何变化时，`parser_artifact_digest` 必须变化，并评估是否升级 `parser_version`；
- Parser 输出数值、舍入、字段映射或预期结果变化时，必须升级 `fixture_version`；
- 仅修复 Parser 实现但不改变 LEAN 原始输出时，不得错误升级 `raw_output_schema_version`。

执行规则：

- 未登记组合不得执行正式回测；
- LEAN Digest 改变时，兼容清单必须更新；
- Parser Digest 与兼容清单不一致时拒绝执行；
- CI 必须运行 Schema Compatibility Test；
- Parser 目录或构建产物变化时必须运行 Golden Fixture；
- 兼容清单不匹配时阻止合并；
- 历史回测记录必须保存当时的 Parser Artifact Digest；
- 前端永远不读取 LEAN 原始输出。

## 14. Celery 与 LEAN 资源隔离

队列分为：

```text
default
lean_backtest
```

初始部署规则：

- 普通任务进入 `default`；
- LEAN 回测只进入 `lean_backtest`；
- LEAN Worker 并发数固定为 1；
- `worker_prefetch_multiplier = 1`；
- 一个 Worker Slot 同时只运行一个 LEAN 容器；
- 扩容通过增加 Worker 实例完成，不提高单实例并发；
- 设定全局运行任务数、单用户运行任务数和最大排队数；
- 容器 CPU、内存、时限和输出上限必须同时生效。

`rate_limit` 仅控制启动速率，不等于队列容量控制。

## 15. Job 模型

状态：

```text
queued
preparing_data
starting_engine
running
parsing_result
succeeded
failed
cancelled
timed_out
```

必须支持：

- 状态；
- 进度；
- 日志；
- 取消；
- 超时；
- 有限重试；
- 错误分类；
- 产物关联；
- 审计。

FastAPI BackgroundTasks 不得承担正式回测或数据同步。

## 16. backtest_runs 扩展字段

`backtest_runs` 可增加：

```text
run_metadata JSONB
run_metadata_schema_version
```

用途仅限：

- 用户标签；
- 运行来源；
- 实验备注；
- 临时兼容元数据。

限制：

- 必须有 Pydantic Schema；
- 禁止保存无法校验的任意结构；
- 禁止长期用 JSONB 替代 factor、model、dataset 等正式外键；
- H/I 阶段成熟后，正式关系通过 Alembic 建立。

字段名称使用 `run_metadata`，避免与 SQLAlchemy 的 `metadata` 概念冲突。

## 17. 前端规则

### 17.1 API

- `generated/` 只由 OpenAPI 生成；
- 只有一个底层 API Client；
- Service 封装业务请求；
- 组件禁止直接 fetch、axios 或拼 URL；
- 禁止组件判断 AKShare、LEAN 或 IBKR 实现。

### 17.2 状态

TanStack Query：

- 行情；
- 回测；
- 组合；
- 订单；
- 账户；
- 缓存和刷新。

Zustand：

- 当前标的；
- 页面布局；
- 图表状态；
- 用户展示偏好。

### 17.3 自选列表

Phase 1 使用：

```text
LocalStorage
+ JSON 导出
+ JSON 导入
```

明确规则：

- Key 使用版本号，例如 `quanttrade.watchlist.v1`；
- 导入 JSON 必须校验 Schema；
- UI 必须注明“仅保存在当前浏览器”；
- 当前不创建 watchlists、watchlist_items 或多用户同步接口。

## 18. 组合模块

实现：

- 组合；
- 现金；
- 净值；
- 持仓快照；
- 策略版本关系；
- 基准；
- 目标权重。

目标权重只用于研究或后续交易意图生成，不得直接绕过 RiskService 下单。

## 19. IBKR Broker 状态与风控

### 19.1 Broker Gateway 异常契约

```python
class BrokerStateResult(BaseModel):
    status: BrokerStateStatus
    state: BrokerState | None
    as_of: datetime | None
    error_code: str | None
    error_message: str | None
    trace_id: str

class IBrokerGateway(Protocol):
    async def get_state(self) -> BrokerStateResult: ...
```

`BrokerStateStatus` 至少包含：

```text
AVAILABLE
STALE
UNAVAILABLE
RECONCILIATION_REQUIRED
```

以下预期运行异常必须由 Infrastructure 转换为 `BrokerStateResult`，不得直接抛给 RiskService：

- 连接断开；
- 超时；
- 限流；
- 会话失效；
- 券商维护；
- 状态暂时不完整。

未预期的代码、配置或数据损坏异常不得静默吞掉。Application 边界必须记录 Trace ID，并对交易流程执行 Fail Closed。

RiskService 只处理类型化状态，不直接捕获 IBKR SDK 网络异常。

### 19.2 状态新鲜度

Broker 状态必须包含：

- broker_state_as_of；
- broker_state_status；
- max_state_staleness_seconds；
- connection_status。

### 19.3 风控分类

本地确定型：

- 订单格式；
- 禁止名单；
- 单笔最大金额；
- 静态标的限额；
- 交易时段。

Broker 状态依赖型：

- 可用资金；
- 当前仓位；
- 未成交订单数；
- 每日盈亏；
- 组合总敞口。

### 19.4 Fail Closed

状态依赖型规则遇到以下情况时必须拒绝：

- IBKR 断线；
- 状态超过最大允许时效；
- 对账未完成；
- Broker 状态未知；
- 数据不一致未处理。

错误：

```text
code = BROKER_STATE_UNKNOWN
result = rejected
```

Paper 和 Live 都采用 Fail Closed；Live 不允许通过配置关闭该规则。

## 20. 交易流程

```text
Strategy Signal
→ TradeIntent
→ RiskCheck
→ Approval
→ BrokerOrder
→ OrderEvent
→ Fill
→ Reconciliation
```

订单必须携带 `idempotency_key`。

网络重试、API 重试或 Worker 重启不得产生重复订单。

## 21. Paper 观察期

Phase F 技术观察期至少覆盖连续 3 个实际交易日。交易日按目标市场交易日历计算，周末和休市日不计入。

每个有效观察日必须生成日终对账结果，三日汇总报告至少包含：

- 观察起止时间和有效交易日；
- IBKR 连接中断次数和重连结果；
- 订单、成交、撤单和风控拒绝数量；
- 未解决订单差异 = 0；
- 未解决成交差异 = 0；
- 未解决持仓差异 = 0；
- 重复订单数 = 0；
- 未解决严重异常数 = 0；
- Kill Switch 演练通过；
- 断线恢复演练通过。

报告保存为：

```text
docs/acceptance/F_PAPER_OBSERVATION_REPORT.md
```

Codex 负责实现记录、汇总和检查功能，但不得假装等待或伪造 3 个交易日数据。系统实际运行达到要求后，Codex 再汇总报告，由用户作最终阶段验收。

## 22. 安全与环境隔离

环境：

```text
Development
Test
Paper
Live
```

Live 必须：

- 独立部署；
- 独立凭证；
- 独立权限；
- 独立数据库或严格独立 Schema；
- 独立 Redis；
- 默认关闭；
- 人工准入；
- 人工审批；
- Kill Switch 演练。

单个环境变量不得直接开启 Live。

## 23. 当前数据库表

当前阶段允许创建：

- instruments；
- data_sources；
- data_snapshots；
- strategies；
- strategy_versions；
- backtest_runs；
- backtest_metrics；
- backtest_trades；
- portfolios；
- portfolio_positions；
- broker_accounts；
- orders；
- fills；
- risk_rules；
- audit_logs；
- job_runs。

当前不创建：

- users；
- watchlists；
- factors；
- datasets；
- features；
- models；
- experiments。

单用户身份在审计中使用固定 `local_operator`。未来引入认证时再增加用户表并迁移。

## 24. 存储职责

### PostgreSQL

结构化业务数据、关系、状态和元数据。

### Redis

- Celery；
- 任务进度；
- 最新行情缓存；
- 复权因子性能缓存；
- 锁；
- 幂等；
- 限流。

所有 Key 必须有命名、TTL、容量和新鲜度语义。

### MinIO

- LEAN 原始输出；
- 日志；
- 策略包；
- 数据快照；
- 复权因子快照；
- 报告。

## 25. API 错误码

至少包括：

```text
VALIDATION_ERROR
DATA_NOT_FOUND
DATA_SOURCE_DEGRADED
DATA_SOURCE_UNAVAILABLE
STALE_DATA_NOT_ALLOWED
DATA_SNAPSHOT_INVALID
WORKSPACE_DIRTY
SOURCE_IDENTITY_UNAVAILABLE
ENGINE_START_FAILED
ENGINE_TIMEOUT
ENGINE_SCHEMA_INCOMPATIBLE
BACKTEST_FAILED
BROKER_UNAVAILABLE
BROKER_STATE_UNKNOWN
RISK_REJECTED
DUPLICATE_ORDER
PERMISSION_DENIED
```

错误必须返回：

- code；
- message；
- trace_id；
- details。

## 26. 测试

### 单元测试

- Domain；
- 指标；
- 风控；
- Parser；
- 参数；
- 状态机。

### 契约测试

Mock 与 LEAN 使用同一 IBacktestEngine 契约。

IBrokerGateway 契约测试必须验证：

- 预期网络异常转换为类型化 `BrokerStateResult`；
- RiskService 不直接接收 IBKR SDK 异常；
- 未预期异常在 Application 边界 Fail Closed。

### Schema Compatibility Test

验证：

- LEAN Digest；
- Parser；
- Raw Schema；
- Fixture。

### Golden Fixture

固定数据、策略、费用、滑点和预期结果。

Parser Artifact Digest 变化时必须重新运行；若解析后的预期结果变化，必须升级 Fixture 版本。

### 集成测试

- PostgreSQL；
- Redis；
- MinIO；
- Celery；
- LEAN；
- AKShare；
- IBKR Paper。

### E2E

- 搜索和 K 线；
- 策略版本；
- 回测；
- 结果；
- 报告；
- Paper 下单；
- 风控拒绝；
- 撤单；
- 对账。

## 27. CI

每次 PR：

```text
后端格式
后端类型
后端单元测试
数据库迁移
OpenAPI 生成和漂移
前端类型
前端单元测试
契约测试
Schema Compatibility Test
Docker 构建
基础安全扫描
```

LEAN Digest、Parser 或 Fixture 相关文件变化时，必须运行 Golden Fixture。

## 28. Codex Loop Engineering

任务结构：

```text
项目计划
→ 阶段 A、B、C……
→ 分支任务包
→ 分支内任务 A0、A1……
→ 一个 PR
→ main
→ 用户验收
→ 下一分支任务包
```

规则：

- 简单阶段一个分支；
- 复杂阶段按稳定边界拆成少量分支；
- 同一分支内完成多个连续任务；
- 每完成一个任务运行相关测试并提交 commit；
- 分支完成后运行完整检查并创建一个 PR；
- 高风险分支必须人工批准；
- 合并后等待用户验收；
- 用户回复“验收通过，继续”后才能领取下一任务包；
- 不使用“超时默认同意”；
- Codex 不得后台自行推进。

## 29. B 阶段设计评审门禁

B-BR1 不拆分新分支，但必须包含中途设计评审：

```text
完成 B0、B1 设计草案
→ 生成 docs/architecture/B_CORE_DESIGN_REVIEW.md
→ 用户确认 Domain Ports、核心 Contract、首个迁移设计
→ Codex 继续 B2、B3
```

设计评审通过后，B2、B3 属于已批准设计的实现。最终仍需 CI、PR 和用户功能验收。

## 30. 里程碑

```text
A 环境与仓库基线
B 架构与契约基线
C 行情与基础看盘
D LEAN 回测 MVP
E 策略与组合
F IBKR Paper
G 受控实盘准备
H 因子研究
I 机器学习研究
```

每一阶段必须完成技术验收和用户验收后才能进入下一阶段。

## 31. 开发红线

1. 禁止直接在 main 开发；
2. 禁止前端直接调用 fetch、axios 或拼 URL；
3. 禁止前端计算正式指标、收益、风控和交易决策；
4. 禁止 Router 直接访问数据库、AKShare、LEAN 或 IBKR；
5. 禁止核心契约使用裸 dict、Any 或 list[dict]；
6. 禁止正式回测运行在 FastAPI BackgroundTasks；
7. 禁止将 LEAN 原始结构返回前端；
8. 禁止未知 LEAN/Parser 组合执行正式回测；
9. 禁止无 TTL 或容量限制的 Redis Key；
10. 禁止覆盖已执行 StrategyVersion；
11. 禁止回测缺少复现字段；
12. 禁止旧缓存用于新正式回测、风控和下单；
13. 禁止 Broker 状态未知时放行状态依赖型风控；
14. 禁止订单绕过 RiskService；
15. 禁止单个环境变量开启 Live；
16. 禁止日志输出密钥和完整账户信息；
17. 禁止在对应阶段前创建高级模块、表和页面；
18. 禁止使用 JSONB 长期代替正式领域关系；
19. 禁止 Codex 因用户长时间未回复而默认验收通过；
20. 禁止数据时间语义不明时自行猜测；
21. 禁止 Dirty Workspace 创建正式 LEAN 回测；
22. 禁止 Parser 代码变化但兼容清单中的 Artifact Digest 不变；
23. 禁止 RiskService 直接处理 IBKR SDK 网络异常；
24. 禁止伪造或跳过 Paper 三个实际交易日观察报告。

## 32. Definition of Done

功能只有同时满足以下条件才完成：

- 职责和边界明确；
- Contract 明确；
- OpenAPI 可生成前端类型；
- 单元、契约和必要集成测试通过；
- 相关 Golden Fixture 通过；
- 错误码稳定；
- Trace ID 和日志完整；
- 时区、复权、数据新鲜度和质量标记明确；
- 安全和权限检查完成；
- 文档同步；
- CI 通过；
- PR 已合并；
- 用户验收通过。
