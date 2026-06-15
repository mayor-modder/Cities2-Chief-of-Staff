# Chief of Staff Claude Code Target Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the plugin generator emit a Claude Code-native plugin package alongside the existing Codex one, publishable into the same `Mayor-Modder-Cities2-Plugins` repo via a separate `.claude-plugin/marketplace.json`, leaving the Codex distribution unchanged.

**Architecture:** Introduce a `Platform` registry in `chief_of_staff/plugin_metadata.py` (each platform = its manifest/mcp/readme/marketplace builders + dist/catalog paths). Refactor `chief_of_staff/plugin_packages.py` so `sync`/`check`/`sync-catalog` loop over the registry. The skill, Node launcher, and vendored Python package are platform-neutral and reused as-is.

**Tech Stack:** Python 3.11+ (stdlib only: `dataclasses`, `pathlib`, `json`, `argparse`, `unittest`), Node.js launcher (unchanged), `pytest`/`unittest` for tests.

**Spec:** `docs/superpowers/specs/2026-06-15-chief-of-staff-claude-target-design.md`

**Conventions in this repo:**
- Run tests with: `python -m pytest tests -q` (or a single test: `python -m pytest tests/test_packaging.py::PackagingTests::test_name -q`).
- All generated text files are written with `newline="\n"`; JSON via the existing `_dumps` helper (2-space indent, trailing newline).
- Commit frequently. Commit messages must use the neutral `mayor-modder` handle only — never a personal name, Windows username, or `C:\Users\...` path.
- End each commit message with the trailer:
  `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`

---

## File Structure

- `chief_of_staff/plugin_metadata.py` — **Modify.** Add `claude_*` builders, a `CLAUDE_MARKETPLACE_NAME` constant, and the `Platform` dataclass + `CODEX`/`CLAUDE` instances + `PLATFORMS` / `PLATFORMS_BY_KEY`.
- `chief_of_staff/plugin_packages.py` — **Modify.** Replace Codex-specific singletons (`DIST_PACKAGE_ROOT`, `CATALOG_PACKAGE_ROOT`, `PACKAGE_ROOTS`, `METADATA_FILES`, `_selected_package_roots`) with registry-driven helpers; loop platforms in `sync_packages`/`check_packages`/`sync_catalog_package`; add `--target` to the CLI.
- `tests/test_packaging.py` — **Modify.** Add Claude packaging tests; update the catalog test to cover both platforms; add a single-target catalog test.
- `tests/test_public_identity.py` — **Modify.** Add a Claude metadata identity test.
- `tests/test_privacy.py` — **Modify.** Add a Claude README privacy test.
- `INSTALL.md` — **Modify.** Add a Claude Code install section.
- `README.md` — **Modify.** Note Claude Code support.

No changes to: the skill, `bin` launcher constant, `vendor` shim, `pyproject.toml`, `.gitignore` (the new `dist/plugins/cities2-chief-of-staff-claude/` is already covered by the `dist/` ignore).

---

## Task 1: Claude metadata builders

**Files:**
- Modify: `chief_of_staff/plugin_metadata.py`
- Test: `tests/test_packaging.py`

- [ ] **Step 1: Write the failing tests**

Add these methods inside `class PackagingTests` in `tests/test_packaging.py` (the class already imports `json`):

```python
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

        self.assertEqual(market["name"], "mayor-modder-cities2")
        self.assertEqual(market["owner"]["name"], "mayor-modder")
        self.assertEqual(market["metadata"]["pluginRoot"], "./plugins")
        self.assertEqual(market["plugins"][0]["name"], "cities2-chief-of-staff")
        self.assertEqual(market["plugins"][0]["source"], "cities2-chief-of-staff-claude")
        self.assertEqual(market["plugins"][0]["version"], "0.1.0")

    def test_claude_readme_has_install_and_privacy(self) -> None:
        from chief_of_staff import plugin_metadata

        text = plugin_metadata.claude_readme_md()

        self.assertIn("/plugin marketplace add mayor-modder/Mayor-Modder-Cities2-Plugins", text)
        self.assertIn("/plugin install cities2-chief-of-staff@mayor-modder-cities2", text)
        self.assertIn("does not collect telemetry", text)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_packaging.py -q -k claude`
Expected: FAIL with `AttributeError: module 'chief_of_staff.plugin_metadata' has no attribute 'claude_plugin_json'`.

