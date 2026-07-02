# B 核心设计评审

生成日期：2026-07-02

任务包：B-BR1
分支：`feature/B-core-foundation`

当前状态：已完成 B0、B1 草案，按门禁暂停，等待人工确认后继续 B2、B3。

## Domain Ports

已在 `backend/app/domains/` 定义第一批纯领域 Port 和数据模型：

| Port | 文件 | 用途 |
|---|---|---|
| `IDataProvider` | `market.py` | 搜索标的、读取 K 线、报价和交易日历 |
| `IDataProviderHealth` | `market.py` | 独立读取行情源健康状态，避免行情接口承担熔断治理 |
| `IBacktestEngine` | `backtest.py` | 提交 Mock 或正式 LEAN 回测请求 |
| `IBrokerGateway` | `broker.py` | 获取券商状态，不暴露 IBKR SDK 异常和字段 |
| `IArtifactStore` | `artifacts.py` | 写入和读取 MinIO 等对象存储中的产物 |
| `IJobQueue` | `jobs.py` | 提交、查询和取消长任务 |
| `ISourceIdentityProvider` | `source_identity.py` | 证明本地 Git 工作区或不可变构建身份 |

依赖边界：

- Domain 只使用标准库类型、`dataclass`、`Protocol` 和枚举；
- Domain 不导入 FastAPI、SQLAlchemy、Redis、AKShare、LEAN、IBKR SDK；
- 已新增依赖方向测试，扫描 `backend/app/domains/*.py` 的导入。

## 核心 Contract

### API 与错误

- `backend/app/contracts/system.py` 定义 `HealthResponse` 和 `ApiErrorResponse`；
- `backend/app/core/errors.py` 定义统一 `ApiError`；
- `main.py` 注册 `ApiError` 处理器，返回 `code`、`message`、`trace_id`、`details`；
- `details` 当前约束为 `Mapping[str, str]`，避免无约束 JSON 结构。

### Trace ID

- `backend/app/core/trace.py` 使用进程内上下文保存当前请求 Trace ID；
- `backend/app/core/middleware.py` 从 `X-Trace-ID` 读取或生成 Trace ID；
- 响应头回写 `X-Trace-ID`；
- `backend/app/core/logging.py` 的 JSON 日志包含 `trace_id`。

### 配置

- `backend/app/core/config.py` 定义 `Settings`；
- 当前只纳入应用名、版本、运行环境、日志级别和 Trace Header；
- 暂不新增数据库、Redis、MinIO、Celery、LEAN 或 IBKR 配置，避免提前进入 B2/B3/F 阶段范围。

### Source Identity

Source Identity 由 `backend/app/infrastructure/source_identity.py` 提供草案实现：

| 场景 | 行为 |
|---|---|
| 不可变构建身份完整 | 返回 `mode=immutable_build` |
| 本地存在 `.git` 且工作区干净 | 返回 `mode=local_git`、`platform_git_sha`、`platform_source_tree_digest`、`git_workspace_clean=true` |
| 本地 Git 工作区有 tracked 修改或未忽略 untracked 文件 | 返回 `WORKSPACE_DIRTY` |
| 无 `.git` 且无完整不可变构建身份 | 返回 `SOURCE_IDENTITY_UNAVAILABLE` |

当前草案中 `platform_source_tree_digest` 对本地 Git 使用 `git rev-parse HEAD^{tree}`。后续正式 LEAN 回测接入前，如需要纳入构建产物或非 Git 跟踪文件，必须在设计中明确扩展规则。

### IBrokerGateway.get_state

- `IBrokerGateway.get_state()` 返回 `BrokerStateResult`；
- `BrokerStateResult` 包含 `status`、`state`、`as_of`、`error_code`、`error_message`、`trace_id`；
- `BrokerState` 包含 `broker_state_as_of`、`broker_state_status`、`max_state_staleness_seconds`、`connection_status`、现金、敞口、未成交订单数和对账状态。

#### BrokerStateResult

`BrokerStateStatus` 当前固定为：

- `AVAILABLE`
- `STALE`
- `UNAVAILABLE`
- `RECONCILIATION_REQUIRED`

#### 预期异常转换

`backend/app/infrastructure/broker_state_mapping.py` 定义预期券商状态失败类型和映射：

