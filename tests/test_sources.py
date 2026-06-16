from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from chief_of_staff.analysis import build_city_report
from chief_of_staff.sources import discover_sources
from chief_of_staff.transit import build_transit_snapshot


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
        self.assertIn("# Chief of Staff Brief", report.markdown)
        self.assertIn("dataexport", report.evidence_sources)
        self.assertIn("infoloombridge", report.missing_optional_sources)
        self.assertIn("Population: 173,422", report.markdown)
        self.assertIn("Active transport lines: 214", report.markdown)

    def test_reports_evidence_coverage_for_missing_optional_companions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mods_data = Path(tmp) / "ModsData"
            dataexport = mods_data / "CS2DataExport"
            dataexport.mkdir(parents=True)
            (dataexport / "latest.json").write_text(
                json.dumps(
                    {
                        "City": {"CityName": "Coverage City"},
                        "Population": {"TotalPopulation": 50000},
                    }
                ),
                encoding="utf-8",
            )

            inventory = discover_sources(mods_data_dir=mods_data)
            report = build_city_report(inventory)

        by_name = {source.name: source.to_dict() for source in inventory.sources}
        self.assertEqual(by_name["dataexport"]["coverage_state"], "usable")
        self.assertEqual(by_name["saveinvestigator"]["coverage_state"], "missing")
        self.assertEqual(by_name["infoloombridge"]["coverage_state"], "missing")
        self.assertIn("## Evidence Coverage", report.markdown)
        self.assertIn("- Cities2-DataExport: usable", report.markdown)
        self.assertIn("- Save Investigator: missing", report.markdown)
        self.assertIn("- Cities2-InfoLoomBridge: missing", report.markdown)
        self.assertIn("Missing Save Investigator limits save-derived diagnosis.", report.markdown)
        self.assertIn("Missing Cities2-InfoLoomBridge limits detailed InfoLoom-derived diagnosis.", report.markdown)

    def test_report_distinguishes_all_missing_sources_from_optional_missing_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            inventory = discover_sources(mods_data_dir=Path(tmp) / "ModsData")
            report = build_city_report(inventory)

        self.assertEqual(
            report.missing_sources,
            ["dataexport", "saveinvestigator", "infoloombridge"],
        )
        self.assertEqual(
            report.missing_optional_sources,
            ["dataexport", "saveinvestigator", "infoloombridge"],
        )
        payload = report.to_dict()
        self.assertEqual(payload["missing_sources"], report.missing_sources)

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

    def test_names_live_transit_hotspots_from_save_investigator(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mods_data = root / "ModsData"
            dataexport = mods_data / "CS2DataExport"
            save_output = root / "SaveInvestigator" / "output" / "20260503-120000"
            dataexport.mkdir(parents=True)
            save_output.mkdir(parents=True)
            (dataexport / "latest.json").write_text(
                json.dumps(
                    {
                        "City": {"CityName": "Copeland"},
                        "TransitLineDetailSemantics": {
                            "Lines": [
                                {
                                    "RouteNumber": 2,
                                    "Mode": "tram",
                                    "LineColor": "#EB131B",
                                    "WaitingPassengersAllStops": 436,
                                    "MaxWaitingPassengersAtStop": 110,
                                },
                                {
                                    "RouteNumber": 5,
                                    "Mode": "tram",
                                    "LineColor": "#FDB913",
                                    "WaitingPassengersAllStops": 90,
                                    "MaxWaitingPassengersAtStop": 55,
                                },
                            ]
                        },
                    }
                ),
                encoding="utf-8",
            )
            (save_output / "city-state-report-facts.json").write_text(
                json.dumps({"EstimatedCompletionPercent": 72}),
                encoding="utf-8",
            )
            (save_output / "transport-report-facts.json").write_text(
                json.dumps(
                    {
                        "LineGroups": [
                            {
                                "Mode": "unresolved",
                                "Lines": [
                                    {
                                        "DisplayName": "Isaiah Streetcar",
                                        "RouteNumber": 2,
                                        "ColorHex": "#EB131B",
                                    },
                                    {
                                        "DisplayName": "Swan Streetcar",
                                        "RouteNumber": 5,
                                        "ColorHex": "#FDB913",
                                    },
                                ],
                            }
                        ],
                        "StationGroups": [
                            {
                                "Mode": "tram",
                                "Stations": [
                                    {
                                        "Name": "Isaiah Junction",
                                        "Mode": "tram",
                                        "ServiceJoinStatus": "resolved",
                                        "ServedLineNames": ["Isaiah Streetcar"],
                                    }
                                ],
                            }
                        ],
                        "TopQueueHotspots": [
                            {
                                "LineDisplayName": "Isaiah Streetcar",
                                "LineEntityIndex": 483376,
                                "RouteNumber": 2,
                                "ColorHex": "#EB131B",
                                "TotalWaitingPassengers": 436,
                                "MaxStopQueue": 110,
                                "TopStop": {
                                    "StopEntityIndex": 261001,
                                    "OwnerEntityIndex": 483376,
                                    "WaitingPassengers": 110,
                                    "StationName": "Isaiah Junction",
                                    "StationMode": "tram",
                                    "StationRole": "station",
                                    "ResolutionStatus": "resolved_by_service_join",
                                },
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            (save_output / "transport-service-join-facts.json").write_text(
                json.dumps(
                    {
                        "Stations": [
                            {
                                "Mode": "tram",
                                "Role": "station",
                                "Name": "Isaiah Junction",
                                "JoinStatus": "resolved",
                                "ExactLines": [
                                    {
                                        "LineEntityIndex": 483376,
                                        "RouteNumber": 2,
                                        "ColorHex": "#EB131B",
                                        "LineName": "Isaiah Streetcar",
                                        "JoinComponentType": "Game.Routes.Connected",
                                    }
                                ],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            inventory = discover_sources(
                mods_data_dir=mods_data,
                save_investigator_output_dir=root / "SaveInvestigator" / "output",
            )
            report = build_city_report(inventory)

        self.assertIn("Isaiah Streetcar: 436 waiting, max stop 110", report.markdown)
        self.assertIn("Swan Streetcar: 90 waiting, max stop 55", report.markdown)
        self.assertLess(report.markdown.index("Save understanding"), report.markdown.index("## Transit Hotspots"))
        self.assertNotIn("Route 2", report.markdown)
        snapshot = build_transit_snapshot(inventory)
        self.assertIn("Isaiah Junction", snapshot["lines"][0]["station_names"])
        self.assertEqual(snapshot["station_services"][0]["line_name"], "Isaiah Streetcar")
        self.assertEqual(snapshot["stations"][0]["name"], "Isaiah Junction")
        self.assertEqual(snapshot["saved_queue_hotspots"][0]["top_stop"]["station_name"], "Isaiah Junction")


if __name__ == "__main__":
    unittest.main()
