from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import SourceInventory, SourceStatus, path_str
from .paths import default_mods_data_dir, default_save_investigator_output_dir


def discover_sources(
    mods_data_dir: Path | str | None = None,
    save_investigator_output_dir: Path | str | None = None,
) -> SourceInventory:
    mods_data = Path(mods_data_dir).expanduser() if mods_data_dir is not None else default_mods_data_dir()
    save_output = (
        Path(save_investigator_output_dir).expanduser()
        if save_investigator_output_dir is not None
        else default_save_investigator_output_dir()
    )
    return SourceInventory(
        [
            _dataexport_status(mods_data),
            _save_investigator_status(save_output),
            _infoloom_status(mods_data),
        ]
    )


def _dataexport_status(mods_data: Path) -> SourceStatus:
    path = mods_data / "CS2DataExport" / "latest.json"
    payload = _read_json(path)
    if payload is None:
        return SourceStatus(
            name="dataexport",
            label="Cities2-DataExport",
            available=False,
            path=path_str(path),
            kind="live_sample",
            message="No DataExport latest.json found.",
        )
    city = _as_dict(payload.get("city"))
    population = _as_dict(payload.get("population"))
    transport = _as_dict(payload.get("transport_proxies"))
    return SourceStatus(
        name="dataexport",
        label="Cities2-DataExport",
        available=True,
        path=path_str(path),
        kind="live_sample",
        message="DataExport latest.json is available.",
        summary={
            "city_name": city.get("city_name"),
            "exported_at_utc": payload.get("exported_at_utc"),
            "schema_version": payload.get("schema_version"),
            "total_population": population.get("total_population"),
            "active_transport_lines": transport.get("active_transport_lines"),
        },
    )


def _infoloom_status(mods_data: Path) -> SourceStatus:
    path = mods_data / "InfoLoomBridge" / "latest.json"
    payload = _read_json(path)
    if payload is None:
        return SourceStatus(
            name="infoloombridge",
            label="Cities2-InfoLoomBridge",
            available=False,
            path=path_str(path),
            kind="optional_live_detail",
            message="No InfoLoomBridge latest.json found.",
        )
    panels = _as_dict(payload.get("panels"))
    return SourceStatus(
        name="infoloombridge",
        label="Cities2-InfoLoomBridge",
        available=True,
        path=path_str(path),
        kind="optional_live_detail",
        message="InfoLoomBridge latest.json is available.",
        summary={
            "exported_at_utc": payload.get("exported_at_utc"),
            "panel_count": len(panels),
            "panels": sorted(panels.keys()),
        },
    )


def _save_investigator_status(output_root: Path) -> SourceStatus:
    latest = _latest_child_dir(output_root)
    if latest is None:
        return SourceStatus(
            name="saveinvestigator",
            label="Save Investigator",
            available=False,
            path=path_str(output_root),
            kind="save_analysis",
            message="No Save Investigator output directory found.",
        )
    city_state = _read_json(latest / "city-state-report-facts.json") or {}
    transport = _read_json(latest / "transport-report-facts.json") or {}
    line_groups = transport.get("lineGroups") if isinstance(transport, dict) else None
    return SourceStatus(
        name="saveinvestigator",
        label="Save Investigator",
        available=True,
        path=path_str(latest),
        kind="save_analysis",
        message="Save Investigator output is available.",
        summary={
            "latest_output": path_str(latest),
            "estimated_completion_percent": _as_dict(city_state).get("estimatedCompletionPercent"),
            "transport_line_group_count": len(line_groups) if isinstance(line_groups, list) else None,
        },
    )


def _latest_child_dir(path: Path) -> Path | None:
    if not path.is_dir():
        return None
    children = [child for child in path.iterdir() if child.is_dir()]
    if not children:
        return None
    return max(children, key=lambda child: child.stat().st_mtime)


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _as_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}
