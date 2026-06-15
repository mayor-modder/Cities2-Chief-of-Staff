# Install Cities2 Chief of Staff

Cities2 Chief of Staff is a Codex plugin for local Cities: Skylines II city
briefing. The plugin bundles the Chief of Staff skill and MCP server launcher.

Your city evidence stays local to your machine and your chosen agent
environment. The project does not collect telemetry, does not phone home, and
does not send game data to the maintainers. See [PRIVACY.md](PRIVACY.md).

## Install In Codex CLI

In your system terminal, add this repository as a Codex plugin marketplace:

```sh
codex plugin marketplace add mayor-modder/Cities2-Chief-of-Staff
```

Then start Codex from the folder where you want to work:

```sh
codex
```

Enter `/plugin`, install **Cities2 Chief of Staff**, then restart Codex.

## Install In The Codex App

1. Open the Codex app and choose **Plugins** from the sidebar.
2. Next to the "Search plugins" input, click **Built by OpenAI**.
3. Click **+ Add more**.
4. Enter source `mayor-modder/Cities2-Chief-of-Staff` and click **Add Marketplace**.
5. Install and enable **Cities2 Chief of Staff**.
6. Fully exit Codex and restart.

## Use The Skill

Type `$` and choose `cities2-chief-of-staff`, or invoke it directly:

```text
$cities2-chief-of-staff:cities2-chief-of-staff Brief me on my city like the mayor.
```

```text
$cities2-chief-of-staff:cities2-chief-of-staff What evidence sources are available for my city?
```

```text
$cities2-chief-of-staff:cities2-chief-of-staff Analyze my latest Cities: Skylines II city evidence.
```

You can also check available skills with `/skills`.

## Evidence Sources

Chief of Staff works without optional companion exports, but the brief is more
useful when more local evidence is available:

- Save Investigator: bundled in this repository and refreshed by report-producing workflows when available.
- Cities2-DataExport: optional live city samples from `ModsData/CS2DataExport/latest.json`.
- Cities2-InfoLoomBridge: optional InfoLoom-derived detail from `ModsData/InfoLoomBridge/latest.json`.

Cities2-DataExport and Cities2-InfoLoomBridge are not bundled by this plugin.
Install them separately only if you want those extra evidence sources.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Plugin does not appear after install | Fully quit and restart Codex. |
| Skill appears but MCP tools are unavailable | Restart Codex after enabling the plugin. |
| Brief says evidence is missing | Confirm the optional companion mod wrote its `latest.json`, or run with the evidence you have. Missing companion evidence is expected and shown in the confidence notes. |
| Save Investigator output looks stale | Use normal report-producing workflows so Chief of Staff refreshes Save Investigator first. Use stale/offline output only when you explicitly pass the skip refresh option from the CLI or MCP config. |

## Source Checkout

For local development, clone the repository and run:

```sh
python -m unittest discover -s tests -p "test_*.py"
python -m chief_of_staff.plugin_packages check
```

To refresh generated plugin package files after changing canonical sources:

```sh
python -m chief_of_staff.plugin_packages sync
```
