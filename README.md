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
- produce a Markdown city report
- expose the same report/status through a small MCP server

Only Python is required for the current CityAdvisor layer. Optional evidence sources make reports better, but they are not required for the tool to start.

## Command Line

Show detected sources:

```powershell
python -m cityadvisor.cli status
```

Build a report:

```powershell
python -m cityadvisor.cli analyze
```

Use explicit paths:

```powershell
python -m cityadvisor.cli analyze `
  --mods-data "$env:USERPROFILE\AppData\LocalLow\Colossal Order\Cities Skylines II\ModsData" `
  --save-investigator-output "C:\path\to\SaveInvestigator\output"
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

Available MCP tools:

- `cityadvisor_get_status`
- `cityadvisor_analyze_city`
- `cityadvisor_get_report`

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
        "--save-investigator-output",
        "<SAVE_INVESTIGATOR_OUTPUT_DIR>"
      ]
    }
  }
}
```

## Evidence Sources

### Save Investigator

Save Investigator is the default save-analysis provider for CityAdvisor. Its source is included under:

```text
tools/SaveInvestigator
```

CityAdvisor reads the JSON artifacts it writes, such as:

- `city-state-report-facts.json`
- `transport-report-facts.json`

The next integration step is to add a CityAdvisor command that builds/runs Save Investigator directly and then refreshes the report.

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

## Development

Run tests:

```powershell
python -m unittest discover -s tests -p "test_*.py"
```
