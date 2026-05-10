from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from cityadvisor.mcp_server import handle_request
from tests.save_investigator_fake import write_fake_dotnet


class McpServerTests(unittest.TestCase):
    def test_lists_cityadvisor_tools(self) -> None:
        response = handle_request({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}, {})
        names = [tool["name"] for tool in response["result"]["tools"]]

        self.assertEqual(
            names,
            [
                "cityadvisor_get_status",
                "cityadvisor_analyze_city",
                "cityadvisor_get_report",
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
                    "params": {"name": "cityadvisor_analyze_city", "arguments": {}},
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
                mock.patch("cityadvisor.paths.Path.cwd", return_value=root),
                mock.patch.dict(
                    os.environ,
                    {
                        "PATH": f"{fake_bin}{os.pathsep}{os.environ.get('PATH', '')}",
                        "CITYADVISOR_DOTNET_COMMAND": str(fake_dotnet),
                        "CITYADVISOR_SAVE_INVESTIGATOR_PROJECT": str(project_path),
                    },
                ),
            ):
                response = handle_request(
                    {
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "tools/call",
                        "params": {"name": "cityadvisor_analyze_city", "arguments": {}},
                    },
                    {"mods_data_dir": str(mods_data)},
                )

        text = response["result"]["content"][0]["text"]
        payload = json.loads(text)
        self.assertIn("Fresh Subway: 30 waiting, max stop 12", payload["markdown"])
        self.assertNotIn("Stale Subway", payload["markdown"])


if __name__ == "__main__":
    unittest.main()
