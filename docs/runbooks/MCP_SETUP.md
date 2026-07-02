# MCP 设置说明

本项目在 `.codex/config.toml` 中启用两个项目级 MCP：

- `playwright`：通过 `npx.cmd -y @playwright/mcp@latest` 启动，用于浏览器自动化和页面检查。
- `context7`：通过 `npx.cmd -y @upstash/context7-mcp@latest` 启动，用于读取较新的第三方库文档。

这里使用 `npx.cmd` 是为了避开 Windows PowerShell 的脚本执行策略限制。

这些配置只在 Codex 信任本项目时加载。修改后通常需要重新打开项目或重启 Codex 会话，新的 MCP 工具才会出现在后续会话里。

本仓库提供 `.npmrc`，让 `npx` 优先使用 `https://registry.npmmirror.com` 拉取包体。不要把 Context7 API Key 或其他密钥写入仓库；如果后续需要更高额度，把密钥放在个人环境变量或用户级 Codex 配置里。

如果设置了个人环境变量 `CONTEXT7_API_KEY`，Codex 会在启动 Context7 MCP 时转发该变量；没有设置时仍可使用 Context7 的默认额度。
