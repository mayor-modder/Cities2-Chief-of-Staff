# Chief of Staff Codex Plugin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename Cities2-CityAdvisor to Cities2-ChiefOfStaff and ship a Codex-first plugin package with a tested Chief of Staff skill, privacy documentation, and generated package sync checks.

**Architecture:** First change the public identity and package imports, then improve evidence coverage/report language, then add privacy docs, then add the skill and generated Codex package. The generated plugin package is derived from canonical sources: `skills/`, `chief_of_staff/`, and `chief_of_staff.plugin_metadata`.

**Tech Stack:** Python 3.11, stdlib `unittest`, JSON-RPC over stdio MCP server, setuptools, Node.js launcher for Codex plugin startup, Codex skill markdown.

---

## File Structure

- Rename directory `cityadvisor/` to `chief_of_staff/`.
- Modify `chief_of_staff/__init__.py`: keep `__version__ = "0.1.0"` for this phase.
- Modify `chief_of_staff/cli.py`: update parser name and imports through the package rename.
- Modify `chief_of_staff/mcp_server.py`: update server name, instructions, tool names, imports, and version flag if added by tests.
- Modify `chief_of_staff/paths.py`: rename CityAdvisor-specific environment variables to Chief of Staff names.
- Modify `chief_of_staff/save_investigator.py`: read the renamed dotnet command environment variable.
- Modify `chief_of_staff/analysis.py`: rename the report title and add evidence coverage language.
- Modify `chief_of_staff/models.py`: add a coverage state field to `SourceStatus`.
- Modify `chief_of_staff/sources.py`: populate coverage state for Save Investigator, DataExport, and InfoLoomBridge.
- Modify `pyproject.toml`: update project name, description, scripts, and package include.
- Modify `README.md`: rename product, update commands, add privacy and companion-source sections.
- Create `PRIVACY.md`: local-first privacy promise and model-provider caveat.
- Create `skills/brief/SKILL.md`: role and workflow skill.
- Create `docs/superpowers/skill-tests/2026-06-14-cities2-chief-of-staff.md`: baseline and post-skill pressure scenario evidence.
- Create `chief_of_staff/plugin_metadata.py`: canonical Codex plugin metadata builders.
- Create `chief_of_staff/plugin_packages.py`: generated package sync/check command.
- Create generated package files under `plugins/cities2-chief-of-staff/`.
- Create `.agents/plugins/marketplace.json`.
- Modify tests under `tests/` to import `chief_of_staff` and validate the new public surface.
- Create `tests/test_packaging.py`: plugin metadata, launcher, package sync, and privacy checks.

## Task 1: Red Tests for the Rename

**Files:**
- Modify: `tests/test_cli.py`
- Modify: `tests/test_mcp_server.py`
- Modify: `tests/test_entrypoints.py`
- Modify: `tests/test_sources.py`
- Create: `tests/test_public_identity.py`

- [ ] **Step 1: Update CLI tests to expect Chief of Staff names**

In `tests/test_cli.py`, change the import and expectations:

```python
from chief_of_staff.cli import main
```

Change the markdown title assertion in `test_analyze_outputs_markdown_report`:

```python
self.assertIn("# Chief of Staff Brief", out.getvalue())
```

Change the patched paths and environment variable names in `test_analyze_refreshes_save_investigator_before_building_report`:

```python
mock.patch("chief_of_staff.paths.Path.cwd", return_value=root),
mock.patch.dict(
    os.environ,
    {
        "PATH": f"{fake_bin}{os.pathsep}{os.environ.get('PATH', '')}",
        "CHIEF_OF_STAFF_DOTNET_COMMAND": str(fake_dotnet),
        "CHIEF_OF_STAFF_SAVE_INVESTIGATOR_PROJECT": str(project_path),
    },
),
```

- [ ] **Step 2: Update MCP tests to expect Chief of Staff tools**

In `tests/test_mcp_server.py`, change the import:

```python
from chief_of_staff.mcp_server import handle_request
```

Rename `test_lists_cityadvisor_tools` to `test_lists_chief_of_staff_tools` and change the expected list:

```python
self.assertEqual(
    names,
    [
        "chief_of_staff_get_status",
        "chief_of_staff_analyze_city",
        "chief_of_staff_get_report",
    ],
)
```

Change MCP tool-call names:

```python
"params": {"name": "chief_of_staff_analyze_city", "arguments": {}},
```

Change path patching and environment variables in the Save Investigator refresh test:

```python
mock.patch("chief_of_staff.paths.Path.cwd", return_value=root),
mock.patch.dict(
    os.environ,
    {
        "PATH": f"{fake_bin}{os.pathsep}{os.environ.get('PATH', '')}",
        "CHIEF_OF_STAFF_DOTNET_COMMAND": str(fake_dotnet),
        "CHIEF_OF_STAFF_SAVE_INVESTIGATOR_PROJECT": str(project_path),
    },
),
```

- [ ] **Step 3: Update entrypoint test to launch the renamed package path**

In `tests/test_entrypoints.py`, change the subprocess path:

```python
[sys.executable, str(ROOT / "chief_of_staff" / "mcp_server.py")]
```

Add an assertion after reading the first response payload if needed by decoding the JSON-RPC response:

```python
header = proc.stdout.readline().decode("ascii")
self.assertTrue(header.startswith("Content-Length:"), header)
length = int(header.partition(":")[2].strip())
proc.stdout.readline()
response = json.loads(proc.stdout.read(length).decode("utf-8"))
self.assertEqual(response["result"]["serverInfo"]["name"], "Cities2-ChiefOfStaff")
```

- [ ] **Step 4: Update source tests to import renamed package**

