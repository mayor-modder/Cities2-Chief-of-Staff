from __future__ import annotations

import os
import sys
from pathlib import Path


def write_fake_dotnet(fake_bin: Path) -> None:
    fake_bin.mkdir()
    fake_runner = fake_bin / "fake_dotnet.py"
    fake_runner.write_text(
        """
from __future__ import annotations

import json
import sys
from pathlib import Path

args = sys.argv[1:]
project_path = Path(args[args.index("--project") + 1])
output_dir = project_path.parent / "bin" / "Debug" / "net8.0" / "output" / "20990101-010101"
output_dir.mkdir(parents=True, exist_ok=True)
(output_dir / "city-state-report-facts.json").write_text(
    json.dumps({"estimatedCompletionPercent": 99}),
    encoding="utf-8",
)
(output_dir / "transport-report-facts.json").write_text(
    json.dumps(
        {
            "LineGroups": [
                {
                    "Mode": "subway",
                    "Lines": [
                        {
                            "DisplayName": "Fresh Subway",
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
print(f"Output: {output_dir}")
""".lstrip(),
        encoding="utf-8",
    )
    if os.name == "nt":
        (fake_bin / "dotnet.cmd").write_text(
            f'@echo off\r\n"{sys.executable}" "{fake_runner}" %*\r\n',
            encoding="utf-8",
        )
    else:
        dotnet = fake_bin / "dotnet"
        dotnet.write_text(
            f'#!/bin/sh\nexec "{sys.executable}" "{fake_runner}" "$@"\n',
            encoding="utf-8",
        )
        dotnet.chmod(0o755)
