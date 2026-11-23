"""Cliente de spl-js-engine: un proceso Node, un lote de pedidos por llamada."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


class SplEngine:
    def __init__(self, engine_root: Path, model_path: Path, script_path: Path):
        self._process = subprocess.Popen(
            ["node", str(script_path), str(engine_root), str(model_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )

    def complete_many(self, orders: list[list[str]]) -> list[dict]:
        if self._process.poll() is not None:
            error = self._process.stderr.read() if self._process.stderr else ""
            raise RuntimeError(f"spl-js-engine terminó antes de tiempo: {error}")
        assert self._process.stdin is not None
        assert self._process.stdout is not None
        self._process.stdin.write(json.dumps(orders) + "\n")
        self._process.stdin.flush()
        line = self._process.stdout.readline()
        if not line:
            error = self._process.stderr.read() if self._process.stderr else ""
            raise RuntimeError(f"spl-js-engine no respondió: {error}")
        return json.loads(line)

    def close(self) -> None:
        if self._process.poll() is None and self._process.stdin is not None:
            self._process.stdin.close()
            self._process.wait(timeout=10)
