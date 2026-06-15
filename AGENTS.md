# Agent Rules

- Keep Cities2-Chief-of-Staff separate from Cities2-MCP. This repo analyzes local city evidence; it should not include the CS2 wiki corpus or mod project scaffolding tools.
- Keep Cities2-DataExport focused on writing city samples. Chief of Staff may read its output, but should not require it.
- Treat InfoLoomBridge and other mod exports as optional evidence sources.
- When generating a city report, refresh Save Investigator first through Chief of Staff's `analyze` or report-producing MCP tools; do not rely on an existing Save Investigator output directory unless the user explicitly asks for a stale/offline read.
- In this Windows workspace, skip `rg`/ripgrep. Use PowerShell search fallbacks such as `Get-ChildItem -Recurse -File | Select-String -Pattern "term"`.