- [ ] **Step 3: Add the `CLAUDE_MARKETPLACE_NAME` constant**

In `chief_of_staff/plugin_metadata.py`, add this line just after the `SKILL_NAMES` constant (around line 18):

```python
CLAUDE_MARKETPLACE_NAME = "mayor-modder-cities2"
```

- [ ] **Step 4: Add the Claude builders**

In `chief_of_staff/plugin_metadata.py`, add these functions immediately after `codex_readme_md()` (end of file, before any registry added in Task 2):

```python
def claude_plugin_json() -> str:
    return _dumps(
        {
            "name": NAME,
            "displayName": DISPLAY_NAME,
            "version": VERSION,
            "description": "Cities2 Chief of Staff for Claude Code.",
            "author": AUTHOR,
            "homepage": REPO_URL,
            "repository": REPO_URL,
            "license": LICENSE,
            "keywords": KEYWORDS,
            "skills": "./skills/",
            "mcpServers": "./.mcp.json",
        }
    )


def claude_mcp_json() -> str:
    return _dumps(
        {
            "mcpServers": {
                NAME: {
                    "command": "node",
                    "args": ["${CLAUDE_PLUGIN_ROOT}/bin/cities2-chief-of-staff-launcher.js"],
                }
            }
        }
    )


def claude_marketplace_json() -> str:
    return _dumps(
        {
            "name": CLAUDE_MARKETPLACE_NAME,
            "description": "Mayor Modder Cities: Skylines II plugins for Claude Code.",
            "owner": AUTHOR,
            "metadata": {"pluginRoot": "./plugins"},
            "plugins": [
                {
                    "name": NAME,
                    "source": "cities2-chief-of-staff-claude",
                    "description": "Local Cities: Skylines II mayoral analysis",
                    "version": VERSION,
                    "category": "productivity",
                }
            ],
        }
    )


def claude_readme_md() -> str:
    return f"""<!-- Generated by chief_of_staff.plugin_packages; edit canonical sources in chief_of_staff/plugin_metadata.py, not this file. -->

# Cities2 Chief of Staff Claude Code plugin

This Claude Code plugin helps Claude turn your local Cities: Skylines II data into
a practical mayoral briefing. It bundles the Chief of Staff skill and a
plugin-local MCP server launcher.

Privacy: the project does not collect telemetry, does not phone home, and does
not send game data to the maintainers. It runs locally through your chosen
agent environment, and only that client or model provider may process prompts
and tool outputs according to your settings. See the repository `PRIVACY.md`.

Install from the shared Mayor Modder Cities2 Plugins marketplace:

```sh
/plugin marketplace add {CATALOG_REPO}
/plugin install {NAME}@{CLAUDE_MARKETPLACE_NAME}
```
"""
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python -m pytest tests/test_packaging.py -q -k claude`
Expected: PASS (4 passed).

- [ ] **Step 6: Commit**

```bash
git add chief_of_staff/plugin_metadata.py tests/test_packaging.py
git commit -m "Add Claude plugin metadata builders" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: Platform registry in plugin_metadata.py

**Files:**
- Modify: `chief_of_staff/plugin_metadata.py`
- Test: `tests/test_packaging.py`

- [ ] **Step 1: Write the failing test**

Add to `class PackagingTests` in `tests/test_packaging.py`:

```python
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
        self.assertEqual(str(claude.catalog_package_root), str(Path("plugins/cities2-chief-of-staff-claude")))
        self.assertEqual(str(claude.catalog_marketplace_rel), str(Path(".claude-plugin/marketplace.json")))
        self.assertEqual(claude.plugin_json(), plugin_metadata.claude_plugin_json())
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_packaging.py::PackagingTests::test_platform_registry_describes_codex_and_claude -q`
Expected: FAIL with `AttributeError: module 'chief_of_staff.plugin_metadata' has no attribute 'PLATFORMS'`.

- [ ] **Step 3: Add imports**

At the top of `chief_of_staff/plugin_metadata.py`, replace the import block:

```python
from __future__ import annotations

import json

