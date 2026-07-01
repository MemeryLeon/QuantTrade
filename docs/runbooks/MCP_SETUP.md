# MCP 设置说明

本项目在 `.codex/config.toml` 中启用两个项目级 MCP：

- `playwright`：通过 `npx -y @playwright/mcp@latest` 启动，用于浏览器自动化和页面检查。
- `context7`：通过 `npx -y @upstash/context7-mcp@latest` 启动，用于读取较新的第三方库文档。

这些配置只在 Codex 信任本项目时加载。修改后通常需要重新打开项目或重启 Codex 会话，新的 MCP 工具才会出现在后续会话里。

本仓库提供 `.npmrc`，让 `npx` 优先使用 `https://registry.npmmirror.com` 拉取包体。不要把 Context7 API Key 或其他密钥写入仓库；如果后续需要更高额度，把密钥放在个人环境变量或用户级 Codex 配置里。
