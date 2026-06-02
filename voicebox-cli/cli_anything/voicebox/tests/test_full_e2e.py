import os
import subprocess
import sys

from click.testing import CliRunner

from cli_anything.voicebox.voicebox_cli import main


def test_help_command_runs():
    result = CliRunner().invoke(main, ["--help"])

    assert result.exit_code == 0
    assert "CLI-Anything harness for Voicebox" in result.output


def test_default_repl_can_quit(tmp_path, monkeypatch):
    monkeypatch.setenv("VOICEBOX_HARNESS_STATE", str(tmp_path / "state.json"))

    result = CliRunner().invoke(main, input="quit\n")

    assert result.exit_code == 0
    assert "Voicebox harness REPL" in result.output


def test_module_entrypoint_help_runs():
    env = os.environ.copy()
    package_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
    env["PYTHONPATH"] = package_root

    result = subprocess.run(
        [sys.executable, "-m", "cli_anything.voicebox", "--help"],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0
    assert "CLI-Anything harness for Voicebox" in result.stdout