from chief_of_staff import __version__ as VERSION
```

with:

```python
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from chief_of_staff import __version__ as VERSION
```

- [ ] **Step 4: Add the registry**

At the end of `chief_of_staff/plugin_metadata.py` (after `claude_readme_md()`), add:

```python
@dataclass(frozen=True)
class Platform:
    key: str
    manifest_dir: str
    plugin_json: Callable[[], str]
    mcp_json: Callable[[], str]
    readme_md: Callable[[], str]
    marketplace_json: Callable[[], str]
    dist_package_root: Path
    catalog_package_root: Path
    catalog_marketplace_rel: Path


CODEX = Platform(
    key="codex",
    manifest_dir=".codex-plugin",
    plugin_json=codex_plugin_json,
    mcp_json=codex_mcp_json,
    readme_md=codex_readme_md,
    marketplace_json=codex_marketplace_json,
    dist_package_root=Path("dist/plugins/cities2-chief-of-staff"),
    catalog_package_root=Path("plugins/cities2-chief-of-staff"),
    catalog_marketplace_rel=Path(".agents/plugins/marketplace.json"),
)

CLAUDE = Platform(
    key="claude",
    manifest_dir=".claude-plugin",
    plugin_json=claude_plugin_json,
    mcp_json=claude_mcp_json,
    readme_md=claude_readme_md,
    marketplace_json=claude_marketplace_json,
    dist_package_root=Path("dist/plugins/cities2-chief-of-staff-claude"),
    catalog_package_root=Path("plugins/cities2-chief-of-staff-claude"),
    catalog_marketplace_rel=Path(".claude-plugin/marketplace.json"),
)

PLATFORMS = (CODEX, CLAUDE)
PLATFORMS_BY_KEY = {platform.key: platform for platform in PLATFORMS}
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `python -m pytest tests/test_packaging.py::PackagingTests::test_platform_registry_describes_codex_and_claude -q`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add chief_of_staff/plugin_metadata.py tests/test_packaging.py
git commit -m "Add platform registry for plugin targets" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: Refactor plugin_packages.py to loop platforms

This refactor keeps every existing Codex test green and starts generating the Claude dist package. It only changes how packages are selected and where metadata is written; `_write_payload`, `_replace_payload`, `LAUNCHER_JS`, `RUN_SERVER_PY`, and all tree-diff helpers are untouched.

**Files:**
- Modify: `chief_of_staff/plugin_packages.py`
- Test: `tests/test_packaging.py` (existing tests are the regression guard)

- [ ] **Step 1: Confirm the regression baseline passes before refactor**

Run: `python -m pytest tests/test_packaging.py -q -k "codex or sync or check or repo_generated or catalog"`
Expected: PASS (existing Codex/sync/check/catalog tests pass).

- [ ] **Step 2: Replace the top-of-file constants**

In `chief_of_staff/plugin_packages.py`, replace this block (the imports plus the path/metadata constants, currently lines 1–30):

```python
from __future__ import annotations

import argparse
import shutil
import tempfile
from pathlib import Path
from typing import Callable, Iterable

from chief_of_staff import plugin_metadata
from chief_of_staff.plugin_metadata import SKILL_NAMES


DIST_PACKAGE_ROOT = Path("dist/plugins/cities2-chief-of-staff")
CATALOG_PACKAGE_ROOT = Path("plugins/cities2-chief-of-staff")
DEFAULT_CATALOG_ROOT = Path("../Mayor-Modder-Cities2-Plugins")

PACKAGE_ROOTS = (DIST_PACKAGE_ROOT,)

METADATA_FILES: dict[Path, tuple[tuple[Path, Callable[[], str]], ...]] = {
    DIST_PACKAGE_ROOT: (
        (DIST_PACKAGE_ROOT / ".codex-plugin" / "plugin.json", plugin_metadata.codex_plugin_json),
        (DIST_PACKAGE_ROOT / ".mcp.json", plugin_metadata.codex_mcp_json),
        (DIST_PACKAGE_ROOT / "README.md", plugin_metadata.codex_readme_md),
    ),
}

MANAGED_DIRS = ("skills", "vendor")
MANAGED_FILES = (Path("bin") / "cities2-chief-of-staff-launcher.js",)
IGNORED_DIRS = {"__pycache__", ".pytest_cache"}
IGNORED_SUFFIXES = {".pyc"}
```

with:

