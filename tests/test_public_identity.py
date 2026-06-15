from __future__ import annotations

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
