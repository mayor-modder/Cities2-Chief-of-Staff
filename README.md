# Cities2-CityAdvisor

Cities2-CityAdvisor is a local analysis layer for Cities: Skylines II city evidence.

It is separate from:

- `Cities2-MCP`, which is for wiki knowledge and mod project workflows
- `Cities2-DataExport`, which is an in-game mod that writes city snapshots
- `Cities2-InfoLoomBridge`, which writes selected InfoLoom-derived data

CityAdvisor reads whatever local evidence is available and turns it into reports an agent or human can use.

## Current First Version

This first version can:

- detect `Cities2-DataExport` output at `ModsData/CS2DataExport/latest.json`
- detect `Cities2-InfoLoomBridge` output at `ModsData/InfoLoomBridge/latest.json`
- detect the newest Save Investigator output directory
- include the Save Investigator source under `tools/SaveInvestigator`
- refresh Save Investigator before report-producing commands
- produce a Markdown city report
- expose the same report/status through a small MCP server

Python is enough to start CityAdvisor, inspect source status, and read existing evidence. Fresh reports run Save Investigator when its project is available, so report-producing commands also need the .NET 8 SDK unless you explicitly request an offline/stale read with `--skip-save-investigator-refresh`.

## Requirements

- Python 3.11+
- .NET 8 SDK for fresh Save Investigator runs
- Optional evidence producers:
  - `Cities2-DataExport`
  - `Cities2-InfoLoomBridge`

## Install

From the repository root:

```powershell
python -m pip install -e .
```

This installs the console commands:

```powershell
cityadvisor --help
cityadvisor-mcp --help
```

## Command Line

Show detected sources:

```powershell
python -m cityadvisor.cli status
```

Or, after installation:

```powershell
cityadvisor status
```

Build a report:

```powershell
python -m cityadvisor.cli analyze
```

Or, after installation:

```powershell
cityadvisor analyze
```

`analyze` refreshes Save Investigator before building the report when
`tools/SaveInvestigator/SaveInvestigator.csproj` is available. This keeps
agent-generated reports from silently using stale save evidence. Use
`status` when you only want to inspect currently detected evidence without
running a new save investigation.

Use explicit paths:

```powershell
python -m cityadvisor.cli analyze `
  --mods-data "$env:USERPROFILE\AppData\LocalLow\Colossal Order\Cities Skylines II\ModsData" `
  --save-path "$env:USERPROFILE\AppData\LocalLow\Colossal Order\Cities Skylines II\Saves\<steam-id>\<save>.cok" `
  --save-investigator-project ".\tools\SaveInvestigator\SaveInvestigator.csproj" `
  --save-investigator-output ".\tools\SaveInvestigator\bin\Debug\net8.0\output"
```

Use an existing Save Investigator output without refreshing:

```powershell
python -m cityadvisor.cli analyze --skip-save-investigator-refresh
```

Print JSON:

```powershell
python -m cityadvisor.cli analyze --json
```

## MCP Server

Start the MCP server with:

```powershell
python -m cityadvisor.mcp_server
```

Or, after installation:

```powershell
cityadvisor-mcp
```

Available MCP tools:

- `cityadvisor_get_status`
- `cityadvisor_analyze_city` refreshes Save Investigator first unless skipped
- `cityadvisor_get_report` refreshes Save Investigator first unless skipped

Example MCP config:

```json
{
  "mcpServers": {
    "cities2-cityadvisor": {
      "command": "<PYTHON_PATH>",
      "args": [
        "<REPO_ROOT>/cityadvisor/mcp_server.py",
        "--mods-data",
        "<MODS_DATA_DIR>",
        "--save-path",
        "<SAVE_FILE.cok>",
        "--save-investigator-project",
        "<REPO_ROOT>/tools/SaveInvestigator/SaveInvestigator.csproj",
        "--save-investigator-output",
        "<SAVE_INVESTIGATOR_OUTPUT_DIR>"
      ]
    }
  }
}
```

`--mods-data`, `--save-path`, `--save-investigator-project`, and `--save-investigator-output` can also be supplied per tool call through the MCP tool arguments. Use `--skip-save-investigator-refresh` only when you intentionally want to analyze already-written Save Investigator output without running a fresh save investigation.

## Evidence Sources

### Save Investigator

Save Investigator is the default save-analysis provider for CityAdvisor. Its source is included under:

```text
tools/SaveInvestigator
```

CityAdvisor reads the JSON artifacts it writes, such as:

- `city-state-report-facts.json`
- `transport-report-facts.json`

Report-producing CLI and MCP commands run Save Investigator directly before building the report when the project is available. If no project is available, CityAdvisor can still read the newest existing output directory.

### Cities2-DataExport

If present, CityAdvisor reads:

```text
ModsData/CS2DataExport/latest.json
```

This provides live city sample data such as population, city name, workforce, transport proxies, and other exported groups.

### Cities2-InfoLoomBridge

If present, CityAdvisor reads:

```text
ModsData/InfoLoomBridge/latest.json
```

This can add more detailed InfoLoom-derived city evidence.

The current report summarizes InfoLoomBridge availability and panel names. Future report versions can promote more of the panel detail into the Markdown summary.

## Development

Run tests:

```powershell
python -m unittest discover -s tests -p "test_*.py"
```