```python
from __future__ import annotations

import argparse
import shutil
import tempfile
from pathlib import Path
from typing import Callable, Iterable

from chief_of_staff import plugin_metadata
from chief_of_staff.plugin_metadata import PLATFORMS, PLATFORMS_BY_KEY, SKILL_NAMES, Platform


DEFAULT_CATALOG_ROOT = Path("../Mayor-Modder-Cities2-Plugins")

MANAGED_DIRS = ("skills", "vendor")
MANAGED_FILES = (Path("bin") / "cities2-chief-of-staff-launcher.js",)
IGNORED_DIRS = {"__pycache__", ".pytest_cache"}
IGNORED_SUFFIXES = {".pyc"}


def _metadata_files(platform: Platform) -> tuple[tuple[Path, Callable[[], str]], ...]:
    root = platform.dist_package_root
    return (
        (root / platform.manifest_dir / "plugin.json", platform.plugin_json),
        (root / ".mcp.json", platform.mcp_json),
        (root / "README.md", platform.readme_md),
    )


def _selected_platforms(package_roots: Iterable[Path] | None) -> tuple[Platform, ...]:
    if package_roots is None:
        return PLATFORMS
    by_root = {platform.dist_package_root: platform for platform in PLATFORMS}
    selected: list[Platform] = []
    for raw in package_roots:
        path = Path(raw)
        platform = by_root.get(path)
        if platform is None:
            raise ValueError(f"Unknown plugin package root: {path}")
        selected.append(platform)
    return tuple(selected)
```

(`LAUNCHER_JS` and `RUN_SERVER_PY` remain immediately below, unchanged.)

- [ ] **Step 3: Rewrite `sync_packages` and `check_packages`**

Replace the existing `sync_packages` and `check_packages` functions with:

```python
def sync_packages(
    repo_root: Path | str = Path.cwd(),
    *,
    package_roots: Iterable[Path] | None = None,
) -> tuple[Path, ...]:
    root = Path(repo_root).resolve()
    changed: list[Path] = []
    for platform in _selected_platforms(package_roots):
        changed.extend(_replace_payload(root, platform.dist_package_root))
        changed.extend(_sync_metadata(root, platform))
    return _unique_sorted(changed)


def check_packages(
    repo_root: Path | str = Path.cwd(),
    *,
    package_roots: Iterable[Path] | None = None,
) -> tuple[Path, ...]:
    root = Path(repo_root).resolve()
    stale: list[Path] = []
    with tempfile.TemporaryDirectory(prefix="chief-of-staff-plugin-payload-") as tmp:
        tmp_package = Path(tmp) / "payload"
        _write_payload(root, tmp_package)
        for platform in _selected_platforms(package_roots):
            package_abs = root / platform.dist_package_root
            for dirname in MANAGED_DIRS:
                stale.extend(_changed_tree_paths(tmp_package / dirname, package_abs / dirname))
            for filename in MANAGED_FILES:
                stale.extend(_changed_paths(tmp_package / filename, package_abs / filename))
            stale.extend(_check_metadata(root, platform))
    return _unique_sorted(stale)
```

- [ ] **Step 4: Rewrite `sync_catalog_package`**

Replace the existing `sync_catalog_package` function with:

```python
def sync_catalog_package(
    catalog_root: Path | str = DEFAULT_CATALOG_ROOT,
    *,
    repo_root: Path | str = Path.cwd(),
    platforms: Iterable[Platform] = PLATFORMS,
) -> tuple[Path, ...]:
    root = Path(repo_root).resolve()
    catalog = Path(catalog_root).resolve()
    changed: list[Path] = []
    for platform in platforms:
        marketplace = catalog / platform.catalog_marketplace_rel
        if not marketplace.is_file():
            raise FileNotFoundError(f"Catalog marketplace not found: {marketplace}")

        sync_packages(root, package_roots=(platform.dist_package_root,))
        source = root / platform.dist_package_root
        target = catalog / platform.catalog_package_root
        if not target.resolve().is_relative_to(catalog):
            raise ValueError(f"Catalog package target escapes catalog root: {target}")

        changed.extend(_changed_tree_paths(source, target))
        if target.exists():
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, target)
    return _unique_sorted(changed)
```

- [ ] **Step 5: Delete the now-unused `_selected_package_roots` and update `_sync_metadata`/`_check_metadata`**

Delete the entire `_selected_package_roots` function. Then replace `_sync_metadata` and `_check_metadata` with platform-based versions:

