from __future__ import annotations

from typing import Any

from .models import CityReport, SourceInventory, SourceStatus


def build_city_report(inventory: SourceInventory) -> CityReport:
    dataexport = _find(inventory, "dataexport")
    save = _find(inventory, "saveinvestigator")
    infoloom = _find(inventory, "infoloombridge")
    city_name = _first_text(
        dataexport.summary.get("city_name") if dataexport else None,
        "Unknown city",
    )
    facts: dict[str, Any] = {}
    lines = ["# CityAdvisor Report", ""]
    lines.append(f"City: {city_name}")
    lines.append("")
    lines.append("## Evidence")
    for source in inventory.sources:
        state = "available" if source.available else "missing"
        lines.append(f"- {source.label}: {state}")
    lines.append("")
    lines.append("## Summary")

    if dataexport and dataexport.available:
        _add_fact_line(lines, facts, "Population", dataexport.summary.get("total_population"), number=True)
        _add_fact_line(lines, facts, "Active transport lines", dataexport.summary.get("active_transport_lines"), number=True)
    if save and save.available:
        _add_fact_line(
            lines,
            facts,
            "Save understanding",
            save.summary.get("estimated_completion_percent"),
            suffix="%",
        )
    if infoloom and infoloom.available:
        panels = infoloom.summary.get("panels")
        if isinstance(panels, list):
            facts["infoloom_panels"] = panels
            lines.append(f"- InfoLoom panels: {', '.join(str(panel) for panel in panels) or 'none'}")

    lines.append("")
    lines.append("## Next Useful Evidence")
    missing_optional = [source.name for source in inventory.sources if not source.available and source.name != "dataexport"]
    if missing_optional:
        for source in inventory.sources:
            if source.name in missing_optional:
                lines.append(f"- {source.label}: {source.message}")
    else:
        lines.append("- All known optional evidence sources are available.")

    return CityReport(
        city_name=city_name,
        evidence_sources=[source.name for source in inventory.available_sources],
        missing_optional_sources=missing_optional,
        markdown="\n".join(lines).strip() + "\n",
        facts=facts,
    )


def _find(inventory: SourceInventory, name: str) -> SourceStatus | None:
    for source in inventory.sources:
        if source.name == name:
            return source
    return None


def _first_text(*values: object) -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "Unknown"


def _add_fact_line(
    lines: list[str],
    facts: dict[str, Any],
    label: str,
    value: object,
    *,
    number: bool = False,
    suffix: str = "",
) -> None:
    if value is None:
        return
    key = label.lower().replace(" ", "_")
    facts[key] = value
    if number and isinstance(value, (int, float)):
        rendered = f"{value:,.0f}"
    else:
        rendered = str(value)
    lines.append(f"- {label}: {rendered}{suffix}")
