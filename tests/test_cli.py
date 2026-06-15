from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from chief_of_staff.cli import main
from tests.save_investigator_fake import write_fake_dotnet


class CliTests(unittest.TestCase):
    def test_status_outputs_json_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mods_data = Path(tmp) / "ModsData"
            dataexport = mods_data / "CS2DataExport"
            dataexport.mkdir(parents=True)
            (dataexport / "latest.json").write_text(
                json.dumps({"city": {"city_name": "CLI City"}, "population": {"total_population": 42}}),
                encoding="utf-8",
            )

            out = io.StringIO()
            with mock.patch("sys.stdout", out):
                rc = main(["status", "--mods-data", str(mods_data), "--json"])

        self.assertEqual(rc, 0)
        payload = json.loads(out.getvalue())
        self.assertEqual(payload["sources"][0]["name"], "dataexport")
        self.assertTrue(payload["sources"][0]["available"])

    def test_analyze_outputs_markdown_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mods_data = Path(tmp) / "ModsData"
            dataexport = mods_data / "CS2DataExport"
            dataexport.mkdir(parents=True)
            (dataexport / "latest.json").write_text(
                json.dumps({"city": {"city_name": "CLI City"}, "population": {"total_population": 42}}),
                encoding="utf-8",
            )

            out = io.StringIO()
            with mock.patch("sys.stdout", out):
                rc = main(["analyze", "--mods-data", str(mods_data), "--skip-save-investigator-refresh"])

        self.assertEqual(rc, 0)
        self.assertIn("# Chief of Staff Brief", out.getvalue())
        self.assertIn("CLI City", out.getvalue())

    def test_analyze_refreshes_save_investigator_before_building_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mods_data = root / "ModsData"
            dataexport = mods_data / "CS2DataExport"
            dataexport.mkdir(parents=True)
            (dataexport / "latest.json").write_text(
                json.dumps(
                    {
                        "city": {"city_name": "Refresh City"},
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

            out = io.StringIO()
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
                mock.patch("sys.stdout", out),
            ):
                rc = main(["analyze", "--mods-data", str(mods_data)])

        self.assertEqual(rc, 0)
        self.assertIn("Fresh Subway: 30 waiting, max stop 12", out.getvalue())
        self.assertNotIn("Stale Subway", out.getvalue())

    def test_analyze_does_not_use_stale_save_output_when_refresh_skips(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mods_data = root / "ModsData"
            dataexport = mods_data / "CS2DataExport"
            dataexport.mkdir(parents=True)
            (dataexport / "latest.json").write_text(
                json.dumps({"city": {"city_name": "No Stale CLI"}, "population": {"total_population": 42}}),
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

            out = io.StringIO()
            with mock.patch("sys.stdout", out):
                rc = main(
                    [
                        "analyze",
                        "--mods-data",
                        str(mods_data),
                        "--save-investigator-output",
                        str(stale_root),
                        "--save-investigator-project",
                        str(root / "missing" / "SaveInvestigator.csproj"),
                    ]
                )

        self.assertEqual(rc, 0)
        self.assertIn("No Stale CLI", out.getvalue())
        self.assertIn("Missing Save Investigator limits save-derived diagnosis.", out.getvalue())
        self.assertNotIn("Save understanding: 99%", out.getvalue())


if __name__ == "__main__":
    unittest.main()