```python
def _sync_metadata(repo_root: Path, platform: Platform) -> tuple[Path, ...]:
    changed: list[Path] = []
    for target_rel, builder in _metadata_files(platform):
        target = repo_root / target_rel
        expected = builder()
        if not target.is_file() or target.read_text(encoding="utf-8") != expected:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(expected, encoding="utf-8", newline="\n")
            changed.append(target)
    return _unique_sorted(changed)


def _check_metadata(repo_root: Path, platform: Platform) -> tuple[Path, ...]:
    stale: list[Path] = []
    for target_rel, builder in _metadata_files(platform):
        target = repo_root / target_rel
        if not target.is_file() or target.read_text(encoding="utf-8") != builder():
            stale.append(target)
    return tuple(stale)
```

(`_write_payload`, `_copy_skills`, `_replace_payload`, `_changed_paths`, `_changed_tree_paths`, `_files_under`, `_unique_sorted` are unchanged.)

- [ ] **Step 6: Add `--target` to the CLI and wire `sync-catalog`**

Replace the `main()` function with:

```python
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sync generated plugin packages.")
    parser.add_argument("command", choices=("sync", "check", "sync-catalog"))
    parser.add_argument("--repo-root", default=Path.cwd())
    parser.add_argument("--catalog-root", default=DEFAULT_CATALOG_ROOT)
    parser.add_argument("--target", choices=("codex", "claude", "all"), default="all")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root)
    if args.command == "sync":
        changed = sync_packages(repo_root)
        if changed:
            print("Updated generated plugin package artifacts:")
            for path in changed:
                print(f"- {path}")
        else:
            print("Plugin package payloads are in sync.")
        return 0

    if args.command == "sync-catalog":
        platforms = PLATFORMS if args.target == "all" else (PLATFORMS_BY_KEY[args.target],)
        changed = sync_catalog_package(args.catalog_root, repo_root=repo_root, platforms=platforms)
        if changed:
            print("Updated catalog plugin package artifacts:")
            for path in changed:
                print(f"- {path}")
        else:
            print("Catalog plugin package is in sync.")
        return 0

    stale = check_packages(repo_root)
    if not stale:
        print("Plugin package payloads are in sync.")
        return 0

    print("Plugin package generated artifacts differ from canonical sources.")
    print("Canonical sources: chief_of_staff/plugin_metadata.py, skills/cities2-chief-of-staff, chief_of_staff")
    print("generated package: dist/plugins/cities2-chief-of-staff")
    print("Run: python -m chief_of_staff.plugin_packages sync")
    print("Stale paths:")
    for path in stale:
        print(f"- {path}")
    return 1
```

(The check-output wording is kept verbatim so `test_plugin_package_check_output_explains_sync_command` still passes; the per-platform stale paths are listed under "Stale paths".)

- [ ] **Step 7: Update the existing catalog test to cover both platforms**

In `tests/test_packaging.py`, replace `test_sync_catalog_package_copies_dist_payload` with:

```python
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
            claude_target = catalog / "plugins" / "cities2-chief-of-staff-claude"

            self.assertTrue((codex_target / ".codex-plugin" / "plugin.json").is_file())
            self.assertTrue((claude_target / ".claude-plugin" / "plugin.json").is_file())
            self.assertTrue((claude_target / ".mcp.json").is_file())
            self.assertTrue((claude_target / "skills" / "cities2-chief-of-staff" / "SKILL.md").is_file())
            self.assertIn(claude_target / ".claude-plugin" / "plugin.json", changed)
```

- [ ] **Step 8: Run the full packaging suite**

Run: `python -m pytest tests/test_packaging.py -q`
Expected: PASS (all existing + Task 1/2 + updated catalog tests pass). The `setUpClass` `sync_packages(ROOT)` now also generates `dist/plugins/cities2-chief-of-staff-claude/`.

- [ ] **Step 9: Commit**

