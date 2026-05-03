from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from cityadvisor.analysis import build_city_report
    from cityadvisor.sources import discover_sources
else:
    from .analysis import build_city_report
    from .sources import discover_sources

JSON = dict[str, Any]
SERVER_NAME = "Cities2-CityAdvisor"
SERVER_INSTRUCTIONS = (
    "Cities2-CityAdvisor analyzes available Cities: Skylines II city evidence. "
    "It works without optional mods, and becomes more useful when Cities2-DataExport, "
    "Cities2-InfoLoomBridge, or Save Investigator outputs are available."
)


def handle_request(message: JSON, config: JSON) -> JSON | None:
    method = str(message.get("method", ""))
    req_id = message.get("id")
    params = message.get("params") if isinstance(message.get("params"), dict) else {}
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2025-06-18",
                "serverInfo": {"name": SERVER_NAME, "version": "0.1.0"},
                "capabilities": {"tools": {"listChanged": False}},
                "instructions": SERVER_INSTRUCTIONS,
            },
        }
    if method == "notifications/initialized":
        return None
    if method == "ping":
        return {"jsonrpc": "2.0", "id": req_id, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": tools_catalog()}}
    if method == "tools/call":
        return _handle_tool_call(req_id, params, config)
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Unknown method: {method}"}}


def tools_catalog() -> list[JSON]:
    return [
        {
            "name": "cityadvisor_get_status",
            "description": "List detected Cities: Skylines II city evidence sources.",
            "inputSchema": {"type": "object", "properties": {}},
        },
        {
            "name": "cityadvisor_analyze_city",
            "description": "Analyze available city evidence and return a structured CityAdvisor report.",
            "inputSchema": {"type": "object", "properties": {}},
        },
        {
            "name": "cityadvisor_get_report",
            "description": "Return the current CityAdvisor report as Markdown.",
            "inputSchema": {"type": "object", "properties": {}},
        },
    ]


def _handle_tool_call(req_id: object, params: JSON, config: JSON) -> JSON:
    name = str(params.get("name", ""))
    args = params.get("arguments") if isinstance(params.get("arguments"), dict) else {}
    inventory = discover_sources(
        mods_data_dir=args.get("mods_data_dir") or config.get("mods_data_dir"),
        save_investigator_output_dir=args.get("save_investigator_output_dir")
        or config.get("save_investigator_output_dir"),
    )
    if name == "cityadvisor_get_status":
        return {"jsonrpc": "2.0", "id": req_id, "result": _text_result(inventory.to_dict())}
    if name == "cityadvisor_analyze_city":
        return {"jsonrpc": "2.0", "id": req_id, "result": _text_result(build_city_report(inventory).to_dict())}
    if name == "cityadvisor_get_report":
        return {"jsonrpc": "2.0", "id": req_id, "result": _text_result(build_city_report(inventory).markdown)}
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32602, "message": f"Unknown tool: {name}"}}


def _text_result(payload: object) -> JSON:
    if isinstance(payload, (dict, list)):
        text = json.dumps(payload, indent=2)
    else:
        text = str(payload)
    return {"content": [{"type": "text", "text": text}]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=SERVER_NAME)
    parser.add_argument("--mods-data")
    parser.add_argument("--save-investigator-output")
    args = parser.parse_args(argv)
    config = {
        "mods_data_dir": args.mods_data,
        "save_investigator_output_dir": args.save_investigator_output,
    }
    while True:
        message = _read_message()
        if message is None:
            return 0
        response = handle_request(message, config)
        if response is not None:
            _send_message(response)


def _read_message() -> JSON | None:
    header_lines: list[str] = []
    while True:
        line = sys.stdin.buffer.readline()
        if line == b"":
            return None
        if line in (b"\r\n", b"\n"):
            break
        header_lines.append(line.decode("ascii", errors="replace").strip())
    length = 0
    for line in header_lines:
        name, _, value = line.partition(":")
        if name.lower() == "content-length":
            length = int(value.strip())
    if length <= 0:
        return None
    payload = sys.stdin.buffer.read(length)
    value = json.loads(payload.decode("utf-8"))
    return value if isinstance(value, dict) else None


def _send_message(message: JSON) -> None:
    payload = json.dumps(message, separators=(",", ":")).encode("utf-8")
    sys.stdout.buffer.write(f"Content-Length: {len(payload)}\r\n\r\n".encode("ascii"))
    sys.stdout.buffer.write(payload)
    sys.stdout.buffer.flush()


if __name__ == "__main__":
    raise SystemExit(main())
