from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from chief_of_staff.mcp_server import handle_request
from tests.save_investigator_fake import write_fake_dotnet


class McpServerTests(unittest.TestCase):
    def test_lists_chief_of_staff_tools(self) -> None:
        response = handle_request({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}, {})
        names = [tool["name"] for tool in response["result"]["tools"]]

        self.assertEqual(
            names,
            [
                "chief_of_staff_get_status",
                "chief_of_staff_analyze_city",
                "chief_of_staff_get_report",
                "chief_of_staff_get_transit",
            ],
        )

    def test_analyze_city_tool_uses_configured_mods_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mods_data = Path(tmp) / "ModsData"
            dataexport = mods_data / "CS2DataExport"
            dataexport.mkdir(parents=True)
            (dataexport / "latest.json").write_text(
                json.dumps({"city": {"city_name": "MCP City"}, "population": {"total_population": 1234}}),
                encoding="utf-8",
            )
            config = {"mods_data_dir": str(mods_data), "skip_save_investigator_refresh": True}

            response = handle_request(
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {"name": "chief_of_staff_analyze_city", "arguments": {}},
                },
                config,
            )

        text = response["result"]["content"][0]["text"]
        payload = json.loads(text)
        self.assertEqual(payload["city_name"], "MCP City")
        self.assertIn("Population: 1,234", payload["markdown"])

    def test_analyze_city_tool_refreshes_save_investigator_before_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mods_data = root / "ModsData"
            dataexport = mods_data / "CS2DataExport"
            dataexport.mkdir(parents=True)
            (dataexport / "latest.json").write_text(
                json.dumps(
                    {
                        "city": {"city_name": "MCP Refresh City"},
                        "transit_line_detail_semantics": {
                            "lines": [
                                {
                                    "route_number": 42,
                                    "mode": "subway",
                                    "line_color": "#123456",
                                    "waiting_passengers_all_stops": 30,
                                    "max_waiting_passengers_at_stop": 12,
                                }
                            ]
                        },
                    }
                ),
                encoding="utf-8",
            )
            tool_root = root / "tools" / "SaveInvestigator"
            project_path = tool_root / "SaveInvestigator.csproj"
            old_output = tool_root / "bin" / "Debug" / "net8.0" / "output" / "20000101-000000"
            old_output.mkdir(parents=True)
            project_path.write_text("<Project />", encoding="utf-8")
            (old_output / "city-state-report-facts.json").write_text(
                json.dumps({"estimatedCompletionPercent": 1}),
                encoding="utf-8",
            )
            (old_output / "transport-report-facts.json").write_text(
                json.dumps(
                    {
                        "LineGroups": [
                            {
                                "Mode": "subway",
                                "Lines": [
                                    {
                                        "DisplayName": "Stale Subway",
                                        "RouteNumber": 42,
                                        "ColorHex": "#123456",
                                    }
                                ],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            fake_bin = root / "fake-bin"
            write_fake_dotnet(fake_bin)
            fake_dotnet = fake_bin / ("dotnet.cmd" if os.name == "nt" else "dotnet")

            with (
                mock.patch("chief_of_staff.paths.Path.cwd", return_value=root),
                mock.patch.dict(
                    os.environ,
                    {
                        "PATH": f"{fake_bin}{os.pathsep}{os.environ.get('PATH', '')}",
                        "CHIEF_OF_STAFF_DOTNET_COMMAND": str(fake_dotnet),
                        "CHIEF_OF_STAFF_SAVE_INVESTIGATOR_PROJECT": str(project_path),
                    },
                ),
            ):
                response = handle_request(
                    {
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "tools/call",
                        "params": {"name": "chief_of_staff_analyze_city", "arguments": {}},
                    },
                    {"mods_data_dir": str(mods_data)},
                )

        text = response["result"]["content"][0]["text"]
        payload = json.loads(text)
        self.assertIn("Fresh Subway: 30 waiting, max stop 12", payload["markdown"])
        self.assertNotIn("Stale Subway", payload["markdown"])

    def test_analyze_city_tool_does_not_use_stale_save_output_when_refresh_skips(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mods_data = root / "ModsData"
            dataexport = mods_data / "CS2DataExport"
            dataexport.mkdir(parents=True)
            (dataexport / "latest.json").write_text(
                json.dumps({"city": {"city_name": "No Stale City"}, "population": {"total_population": 1234}}),
                encoding="utf-8",
            )
            stale_root = root / "stale-save-output"
            stale_output = stale_root / "20000101-000000"
            stale_output.mkdir(parents=True)
            (stale_output / "city-state-report-facts.json").write_text(
                json.dumps({"estimatedCompletionPercent": 99}),
                encoding="utf-8",
            )
            (stale_output / "transport-report-facts.json").write_text("{}", encoding="utf-8")

            response = handle_request(
                {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {"name": "chief_of_staff_analyze_city", "arguments": {}},
                },
                {
                    "mods_data_dir": str(mods_data),
                    "save_investigator_output_dir": str(stale_root),
                    "save_investigator_project": str(root / "missing" / "SaveInvestigator.csproj"),
                },
            )

        text = response["result"]["content"][0]["text"]
        payload = json.loads(text)
        self.assertEqual(payload["city_name"], "No Stale City")
        self.assertNotIn("saveinvestigator", payload["evidence_sources"])
        self.assertIn("saveinvestigator", payload["missing_sources"])
        self.assertNotIn("Save understanding: 99%", payload["markdown"])

    def test_get_transit_tool_returns_resolved_line_and_station_names(self) -> None:
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
                        "TransitLineDetailSemantics": {
                            "Lines": [
                                {
                                    "RouteNumber": 5,
                                    "Mode": "subway",
                                    "LineColor": "#FFD100",
                                    "WaitingPassengersAllStops": 785,
                                    "MaxWaitingPassengersAtStop": 312,
                                    "Stops": [
                                        {
                                            "WaypointEntityIndex": 841161,
                                            "StopName": None,
                                            "WaitingPassengers": 312,
                                            "RoutePosition": 0.9621,
                                        }
                                    ],
                                }
                            ]
                        }
                    }
                ),
                encoding="utf-8",
            )
            (save_output / "city-state-report-facts.json").write_text("{}", encoding="utf-8")
            (save_output / "transport-report-facts.json").write_text(
                json.dumps(
                    {
                        "LineGroups": [
                            {
                                "Mode": "subway",
                                "Lines": [
                                    {
                                        "DisplayName": "Gold Line",
                                        "LineEntityIndex": 950806,
                                        "RouteNumber": 5,
                                        "ColorHex": "#FFD100",
                                    }
                                ],
                            }
                        ],
                        "StationGroups": [
                            {
                                "Mode": "subway",
                                "Stations": [
                                    {
                                        "Name": "Jacob Circle",
                                        "Mode": "subway",
                                        "ServiceJoinStatus": "resolved",
                                        "ServedLineNames": ["Gold Line"],
                                    }
                                ],
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
                                "Mode": "subway",
                                "Role": "station",
                                "Name": "Jacob Circle",
                                "JoinStatus": "resolved",
                                "ExactLines": [
                                    {
                                        "LineEntityIndex": 950806,
                                        "RouteNumber": 5,
                                        "ColorHex": "#FFD100",
                                        "LineName": "Gold Line",
                                        "JoinComponentType": "Game.Routes.Connected",
                                    }
                                ],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            response = handle_request(
                {
                    "jsonrpc": "2.0",
                    "id": 4,
                    "method": "tools/call",
                    "params": {"name": "chief_of_staff_get_transit", "arguments": {}},
                },
                {
                    "mods_data_dir": str(mods_data),
                    "save_investigator_output_dir": str(root / "SaveInvestigator" / "output"),
                    "skip_save_investigator_refresh": True,
                },
            )

        text = response["result"]["content"][0]["text"]
        payload = json.loads(text)
        self.assertEqual(payload["line_name_resolution"], "save_investigator")
        self.assertEqual(payload["station_name_resolution"], "save_investigator")
        self.assertEqual(payload["lines"][0]["name"], "Gold Line")
        self.assertIn("Jacob Circle", payload["lines"][0]["station_names"])
        self.assertEqual(payload["station_services"][0]["station_name"], "Jacob Circle")
        self.assertEqual(payload["station_services"][0]["line_name"], "Gold Line")
        self.assertEqual(payload["unresolved_live_stop_queues"][0]["line_name"], "Gold Line")
        self.assertIn("waypoint-to-station", payload["unresolved_live_stop_queues"][0]["unresolved_reason"])


if __name__ == "__main__":
    unittest.main()