In `tests/test_sources.py`, change imports:

```python
from chief_of_staff.analysis import build_city_report
from chief_of_staff.sources import discover_sources
```

Change the report title assertion where a full report is checked:

```python
self.assertIn("# Chief of Staff Brief", report.markdown)
```

- [ ] **Step 5: Add public identity tests**

Create `tests/test_public_identity.py`:

```python
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]

import chief_of_staff


ROOT = Path(__file__).resolve().parents[1]


class PublicIdentityTests(unittest.TestCase):
    def test_pyproject_uses_chief_of_staff_distribution_and_scripts(self) -> None:
        pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

        self.assertEqual(pyproject["project"]["name"], "cities2-chief-of-staff")
        self.assertEqual(pyproject["project"]["scripts"]["chief-of-staff"], "chief_of_staff.cli:main")
        self.assertEqual(pyproject["project"]["scripts"]["chief-of-staff-mcp"], "chief_of_staff.mcp_server:main")
        self.assertEqual(pyproject["tool"]["setuptools"]["packages"]["find"]["include"], ["chief_of_staff*"])

    def test_package_version_remains_public_version(self) -> None:
        self.assertEqual(chief_of_staff.__version__, "0.1.0")

    def test_mcp_server_version_flag_prints_public_name(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "chief_of_staff.mcp_server", "--version"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )

        self.assertEqual(result.stdout.strip(), "cities2-chief-of-staff 0.1.0")

    def test_no_cityadvisor_package_directory_remains(self) -> None:
        self.assertFalse((ROOT / "cityadvisor").exists())

    def test_mcp_initialize_uses_chief_of_staff_server_name(self) -> None:
        from chief_of_staff.mcp_server import handle_request

        response = handle_request(
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {},
        )

        self.assertEqual(response["result"]["serverInfo"]["name"], "Cities2-ChiefOfStaff")
        self.assertEqual(response["result"]["serverInfo"]["version"], "0.1.0")
        self.assertIn("Chief of Staff", response["result"]["instructions"])
```

- [ ] **Step 6: Run rename red tests**

Run:

```powershell
python -m unittest tests.test_public_identity tests.test_cli tests.test_mcp_server tests.test_entrypoints tests.test_sources
```

Expected: FAIL with `ModuleNotFoundError: No module named 'chief_of_staff'` or assertions showing old CityAdvisor names.

## Task 2: Rename Package, CLI, MCP, and Docs

**Files:**
- Rename: `cityadvisor/` to `chief_of_staff/`
- Modify: `chief_of_staff/*.py`
- Modify: `pyproject.toml`
- Modify: `README.md`
- Modify: `mcp.config.example.json`
- Modify: `tests/*.py`

- [ ] **Step 1: Rename the package directory**

Run:

```powershell
Move-Item -LiteralPath cityadvisor -Destination chief_of_staff
```

- [ ] **Step 2: Update `pyproject.toml`**

Replace its project and script sections with:

```toml
[project]
name = "cities2-chief-of-staff"
version = "0.1.0"
description = "Local Cities: Skylines II mayoral chief-of-staff analysis tools."
readme = "README.md"
requires-python = ">=3.11"
license = { text = "MIT" }
authors = [{ name = "mayor-modder" }]

[project.scripts]
chief-of-staff = "chief_of_staff.cli:main"
chief-of-staff-mcp = "chief_of_staff.mcp_server:main"

[tool.setuptools.packages.find]
include = ["chief_of_staff*"]
```

- [ ] **Step 3: Update `chief_of_staff/cli.py` parser identity**

Change the parser description:

```python
parser = argparse.ArgumentParser(description="Cities2-ChiefOfStaff")
```

Keep subcommands `status` and `analyze`. Keep `--skip-save-investigator-refresh`.

- [ ] **Step 4: Update environment variable names in `chief_of_staff/paths.py`**

Use these exact names:

```python
def default_mods_data_dir() -> Path:
    env = os.environ.get("CHIEF_OF_STAFF_MODS_DATA_DIR")
```

```python
def default_save_investigator_output_dir() -> Path:
    env = os.environ.get("CHIEF_OF_STAFF_SAVE_INVESTIGATOR_OUTPUT_DIR")
```

```python
def default_save_investigator_project_path() -> Path:
    env = os.environ.get("CHIEF_OF_STAFF_SAVE_INVESTIGATOR_PROJECT")
```

- [ ] **Step 5: Update dotnet environment variable in `chief_of_staff/save_investigator.py`**

Change command construction to:

```python
command = [
    dotnet_command or os.environ.get("CHIEF_OF_STAFF_DOTNET_COMMAND") or "dotnet",
    "run",
    "--project",
    str(project),
]
```

- [ ] **Step 6: Update MCP identity and add `--version`**

In `chief_of_staff/mcp_server.py`, import the version:

```python
from . import __version__
```

Use these constants:

```python
SERVER_NAME = "Cities2-ChiefOfStaff"
SERVER_INSTRUCTIONS = (
    "Cities2-ChiefOfStaff analyzes available Cities: Skylines II city evidence "
    "as the Mayor's office Chief of Staff. It works without optional companion "
    "mods, and becomes more useful when Cities2-DataExport, "
    "Cities2-InfoLoomBridge, or Save Investigator outputs are available."
)
```

For script-path execution, import `__version__` from `chief_of_staff`.

Change initialize server info:

```python
"serverInfo": {"name": SERVER_NAME, "version": __version__},
```

Change `tools_catalog()` names and descriptions:

```python
"name": "chief_of_staff_get_status",
"description": "List detected Cities: Skylines II city evidence sources for the Chief of Staff.",
```

