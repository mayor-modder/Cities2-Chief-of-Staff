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
