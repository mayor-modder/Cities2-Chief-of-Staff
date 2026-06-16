# Cities2 Chief of Staff Codex Plugin Design

## Purpose

Rename Cities2-CityAdvisor to Cities2-ChiefOfStaff and package it as a Codex
plugin first. The project remains a local city-evidence analysis layer for
Cities: Skylines II, but its agent-facing identity becomes the Mayor's office
Chief of Staff: evidence-driven, operational, privacy-preserving, and focused
on advising the player as mayor.

This phase does not add Claude or Antigravity packages. It should leave the
packaging boundaries clean enough to add those distributions later without
redesigning the generator.

## Identity and Scope

This is a clean rename, not a compatibility transition. There are no external
users to preserve old names for, so the implementation should remove the old
CityAdvisor public surface instead of keeping aliases.

Planned identity changes:

- Project/user-facing name: Cities2-ChiefOfStaff.
- Python distribution name: `cities2-chief-of-staff`.
- Python package: `cityadvisor` to `chief_of_staff`.
- CLI scripts: `cityadvisor` and `cityadvisor-mcp` to `chief-of-staff` and
  `chief-of-staff-mcp`.
- MCP server name: `Cities2-CityAdvisor` to `Cities2-ChiefOfStaff`.
- MCP tools: `cityadvisor_get_status`, `cityadvisor_analyze_city`, and
  `cityadvisor_get_report` to `chief_of_staff_get_status`,
  `chief_of_staff_analyze_city`, and `chief_of_staff_get_report`.
- Codex plugin name: `cities2-chief-of-staff`.
- Skill name: `brief`.

The Chief of Staff role should brief the mayor on current city conditions,
surface risks, recommend priorities, and name missing evidence that would
improve confidence.

## Independence from Cities2-MCP

Chief of Staff is independent from Cities2-MCP. It must not depend on, vendor,
or require the Cities2-MCP wiki corpus, mod scaffolding workflows, or MCP
server.

The two projects are complementary:

- Chief of Staff owns local city evidence analysis, reports, and mayor-facing
  advice.
- Cities2-MCP owns game knowledge, wiki/encyclopedia retrieval, and modding
  workflows.

When both plugins are installed, skills should route cleanly. Questions about a
specific city state or exported evidence belong to Chief of Staff. Questions
about game mechanics, mod scaffolding, mod debugging, or releases belong to
Cities2-MCP. Some workflows may use both, but neither package should require
the other.

## Codex Packaging Architecture

Mirror the Cities2-MCP Codex plugin packaging pattern, scaled down for this
project:

- Add canonical plugin metadata builders in `chief_of_staff/plugin_metadata.py`.
- Add a generated package sync/check command in
  `chief_of_staff/plugin_packages.py`.
- Generate the Codex package at `plugins/cities2-chief-of-staff/`.
- Generate `plugins/cities2-chief-of-staff/.codex-plugin/plugin.json`.
- Generate `plugins/cities2-chief-of-staff/.mcp.json`.
- Generate `plugins/cities2-chief-of-staff/README.md`.
- Generate `.agents/plugins/marketplace.json`.
- Generate `plugins/cities2-chief-of-staff/bin/cities2-chief-of-staff-launcher.js`.
- Vendor the Python package into
  `plugins/cities2-chief-of-staff/vendor/chief_of_staff/`.
- Add `plugins/cities2-chief-of-staff/vendor/run_server.py`.

The launcher should find Python 3.11 or newer, support a configurable
`CITIES2_CHIEF_OF_STAFF_PYTHON` interpreter environment variable, and run the
vendored MCP server without requiring a separate package install.

The generated package check should fail when generated metadata, skills,
launcher, or vendored package payloads drift from canonical sources.

## Chief of Staff Skill

Add one Codex skill at `skills/brief/SKILL.md` and include it
in the generated plugin package.

The skill should teach the agent to embody the Mayor's office Chief of Staff:

- Use Chief of Staff MCP tools when available for local city evidence.
- Refresh Save Investigator before report-producing workflows unless the user
  explicitly requests stale or offline evidence.
- Treat Save Investigator, Cities2-DataExport, and Cities2-InfoLoomBridge as
  evidence sources with separate coverage and freshness.
- Separate observed evidence, interpretation, recommended mayoral actions, and
  follow-up investigation.
- Avoid overconfident diagnosis from partial evidence.
- Route game knowledge and modding questions to Cities2-MCP when that is the
  right tool, without depending on it.
- Avoid including private local paths, account names, save names, or raw export
  details in public artifacts unless the user explicitly requests it.

The skill must be developed using the writing-skills workflow. Before writing
or editing the skill, create pressure scenarios and observe baseline behavior
without the skill. Then write the skill, run the same scenarios with the skill,
and refine until the agent reliably follows the Chief of Staff behavior.

Pressure scenarios should include:

- Missing Cities2-DataExport or InfoLoomBridge evidence.
- Stale Save Investigator output when a user asks for a current report.
- A request for confident diagnosis from partial evidence.
- A request for a concise mayor-facing brief.
- A game knowledge or modding question that belongs in Cities2-MCP.

## Evidence Companions

Cities2-DataExport and Cities2-InfoLoomBridge remain optional and external in
this phase. They are important evidence sources, but the Codex plugin should not
bundle or install in-game mods yet.

Their absence should be visible and actionable. Status and report flows should
treat evidence coverage as a first-class concept, including whether each source
is detected, missing, stale, or usable. When evidence is thin, the Chief of
Staff should still brief the mayor but identify which conclusions are weaker
and which optional companion source would improve confidence.

The README, plugin README, and skill should explain the optional companion
sources. A later phase may add explicit companion bundling or installer
workflows after the core Codex plugin is stable.

## Privacy

Privacy is a product feature. Chief of Staff analyzes local city evidence
through the user's chosen agent environment and should not independently collect
telemetry, phone home, or send game data to the maintainers.

Implementation requirements:

- Add a root `PRIVACY.md`.
- Link the privacy policy from Codex plugin metadata.
- Mention the privacy model in the README and generated plugin README.
- Do not add analytics, telemetry, remote crash reporting, maintainer-owned
  services, or other network calls.
- Keep future companion install workflows explicit and local-first.
- Keep public artifacts free of personal identifiers, private paths, save names,
  account names, and raw local exports unless the user explicitly requests
  otherwise.

The project should phrase this carefully: it does not independently transmit
data, but the user's selected agent client or model provider may process prompts
and tool outputs according to that provider's own settings.

## Testing and Verification

Use test-first implementation for code changes and skill-test-first development
for the Chief of Staff skill.

Focused code/package tests should cover:

- Python package rename and public entry points.
- CLI status/report behavior after the rename.
- MCP initialize and tool list responses using Chief of Staff names.
- MCP tool calls for status, structured city analysis, and Markdown report.
- Generated Codex plugin metadata staying in sync with canonical builders.
- Launcher `--version` and basic MCP startup from the vendored payload.
- Plugin package contents: skill, launcher, vendored package, `.mcp.json`, and
  `.codex-plugin/plugin.json`.
- Privacy metadata links and README privacy language.
- Absence of old CityAdvisor names from generated public artifacts.
- Evidence coverage behavior for missing optional companion sources.

Skill verification should document baseline failures, post-skill behavior, and
any refinements made to close gaps.

Required gates for this phase:

- `python -m unittest discover -s tests -p "test_*.py"`
- `python -m chief_of_staff.plugin_packages check`
- Launcher smoke tests from the generated plugin package.
- Manual review of generated public artifacts for privacy-sensitive identifiers.

## Out of Scope

- Claude plugin packaging.
- Antigravity plugin packaging.
- Bundling or installing Cities2-DataExport.
- Bundling or installing Cities2-InfoLoomBridge.
- Depending on Cities2-MCP.
- Keeping compatibility shims for old CityAdvisor package, CLI, or MCP tool
  names.