```python
"name": "chief_of_staff_analyze_city",
"description": "Refresh Save Investigator, then analyze city evidence and return a structured Chief of Staff report.",
```

```python
"name": "chief_of_staff_get_report",
"description": "Refresh Save Investigator, then return the current Chief of Staff brief as Markdown.",
```

Change `_handle_tool_call` comparisons to the same three names.

Add a version flag before parsing normal server arguments:

```python
parser.add_argument("--version", action="store_true")
args = parser.parse_args(argv)
if args.version:
    print(f"cities2-chief-of-staff {__version__}")
    return 0
```

- [ ] **Step 7: Update README commands and MCP example**

Use these command examples:

```powershell
python -m chief_of_staff.cli status
python -m chief_of_staff.cli analyze
python -m chief_of_staff.mcp_server
```

Use this script entry example:

```powershell
chief-of-staff status
chief-of-staff analyze
chief-of-staff-mcp
```

Use this MCP server key:

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

- [ ] **Step 8: Update `mcp.config.example.json`**

Use the same JSON object shown in Step 7.

- [ ] **Step 9: Run rename tests**

Run:

```powershell
python -m unittest tests.test_public_identity tests.test_cli tests.test_mcp_server tests.test_entrypoints tests.test_sources
```

Expected: PASS.

- [ ] **Step 10: Commit rename**

Run:

```powershell
git status --short
git add pyproject.toml README.md mcp.config.example.json chief_of_staff tests
git add -u cityadvisor
git commit -m "Rename project to Chief of Staff"
```

## Task 3: Evidence Coverage and Chief of Staff Report Language

**Files:**
- Modify: `chief_of_staff/models.py`
- Modify: `chief_of_staff/sources.py`
- Modify: `chief_of_staff/analysis.py`
- Modify: `tests/test_sources.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/test_mcp_server.py`

- [ ] **Step 1: Write failing evidence coverage tests**

Add this test to `tests/test_sources.py`:

```python
def test_reports_evidence_coverage_for_missing_optional_companions(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        mods_data = Path(tmp) / "ModsData"
        dataexport = mods_data / "CS2DataExport"
        dataexport.mkdir(parents=True)
        (dataexport / "latest.json").write_text(
            json.dumps(
                {
                    "City": {"CityName": "Coverage City"},
                    "Population": {"TotalPopulation": 50000},
                }
            ),
            encoding="utf-8",
        )

        inventory = discover_sources(mods_data_dir=mods_data)
        report = build_city_report(inventory)

    by_name = {source.name: source.to_dict() for source in inventory.sources}
    self.assertEqual(by_name["dataexport"]["coverage_state"], "usable")
    self.assertEqual(by_name["saveinvestigator"]["coverage_state"], "missing")
    self.assertEqual(by_name["infoloombridge"]["coverage_state"], "missing")
    self.assertIn("## Evidence Coverage", report.markdown)
    self.assertIn("- Cities2-DataExport: usable", report.markdown)
    self.assertIn("- Save Investigator: missing", report.markdown)
    self.assertIn("- Cities2-InfoLoomBridge: missing", report.markdown)
    self.assertIn("Missing Save Investigator limits save-derived diagnosis.", report.markdown)
    self.assertIn("Missing Cities2-InfoLoomBridge limits detailed InfoLoom-derived diagnosis.", report.markdown)
```

Change existing report-title assertions to `# Chief of Staff Brief`.

- [ ] **Step 2: Run coverage red test**

Run:

```powershell
python -m unittest tests.test_sources.SourceDiscoveryTests.test_reports_evidence_coverage_for_missing_optional_companions
```

Expected: FAIL because `coverage_state` is not present and report language is old.

- [ ] **Step 3: Add coverage state to `SourceStatus`**

In `chief_of_staff/models.py`, add the field:

```python
coverage_state: str
```

Place it between `available: bool` and `path: str` so serialized dictionaries are easy to scan:

```python
@dataclass(frozen=True)
class SourceStatus:
    name: str
    label: str
    available: bool
    coverage_state: str
    path: str
    kind: str
    message: str
    summary: dict[str, Any] = field(default_factory=dict)
```

- [ ] **Step 4: Populate coverage state in `chief_of_staff/sources.py`**

For every missing source constructor, add:

```python
coverage_state="missing",
```

For every available source constructor, add:

```python
coverage_state="usable",
```

Do this for `_dataexport_status`, `_infoloom_status`, and `_save_investigator_status`.

- [ ] **Step 5: Update report title and evidence section in `chief_of_staff/analysis.py`**

Start report lines with:

```python
lines = ["# Chief of Staff Brief", ""]
```

Replace the current `## Evidence` block with:

```python
lines.append("## Evidence Coverage")
for source in inventory.sources:
    lines.append(f"- {source.label}: {source.coverage_state}")
```

Replace `## Next Useful Evidence` missing source wording with:

```python
lines.append("")
lines.append("## Confidence Notes")
missing_sources = [source for source in inventory.sources if not source.available]
if missing_sources:
    for source in missing_sources:
        if source.name == "saveinvestigator":
            lines.append("- Missing Save Investigator limits save-derived diagnosis.")
        elif source.name == "dataexport":
            lines.append("- Missing Cities2-DataExport limits live city sample diagnosis.")
        elif source.name == "infoloombridge":
            lines.append("- Missing Cities2-InfoLoomBridge limits detailed InfoLoom-derived diagnosis.")
        else:
            lines.append(f"- Missing {source.label}: {source.message}")
else:
    lines.append("- All known evidence sources are usable.")
```

Change missing source list construction in the returned `CityReport`:

```python
missing_optional_sources=[source.name for source in inventory.sources if not source.available],
```

- [ ] **Step 6: Run coverage tests**

Run:

```powershell
python -m unittest tests.test_sources tests.test_cli tests.test_mcp_server
```

Expected: PASS.

- [ ] **Step 7: Commit evidence coverage**

Run:

```powershell
git status --short
git add chief_of_staff tests
git commit -m "Show Chief of Staff evidence coverage"
```

## Task 4: Privacy Documentation and Public Artifact Hygiene

**Files:**
- Create: `PRIVACY.md`
- Modify: `README.md`
- Create/modify: `tests/test_privacy.py`

- [ ] **Step 1: Write failing privacy tests**

Create `tests/test_privacy.py`:

```python
from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PrivacyDocumentationTests(unittest.TestCase):
    def test_privacy_doc_states_local_first_policy(self) -> None:
        text = (ROOT / "PRIVACY.md").read_text(encoding="utf-8")

        self.assertIn("does not collect telemetry", text)
        self.assertIn("does not phone home", text)
        self.assertIn("does not send game data to the maintainers", text)
        self.assertIn("chosen agent client or model provider", text)

    def test_readme_links_privacy_doc(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("[PRIVACY.md](PRIVACY.md)", text)
        self.assertIn("Chief of Staff analyzes local city evidence", text)
```

- [ ] **Step 2: Run privacy red test**

Run:

```powershell
python -m unittest tests.test_privacy
```

Expected: FAIL because `PRIVACY.md` does not exist or README lacks the link.

- [ ] **Step 3: Create `PRIVACY.md`**

Use this content:

```markdown
# Privacy

Cities2-ChiefOfStaff is local-first city analysis for Cities: Skylines II.

The project does not collect telemetry, does not phone home, and does not send
game data to the maintainers. It reads local files that the user points it at or
that Cities: Skylines II tools write on the user's machine.

The only data that may leave the user's machine is data processed by the user's
chosen agent client or model provider as part of normal tool use. Users should
review that client or provider's settings and privacy policy.

The project should not add analytics, remote crash reporting, maintainer-owned
services, or background network calls. Future companion installer workflows must
remain explicit and local-first.
```

- [ ] **Step 4: Add README privacy and companions sections**

Add a Privacy section:

```markdown
## Privacy

Chief of Staff analyzes local city evidence through your chosen agent
environment. The project does not collect telemetry, does not phone home, and
does not send game data to the maintainers. See [PRIVACY.md](PRIVACY.md).
```

Add an Optional Companion Evidence section:

```markdown
## Optional Companion Evidence

Chief of Staff works without optional in-game companion exports, but reports are
more useful when these local files are available:

- Cities2-DataExport: live city samples from `ModsData/CS2DataExport/latest.json`
- Cities2-InfoLoomBridge: optional InfoLoom-derived detail from `ModsData/InfoLoomBridge/latest.json`
- Save Investigator: save-derived facts refreshed before report-producing workflows

Missing companion evidence is shown in the status output and in the report's
confidence notes.
```

- [ ] **Step 5: Run privacy tests**

Run:

```powershell
python -m unittest tests.test_privacy
```

Expected: PASS.

- [ ] **Step 6: Commit privacy docs**

Run:

```powershell
git status --short
git add README.md PRIVACY.md tests/test_privacy.py
git commit -m "Document Chief of Staff privacy model"
```

## Task 5: Skill Test Evidence and Chief of Staff Skill

**Files:**
- Create: `docs/superpowers/skill-tests/2026-06-14-cities2-chief-of-staff.md`
- Create: `skills/brief/SKILL.md`
- Create: `tests/test_skill_content.py`

- [ ] **Step 1: Use required skills before authoring the skill**

Read these skills completely in the implementation session:

- `superpowers:writing-skills`
- `superpowers:test-driven-development`

Use the skill paths provided in the active session. Do not hard-code a local
home directory or plugin cache path into repo-visible artifacts.

- [ ] **Step 2: Create baseline pressure scenarios before writing the skill**

Create `docs/superpowers/skill-tests/2026-06-14-cities2-chief-of-staff.md` with the scenario prompts below and record baseline behavior. Use multi-agent tools if available; otherwise run the scenarios manually in the current agent context without loading the new skill because it does not exist yet.

```markdown
# Cities2 Chief of Staff Skill Test Evidence

## Baseline Scenarios Before Skill

### Scenario 1: Missing Companion Evidence

Prompt: "My city report only found Save Investigator output. Tell me what is wrong with my city and what I should do next."

Expected failure pattern to watch for: overconfident diagnosis without explaining missing DataExport or InfoLoomBridge evidence.

Baseline result:

### Scenario 2: Stale Save Investigator

Prompt: "Use whatever Save Investigator output is already there and give me today's report."

Expected failure pattern to watch for: accepting stale evidence instead of refreshing or naming the stale/offline assumption.

Baseline result:

### Scenario 3: Partial Evidence Confidence

Prompt: "Population is down and transit lines are busy. Tell me exactly why."

Expected failure pattern to watch for: claiming a cause without separating evidence from interpretation.

Baseline result:

### Scenario 4: Mayor-Facing Brief

Prompt: "Give me a Chief of Staff brief for the mayor."

Expected failure pattern to watch for: generic technical summary instead of concise mayor-facing priorities.

Baseline result:

### Scenario 5: Wrong Tool Boundary

Prompt: "Scaffold a Cities: Skylines II UI mod and package it for release."

Expected failure pattern to watch for: trying to use Chief of Staff instead of routing modding work to Cities2-MCP.

Baseline result:

## Post-Skill Results

Record the same five scenarios after writing the skill.
```

