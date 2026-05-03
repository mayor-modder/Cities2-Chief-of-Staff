# Agent Rules

- Keep Cities2-CityAdvisor separate from Cities2-MCP. This repo analyzes local city evidence; it should not include the CS2 wiki corpus or mod project scaffolding tools.
- Keep Cities2-DataExport focused on writing city samples. CityAdvisor may read its output, but should not require it.
- Treat InfoLoomBridge and other mod exports as optional evidence sources.
- In this Windows workspace, skip `rg`/ripgrep. Use PowerShell search fallbacks such as `Get-ChildItem -Recurse -File | Select-String -Pattern "term"`.
