from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class EntrypointTests(unittest.TestCase):
    def test_mcp_server_runs_when_launched_by_file_path(self) -> None:
        proc = subprocess.Popen(
            [sys.executable, str(ROOT / "cityadvisor" / "mcp_server.py")],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert proc.stdin is not None
        assert proc.stdout is not None
        try:
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"protocolVersion": "2025-06-18"},
            }
            payload = json.dumps(request).encode("utf-8")
            proc.stdin.write(f"Content-Length: {len(payload)}\r\n\r\n".encode("ascii") + payload)
            proc.stdin.flush()
            header = proc.stdout.readline().decode("ascii")
            self.assertTrue(header.startswith("Content-Length:"), header)
        finally:
            proc.terminate()
            proc.wait(timeout=5)
            if proc.stdin is not None:
                proc.stdin.close()
            if proc.stdout is not None:
                proc.stdout.close()
            if proc.stderr is not None:
                proc.stderr.close()


if __name__ == "__main__":
    unittest.main()