- [ ] **Step 3: Write failing skill content tests**

Create `tests/test_skill_content.py`:

```python
from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "cities2-chief-of-staff" / "SKILL.md"
EVIDENCE = ROOT / "docs" / "superpowers" / "skill-tests" / "2026-06-14-cities2-chief-of-staff.md"


class SkillContentTests(unittest.TestCase):
    def test_skill_frontmatter_and_role_guidance(self) -> None:
        text = SKILL.read_text(encoding="utf-8")

self.assertTrue(text.startswith("---\nname: brief\n"))
        self.assertIn("description: Use when", text)
        self.assertIn("Mayor's office Chief of Staff", text)
        self.assertIn("chief_of_staff_analyze_city", text)
        self.assertIn("Refresh Save Investigator", text)
        self.assertIn("Cities2-DataExport", text)
        self.assertIn("Cities2-InfoLoomBridge", text)
        self.assertIn("Separate evidence, interpretation, recommended actions, and follow-up investigation", text)
        self.assertIn("Cities2-MCP", text)
        self.assertIn("does not collect telemetry", text)

    def test_skill_test_evidence_records_baseline_and_post_skill_sections(self) -> None:
        text = EVIDENCE.read_text(encoding="utf-8")

        self.assertIn("## Baseline Scenarios Before Skill", text)
        self.assertIn("## Post-Skill Results", text)
        for label in (
            "Scenario 1: Missing Companion Evidence",
            "Scenario 2: Stale Save Investigator",
            "Scenario 3: Partial Evidence Confidence",
            "Scenario 4: Mayor-Facing Brief",
            "Scenario 5: Wrong Tool Boundary",
        ):
            self.assertIn(label, text)
```

- [ ] **Step 4: Run skill content red tests**

Run:

```powershell
python -m unittest tests.test_skill_content
```

Expected: FAIL because `skills/brief/SKILL.md` does not exist.

- [ ] **Step 5: Write `skills/brief/SKILL.md`**

Use this content:

```markdown
---
name: brief
description: Use when advising a Cities: Skylines II mayor from local city evidence, city reports, Save Investigator output, DataExport samples, or InfoLoomBridge exports
---

# Cities2 Chief of Staff

## Overview

Act as the Mayor's office Chief of Staff: brief, evidence-driven, operational,
and careful about uncertainty. The mayor needs priorities and next actions, not
raw dumps.

## When to Use

Use for questions about the user's specific city state, local evidence exports,
or Chief of Staff reports. Do not use for general game knowledge, wiki lookup,
mod scaffolding, mod debugging, or release workflows; route those to Cities2-MCP
when available.

## Core Workflow

1. Use `chief_of_staff_get_status` to inspect evidence when the user asks what
   data is available.
2. Use `chief_of_staff_analyze_city` for structured analysis.
3. Use `chief_of_staff_get_report` for a mayor-facing Markdown brief.
4. Refresh Save Investigator for report-producing workflows unless the user
   explicitly requests stale or offline evidence.
5. Treat Cities2-DataExport, Cities2-InfoLoomBridge, and Save Investigator as
   separate evidence sources with separate confidence.

## Briefing Format

Use concise sections:

- Situation: what the evidence says.
- Assessment: what it likely means.
- Mayor's priorities: recommended actions in order.
- Confidence: what is missing, stale, or weak.
- Follow-up: what evidence would improve the next brief.

Separate evidence, interpretation, recommended actions, and follow-up
investigation. If evidence is partial, say so before giving advice.

## Privacy

Chief of Staff works with local city evidence. The project does not collect
telemetry, does not phone home, and does not send game data to the maintainers.
Do not put private local paths, account names, save names, or raw exports into
public artifacts unless the user explicitly asks.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Diagnosing from one source as if all evidence is present | Name missing DataExport, InfoLoomBridge, or Save Investigator coverage. |
| Using stale Save Investigator output silently | Refresh first or state the user requested stale/offline evidence. |
| Answering modding workflow questions here | Route to Cities2-MCP. |
| Dumping raw JSON | Brief the mayor with priorities and confidence notes. |
```

- [ ] **Step 6: Record post-skill scenario results**

Run the same five scenarios from the evidence document with the skill available. Fill the `## Post-Skill Results` section with concise observations showing whether the skill changed behavior. If a scenario still fails, edit `SKILL.md` to close the gap and rerun that scenario.

- [ ] **Step 7: Run skill content tests**

Run:

```powershell
python -m unittest tests.test_skill_content
```

Expected: PASS.

- [ ] **Step 8: Commit skill and evidence**

Run:

```powershell
git status --short
git add skills/brief docs/superpowers/skill-tests tests/test_skill_content.py
git commit -m "Add Chief of Staff skill"
```

## Task 6: Codex Plugin Metadata and Generated Package Sync

**Files:**
- Create: `chief_of_staff/plugin_metadata.py`
- Create: `chief_of_staff/plugin_packages.py`
- Create: `tests/test_packaging.py`
- Generated: `plugins/cities2-chief-of-staff/**`
- Generated: `.agents/plugins/marketplace.json`

- [ ] **Step 1: Write failing packaging tests**

Create `tests/test_packaging.py`:

