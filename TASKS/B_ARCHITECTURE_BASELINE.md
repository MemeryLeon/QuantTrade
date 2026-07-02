# 阶段 B：架构与契约基线

## 阶段目标

建立模块化单体、强类型契约、存储、异步任务、Mock 回测、前端 OpenAPI 和 CI。

## 去歧义执行规则

- 本文件中的“必须”表示不可跳过。
- 本文件中的“不得”表示禁止实现。
- 未写明的框架、字段、阈值或算法不得由 Codex 自行新增；需要时先记录问题并请求人工决定。
- 简单阶段使用一个分支；复杂阶段仅按本文件列出的分支任务包拆分。

## B-BR1 分支任务包

- **工作分支**：`feature/B-core-foundation`
- **人工门禁**：先设计评审，后实现；完成 B0、B1 草案后必须暂停并请求人工确认
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


### B0：后端模块化骨架

状态：DONE

#### 工作内容

- 建立 api、application、domains、infrastructure、contracts、workers、core。
- 保持 `API → Application → Domain ← Infrastructure`。
- 现有代码只做兼容迁移，不盲目重写。

#### 任务验收

- 后端可启动。
- Domain 不导入基础设施框架。
- 相关测试通过后创建一次 commit。

### B1：配置、错误、日志与核心 Port

状态：DONE

#### 工作内容

- 实现环境配置、ApiError、Trace ID、JSON 日志和健康检查。
- 定义 IDataProvider、IDataProviderHealth、IBacktestEngine、IBrokerGateway、IArtifactStore、IJobQueue 和 ISourceIdentityProvider。
- `IBrokerGateway.get_state()` 返回类型化 `BrokerStateResult`。
- 连接断开、超时、限流、会话失效、维护和暂时不完整必须转换为 AVAILABLE/STALE/UNAVAILABLE/RECONCILIATION_REQUIRED，不得直接抛给 RiskService。
- 未预期异常由 Application 边界记录并 Fail Closed，不得静默吞掉。
- 核心契约禁止裸 dict、Any 和 list[dict]。
- 生成 `docs/architecture/B_CORE_DESIGN_REVIEW.md`，包含 Port、Broker 异常契约、Source Identity、Contract 和首个迁移草案，然后暂停等待人工确认。

#### 任务验收

- 依赖方向检查通过。
- Broker 预期异常类型化契约测试通过。
- Source Identity 能区分本地 Git 工作区与不可变构建。
- 设计评审文档已获人工确认。
- 相关测试通过后创建一次 commit。

### B2：PostgreSQL、Redis 与 MinIO 基础

状态：DONE

#### 工作内容

- 建立 SQLAlchemy、Alembic、Redis 和 MinIO 适配器。
- 首批表只包含当前阶段需要内容；不得创建用户、因子、模型等空表。
- Redis Key 必须有命名、TTL、容量和新鲜度。

#### 任务验收

- 迁移可升级和回滚。
- Redis 与 MinIO 集成测试通过。
- 相关测试通过后创建一次 commit。

### B3：Job、专用队列与 Mock 回测

状态：DOING

#### 工作内容

- 实现 Job 状态机、普通 Celery Worker 和 `lean_backtest` 专用队列配置。
- LEAN Worker 初始并发固定为 1，prefetch 固定为 1。
- 实现 MockBacktestEngine、进度、日志、取消、超时和有限重试。

#### 任务验收

- Mock 后端闭环通过。
- 队列和并发配置测试通过。
- 相关测试通过后创建一次 commit。

### 分支任务包完成条件

- 本任务包内全部任务完成。
- 完整检查通过。
- PR 描述包含范围、测试、风险、迁移、回滚和未完成项。
- 按门禁规则完成合并。
- 用户验收通过后才能领取下一任务包。

## B-BR2 分支任务包

- **工作分支**：`feature/B-frontend-ci`
- **人工门禁**：普通；OpenAPI 破坏性变化必须人工批准
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


### B4：前端骨架与 OpenAPI 类型

#### 工作内容

- 建立 React、TypeScript、TanStack Query、Zustand 标准目录。
- 生成唯一 API Client 和 OpenAPI 类型。
- 组件禁止直接 fetch、axios 或拼接 URL。

#### 任务验收

- 前端构建和类型检查通过。
- OpenAPI 漂移检查通过。
- 相关测试通过后创建一次 commit。

### B5：Mock 页面、测试与 CI

#### 工作内容

- 实现 Mock 回测提交、进度、日志、取消和结果页面。
- 建立后端单测、契约测试、前端单测、最小 E2E 和 GitHub Actions。
- CI 失败时不得合并。

#### 任务验收

- Mock 回测 E2E 通过。
- 完整 CI 通过。
- 相关测试通过后创建一次 commit。

### 分支任务包完成条件

- 本任务包内全部任务完成。
- 完整检查通过。
- PR 描述包含范围、测试、风险、迁移、回滚和未完成项。
- 按门禁规则完成合并。
- 用户验收通过后才能领取下一任务包。
