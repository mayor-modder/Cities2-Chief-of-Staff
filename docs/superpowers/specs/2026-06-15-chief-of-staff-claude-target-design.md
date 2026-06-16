# Chief of Staff — Claude Code distribution target

Date: 2026-06-15
Status: Approved (design)

## Goal

Teach the existing Cities2 Chief of Staff plugin generator to emit a second,
Claude Code-native plugin package alongside the current Codex package, and
publish it into the *same* `Mayor-Modder-Cities2-Plugins` marketplace repo via a
separate `.claude-plugin/marketplace.json`. The working Codex distribution must
be left byte-for-byte unchanged.

This realizes the "leave packaging boundaries clean enough to add Claude and
Antigravity later" intent recorded in the original Codex plugin design.

## Background (current state)

The generator is driven by two canonical modules:

- `chief_of_staff/plugin_metadata.py` — pure string builders for the Codex
  manifest (`codex_plugin_json`), MCP launcher config (`codex_mcp_json`), README
  (`codex_readme_md`), and a reference marketplace builder (`codex_marketplace_json`).
- `chief_of_staff/plugin_packages.py` — the `sync` / `check` / `sync-catalog`
  pipeline. It writes a platform-agnostic payload (skill + vendored Python
  package + Node launcher via `_write_payload`) and then writes the per-package
  metadata files listed in `METADATA_FILES`.

Established facts the design relies on:

- The **skill** (`skills/cities2-chief-of-staff/SKILL.md`), the **Node launcher**
  (`bin/cities2-chief-of-staff-launcher.js`), and the **vendored package**
  (`vendor/chief_of_staff/`) are platform-neutral and already shared via
  `_write_payload`. The launcher resolves its own root from `__dirname`
  (`selfRoot = path.resolve(__dirname, "..")`), so it does not depend on `cwd`.
- `marketplace.json` is **not** emitted by the `sync` pipeline today.
  `codex_marketplace_json()` exists only as a reference builder; the catalog repo
  owns the real file, and `sync_catalog_package` requires it to pre-exist before
  copying the payload in.
- Tests assert per-artifact (`tests/test_packaging.py`) and gate drift via
  `check_packages(ROOT)` with no explicit `package_roots`.

Claude Code plugin/marketplace schema (confirmed against current docs):

- Plugin manifest lives at `.claude-plugin/plugin.json`. Only `name` is required;
  it supports `displayName` (top-level), `version`, `description`, `author`,
  `homepage`, `repository`, `license`, `keywords`, and component paths including
  `skills: "./skills/"` and `mcpServers: "./.mcp.json"`. Unrecognized fields are
  ignored.
- Marketplace manifest lives at `.claude-plugin/marketplace.json`. Required:
  `name` (kebab-case identifier used in install commands), `owner` (`{name, …}`),
  and `plugins[]`. `metadata.pluginRoot` sets a base dir so plugin `source` can be
  a relative directory name. A relative-path `source` resolves against the
  marketplace root and works for git-hosted marketplaces.
- Skills use the same `SKILL.md` + YAML frontmatter (`name`, `description`) format
  as Codex/Anthropic; a plugin's `skills/` directory is auto-discovered. Plugin
  skills are namespaced `/<plugin>:<skill>`.
- A bundled MCP server uses a standard `mcpServers` map (command/args/env/cwd).
  The `${CLAUDE_PLUGIN_ROOT}` path variable points at the installed plugin dir and
  is the correct way to reference the launcher.
- Install flow: `/plugin marketplace add <owner/repo>` then
  `/plugin install <plugin>@<marketplace-name>`.

## Architecture: platform registry

Replace the Codex-specific singletons with a small registry so `sync` / `check` /
`sync-catalog` operate generically over platforms. Adding Antigravity later
becomes one registry entry plus four builders.

Define a `Platform` descriptor in `plugin_metadata.py` (preserves the existing
one-way dependency `plugin_packages` → `plugin_metadata`):

```python
@dataclass(frozen=True)
class Platform:
    key: str                       # "codex" | "claude"
    manifest_dir: str              # ".codex-plugin" | ".claude-plugin"
    plugin_json: Callable[[], str]
    mcp_json: Callable[[], str]
    readme_md: Callable[[], str]
    marketplace_json: Callable[[], str]   # reference builder; catalog-owned
    dist_package_root: Path        # dist/plugins/<dir>
    catalog_package_root: Path     # plugins/<dir>
    catalog_marketplace_rel: Path  # path to that platform's marketplace.json in catalog

PLATFORMS = (CODEX, CLAUDE)
```

