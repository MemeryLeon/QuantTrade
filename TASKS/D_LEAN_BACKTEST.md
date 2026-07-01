# 阶段 D：LEAN 回测 MVP

## 阶段目标

完成策略版本、LEAN 运行、兼容绑定、异步回测、解析、复现和前端。

## 去歧义执行规则

- 本文件中的“必须”表示不可跳过。
- 本文件中的“不得”表示禁止实现。
- 未写明的框架、字段、阈值或算法不得由 Codex 自行新增；需要时先记录问题并请求人工决定。
- 简单阶段使用一个分支；复杂阶段仅按本文件列出的分支任务包拆分。

## D-BR1 分支任务包

- **工作分支**：`feature/D-lean-runtime`
- **人工门禁**：高风险：LEAN Digest、资源限制、回测 Contract、费用和滑点需人工批准
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


### D0：固定 LEAN 环境与专用 Worker

#### 工作内容

- 固定 LEAN 镜像 Digest。
- LEAN 回测只进入 `lean_backtest` 队列，Worker concurrency=1，prefetch=1。
- 配置 CPU、内存、超时、输出、临时目录、只读数据目录和最大排队数。

#### 任务验收

- 容器可重复启动、退出和清理。
- 并发限制可验证。
- 相关测试通过后创建一次 commit。

### D1：策略版本、回测契约与 run_metadata

#### 工作内容

- 实现 Strategy、StrategyVersion 和不可变规则。
- BacktestRequest 必须包含数据快照、复权、费用和滑点。
- 定义 SourceIdentity，支持 local_git 与 immutable_build 两种模式。
- 本地正式回测在 Dirty Workspace 时使用 `WORKSPACE_DIRTY` 拒绝。
- 无法取得可信源码身份时使用 `SOURCE_IDENTITY_UNAVAILABLE` 拒绝。
- `backtest_runs` 增加 `run_metadata JSONB` 和 schema version，仅用于受约束元数据。

#### 任务验收

- 不可变规则通过。
- run_metadata 有 Pydantic Schema。
- Dirty Git、untracked 文件和不可变构建身份测试通过。
- Mock 回测不被 Dirty Workspace 拦截，正式 LEAN 回测必须被拦截。
- 相关测试通过后创建一次 commit。

### D2：LEAN Adapter、Worker 与 API

#### 工作内容

- 实现 LeanBacktestAdapter、Worker、日志、取消、超时和标准异常。
- 提供创建、状态、结果、日志和取消接口。
- 未登记的 LEAN/Parser 兼容组合不得执行。
- 正式回测创建接口必须在入队前完成 Source Identity 和数据源新鲜度校验。

#### 任务验收

- 正式 LEAN 任务异步执行。
- 错误码稳定。
- 相关测试通过后创建一次 commit。

### 分支任务包完成条件

- 本任务包内全部任务完成。
- 完整检查通过。
- PR 描述包含范围、测试、风险、迁移、回滚和未完成项。
- 按门禁规则完成合并。
- 用户验收通过后才能领取下一任务包。

## D-BR2 分支任务包

- **工作分支**：`feature/D-result-pipeline`
- **人工门禁**：高风险：Parser、Schema、Fixture 和金融结果语义必须人工确认
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


### D3：Parser 兼容清单、结果归档与复现

#### 工作内容

- 创建 `lean/compatibility/manifest.yaml`。
- 绑定 lean_image_digest、parser_version、parser_artifact_digest、raw_output_schema_version、fixture_version。
- 原始结果和日志存 MinIO；Parser 转为标准领域模型。
- 保存平台 Git SHA、Source Tree Digest、后端镜像 Digest、策略 Artifact Digest 和 Parser Artifact Digest。
- 保存全部复现字段。

#### 任务验收

- 前端不接触原始结构。
- 未知兼容组合被拒绝。
- 相关测试通过后创建一次 commit。

### D4：Schema Compatibility Test 与 Golden Fixture

#### 工作内容

- CI 检查兼容清单和实际 Parser Artifact Digest。
- Parser 代码变化必须导致 Artifact Digest 变化。
- LEAN 原始结构变化才升级 raw_output_schema_version。
- Parser 解析结果变化时升级 fixture_version。
- LEAN Digest、Parser Artifact 或 Schema 变化时强制运行 Golden Fixture。
- 覆盖启动失败、超时、取消、解析失败、数据无效和输出超限。

#### 任务验收

- 兼容不匹配时 CI 失败。
- 重复回测结果在容差内一致。
- 相关测试通过后创建一次 commit。

### 分支任务包完成条件

- 本任务包内全部任务完成。
- 完整检查通过。
- PR 描述包含范围、测试、风险、迁移、回滚和未完成项。
- 按门禁规则完成合并。
- 用户验收通过后才能领取下一任务包。

## D-BR3 分支任务包

- **工作分支**：`feature/D-backtest-ui`
- **人工门禁**：普通；最终复权、费用、滑点和交易结果由用户验收
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


### D5：回测进度、结果和产物页面

#### 工作内容

- 展示状态、日志、取消、资金曲线、回撤、指标、交易记录和复现信息。
- 数据源为 degraded/unavailable 时禁用正式回测提交，并显示最后成功时间与 stale_age_seconds。
- 解析 `DATA_SOURCE_DEGRADED`、`DATA_SOURCE_UNAVAILABLE`、`WORKSPACE_DIRTY` 和 `SOURCE_IDENTITY_UNAVAILABLE` 为明确中文提示。
- 提供受控产物下载，不暴露服务端路径。

#### 任务验收

- 完整 E2E 通过。
- 前端禁用不是唯一门禁，绕过前端后服务端仍拒绝不合格请求。
- 页面数据与 API 一致。
- 相关测试通过后创建一次 commit。

### D6：LEAN 阶段总验收

#### 工作内容

- 验证异步、资源限制、兼容绑定、复现、Golden Fixture 和页面。
- 人工确认数据快照、复权、手续费、滑点和交易结果。

#### 任务验收

- Phase D 验收通过。
- 相关测试通过后创建一次 commit。

### 分支任务包完成条件

- 本任务包内全部任务完成。
- 完整检查通过。
- PR 描述包含范围、测试、风险、迁移、回滚和未完成项。
- 按门禁规则完成合并。
- 用户验收通过后才能领取下一任务包。
