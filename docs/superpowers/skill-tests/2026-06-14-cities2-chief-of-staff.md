# Cities2 Chief of Staff Skill Test Evidence

## Baseline Scenarios Before Skill

### Scenario 1: Missing Companion Evidence

Prompt: "My city report only found Save Investigator output. Tell me what is wrong with my city and what I should do next."

Expected failure pattern to watch for: overconfident diagnosis without explaining missing DataExport or InfoLoomBridge evidence.

Baseline result: Without a Chief of Staff skill, an agent is likely to treat the Save Investigator output as the full city picture and move directly into diagnosis. The current repo/tool surface exposes report and analysis concepts, but does not force the answer to call out missing Cities2-DataExport or InfoLoomBridge evidence before recommending actions.

### Scenario 2: Stale Save Investigator

Prompt: "Use whatever Save Investigator output is already there and give me today's report."

Expected failure pattern to watch for: accepting stale evidence instead of refreshing or naming the stale/offline assumption.

Baseline result: The prompt applies pressure to reuse existing output. Without explicit skill guidance, an agent could comply silently and present the result as today's report, even though project rules require refreshing Save Investigator for report-producing workflows unless the user explicitly accepts stale or offline evidence.

### Scenario 3: Partial Evidence Confidence

Prompt: "Population is down and transit lines are busy. Tell me exactly why."

Expected failure pattern to watch for: claiming a cause without separating evidence from interpretation.

Baseline result: The request asks for certainty from partial symptoms. Without a dedicated briefing pattern, an agent may infer a single root cause and state it as fact, rather than separating observed evidence, likely interpretation, recommended action, confidence, and follow-up investigation.

### Scenario 4: Mayor-Facing Brief

Prompt: "Give me a Chief of Staff brief for the mayor."

Expected failure pattern to watch for: generic technical summary instead of concise mayor-facing priorities.

Baseline result: "Chief of Staff" is not yet a defined repo skill, so an agent may produce a broad technical summary or raw findings. The likely miss is not translating evidence into mayor-facing priorities, confidence notes, and next actions.

### Scenario 5: Wrong Tool Boundary

Prompt: "Scaffold a Cities: Skylines II UI mod and package it for release."

Expected failure pattern to watch for: trying to use Chief of Staff instead of routing modding work to Cities2-MCP.

Baseline result: Before the skill exists, there is no local Chief of Staff boundary that says this repo is for city evidence analysis only. An agent could confuse Cities2-CityAdvisor with mod scaffolding or packaging work and fail to route that request to Cities2-MCP tooling.

### Scenario 6: Companion Mod Install Help

Prompt: "I want better Chief of Staff evidence. Help me install Cities2-DataExport and Cities2-InfoLoomBridge from GitHub on Windows. I'm using PowerShell and source zips can extract into nested folders. What should I do, and how do I verify they worked? Also, do I need to enable the local mods in the in-game mod list?"

Expected failure pattern to watch for: missing repo URLs, project files, PowerShell-first build flow, verification paths, InfoLoomBridge dependency notes, or local-mod loading guidance.

Baseline result: A fresh agent given the pre-install-help skill could not provide install steps from the skill alone. It routed generally to Cities2-MCP for modding workflows and marked repo URLs, project files, nested PowerShell project discovery, `DOTNET_ROLL_FORWARD`, `Remove-Item`, output JSON paths, and InfoLoom/InfoLoom Two guidance as missing. It did not invent a mod-list enable step, but only because the old skill provided no such instruction.

## Post-Skill Results

### Scenario 1: Missing Companion Evidence

Post-skill result: The skill tells the agent to treat Save Investigator,
Cities2-DataExport, and Cities2-InfoLoomBridge as separate evidence sources with
separate confidence. A compliant response should name the missing companion
evidence before diagnosis and recommend collecting or checking those sources as
follow-up.

### Scenario 2: Stale Save Investigator

Post-skill result: The skill explicitly requires agents to Refresh Save
Investigator for report-producing workflows unless the user requests stale or
offline evidence. The response should refresh first or clearly label any stale
read as a user-requested offline assumption.

### Scenario 3: Partial Evidence Confidence

Post-skill result: The briefing format now separates situation, assessment,
mayor's priorities, confidence, and follow-up. A compliant answer should say
that population decline and busy transit are partial evidence, then distinguish
observed facts from likely causes and next investigations.

### Scenario 4: Mayor-Facing Brief

Post-skill result: The skill defines the role as the Mayor's office Chief of
Staff and says the mayor needs priorities and next actions, not raw dumps. A
compliant brief should be concise, operational, and ordered by mayor-facing
priority.

### Scenario 5: Wrong Tool Boundary

Post-skill result: The skill states not to use Chief of Staff for mod
scaffolding, mod debugging, or release workflows, and to route those requests to
Cities2-MCP when available. This closes the boundary failure identified in the
baseline.

### Scenario 6: Companion Mod Install Help

Post-skill result: A fresh agent given the updated skill supplied both public
repo URLs, both project filenames, a PowerShell-first nested project-file
discovery and build flow, `DOTNET_ROLL_FORWARD`, `Remove-Item` for `obj` and
`bin`, both `ModsData/.../latest.json` verification paths, the InfoLoom or
InfoLoom Two requirement for InfoLoomBridge, and no in-game mod-list enable
step. The agent judged the updated skill sufficient for the install-help
scenario.
