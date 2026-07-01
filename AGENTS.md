# QuantTrade Codex 工作规则

## 附录：常用操作约定

- 如果rg不可用，则使用 PowerShell 原生命令：
- 找文件：`Get-ChildItem -Recurse -File`
- 搜文本：`Select-String`
- 读取包含中文的文件时，优先显式使用 UTF-8：
- `Get-Content .\agent.md -Encoding UTF8`
- 如果文件已经被错误编码写入，不要靠猜测修复，先确认原始内容，再重新按 UTF-8 保存
- 数据获取使用代理配置，当前机器的 HTTP 代理地址是 http://127.0.0.1:18081
- 依赖包体和文件优先使用国内镜像源，如不适用或者会影响环境稳定则换成正式源

## 0. 沟通与通用原则

- 所有实现必须易维护、易扩展，不允许为了当前需求硬编码
- 不要搞兜底实现，兜底实现会掩盖主流程的错误
- 遇到不确定的信息，不要猜测，优先查官方文档和已有文档或明确指出需要确认的地方
- 分析 bug和编写代码时，要从第一性原理出发


## 1. 读取顺序

每次开始工作必须读取：

1. `PROJECT_PLAN.md`
2. `TASKS/INDEX.md`
3. 当前阶段任务文件
4. 当前任务涉及的代码和测试
5. 相关 ADR、设计评审和验收记录

## 2. 任务领取

- 只领取第一个依赖已完成且状态为 READY 的分支任务包。
- 不得跳过任务包。
- 不得提前开发后续阶段。
- 不得因用户未及时回复而默认通过验收。

## 3. 分支规则

- 简单阶段一个分支。
- 复杂阶段只使用任务文件中列出的少量分支。
- 同一分支连续完成多个任务。
- 每个任务至少一次清晰 commit。
- 一个分支任务包只创建一个 PR。
- CI 失败继续在原分支修复。

## 4. 设计评审

B-BR1 特殊规则：

- 完成 B0、B1 草案；
- 生成 `docs/architecture/B_CORE_DESIGN_REVIEW.md`；
- 停止编码并请求人工确认；
- 获得确认后继续同一分支完成 B2、B3；
- 不创建额外分支。

## 5. 架构红线

`API → Application → Domain ← Infrastructure`

- LEAN 是唯一正式量化引擎。
- Domain 不依赖框架和外部 SDK。
- Router 不直接访问数据库、AKShare、LEAN 或 IBKR。
- 前端不直接 fetch/axios，不拼 URL。
- 正式指标、收益、风控和交易决策不在前端计算。
- 长任务不使用 FastAPI BackgroundTasks。

## 6. 数据红线

- 旧缓存只允许用于行情展示，必须明确标记延迟。
- 旧缓存不得用于新正式回测、风控或交易。
- 数据时间语义不明时停止，不得猜测。
- data_snapshots 只在 PostgreSQL 保存元数据，大文件存 MinIO。
- Redis 只作性能缓存，不是复现依据。

## 7. LEAN 与复现红线

- LEAN Digest、Parser Version、Parser Artifact Digest、Raw Schema 和 Fixture 必须在兼容清单中绑定。
- Parser 代码变化时 Artifact Digest 必须变化。
- 只有 LEAN 原始输出结构变化时才升级 Raw Schema Version。
- Parser 解析结果变化时升级 Fixture Version。
- 未登记组合不得执行正式回测。
- 本地 Dirty Workspace 不得创建正式 LEAN 回测，返回 `WORKSPACE_DIRTY`。
- 部署环境必须提供不可变构建身份；缺失时返回 `SOURCE_IDENTITY_UNAVAILABLE`。
- 兼容变更必须运行 Schema Compatibility Test 和 Golden Fixture。
- 前端不得看到 LEAN 原始结构。
- LEAN 专用 Worker 初始 concurrency=1、prefetch=1。

## 8. Broker 与风控红线

- Broker 预期网络和可用性异常必须转换为类型化 BrokerStateResult。
- RiskService 不得直接捕获或处理 IBKR SDK 网络异常。
- 未预期异常由 Application 边界记录并 Fail Closed。
- Broker 状态必须有时间戳和新鲜度。
- 状态未知、断线、过期或对账未完成时，状态依赖型风控必须拒绝。
- 错误码为 `BROKER_STATE_UNKNOWN`。
- 订单必须通过 RiskService。
- Live 默认关闭，Codex 不得自行批准 Go。
- Phase F 必须有至少连续 3 个实际交易日的真实观察报告；不得伪造或跳过。

## 9. JSONB 限制

`backtest_runs.run_metadata`：

- 必须有 Schema 和版本；
- 只存受约束元数据；
- 不得长期替代 factor、model、dataset 外键。

## 10. 完成规则

分支任务包完成必须满足：

- 全部任务完成；
- `make check` 通过；
- 必要集成和 E2E 通过；
- 文档和 OpenAPI 同步；
- PR 描述完整；
- 按人工门禁合并；
- 用户验收通过。

用户回复“验收通过，继续”后，更新状态并领取下一 READY 任务包。
