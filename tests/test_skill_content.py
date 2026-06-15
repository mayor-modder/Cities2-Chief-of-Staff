from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "cities2-chief-of-staff" / "SKILL.md"
EVIDENCE = ROOT / "docs" / "superpowers" / "skill-tests" / "2026-06-14-cities2-chief-of-staff.md"


class SkillContentTests(unittest.TestCase):
    def test_skill_frontmatter_and_role_guidance(self) -> None:
        text = SKILL.read_text(encoding="utf-8")

        self.assertTrue(text.startswith("---\nname: cities2-chief-of-staff\n"))
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