| 预期失败 | 转换状态 |
|---|---|
| 连接断开 | `UNAVAILABLE` |
| 超时 | `STALE` |
| 限流 | `STALE` |
| 会话失效 | `UNAVAILABLE` |
| 券商维护 | `UNAVAILABLE` |
| 状态暂时不完整 | `RECONCILIATION_REQUIRED` |

这些转换属于 Infrastructure 边界职责。RiskService 后续只应读取 `BrokerStateResult`，不得捕获或判断 IBKR SDK 网络异常。

#### 未预期异常边界

`backend/app/application/broker_state_service.py` 定义应用边界草案：

- 调用 `IBrokerGateway.get_state()`；
- 若出现未预期异常，记录结构化日志；
- 返回 `status=UNAVAILABLE`、`error_code=BROKER_STATE_UNKNOWN`；
- 交易相关流程后续必须 Fail Closed。

## 首个 Alembic 迁移

B2 才允许建立 SQLAlchemy、Alembic、Redis 和 MinIO 适配器。本评审草案建议首个 Alembic 迁移只创建 B2/B3 必需的基础表，不提前创建用户、因子、模型、数据集等未来阶段空表。

建议首个迁移范围：

| 表 | 阶段用途 | 备注 |
|---|---|---|
| `job_runs` | B3 长任务状态、进度、错误和产物关联 | 状态枚举必须匹配 `JobState` |

以下表虽然在项目计划允许范围内，但不建议作为首个迁移一次性创建，应在对应阶段按验收需要推进：

- `instruments`
- `data_sources`
- `data_snapshots`
- `strategies`
- `strategy_versions`
- `backtest_runs`
- `backtest_metrics`
- `backtest_trades`
- `portfolios`
- `portfolio_positions`
- `broker_accounts`
- `orders`
- `fills`
- `risk_rules`
- `audit_logs`

不创建：

- `users`
- `watchlists`
- `watchlist_items`
- `factors`
- `datasets`
- `features`
- `models`
- `experiments`

## 依赖方向

目标方向保持：

```text
API → Application → Domain ← Infrastructure
```

当前实现：

- API：`backend/app/api/v1/*` 只处理 HTTP 路由和响应模型；
- Application：`backend/app/application/*` 编排 Port，负责应用边界 Fail Closed；
- Domain：`backend/app/domains/*` 定义纯业务模型和 Port；
- Infrastructure：`backend/app/infrastructure/*` 提供 Source Identity 和 Broker 预期异常转换草案；
- Core：`backend/app/core/*` 放配置、日志、Trace ID 和 API 错误。

已验证：

- `.\make.cmd test` 通过；
- Domain 依赖方向测试通过；
- Broker 预期异常契约测试通过；
- Source Identity 本地 Git 与不可变构建区分测试通过；
- 健康检查仍兼容 A 阶段 `/health -> {"status":"ok"}`。

## 数据和时间语义

本次只建立类型边界，不拉取、不保存、不改写行情数据。

已固定的时间语义：

- `Bar.observed_at` 表示行情观察时间；
- `BarsResult.as_of` 和 `Quote.as_of` 表示返回数据实际时间；
- `DataSourceHealth.checked_at` 表示健康检查时间；
- `DataSourceHealth.last_success_at` 表示数据源最后成功时间；
- `BrokerState.broker_state_as_of` 表示券商状态时间；
- API 和领域模型要求调用方传入带明确语义的时间，后续 C/D/F 阶段不得在语义不清时猜测。

已固定的数据质量标记：

- `MISSING_BARS`
- `DUPLICATE_BARS`
- `OUT_OF_ORDER`
- `STALE_CACHE`
- `PROVIDER_DEGRADED`
- `PROVIDER_UNAVAILABLE`
- `ADJUSTMENT_FACTOR_MISSING`
- `CALENDAR_MISMATCH`
- `TIMEZONE_AMBIGUOUS`

## 需要人工决定的问题

1. Source Identity 本地 `platform_source_tree_digest` 是否接受 Git Tree SHA 草案，还是必须在 D 阶段正式 LEAN 回测前改为覆盖额外构建产物的 SHA-256 清单？
2. 首个 Alembic 迁移是否只创建 `job_runs`，还是 B2 需要同时创建最小 `audit_logs` 以承载应用边界错误审计？
3. Broker 预期失败中，`TIMEOUT` 和 `RATE_LIMITED` 当前映射为 `STALE`，是否符合后续 Paper 风控的预期？若希望更保守，可改为 `UNAVAILABLE`。

## 评审结果

- [ ] 通过
- [ ] 退回修改