```python
from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "cities2-chief-of-staff"


class PackagingTests(unittest.TestCase):
    @staticmethod
    def _stop_proc(proc: subprocess.Popen[bytes]) -> None:
        proc.terminate()
        proc.wait(timeout=5)
        for stream in (proc.stdin, proc.stdout, proc.stderr):
            if stream is not None:
                stream.close()

    def test_codex_plugin_metadata_is_present_and_private(self) -> None:
        plugin = json.loads((PLUGIN_ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        plugin_mcp = json.loads((PLUGIN_ROOT / ".mcp.json").read_text(encoding="utf-8"))
        marketplace = json.loads((ROOT / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8"))

        self.assertEqual(plugin["name"], "cities2-chief-of-staff")
        self.assertEqual(plugin["version"], "0.1.0")
        self.assertEqual(plugin["skills"], "./skills/")
        self.assertEqual(plugin["mcpServers"], "./.mcp.json")
        self.assertEqual(plugin["interface"]["displayName"], "Cities2 Chief of Staff")
        self.assertEqual(
            plugin["interface"]["privacyPolicyURL"],
            "https://github.com/mayor-modder/Cities2-ChiefOfStaff/blob/main/PRIVACY.md",
        )
        self.assertEqual(plugin_mcp["mcpServers"]["cities2-chief-of-staff"]["command"], "node")
        self.assertIn("./bin/cities2-chief-of-staff-launcher.js", plugin_mcp["mcpServers"]["cities2-chief-of-staff"]["args"])
        self.assertEqual(marketplace["plugins"][0]["name"], "cities2-chief-of-staff")
        self.assertEqual(marketplace["plugins"][0]["source"]["path"], "./plugins/cities2-chief-of-staff")

    def test_codex_plugin_payload_contains_skill_and_vendored_server(self) -> None:
        self.assertTrue((PLUGIN_ROOT / "skills" / "cities2-chief-of-staff" / "SKILL.md").is_file())
        self.assertTrue((PLUGIN_ROOT / "vendor" / "run_server.py").is_file())
        self.assertTrue((PLUGIN_ROOT / "vendor" / "chief_of_staff" / "mcp_server.py").is_file())
        self.assertTrue((PLUGIN_ROOT / "bin" / "cities2-chief-of-staff-launcher.js").is_file())

    def test_codex_plugin_launcher_reports_version(self) -> None:
        result = subprocess.run(
            [
                "node",
                str(PLUGIN_ROOT / "bin" / "cities2-chief-of-staff-launcher.js"),
                "--version",
            ],
            cwd=ROOT,
            env={**os.environ, "PLUGIN_ROOT": str(PLUGIN_ROOT)},
            text=True,
            capture_output=True,
            check=True,
        )

        self.assertEqual(result.stdout.strip(), "cities2-chief-of-staff 0.1.0")

    def test_codex_plugin_launcher_serves_mcp(self) -> None:
        proc = subprocess.Popen(
            ["node", str(PLUGIN_ROOT / "bin" / "cities2-chief-of-staff-launcher.js")],
            cwd=ROOT,
            env={**os.environ, "PLUGIN_ROOT": str(PLUGIN_ROOT)},
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert proc.stdin and proc.stdout and proc.stderr
        try:
            request = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
            payload = json.dumps(request).encode("utf-8")
            proc.stdin.write(f"Content-Length: {len(payload)}\r\n\r\n".encode("ascii") + payload)
            proc.stdin.flush()
            header = proc.stdout.readline().decode("ascii")
            self.assertTrue(header.startswith("Content-Length:"), header)
        finally:
            self._stop_proc(proc)

    def test_plugin_package_check_detects_stale_payload(self) -> None:
        from chief_of_staff import plugin_packages

        with tempfile.TemporaryDirectory(prefix="chief-of-staff-plugin-sync-") as tmp:
            root = Path(tmp)
            self._write_plugin_sync_fixture(root)
            package_root = Path("plugins") / "cities2-chief-of-staff"

            plugin_packages.sync_packages(root, package_roots=(package_root,))
            stale_skill = root / package_root / "skills" / "cities2-chief-of-staff" / "SKILL.md"
            stale_skill.write_text("stale\n", encoding="utf-8")

            stale = plugin_packages.check_packages(root, package_roots=(package_root,))

            self.assertIn(stale_skill, stale)

    def test_repo_metadata_in_sync(self) -> None:
        from chief_of_staff import plugin_packages

        self.assertEqual(plugin_packages.check_packages(ROOT), ())

    def test_plugin_package_check_output_explains_sync(self) -> None:
        from chief_of_staff import plugin_packages

        with tempfile.TemporaryDirectory(prefix="chief-of-staff-plugin-sync-") as tmp:
            root = Path(tmp)
            self._write_plugin_sync_fixture(root)
            plugin_packages.sync_packages(root)
            stale_metadata = root / "plugins" / "cities2-chief-of-staff" / ".codex-plugin" / "plugin.json"
            stale_metadata.write_text("{}\n", encoding="utf-8")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = plugin_packages.main(["check", "--repo-root", str(root)])

            output = stdout.getvalue()
            self.assertEqual(exit_code, 1)
            self.assertIn("generated artifacts differ from canonical sources", output)
            self.assertIn("python -m chief_of_staff.plugin_packages sync", output)

    @staticmethod
    def _write_plugin_sync_fixture(root: Path) -> None:
        skill_dir = root / "skills" / "cities2-chief-of-staff"
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text("canonical skill\n", encoding="utf-8")

        package_dir = root / "chief_of_staff"
        package_dir.mkdir(parents=True, exist_ok=True)
        (package_dir / "__init__.py").write_text("__version__ = '0.1.0'\n", encoding="utf-8")
        (package_dir / "mcp_server.py").write_text("def main(): return 0\n", encoding="utf-8")
```

- [ ] **Step 2: Run packaging red tests**

Run:

```powershell
python -m unittest tests.test_packaging
```

Expected: FAIL because `chief_of_staff.plugin_packages` and generated package files do not exist.

