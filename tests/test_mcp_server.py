from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from cityadvisor.mcp_server import handle_request


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
            config = {"mods_data_dir": str(mods_data)}

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


if __name__ == "__main__":
    unittest.main()
