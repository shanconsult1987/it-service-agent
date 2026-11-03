import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

STARTUP_CHECK = """
import runpy
import sys
from pathlib import Path
from unittest.mock import patch

mode, target = sys.argv[1:]
with patch("http.server.HTTPServer") as server:
    if mode == "script":
        sys.path.insert(0, str(Path(target).parent))
        runpy.run_path(target, run_name="__main__")
    else:
        runpy.run_module(target, run_name="__main__")
    assert server.call_args.args[0] == ("127.0.0.1", 8000)
    assert server.call_args.args[1].__name__ == "Handler"
    server.return_value.serve_forever.assert_called_once_with()
"""


class ServerStartupTests(unittest.TestCase):
    def check_startup(self, mode, target, cwd):
        result = subprocess.run(
            [sys.executable, "-c", STARTUP_CHECK, mode, target],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("IT Service Agent running", result.stdout)

    def test_direct_file_from_outside_project(self):
        with tempfile.TemporaryDirectory() as cwd:
            self.check_startup("script", str(ROOT / "app" / "server.py"), cwd)

    def test_module_from_project_root(self):
        self.check_startup("module", "app.server", ROOT)
