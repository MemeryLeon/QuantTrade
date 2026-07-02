# C-BR2 行情前端验收记录

日期：2026-07-02

任务包：C-BR2

分支：`feature/C-market-ui`

## 范围

- 行情页：标的搜索、日线 K 线、成交量、指标和基础信息。
- 数据说明：展示 provider、market、timezone、adjustment、as_of 和 quality_flags。
- 数据警告：数据源 degraded、unavailable、recovering 或延迟缓存时显示全局横幅。
- 本地自选：使用 `quanttrade.watchlist.v1` 保存到 LocalStorage。
- 导入导出：导出版本化 JSON，导入时校验 Schema，非法 JSON 拒绝。

## 数据安全检查

- 指标由后端 `/market/indicators` 计算，前端只渲染返回值。
- 延迟缓存只在行情展示页显示，响应中的 `is_delayed`、`as_of`、`stale_age_seconds` 和 `quality_flags` 原样展示。
- 未创建 `watchlists` 或 `watchlist_items` 后端表。
- 未新增多设备同步接口。

## 自动化验收

- 后端行情与指标相关测试通过。
- 前端单元测试通过。
- 前端构建通过。
- E2E 覆盖加载、切换、降级、异常、自选刷新恢复和非法 JSON 拒绝。

## 人工体验验收

- 页面、数据警告和自选体验等待用户最终确认。