```bash
git add chief_of_staff/plugin_packages.py tests/test_packaging.py
git commit -m "Drive plugin sync from the platform registry" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: Claude dist package tests

**Files:**
- Modify: `tests/test_packaging.py`

- [ ] **Step 1: Add the Claude dist root constant**

Near the top of `tests/test_packaging.py`, just after the existing `PLUGIN_ROOT = ROOT / "dist" / "plugins" / "cities2-chief-of-staff"` line, add:

```python
CLAUDE_PLUGIN_ROOT = ROOT / "dist" / "plugins" / "cities2-chief-of-staff-claude"
```

- [ ] **Step 2: Write the failing tests**

Add to `class PackagingTests`:

```python
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
            self._write_plugin_sync_fixture(root)

            plugin_packages.sync_catalog_package(
                catalog, repo_root=root, platforms=(plugin_metadata.CODEX,)
            )

            self.assertTrue((catalog / "plugins" / "cities2-chief-of-staff" / ".codex-plugin" / "plugin.json").is_file())
            self.assertFalse((catalog / "plugins" / "cities2-chief-of-staff-claude").exists())
```

- [ ] **Step 3: Run the tests to verify they pass**

Run: `python -m pytest tests/test_packaging.py -q -k "claude_dist or single_platform"`
Expected: PASS. (The `setUpClass` already synced the Claude dist; the launcher is shared, so `initialize` works against the Claude payload.)

- [ ] **Step 4: Commit**

```bash
git add tests/test_packaging.py
git commit -m "Cover Claude dist package and targeted catalog sync" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: Extend privacy and public-identity tests to Claude artifacts

**Files:**
- Modify: `tests/test_public_identity.py`
- Modify: `tests/test_privacy.py`

- [ ] **Step 1: Write the failing public-identity test**

In `tests/test_public_identity.py`, add `import json` to the import block (after `import subprocess`), then add to `class PublicIdentityTests`:

```python
    def test_claude_metadata_uses_public_identity_only(self) -> None:
        from chief_of_staff import plugin_metadata

        plugin = json.loads(plugin_metadata.claude_plugin_json())
        market = json.loads(plugin_metadata.claude_marketplace_json())

        self.assertEqual(plugin["name"], "cities2-chief-of-staff")
        self.assertEqual(plugin["version"], "0.1.0")
        self.assertEqual(plugin["author"]["name"], "mayor-modder")
        self.assertEqual(market["name"], "mayor-modder-cities2")
        self.assertEqual(market["owner"]["name"], "mayor-modder")

        for blob in (
            plugin_metadata.claude_plugin_json(),
            plugin_metadata.claude_marketplace_json(),
            plugin_metadata.claude_readme_md(),
        ):
            self.assertNotIn("C:\\Users", blob)
            self.assertNotIn("/Users/", blob)
```

- [ ] **Step 2: Write the failing privacy test**

In `tests/test_privacy.py`, add to `class PrivacyDocumentationTests`:

```python
    def test_claude_readme_states_local_first_policy(self) -> None:
        from chief_of_staff import plugin_metadata

        text = plugin_metadata.claude_readme_md()

        self.assertIn("does not collect telemetry", text)
        self.assertIn("does not phone home", text)
        self.assertIn("does not send game data to the maintainers", text)
        self.assertIn("/plugin install cities2-chief-of-staff@mayor-modder-cities2", text)
```

- [ ] **Step 3: Run the tests to verify they pass**

Run: `python -m pytest tests/test_public_identity.py tests/test_privacy.py -q`
Expected: PASS. (These exercise builders already implemented in Task 1, so they pass immediately — they are regression guards for privacy.)

- [ ] **Step 4: Commit**

```bash
git add tests/test_public_identity.py tests/test_privacy.py
git commit -m "Guard Claude artifacts for privacy and public identity" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 6: Documentation

**Files:**
- Modify: `INSTALL.md`
- Modify: `README.md`

- [ ] **Step 1: Read the current docs**

Run: open `INSTALL.md` and `README.md` and locate the existing Codex marketplace install instructions (in `INSTALL.md` around the `codex plugin marketplace add mayor-modder/Mayor-Modder-Cities2-Plugins` line).

- [ ] **Step 2: Add a Claude Code section to `INSTALL.md`**

Immediately after the existing Codex install steps (after the block that ends the Codex marketplace/plugin install instructions), add:

```markdown
## Install in Claude Code

In Claude Code, add the shared Mayor Modder Cities2 Plugins marketplace and
install the plugin:

```text
/plugin marketplace add mayor-modder/Mayor-Modder-Cities2-Plugins
/plugin install cities2-chief-of-staff@mayor-modder-cities2
```