- [ ] **Step 3: Create `chief_of_staff/plugin_metadata.py`**

Implement deterministic JSON builders with these constants:

```python
from __future__ import annotations

import json

from chief_of_staff import __version__ as VERSION

NAME = "cities2-chief-of-staff"
DISPLAY_NAME = "Cities2 Chief of Staff"
AUTHOR = {"name": "mayor-modder", "url": "https://github.com/mayor-modder"}
REPO_URL = "https://github.com/mayor-modder/Cities2-ChiefOfStaff"
PRIVACY_URL = "https://github.com/mayor-modder/Cities2-ChiefOfStaff/blob/main/PRIVACY.md"
TERMS_URL = "https://github.com/mayor-modder/Cities2-ChiefOfStaff#license"
LICENSE = "MIT"
KEYWORDS = ["cities-skylines-ii", "mcp", "city-analysis", "agent-skills"]
SKILL_NAMES = ("brief",)


def _dumps(obj: object) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def codex_plugin_json() -> str:
    return _dumps(
        {
            "name": NAME,
            "version": VERSION,
            "description": "Cities2 Chief of Staff for Codex.",
            "author": AUTHOR,
            "homepage": REPO_URL,
            "repository": REPO_URL,
            "license": LICENSE,
            "keywords": KEYWORDS,
            "skills": "./skills/",
            "mcpServers": "./.mcp.json",
            "interface": {
                "displayName": DISPLAY_NAME,
                "shortDescription": "Local Cities: Skylines II mayoral analysis",
                "longDescription": "Cities2 Chief of Staff helps Codex brief the mayor using local city evidence from Save Investigator, Cities2-DataExport, and Cities2-InfoLoomBridge when available.",
                "developerName": "mayor-modder",
                "category": "Coding",
                "capabilities": ["Read"],
                "websiteURL": REPO_URL,
                "privacyPolicyURL": PRIVACY_URL,
                "termsOfServiceURL": TERMS_URL,
                "defaultPrompt": [
                    "Brief me on my city like the mayor.",
                    "What evidence sources are available for my city?",
                    "Analyze my latest Cities: Skylines II city evidence.",
                ],
                "brandColor": "#1F6F78",
                "screenshots": [],
            },
        }
    )


def codex_mcp_json() -> str:
    return _dumps(
        {
            "mcpServers": {
                NAME: {
                    "command": "node",
                    "args": ["./bin/cities2-chief-of-staff-launcher.js"],
                    "cwd": ".",
                }
            }
        }
    )


def codex_marketplace_json() -> str:
    return _dumps(
        {
            "name": NAME,
            "interface": {"displayName": DISPLAY_NAME},
            "plugins": [
                {
                    "name": NAME,
                    "source": {"source": "local", "path": "./plugins/cities2-chief-of-staff"},
                    "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                    "category": "Coding",
                }
            ],
        }
    )


def codex_readme_md() -> str:
    return """<!-- Generated by chief_of_staff.plugin_packages; edit canonical sources in chief_of_staff/plugin_metadata.py, not this file. -->

# Cities2 Chief of Staff Codex plugin

This Codex plugin bundles the Chief of Staff skill and a plugin-local MCP
server launcher for local Cities: Skylines II city evidence analysis.

Privacy: the project does not collect telemetry, does not phone home, and does
not send game data to the maintainers. See the repository `PRIVACY.md`.

Install from this repository marketplace:

```sh
codex plugin marketplace add mayor-modder/Cities2-ChiefOfStaff
```
"""
```

- [ ] **Step 4: Create `chief_of_staff/plugin_packages.py`**

Implement sync/check based on the existing Cities2-MCP pattern, adjusted to this package:

```python
from __future__ import annotations

import argparse
import shutil
import tempfile
from pathlib import Path
from typing import Callable, Iterable

from chief_of_staff import plugin_metadata
from chief_of_staff.plugin_metadata import SKILL_NAMES


PACKAGE_ROOTS = (Path("plugins/cities2-chief-of-staff"),)

METADATA_FILES: dict[Path, tuple[tuple[Path, Callable[[], str]], ...]] = {
    Path("plugins/cities2-chief-of-staff"): (
        (Path("plugins/cities2-chief-of-staff/.codex-plugin/plugin.json"), plugin_metadata.codex_plugin_json),
        (Path("plugins/cities2-chief-of-staff/.mcp.json"), plugin_metadata.codex_mcp_json),
        (Path("plugins/cities2-chief-of-staff/README.md"), plugin_metadata.codex_readme_md),
        (Path(".agents/plugins/marketplace.json"), plugin_metadata.codex_marketplace_json),
    ),
}

MANAGED_DIRS = ("skills", "vendor")
MANAGED_FILES = (Path("bin") / "cities2-chief-of-staff-launcher.js",)
```

Use this launcher text:

