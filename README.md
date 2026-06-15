# Cities2-Chief-of-Staff

Cities2-Chief-of-Staff is a local mayoral chief-of-staff analysis layer for Cities: Skylines II city evidence.

It is separate from:

- `Cities2-MCP`, which is for wiki knowledge and mod project workflows
- `Cities2-DataExport`, which is an in-game mod that writes city snapshots
- `Cities2-InfoLoomBridge`, which writes selected InfoLoom-derived data

Chief of Staff reads whatever local evidence is available and turns it into briefs an agent or human can use.

Install the Codex plugin with [INSTALL.md](INSTALL.md).

## Privacy

Chief of Staff analyzes local city evidence through your chosen agent
environment. The project does not collect telemetry, does not phone home, and
does not send game data to the maintainers. See [PRIVACY.md](PRIVACY.md).

## Current First Version

This first version can:

- detect `Cities2-DataExport` output at `ModsData/CS2DataExport/latest.json`
- detect `Cities2-InfoLoomBridge` output at `ModsData/InfoLoomBridge/latest.json`
- detect the newest Save Investigator output directory
- include the Save Investigator source under `tools/SaveInvestigator`
- produce a Markdown city brief
- expose the same brief/status through a small MCP server

Only Python is required for the current Chief of Staff layer. Optional evidence sources make briefs better, but they are not required for the tool to start.

## Optional Companion Evidence

Chief of Staff works without optional in-game companion exports, but reports are
more useful when these local files are available:

- Cities2-DataExport: live city samples from `ModsData/CS2DataExport/latest.json`
- Cities2-InfoLoomBridge: optional InfoLoom-derived detail from `ModsData/InfoLoomBridge/latest.json`
- Save Investigator: save-derived facts refreshed before report-producing workflows

Missing companion evidence is shown in the status output and in the report's
confidence notes.

## Command Line

Show detected sources:

```powershell
python -m chief_of_staff.cli status
```

Build a brief:

```powershell
python -m chief_of_staff.cli analyze
```

`analyze` refreshes Save Investigator before building the brief when
`tools/SaveInvestigator/SaveInvestigator.csproj` is available. This keeps
agent-generated briefs from silently using stale save evidence. Use `status`
when you only want to inspect currently detected evidence without running a new
save investigation.

Use explicit paths:

```powershell
python -m chief_of_staff.cli analyze `
  --mods-data "$env:USERPROFILE\AppData\LocalLow\Colossal Order\Cities Skylines II\ModsData" `
  --save-path "$env:USERPROFILE\AppData\LocalLow\Colossal Order\Cities Skylines II\Saves\<steam-id>\<save>.cok" `
  --save-investigator-output "C:\path\to\SaveInvestigator\output"
```

Use an existing Save Investigator output without refreshing:

```powershell
python -m chief_of_staff.cli analyze --skip-save-investigator-refresh
```

Print JSON:

```powershell
python -m chief_of_staff.cli analyze --json
```

Installed console scripts:

```powershell
chief-of-staff status
chief-of-staff analyze
```

## MCP Server

Start the MCP server with:

```powershell
python -m chief_of_staff.mcp_server
```

Installed MCP console script:

```powershell
chief-of-staff-mcp
```

Available MCP tools:

- `chief_of_staff_get_status`
- `chief_of_staff_analyze_city` refreshes Save Investigator first
- `chief_of_staff_get_report` refreshes Save Investigator first

Example MCP config:

```json
{
  "mcpServers": {
    "cities2-chief-of-staff": {
      "command": "<PYTHON_PATH>",
      "args": [
        "<REPO_ROOT>/chief_of_staff/mcp_server.py",
        "--mods-data",
        "<MODS_DATA_DIR>",
        "--save-investigator-output",
        "<SAVE_INVESTIGATOR_OUTPUT_DIR>"
      ]
    }
  }
}
```

## Evidence Sources

### Save Investigator

Save Investigator is the default save-analysis provider for Chief of Staff. Its source is included under:

```text
tools/SaveInvestigator
```

Chief of Staff reads the JSON artifacts it writes, such as:

- `city-state-report-facts.json`
- `transport-report-facts.json`

`chief-of-staff analyze` and the report-producing MCP tools run Save Investigator before building a brief. Use `--skip-save-investigator-refresh` only when you explicitly want to inspect existing output offline.

### Cities2-DataExport

If present, Chief of Staff reads:

```text
ModsData/CS2DataExport/latest.json
```

This provides live city sample data such as population, city name, workforce, transport proxies, and other exported groups.

### Cities2-InfoLoomBridge

If present, Chief of Staff reads:

```text
ModsData/InfoLoomBridge/latest.json
```

This can add more detailed InfoLoom-derived city evidence.

## Development

Run tests:

```powershell
python -m unittest discover -s tests -p "test_*.py"
```
