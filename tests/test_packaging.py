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
CLAUDE_PLUGIN_ROOT = ROOT / "dist" / "plugins" / "cities2-chief-of-staff-claude"


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
            (catalog / ".claude-plugin").mkdir(parents=True)
            (catalog / ".claude-plugin" / "marketplace.json").write_text("{}\n", encoding="utf-8")
            self._write_plugin_sync_fixture(root)

            changed = plugin_packages.sync_catalog_package(catalog, repo_root=root)
            codex_target = catalog / "plugins" / "cities2-chief-of-staff"
            claude_target = catalog / "integrations" / "anthropic" / "cities2-chief-of-staff"

            self.assertTrue((codex_target / ".codex-plugin" / "plugin.json").is_file())
            self.assertTrue((claude_target / ".claude-plugin" / "plugin.json").is_file())
            self.assertTrue((claude_target / ".mcp.json").is_file())
            self.assertTrue((claude_target / "skills" / "cities2-chief-of-staff" / "SKILL.md").is_file())
            self.assertIn(claude_target / ".claude-plugin" / "plugin.json", changed)

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
            self.assertIn("generated packages:", output)
            self.assertIn("dist/plugins/cities2-chief-of-staff", output)
            self.assertIn("dist/plugins/cities2-chief-of-staff-claude", output)
            self.assertIn("python -m chief_of_staff.plugin_packages sync", output)
            self.assertIn(str(stale_metadata), output)

    def test_claude_plugin_json_is_lean_and_native(self) -> None:
        from chief_of_staff import plugin_metadata

        plugin = json.loads(plugin_metadata.claude_plugin_json())

        self.assertEqual(plugin["name"], "cities2-chief-of-staff")
        self.assertEqual(plugin["displayName"], "Cities2 Chief of Staff")
        self.assertEqual(plugin["version"], "0.1.0")
        self.assertEqual(plugin["description"], "Cities2 Chief of Staff for Claude Code.")
        self.assertEqual(plugin["skills"], "./skills/")
        self.assertEqual(plugin["mcpServers"], "./.mcp.json")
        self.assertEqual(plugin["author"]["name"], "mayor-modder")
        self.assertNotIn("interface", plugin)

    def test_claude_mcp_json_uses_plugin_root_variable(self) -> None:
        from chief_of_staff import plugin_metadata

        server = json.loads(plugin_metadata.claude_mcp_json())["mcpServers"]["cities2-chief-of-staff"]

        self.assertEqual(server["command"], "node")
        self.assertEqual(
            server["args"],
            ["${CLAUDE_PLUGIN_ROOT}/bin/cities2-chief-of-staff-launcher.js"],
        )
        self.assertNotIn("cwd", server)

    def test_claude_marketplace_reference_shape(self) -> None:
        from chief_of_staff import plugin_metadata

        market = json.loads(plugin_metadata.claude_marketplace_json())

        self.assertEqual(market["name"], "mayor-modder-cities2-plugins")
        self.assertEqual(market["owner"]["name"], "mayor-modder")
        self.assertEqual(market["plugins"][0]["name"], "cities2-chief-of-staff")
        self.assertEqual(market["plugins"][0]["source"], "./integrations/anthropic/cities2-chief-of-staff")
        self.assertEqual(market["plugins"][0]["version"], "0.1.0")
        self.assertEqual(market["plugins"][0]["author"]["name"], "mayor-modder")

    def test_claude_readme_has_install_and_privacy(self) -> None:
        from chief_of_staff import plugin_metadata

        text = plugin_metadata.claude_readme_md()

        self.assertIn("/plugin marketplace add mayor-modder/Mayor-Modder-Cities2-Plugins", text)
        self.assertIn("/plugin install cities2-chief-of-staff@mayor-modder-cities2-plugins", text)
        self.assertIn("does not collect telemetry", text)

    def test_platform_registry_describes_codex_and_claude(self) -> None:
        from chief_of_staff import plugin_metadata

        keys = {platform.key for platform in plugin_metadata.PLATFORMS}
        self.assertEqual(keys, {"codex", "claude"})

        codex = plugin_metadata.PLATFORMS_BY_KEY["codex"]
        claude = plugin_metadata.PLATFORMS_BY_KEY["claude"]

        self.assertEqual(codex.manifest_dir, ".codex-plugin")
        self.assertEqual(str(codex.dist_package_root), str(Path("dist/plugins/cities2-chief-of-staff")))
        self.assertEqual(str(codex.catalog_marketplace_rel), str(Path(".agents/plugins/marketplace.json")))

        self.assertEqual(claude.manifest_dir, ".claude-plugin")
        self.assertEqual(str(claude.dist_package_root), str(Path("dist/plugins/cities2-chief-of-staff-claude")))
        self.assertEqual(str(claude.catalog_package_root), str(Path("integrations/anthropic/cities2-chief-of-staff")))
        self.assertEqual(str(claude.catalog_marketplace_rel), str(Path(".claude-plugin/marketplace.json")))
        self.assertEqual(claude.plugin_json(), plugin_metadata.claude_plugin_json())

    def test_claude_dist_metadata_is_present_and_lean(self) -> None:
        plugin = json.loads((CLAUDE_PLUGIN_ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        plugin_mcp = json.loads((CLAUDE_PLUGIN_ROOT / ".mcp.json").read_text(encoding="utf-8"))

        self.assertEqual(plugin["name"], "cities2-chief-of-staff")
        self.assertEqual(plugin["displayName"], "Cities2 Chief of Staff")
        self.assertEqual(plugin["version"], "0.1.0")
        self.assertEqual(plugin["skills"], "./skills/")
        self.assertEqual(plugin["mcpServers"], "./.mcp.json")
        self.assertNotIn("interface", plugin)

        server = plugin_mcp["mcpServers"]["cities2-chief-of-staff"]
        self.assertEqual(server["command"], "node")
        self.assertIn("${CLAUDE_PLUGIN_ROOT}/bin/cities2-chief-of-staff-launcher.js", server["args"])
        self.assertNotIn("cwd", server)

    def test_claude_dist_payload_contains_skill_and_vendored_server(self) -> None:
        self.assertTrue((CLAUDE_PLUGIN_ROOT / "skills" / "cities2-chief-of-staff" / "SKILL.md").is_file())
        self.assertTrue((CLAUDE_PLUGIN_ROOT / "vendor" / "run_server.py").is_file())
        self.assertTrue((CLAUDE_PLUGIN_ROOT / "vendor" / "chief_of_staff" / "mcp_server.py").is_file())
        self.assertTrue((CLAUDE_PLUGIN_ROOT / "bin" / "cities2-chief-of-staff-launcher.js").is_file())

    def test_claude_dist_launcher_serves_mcp_initialize(self) -> None:
        proc = subprocess.Popen(
            ["node", str(CLAUDE_PLUGIN_ROOT / "bin" / "cities2-chief-of-staff-launcher.js")],
            cwd=ROOT,
            env={**os.environ, "PLUGIN_ROOT": str(CLAUDE_PLUGIN_ROOT)},
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

    def test_sync_catalog_package_target_selects_single_platform(self) -> None:
        from chief_of_staff import plugin_metadata, plugin_packages

        with tempfile.TemporaryDirectory(prefix="chief-of-staff-plugin-sync-") as tmp:
            root = Path(tmp)
            catalog = root / "catalog"
            (catalog / ".agents" / "plugins").mkdir(parents=True)
            (catalog / ".agents" / "plugins" / "marketplace.json").write_text("{}\n", encoding="utf-8")
            # Claude marketplace is present too, so the absent Claude payload below
            # proves targeting (not just the marketplace existence guard) skipped it.
            (catalog / ".claude-plugin").mkdir(parents=True)
            (catalog / ".claude-plugin" / "marketplace.json").write_text("{}\n", encoding="utf-8")
            self._write_plugin_sync_fixture(root)

            plugin_packages.sync_catalog_package(
                catalog, repo_root=root, platforms=(plugin_metadata.CODEX,)
            )

            self.assertTrue((catalog / "plugins" / "cities2-chief-of-staff" / ".codex-plugin" / "plugin.json").is_file())
            self.assertFalse((catalog / "integrations" / "anthropic" / "cities2-chief-of-staff").exists())

    @staticmethod
    def _write_plugin_sync_fixture(root: Path) -> None:
        skill_dir = root / "skills" / "cities2-chief-of-staff"
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text("canonical skill\n", encoding="utf-8")

        package_dir = root / "chief_of_staff"
        package_dir.mkdir(parents=True, exist_ok=True)
        (package_dir / "__init__.py").write_text('__version__ = "0.1.0"\n', encoding="utf-8")
        (package_dir / "mcp_server.py").write_text("def main(): return 0\n", encoding="utf-8")
