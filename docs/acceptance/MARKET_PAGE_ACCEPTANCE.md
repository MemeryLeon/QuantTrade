# QuantTrade 行情页专业化验收清单

日期：2026-07-02

分支：`feature/C-market-page-professional`

## 子任务验收

| 子任务 | 自动检查 | 自审结果 | 状态 |
|---|---|---|---|
| 行情数据正确性与状态 | `pytest backend/tests/test_akshare_market_data.py backend/tests/test_market_domain_contract.py` 通过 | 后端接口已支持日/周/月；周/月由日线按交易所时区聚合；延迟、来源、质量标记继续由服务端输出 | DONE |
| 主图、周期、复权和指标 | `pytest backend/tests/test_akshare_market_data.py backend/tests/test_market_snapshots_and_indicators.py`、`npm run build`、`npm run e2e -- --reporter=line tests/e2e/market.spec.ts` 通过 | 主图已切换 Lightweight Charts；周期和复权进入接口请求；指标参数由后端计算并在页面管理；图表支持十字光标、缩放、拖动、重置和全屏 | DONE |
| 搜索、自选、详情和用户偏好 | `pytest backend/tests/test_akshare_market_data.py`、`npm run build`、`npm run e2e -- --reporter=line tests/e2e/market.spec.ts` 通过 | 新增报价详情接口；搜索支持输入防抖和最近访问；自选保留旧 JSON 兼容并记录加入时间；周期、复权、指标参数和显隐偏好可安全保存与恢复 | DONE |
| 视觉收口、性能和 E2E | 待运行 | 待填写 | TODO |

## P0 验收项

| 验收项 | 结果 | 证据 |
|---|---|---|
| 专业桌面布局 | TODO | 待填写 |
| 标的搜索可用 | TODO | 待填写 |
| 标的标题和基础报价完整 | TODO | 待填写 |
| 自选列表完整 | TODO | 待填写 |
| K 线和成交量由 Lightweight Charts 渲染 | TODO | 待填写 |
| 日线、周线、月线可切换 | TODO | 待填写 |
| 不复权、前复权、后复权可切换 | TODO | 待填写 |
| SMA、EMA、MACD、RSI、布林带、ADX 可配置 | TODO | 待填写 |
| 图表十字光标、缩放、拖动、重置 | TODO | 待填写 |
| 数据更新时间和来源清楚 | TODO | 待填写 |
| 延迟数据与质量警告明确 | TODO | 待填写 |
| 加载、空数据、错误和重试状态 | TODO | 待填写 |
| 图表全屏 | TODO | 待填写 |
| 用户偏好保存并安全恢复 | TODO | 待填写 |
| 深色专业视觉风格 | TODO | 待填写 |
| 单元测试通过 | TODO | 待填写 |
| E2E 通过 | TODO | 待填写 |
| `make check` 通过 | TODO | 待填写 |
| `make test` 通过 | TODO | 待填写 |
| `make e2e` 通过 | TODO | 待填写 |

## 最终截图

待补充。

## 未完成 P1

待补充。

## 风险和回滚

待补充。