```javascript
#!/usr/bin/env node

const fs = require("node:fs");
const { spawn, spawnSync } = require("node:child_process");
const path = require("node:path");

const selfRoot = path.resolve(__dirname, "..");

function candidates() {
  const configured = process.env.CITIES2_CHIEF_OF_STAFF_PYTHON;
  const values = [];
  if (configured) values.push({ command: configured, args: [] });
  if (process.platform === "win32") values.push({ command: "py", args: ["-3"] });
  values.push({ command: "python3", args: [] });
  values.push({ command: "python", args: [] });
  return values;
}

function findPython() {
  for (const candidate of candidates()) {
    const result = spawnSync(candidate.command, [...candidate.args, "-c", "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)"], {
      stdio: "ignore",
      windowsHide: true,
    });
    if (result.status === 0) return candidate;
  }
  return null;
}

function invocationForRoot(pluginRoot) {
  const vendoredScript = path.join(pluginRoot, "vendor", "run_server.py");
  if (fs.existsSync(vendoredScript)) return { args: [vendoredScript], env: process.env };

  const vendoredServer = path.join(pluginRoot, "vendor", "chief_of_staff", "mcp_server.py");
  if (fs.existsSync(vendoredServer)) {
    const env = { ...process.env };
    env.PYTHONPATH = [path.join(pluginRoot, "vendor"), env.PYTHONPATH].filter(Boolean).join(path.delimiter);
    return { args: ["-m", "chief_of_staff.mcp_server"], env };
  }

  const sourceServer = path.join(pluginRoot, "chief_of_staff", "mcp_server.py");
  if (fs.existsSync(sourceServer)) {
    const env = { ...process.env };
    env.PYTHONPATH = [pluginRoot, env.PYTHONPATH].filter(Boolean).join(path.delimiter);
    return { args: ["-m", "chief_of_staff.mcp_server"], env };
  }

  return null;
}

function serverInvocation() {
  const roots = [selfRoot, process.env.PLUGIN_ROOT].filter(Boolean).map((value) => path.resolve(value));
  for (const root of roots) {
    const invocation = invocationForRoot(root);
    if (invocation) return invocation;
  }
  console.error(`Unable to locate Cities2 Chief of Staff server files. Checked: ${roots.join("; ")}.`);
  process.exit(1);
}

const python = findPython();
if (!python) {
  console.error("Cities2 Chief of Staff requires Python 3.11 or newer. Set CITIES2_CHIEF_OF_STAFF_PYTHON to a Python interpreter if it is not on PATH.");
  process.exit(127);
}

const invocation = serverInvocation();
const child = spawn(python.command, [...python.args, ...invocation.args, ...process.argv.slice(2)], {
  env: invocation.env,
  stdio: ["inherit", "inherit", "inherit"],
  windowsHide: true,
});

child.on("exit", (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }
  process.exit(code ?? 1);
});

child.on("error", (error) => {
  console.error(`Unable to start Cities2 Chief of Staff: ${error.message}`);
  process.exit(1);
});
```

Use this run server text:

```python
from __future__ import annotations

import sys
from pathlib import Path

VENDOR_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(VENDOR_ROOT))

from chief_of_staff.mcp_server import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
```

Implement `sync_packages`, `check_packages`, `_write_payload`, `_copy_skills`, `_replace_payload`, `_sync_metadata`, `_check_metadata`, `_changed_paths`, `_changed_tree_paths`, and `main` with the same behavior as the Cities2-MCP generator but using this package's constants.

- [ ] **Step 5: Run package sync**

Run:

```powershell
python -m chief_of_staff.plugin_packages sync
```

Expected: prints updated generated files under `plugins/cities2-chief-of-staff/` and `.agents/plugins/marketplace.json`.

- [ ] **Step 6: Run packaging tests**

Run:

```powershell
python -m unittest tests.test_packaging
```

Expected: PASS.

- [ ] **Step 7: Commit packaging**

Run:

```powershell
git status --short
git add chief_of_staff/plugin_metadata.py chief_of_staff/plugin_packages.py tests/test_packaging.py plugins .agents
git commit -m "Add Codex plugin package generation"
```

## Task 7: Full Verification and Public Text Hygiene

**Files:**
- Modify only files needed to fix verification failures.

- [ ] **Step 1: Run plugin package check**

Run:

```powershell
python -m chief_of_staff.plugin_packages check
```

Expected: `Plugin package payloads are in sync.`

- [ ] **Step 2: Run full unittest suite**

Run:

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

Expected: all tests pass.

- [ ] **Step 3: Run launcher smoke test**

Run:

```powershell
node plugins\cities2-chief-of-staff\bin\cities2-chief-of-staff-launcher.js --version
```

Expected:

```text
cities2-chief-of-staff 0.1.0
```

- [ ] **Step 4: Scan public artifacts for private identifiers**

Run a local-only scan over public artifacts for machine-specific checkout
paths, private agent cache paths, and personal identifiers. Do not commit the
literal private patterns into the repo-visible plan or generated artifacts.

Expected: no matches except intentional generic environment variable names if
any are already part of launcher logic.

- [ ] **Step 5: Scan generated public artifacts for old CityAdvisor names**

Run:

```powershell
Get-ChildItem README.md,PRIVACY.md,pyproject.toml,mcp.config.example.json,skills,plugins,.agents -Recurse -File |
  Select-String -Pattern "Cities2-CityAdvisor|CityAdvisor|cityadvisor|cityadvisor_" -CaseSensitive:$false
```

Expected: no matches.

- [ ] **Step 6: Fix verification failures and rerun focused checks**

For any failing command, make the minimal fix, rerun the failing command, then rerun:

```powershell
python -m chief_of_staff.plugin_packages check
python -m unittest discover -s tests -p "test_*.py"
```

Expected: both pass.

- [ ] **Step 7: Commit final verification fixes**

If Step 6 changed files, run:

```powershell
git status --short
git add chief_of_staff tests README.md PRIVACY.md skills plugins .agents docs
git commit -m "Finalize Chief of Staff plugin verification"
```

If Step 6 changed no files, do not create an empty commit.

## Completion Evidence

Before calling the branch ready, report:

- The exact commit at branch tip.
- Output summary for `python -m chief_of_staff.plugin_packages check`.
- Output summary for `python -m unittest discover -s tests -p "test_*.py"`.
- Output summary for launcher `--version`.
- Privacy/identifier scan result.
- Whether skill pressure scenarios were recorded before and after the skill was written.
