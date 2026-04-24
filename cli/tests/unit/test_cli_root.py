from click.testing import CliRunner

from acap_dotfiles.cli import main


def test_version_prints_package_version() -> None:
    result = CliRunner().invoke(main, ["--version"])
    assert result.exit_code == 0
    # Format: "dots, version 0.1.0"
    assert "dots, version " in result.stdout
    assert "0.1.0" in result.stdout


def test_help_lists_all_eleven_verbs() -> None:
    result = CliRunner().invoke(main, ["--help"])
    assert result.exit_code == 0
    for verb in (
        "apply",
        "update",
        "status",
        "doctor",
        "backup",
        "restore",
        "ssh",
        "host",
        "manifest",
        "release",
        "migrate-from-legacy",
    ):
        assert verb in result.stdout
