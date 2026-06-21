from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "cities2-chief-of-staff" / "SKILL.md"
OPENAI_YAML = ROOT / "skills" / "cities2-chief-of-staff" / "agents" / "openai.yaml"
EVIDENCE = ROOT / "docs" / "superpowers" / "skill-tests" / "2026-06-14-cities2-chief-of-staff.md"


class SkillContentTests(unittest.TestCase):
    def test_skill_frontmatter_and_role_guidance(self) -> None:
        text = SKILL.read_text(encoding="utf-8")
        frontmatter = _parse_frontmatter(text)

        self.assertTrue(text.startswith("---\nname: cities2-chief-of-staff\n"))
        self.assertEqual(frontmatter["name"], "cities2-chief-of-staff")
        self.assertTrue(frontmatter["description"].startswith("Use when"))
        self.assertIn('short-description: "Brief CS2 mayors from local city evidence"', text)
        self.assertIn("Mayor's office Chief of Staff", text)
        self.assertIn("chief_of_staff_analyze_city", text)
        self.assertIn("Refresh Save Investigator", text)
        self.assertIn("Cities2-DataExport", text)
        self.assertIn("Cities2-InfoLoomBridge", text)
        self.assertIn("Separate evidence, interpretation, recommended actions, and follow-up investigation", text)
        self.assertIn("Cities2-MCP", text)
        self.assertIn("does not collect telemetry", text)
        normalized = " ".join(text.split())
        self.assertIn(
            "Never put private local paths, account names, save names, or raw exports into public artifacts",
            normalized,
        )

    def test_skill_ui_metadata_preserves_display_label(self) -> None:
        text = OPENAI_YAML.read_text(encoding="utf-8")

        self.assertIn('display_name: "Cities2 Chief of Staff"', text)
        self.assertIn('short_description: "Brief CS2 mayors from local city evidence"', text)
        self.assertIn('default_prompt: "Use $cities2-chief-of-staff ', text)
        self.assertIn('value: "cities2-chief-of-staff"', text)
        self.assertIn("Chief of Staff local server", text)

    def test_skill_teaches_companion_mod_install_help(self) -> None:
        text = SKILL.read_text(encoding="utf-8")
        normalized = " ".join(text.split())

        self.assertIn("https://github.com/mayor-modder/Cities2-DataExport", text)
        self.assertIn("https://github.com/mayor-modder/Cities2-InfoLoomBridge", text)
        self.assertIn("CS2DataExport.csproj", text)
        self.assertIn("InfoLoomBridge.csproj", text)
        self.assertIn("DOTNET_ROLL_FORWARD", text)
        self.assertIn("Remove-Item", text)
        self.assertIn("dotnet build", text)
        self.assertIn("ModsData/CS2DataExport/latest.json", text)
        self.assertIn("ModsData/InfoLoomBridge/latest.json", text)
        self.assertIn("Do not tell users to enable the local mod in the mod list", normalized)

    def test_skill_teaches_specific_infoloomtwo_dependency_check(self) -> None:
        text = SKILL.read_text(encoding="utf-8")
        normalized = " ".join(text.split())

        self.assertIn("https://mods.paradoxplaza.com/mods/91433/Windows", text)
        self.assertIn("https://github.com/bruceyboy24804/InfoLoom", text)
        self.assertIn("InfoLoomTwo.dll", text)
        self.assertIn("InfoLoomTwo_win_x86_64.dll", text)
        self.assertIn(".cache/Mods/pdx_mods", text)
        self.assertIn("Mods/InfoLoom", text)
        self.assertIn("Do not treat unrelated InfoLoom-family mods as sufficient", normalized)

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
            "Scenario 6: Companion Mod Install Help",
            "Scenario 7: Specific InfoLoom Two Dependency",
        ):
            self.assertIn(label, text)


def _parse_frontmatter(text: str) -> dict[str, str]:
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise AssertionError("missing frontmatter")
    metadata: dict[str, str] = {}
    for line in lines[1:]:
        if line == "---":
            return metadata
        key, separator, value = line.partition(":")
        if not separator:
            raise AssertionError(f"invalid frontmatter line: {line}")
        if ":" in value and not (value.strip().startswith('"') and value.strip().endswith('"')):
            raise AssertionError(f"unquoted colon in frontmatter value: {line}")
        metadata[key] = value.strip().strip('"')
    raise AssertionError("unterminated frontmatter")
