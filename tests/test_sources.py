from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from cityadvisor.analysis import build_city_report
from cityadvisor.sources import discover_sources


class SourceDiscoveryTests(unittest.TestCase):
    def test_discovers_dataexport_infoloom_and_save_investigator_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mods_data = root / "ModsData"
            dataexport = mods_data / "CS2DataExport"
            infoloom = mods_data / "InfoLoomBridge"
            save_output = root / "SaveInvestigator" / "output" / "20260503-120000"
            dataexport.mkdir(parents=True)
            infoloom.mkdir(parents=True)
            save_output.mkdir(parents=True)

            (dataexport / "latest.json").write_text(
                json.dumps(
                    {
                        "schema_version": "2.6.0",
                        "exported_at_utc": "2026-05-03T12:00:00Z",
                        "city": {"city_name": "Evergreen Bay", "status": "ok"},
                        "population": {"total_population": 173422, "status": "ok"},
                        "workforce": {"unemployed": 3200, "workers": 104000},
                    }
                ),
                encoding="utf-8",
            )
            (infoloom / "latest.json").write_text(
                json.dumps({"exported_at_utc": "2026-05-03T12:01:00Z", "panels": {"demographics": {}}}),
                encoding="utf-8",
            )
            (save_output / "city-state-report-facts.json").write_text(
                json.dumps({"estimatedCompletionPercent": 72, "sections": []}),
                encoding="utf-8",
            )
            (save_output / "transport-report-facts.json").write_text(
                json.dumps({"lineGroups": [{"mode": "bus", "lineCount": 22}]}),
                encoding="utf-8",
            )

            inventory = discover_sources(mods_data_dir=mods_data, save_investigator_output_dir=root / "SaveInvestigator" / "output")

        by_name = {source.name: source for source in inventory.sources}
        self.assertTrue(by_name["dataexport"].available)
        self.assertTrue(by_name["infoloombridge"].available)
        self.assertTrue(by_name["saveinvestigator"].available)
        self.assertEqual(by_name["dataexport"].summary["city_name"], "Evergreen Bay")
        self.assertEqual(by_name["saveinvestigator"].summary["latest_output"], str(save_output))

    def test_builds_report_from_available_evidence_without_requiring_optional_mods(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mods_data = Path(tmp) / "ModsData"
            dataexport = mods_data / "CS2DataExport"
            dataexport.mkdir(parents=True)
            (dataexport / "latest.json").write_text(
                json.dumps(
                    {
                        "exported_at_utc": "2026-05-03T12:00:00Z",
                        "city": {"city_name": "Evergreen Bay"},
                        "population": {"total_population": 173422},
                        "transport_proxies": {"active_transport_lines": 214},
                    }
                ),
                encoding="utf-8",
            )

            inventory = discover_sources(mods_data_dir=mods_data)
            report = build_city_report(inventory)

        self.assertEqual(report.city_name, "Evergreen Bay")
        self.assertIn("dataexport", report.evidence_sources)
        self.assertIn("infoloombridge", report.missing_optional_sources)
        self.assertIn("Population: 173,422", report.markdown)
        self.assertIn("Active transport lines: 214", report.markdown)

    def test_reads_power_shell_utf8_json_with_bom(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mods_data = Path(tmp) / "ModsData"
            dataexport = mods_data / "CS2DataExport"
            dataexport.mkdir(parents=True)
            (dataexport / "latest.json").write_bytes(
                b'\xef\xbb\xbf{"city":{"city_name":"BOM Bay"},"population":{"total_population":50}}'
            )

            inventory = discover_sources(mods_data_dir=mods_data)
            report = build_city_report(inventory)

        self.assertEqual(report.city_name, "BOM Bay")
        self.assertIn("Population: 50", report.markdown)

    def test_reads_current_dataexport_pascal_case_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mods_data = Path(tmp) / "ModsData"
            dataexport = mods_data / "CS2DataExport"
            dataexport.mkdir(parents=True)
            (dataexport / "latest.json").write_text(
                json.dumps(
                    {
                        "SchemaVersion": "2.6.0",
                        "ExportedAtUtc": "2026-05-03T20:28:12Z",
                        "City": {"CityName": "Pascal City", "Status": "ok"},
                        "Population": {"TotalPopulation": 176073, "Status": "ok"},
                        "TransportProxies": {"ActiveTransportLines": 25},
                    }
                ),
                encoding="utf-8",
            )

            inventory = discover_sources(mods_data_dir=mods_data)
            report = build_city_report(inventory)

        source = inventory.sources[0]
        self.assertEqual(source.summary["schema_version"], "2.6.0")
        self.assertEqual(report.city_name, "Pascal City")
        self.assertIn("Population: 176,073", report.markdown)
        self.assertIn("Active transport lines: 25", report.markdown)


if __name__ == "__main__":
    unittest.main()