Path assignments:

| Platform | manifest_dir | dist_package_root | catalog_package_root | catalog_marketplace_rel |
|----------|--------------|-------------------|----------------------|-------------------------|
| codex | `.codex-plugin` | `dist/plugins/cities2-chief-of-staff` | `plugins/cities2-chief-of-staff` | `.agents/plugins/marketplace.json` |
| claude | `.claude-plugin` | `dist/plugins/cities2-chief-of-staff-claude` | `plugins/cities2-chief-of-staff-claude` | `.claude-plugin/marketplace.json` |

The Codex row keeps its exact current paths, so existing output and installs are
untouched.

### `plugin_packages.py` changes

- Derive the per-platform metadata file set (`<manifest_dir>/plugin.json`,
  `.mcp.json`, `README.md`) from each `Platform` instead of the hard-coded
  `METADATA_FILES` dict.
- `sync_packages` / `check_packages`: loop over `PLATFORMS` (default), writing
  `_write_payload` into each platform's `dist_package_root` and syncing/checking
  that platform's metadata files. Keep the existing `package_roots`-style override
  capability for targeted tests.
- `sync_catalog_package`: take a target selection. For each selected platform,
  require `catalog_root / platform.catalog_marketplace_rel` to exist, then copy
  `dist_package_root` → `catalog_root / catalog_package_root`. The existing
  catalog-escape guard is retained.
- CLI: `sync` and `check` cover all platforms. `sync-catalog` gains
  `--target codex|claude|all` (default `all`). `--catalog-root` is unchanged.

`_write_payload`, `_replace_payload`, the launcher/run-server constants, and all
tree-diff helpers are reused unchanged.

## Claude metadata builders (`plugin_metadata.py`)

Shared constants (`NAME`, `DISPLAY_NAME`, `AUTHOR`, `REPO_URL`, `PRIVACY_URL`,
`TERMS_URL`, `LICENSE`, `KEYWORDS`, `SKILL_NAMES`) are reused. New builders:

### `claude_plugin_json()` → `.claude-plugin/plugin.json`

Lean Claude-native manifest. The Codex `interface{}` block (brandColor,
defaultPrompt, capabilities, screenshots, category, developerName, the various
URLs) is **dropped** — those are Codex-only and Claude ignores them.

```json
{
  "name": "cities2-chief-of-staff",
  "displayName": "Cities2 Chief of Staff",
  "version": "<VERSION>",
  "description": "Cities2 Chief of Staff for Claude Code.",
  "author": { "name": "mayor-modder", "url": "https://github.com/mayor-modder" },
  "homepage": "https://github.com/mayor-modder/Cities2-Chief-of-Staff",
  "repository": "https://github.com/mayor-modder/Cities2-Chief-of-Staff",
  "license": "MIT",
  "keywords": ["cities-skylines-ii", "mcp", "city-analysis", "agent-skills"],
  "skills": "./skills/",
  "mcpServers": "./.mcp.json"
}
```

### `claude_mcp_json()` → `.mcp.json`

Same Node launcher, referenced through Claude's path variable. No `cwd` is needed
because the launcher self-locates from `__dirname`.

```json
{
  "mcpServers": {
    "cities2-chief-of-staff": {
      "command": "node",
      "args": ["${CLAUDE_PLUGIN_ROOT}/bin/cities2-chief-of-staff-launcher.js"]
    }
  }
}
```

### `claude_marketplace_json()` → reference for `.claude-plugin/marketplace.json`

Catalog-owned (parallels `codex_marketplace_json`); used to author the catalog
file once and to assert shape in tests.

```json
{
  "name": "mayor-modder-cities2",
  "description": "Mayor Modder Cities: Skylines II plugins for Claude Code.",
  "owner": { "name": "mayor-modder", "url": "https://github.com/mayor-modder" },
  "metadata": { "pluginRoot": "./plugins" },
  "plugins": [
    {
      "name": "cities2-chief-of-staff",
      "source": "cities2-chief-of-staff-claude",
      "description": "Local Cities: Skylines II mayoral analysis",
      "version": "<VERSION>",
      "category": "productivity"
    }
  ]
}
```

### `claude_readme_md()` → `README.md`

Claude install instructions:

```
/plugin marketplace add mayor-modder/Mayor-Modder-Cities2-Plugins
/plugin install cities2-chief-of-staff@mayor-modder-cities2
```

Retains the same privacy paragraph as the Codex README.

## Skill

Shared verbatim. The single `skills/cities2-chief-of-staff/SKILL.md` is copied
into both dist payloads by the existing `_copy_skills`. On Claude it is namespaced
`/cities2-chief-of-staff:cities2-chief-of-staff`. Its "route game knowledge and
modding to Cities2-MCP" guidance remains valid because Cities2-MCP is also a
Claude plugin. No Claude skill variant is created.

## Catalog repo layout (after publish)

```
Mayor-Modder-Cities2-Plugins/
  .agents/plugins/marketplace.json        # Codex — unchanged
  .claude-plugin/marketplace.json         # Claude — NEW, authored once from claude_marketplace_json()
  plugins/
    cities2-chief-of-staff/               # Codex payload — unchanged
    cities2-chief-of-staff-claude/        # Claude payload — NEW
```

Install identity is `cities2-chief-of-staff` on both platforms; only the directory
name differs so the two payloads coexist in one repo. Authoring
`.claude-plugin/marketplace.json` in the catalog repo is a one-time manual step
(the repo is external to this worktree); its canonical content is produced by
`claude_marketplace_json()`. `sync-catalog --target claude` then requires that
file to exist and copies `dist/plugins/cities2-chief-of-staff-claude/` →
`plugins/cities2-chief-of-staff-claude/`.

## Tests (TDD, mirroring existing style in `tests/test_packaging.py`)

New / extended coverage:

- Claude manifest present and correct: `name`, top-level `displayName`, `version`,
  `skills == "./skills/"`, `mcpServers == "./.mcp.json"`; assert the Codex
  `interface` block is absent.
- Claude `.mcp.json`: `command == "node"` and args contain
  `${CLAUDE_PLUGIN_ROOT}/bin/cities2-chief-of-staff-launcher.js`.
- Claude payload contains the skill, `vendor/run_server.py`,
  `vendor/chief_of_staff/mcp_server.py`, and the launcher (reuse existing
  payload assertions against the Claude dist root).
- Launcher `--version` and MCP `initialize` round-trip — reused against the Claude
  payload (same launcher binary, so this confirms parity).
- `claude_marketplace_json()` parses; has `owner.name`, kebab-case `name`,
  `plugins[0].name == "cities2-chief-of-staff"`, and a resolvable `source`.
- `sync-catalog --target claude`: with `.claude-plugin/marketplace.json`
  pre-existing in the fixture catalog, payload is copied to
  `plugins/cities2-chief-of-staff-claude/`.
- `check_packages(ROOT)` (no args) now loops platforms and gates Claude drift —
  add an assertion that the repo's generated Claude package is in sync.
- Extend `tests/test_privacy.py` and `tests/test_public_identity.py` so the
  Claude artifacts are also scanned: no personal identifiers, neutral
  `mayor-modder` handle/paths only, and the privacy policy reference is present.

## Documentation

- `INSTALL.md`: add a Claude Code section with the `/plugin marketplace add` and
  `/plugin install …@mayor-modder-cities2` commands.
- `README.md`: note Claude Code support alongside Codex.
- Codex README/builder unchanged; the Claude README is generated by
  `claude_readme_md()`.

## Privacy

All builders reuse the existing neutral `mayor-modder` handle and repo URLs; no
personal name, Windows username, or home-directory path is introduced. The
extended privacy/public-identity tests enforce this for the new artifacts.

## Out of scope

- Antigravity packaging (the registry makes it a future one-entry addition).
- Authoring/committing files inside the external `Mayor-Modder-Cities2-Plugins`
  repo (documented as a manual publish step; this change only produces the
  canonical content and the `sync-catalog` mechanism).
- Any change to the Codex manifest, payload, or marketplace files.

## Decisions (confirmed)

- Same marketplace repo, both manifests (`.agents/plugins/marketplace.json` for
  Codex, `.claude-plugin/marketplace.json` for Claude), separate payload dirs.
- Generator structured as a platform registry (refactor), not parallel functions.
- Claude marketplace id `mayor-modder-cities2`; Claude payload dir
  `cities2-chief-of-staff-claude`.
- Drop the Codex `interface{}` block from the Claude manifest.
- `sync-catalog` defaults to `all` platforms.
