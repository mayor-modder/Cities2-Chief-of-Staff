from __future__ import annotations

import unittest
from pathlib import Path
from unittest import mock

from chief_of_staff.paths import default_save_investigator_project_path


ROOT = Path(__file__).resolve().parents[1]


class PathTests(unittest.TestCase):
    def test_default_save_investigator_project_path_uses_install_root_not_cwd(self) -> None:
        unrelated = ROOT / "not-the-plugin-root"

        with mock.patch("chief_of_staff.paths.Path.cwd", return_value=unrelated):
            path = default_save_investigator_project_path()

        self.assertEqual(path, ROOT / "tools" / "SaveInvestigator" / "SaveInvestigator.csproj")


if __name__ == "__main__":
    unittest.main()
