from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from cityadvisor.cli import main


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
                rc = main(["analyze", "--mods-data", str(mods_data)])

        self.assertEqual(rc, 0)
        self.assertIn("# CityAdvisor Report", out.getvalue())
        self.assertIn("CLI City", out.getvalue())


if __name__ == "__main__":
    unittest.main()
