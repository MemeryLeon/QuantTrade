# QuantTrade 行情页差距报告

日期：2026-07-02

分支：`feature/C-market-page-professional`

## 1. 当前已经实现的功能

- 首页展示行情页。
- 可搜索标的并切换。
- 可请求日线 K 线和成交量。
- 后端已有 `/market/bars`、`/market/indicators`、`/market/instruments/search` 和数据源健康接口。
- 页面展示 provider、market、timezone、adjustment、as_of 和 quality_flags。
- 数据源 degraded 或旧缓存时有全局警告。
- 自选使用 `quanttrade.watchlist.v1` 保存到 LocalStorage。
- 自选 JSON 导入导出有基础 Schema 校验。
- E2E 覆盖加载、切换、降级、异常、自选刷新恢复和非法 JSON 拒绝。

## 2. 当前实现但存在问题的功能

- K 线图是手写 SVG，不是项目技术栈要求的 Lightweight Charts。
- 图表没有专业缩放、拖动、十字光标、价格轴和时间轴交互。
- 指标只是固定展示最新值，不能添加、删除、隐藏、改参数。
- 后端指标参数固定为单套默认值，不支持请求参数。
- 搜索需要手动提交，没有防抖和键盘选择。
- 自选没有分组、排序、最新价和涨跌幅。
- 页面仍是卡片式纵向布局，不是专业看盘三栏工作台。
- 右侧详情字段不足，缺少最新价、涨跌额、涨跌幅、今开、昨收、最高、最低、成交额等。
- 加载、空数据、错误、重试状态不够细。
- 偏好只保存自选，没有保存周期、复权、图表类型、指标、侧栏折叠和主题。

## 3. 当前完全缺失的功能

- 周线、月线正式后端聚合。
- 图表类型切换。
- 全屏图表。
- 视图重置。
- 左右侧栏折叠。
- 最近访问标的。
- 用户偏好版本化存储。
- 指标管理器。
- 详情面板的完整报价和数据质量分区。
- 最终页面截图和完整专业化验收记录。

## 4. 当前视觉和交互问题

- 视觉仍偏浅色后台卡片，不像专业行情工作台。
- 主图高度和视觉权重不足。
- 信息分区较散，用户扫读效率低。
- 控件尺寸偏大，不够紧凑。
- 数字未统一等宽和右对齐。
- 颜色 token 分散在 CSS 中。

## 5. 当前接口和数据问题

- `BarsResponse.resolution` 只允许 `daily`。
- `AkshareDataProvider` 明确拒绝非 daily。
- 周线、月线如果在前端做会违反正式数据语义，必须后端聚合。
- `/market/indicators` 没有指标参数输入，无法支持用户配置。
- 当前没有 quote API 暴露给前端，最新价和涨跌幅只能从 bars 派生，语义上是日线收盘快照，不是实时盘口。
- AKShare 搜索结果没有证券类型字段，P0 先展示市场和 A 股类型文案，不伪造额外类型。

## 6. 本次必须完成的 P0 项

1. 后端支持 `daily`、`weekly`、`monthly` 周期，并保持时间、复权和质量标记语义。
2. 后端指标接口支持参数化请求，前端不计算正式指标。
3. 前端用 Lightweight Charts 替换手写 SVG 主图。
4. 实现专业三栏布局、全局状态、详情面板、工具栏、折叠和全屏。
5. 搜索防抖、键盘选择、最近访问。
6. 自选分组、增删、重命名、排序、切换和刷新恢复。
7. 本地偏好版本化保存和安全恢复默认。
8. 加载、空数据、错误、重试和降级状态。
9. 单元测试、组件或 E2E 覆盖补齐。
10. `make check`、`make test`、`make e2e` 通过。

## 7. 可以后置的 P1 项

- 分时周期：1m、5m、15m、30m、60m。
- 画线工具。
- 截图工具。
- 多图布局。
- 多标的叠加对比。
- 新闻、财务和研报。
- WebSocket 实时推送。
- 手机端完整专业看盘。

## 8. 涉及的文件和模块

- `backend/app/domains/market.py`
- `backend/app/domains/indicators.py`
- `backend/app/application/market_data.py`
- `backend/app/contracts/market.py`
- `backend/app/api/v1/market.py`
- `backend/app/infrastructure/akshare_market_data.py`
- `backend/tests/test_akshare_market_data.py`
- `backend/tests/test_market_snapshots_and_indicators.py`
- `frontend/package.json`
- `frontend/src/services/market.ts`
- `frontend/src/pages/MarketPage.tsx`
- `frontend/src/stores/watchlistStore.ts`
- `frontend/src/styles.css`
- `frontend/tests/**`
- `frontend/tests/e2e/market.spec.ts`

## 9. 实施顺序

1. 行情数据正确性与状态。
2. 主图、周期、复权和指标。
3. 搜索、自选、详情和用户偏好。
4. 视觉收口、性能和 E2E。

每个子任务完成后先自审，发现问题在同一子任务内修复，再提交。

## 10. 风险和回滚方式

风险：

- 周线、月线聚合若语义错误，会污染正式行情展示。
- 指标参数化如果前后端默认值不一致，会造成显示误导。
- Lightweight Charts 接入如果生命周期处理不好，会产生重复实例或内存泄漏。
- 自选分组结构升级可能影响旧 LocalStorage。

回滚：

- 每个子任务单独提交，可按提交回退。
- 后端 API 保持已有 daily 默认兼容。
- 本地偏好使用新版本 key，旧自选保留迁移或安全默认。
- 图表替换如失败，可临时回滚到上一提交的 SVG 图，但不得标记专业化完成。
