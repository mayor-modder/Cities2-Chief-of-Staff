from __future__ import annotations

import io
import json
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "dist" / "plugins" / "cities2-chief-of-staff"


class PackagingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from chief_of_staff import plugin_packages

        plugin_packages.sync_packages(ROOT)

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

        self.assertEqual(plugin["name"], "cities2-chief-of-staff")
        self.assertEqual(plugin["version"], "0.1.0")
        self.assertEqual(plugin["skills"], "./skills/")
        self.assertEqual(plugin["mcpServers"], "./.mcp.json")
        self.assertEqual(plugin["interface"]["displayName"], "Cities2 Chief of Staff")
        self.assertEqual(plugin["interface"]["category"], "Coding")
        self.assertEqual(plugin["interface"]["capabilities"], ["Read", "Write"])
        self.assertEqual(plugin["interface"]["brandColor"], "#1F6F78")
        self.assertEqual(
            plugin["interface"]["privacyPolicyURL"],
            "https://github.com/mayor-modder/Cities2-Chief-of-Staff/blob/main/PRIVACY.md",
        )
        self.assertIn("defaultPrompt", plugin["interface"])
        self.assertEqual(
            plugin["interface"]["defaultPrompt"],
            [
                "Prepare today's mayoral briefing.",
                "Show me the city's top priorities.",
                "Recommend the next moves for my city.",
            ],
        )
        self.assertNotIn("Brief me on my city like the mayor.", plugin["interface"]["defaultPrompt"])
        self.assertNotIn("Brief me on my latest city evidence.", plugin["interface"]["defaultPrompt"])

        server = plugin_mcp["mcpServers"]["cities2-chief-of-staff"]
        self.assertEqual(server["command"], "node")
        self.assertIn("./bin/cities2-chief-of-staff-launcher.js", server["args"])
        self.assertEqual(server["cwd"], ".")

    def test_codex_plugin_payload_contains_skill_and_vendored_server(self) -> None:
        self.assertTrue((PLUGIN_ROOT / "skills" / "cities2-chief-of-staff" / "SKILL.md").is_file())
        self.assertTrue((PLUGIN_ROOT / "vendor" / "run_server.py").is_file())
        self.assertTrue((PLUGIN_ROOT / "vendor" / "chief_of_staff" / "mcp_server.py").is_file())
        self.assertTrue((PLUGIN_ROOT / "bin" / "cities2-chief-of-staff-launcher.js").is_file())

    def test_codex_plugin_launcher_reports_version(self) -> None:
        result = subprocess.run(
            ["node", str(PLUGIN_ROOT / "bin" / "cities2-chief-of-staff-launcher.js"), "--version"],
            cwd=ROOT,
            env={**os.environ, "PLUGIN_ROOT": str(PLUGIN_ROOT)},
            text=True,
            capture_output=True,
            check=True,
        )

        self.assertEqual(result.stdout.strip(), "cities2-chief-of-staff 0.1.0")

    def test_codex_plugin_launcher_serves_mcp_initialize(self) -> None:
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
            content_length = int(header.split(":", 1)[1].strip())
            self.assertEqual(proc.stdout.readline(), b"\r\n")
            response = json.loads(proc.stdout.read(content_length).decode("utf-8"))

            self.assertEqual(response["result"]["serverInfo"]["name"], "Cities2-ChiefOfStaff")
            self.assertEqual(response["result"]["serverInfo"]["version"], "0.1.0")
        finally:
            self._stop_proc(proc)

    def test_plugin_package_sync_and_check_detect_stale_payload(self) -> None:
        from chief_of_staff import plugin_packages

        with tempfile.TemporaryDirectory(prefix="chief-of-staff-plugin-sync-") as tmp:
            root = Path(tmp)
            self._write_plugin_sync_fixture(root)
            package_root = Path("dist") / "plugins" / "cities2-chief-of-staff"

            changed = plugin_packages.sync_packages(root, package_roots=(package_root,))
            stale_skill = root / package_root / "skills" / "cities2-chief-of-staff" / "SKILL.md"
            stale_skill.write_text("stale\n", encoding="utf-8")

            stale = plugin_packages.check_packages(root, package_roots=(package_root,))

            self.assertIn(stale_skill, changed)
            self.assertIn(stale_skill, stale)

    def test_plugin_package_check_detects_generated_cache_artifacts(self) -> None:
        from chief_of_staff import plugin_packages

        with tempfile.TemporaryDirectory(prefix="chief-of-staff-plugin-sync-") as tmp:
            root = Path(tmp)
            self._write_plugin_sync_fixture(root)
            package_root = Path("dist") / "plugins" / "cities2-chief-of-staff"

            plugin_packages.sync_packages(root, package_roots=(package_root,))
            cache_file = root / package_root / "vendor" / "chief_of_staff" / "__pycache__" / "mcp_server.pyc"
            cache_file.parent.mkdir(parents=True)
            cache_file.write_bytes(b"cache")

            stale = plugin_packages.check_packages(root, package_roots=(package_root,))

            self.assertIn(cache_file, stale)

    def test_repo_generated_plugin_package_is_in_sync(self) -> None:
        from chief_of_staff import plugin_packages

        self.assertEqual(plugin_packages.check_packages(ROOT), ())

    def test_sync_catalog_package_copies_dist_payload(self) -> None:
        from chief_of_staff import plugin_packages

        with tempfile.TemporaryDirectory(prefix="chief-of-staff-plugin-sync-") as tmp:
            root = Path(tmp)
            catalog = root / "catalog"
            (catalog / ".agents" / "plugins").mkdir(parents=True)
            (catalog / ".agents" / "plugins" / "marketplace.json").write_text("{}\n", encoding="utf-8")
            self._write_plugin_sync_fixture(root)

            changed = plugin_packages.sync_catalog_package(catalog, repo_root=root)
            target = catalog / "plugins" / "cities2-chief-of-staff"

            self.assertTrue((target / ".codex-plugin" / "plugin.json").is_file())
            self.assertTrue((target / ".mcp.json").is_file())
            self.assertTrue((target / "skills" / "cities2-chief-of-staff" / "SKILL.md").is_file())
            self.assertIn(target / ".codex-plugin" / "plugin.json", changed)

    def test_plugin_package_check_output_explains_sync_command(self) -> None:
        from chief_of_staff import plugin_packages

        with tempfile.TemporaryDirectory(prefix="chief-of-staff-plugin-sync-") as tmp:
            root = Path(tmp)
            self._write_plugin_sync_fixture(root)
            plugin_packages.sync_packages(root)
            stale_metadata = root / "dist" / "plugins" / "cities2-chief-of-staff" / ".codex-plugin" / "plugin.json"
            stale_metadata.write_text("{}\n", encoding="utf-8")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = plugin_packages.main(["check", "--repo-root", str(root)])

            output = stdout.getvalue()
            self.assertEqual(exit_code, 1)
            self.assertIn("generated artifacts differ from canonical sources", output)
            self.assertIn("canonical sources", output)
            self.assertIn("generated package: dist/plugins/cities2-chief-of-staff", output)
            self.assertIn("python -m chief_of_staff.plugin_packages sync", output)
            self.assertIn(str(stale_metadata), output)

    @staticmethod
    def _write_plugin_sync_fixture(root: Path) -> None:
        skill_dir = root / "skills" / "cities2-chief-of-staff"
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text("canonical skill\n", encoding="utf-8")

        package_dir = root / "chief_of_staff"
        package_dir.mkdir(parents=True, exist_ok=True)
        (package_dir / "__init__.py").write_text('__version__ = "0.1.0"\n', encoding="utf-8")
        (package_dir / "mcp_server.py").write_text("def main(): return 0\n", encoding="utf-8")
