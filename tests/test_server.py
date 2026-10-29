from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize("launch_mode", ["script", "module"])
def test_server_starts_with_package_imports(tmp_path, launch_mode):
    script = """
import runpy
import sys
from pathlib import Path
from unittest.mock import patch

root = Path(sys.argv[1])
mode = sys.argv[2]
sys.path[0] = str(root / "app" if mode == "script" else root)

with patch("http.server.HTTPServer") as server:
    if mode == "script":
        namespace = runpy.run_path(str(root / "app" / "server.py"), run_name="__main__")
    else:
        namespace = runpy.run_module("app.server", run_name="__main__")
    server.assert_called_once_with(("127.0.0.1", 8000), namespace["Handler"])
    server.return_value.serve_forever.assert_called_once_with()
    assert callable(namespace["investigate"])
    assert callable(namespace["generate_resolution"])
    assert isinstance(namespace["orchestrator"], namespace["ITServiceOrchestrator"])
"""
    result = subprocess.run(
        [sys.executable, "-c", script, str(ROOT), launch_mode],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=15,
    )

    assert result.returncode == 0, result.stdout + result.stderr
