import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "apps.cli", *args],
        capture_output=True, text=True, cwd=ROOT)


def test_help():
    result = run_cli("--help")
    assert result.returncode == 0
    assert "run" in result.stdout


def test_missing_command():
    assert run_cli().returncode == 2


def test_missing_file():
    result = run_cli("run", "/nonexistent/doc.txt")
    assert result.returncode == 2
    assert "not found" in result.stderr


def test_verbose_flag_accepted():
    result = run_cli("run", "--help")
    assert "--verbose" in result.stdout


def test_screenshots_flag_accepted():
    result = run_cli("run", "--help")
    assert "--screenshots" in result.stdout