The plugin bundles the Chief of Staff skill (namespaced
`/cities2-chief-of-staff:cities2-chief-of-staff`) and a plugin-local MCP server.
It requires Python 3.11 or newer on your PATH; set
`CITIES2_CHIEF_OF_STAFF_PYTHON` to a specific interpreter if needed.
```

- [ ] **Step 3: Note Claude support in `README.md`**

Find the sentence in `README.md` that describes Codex installation/support and add a neighboring line noting Claude Code. For example, after the existing install/marketplace mention, add:

```markdown
Cities2 Chief of Staff ships for both Codex and Claude Code from the shared
Mayor Modder Cities2 Plugins marketplace. See [INSTALL.md](INSTALL.md) for
per-client steps.
```

(If `README.md` already has an install section heading, place this line under it; keep wording neutral and do not introduce any personal identifiers.)

- [ ] **Step 4: Verify docs tests still pass**

Run: `python -m pytest tests/test_privacy.py -q`
Expected: PASS (`test_readme_links_privacy_doc` still finds `[PRIVACY.md](PRIVACY.md)` and the existing README sentence).

- [ ] **Step 5: Commit**

```bash
git add INSTALL.md README.md
git commit -m "Document Claude Code installation" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 7: Full verification and sync

**Files:** none (verification only)

- [ ] **Step 1: Regenerate all packages**

Run: `python -m chief_of_staff.plugin_packages sync`
Expected: prints updated artifacts under both `dist/plugins/cities2-chief-of-staff/` and `dist/plugins/cities2-chief-of-staff-claude/` (or "in sync" if already generated by the test runs).

- [ ] **Step 2: Confirm no drift**

Run: `python -m chief_of_staff.plugin_packages check`
Expected: `Plugin package payloads are in sync.` and exit code 0.

- [ ] **Step 3: Run the entire test suite**

Run: `python -m pytest tests -q`
Expected: PASS (no failures, no errors).

- [ ] **Step 4: Confirm the Codex distribution is unchanged**

Run: `git status --porcelain dist/plugins/cities2-chief-of-staff`
Expected: no output for the Codex package contents beyond what was already committed/ignored (the Codex `.codex-plugin/plugin.json`, `.mcp.json`, and `README.md` builders were not modified, so their generated output is byte-identical). `dist/` is gitignored, so the practical check is that `git diff` shows no changes to `chief_of_staff/plugin_metadata.py`'s `codex_*` functions.

- [ ] **Step 5: Final confirmation commit (if any docs/generated tracked files changed)**

```bash
git status
# If only dist/ (ignored) changed, nothing to commit. Otherwise:
git add -A
git commit -m "Finalize Claude Code target wiring" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Post-implementation: catalog repo publish (manual, external)

This repo cannot create files in the external `Mayor-Modder-Cities2-Plugins` repo. After merging, the maintainer performs a one-time setup there:

1. Create `.claude-plugin/marketplace.json` in the catalog repo using the canonical content from `python -c "from chief_of_staff import plugin_metadata; print(plugin_metadata.claude_marketplace_json())"`.
2. From this repo, run `python -m chief_of_staff.plugin_packages sync-catalog --target claude --catalog-root ../Mayor-Modder-Cities2-Plugins` to copy the Claude payload into `plugins/cities2-chief-of-staff-claude/`.
3. Commit and push the catalog repo.
4. Verify end-to-end in Claude Code: `/plugin marketplace add mayor-modder/Mayor-Modder-Cities2-Plugins` then `/plugin install cities2-chief-of-staff@mayor-modder-cities2`.

---

## Self-Review Notes

- **Spec coverage:** platform registry (Tasks 2–3), Claude builders incl. `${CLAUDE_PLUGIN_ROOT}` mcp + dropped `interface` block (Task 1), shared skill/launcher/vendor (reused, no task needed), same-repo dual marketplace + `--target` default `all` (Tasks 3–4), tests incl. privacy/identity (Tasks 4–5), docs (Task 6), Codex frozen (verified Task 7 Step 4). Catalog publish documented as manual external step (post-implementation section). All spec sections map to a task.
- **Placeholder scan:** no TBD/TODO; every code step shows full code; commands have expected output.
- **Type/name consistency:** `Platform` fields, `_metadata_files`, `_selected_platforms`, `PLATFORMS_BY_KEY`, and `claude_*` builder names are used identically across Tasks 1–5; `package_roots` default changed to `None` consistently in both `sync_packages` and `check_packages`.
