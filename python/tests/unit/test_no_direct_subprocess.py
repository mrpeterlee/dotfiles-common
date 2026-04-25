import ast
from pathlib import Path

ALLOWED = {
    "src/acap_dotfiles/core/chezmoi.py",
    "src/acap_dotfiles/core/git.py",
    "src/acap_dotfiles/io/exec.py",
    "src/acap_dotfiles/commands/doctor.py",
    "src/acap_dotfiles/commands/release.py",
}


def test_no_direct_subprocess_outside_wrapper() -> None:
    root = Path(__file__).resolve().parents[2] / "src" / "acap_dotfiles"
    offenders: list[str] = []
    for py in root.rglob("*.py"):
        # Use `.as_posix()` so the relative path uses forward slashes on
        # Windows too — `ALLOWED` is declared with POSIX-style separators
        # and `str(WindowsPath(...))` would produce backslashes that miss
        # the comparison.
        rel = py.relative_to(root.parent.parent).as_posix()
        if rel in ALLOWED:
            continue
        tree = ast.parse(py.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "subprocess":
                offenders.append(f"{rel}: from subprocess import")
            if isinstance(node, ast.Import) and any(a.name == "subprocess" for a in node.names):
                offenders.append(f"{rel}: import subprocess")
    assert not offenders, "Direct subprocess use outside wrapper:\n" + "\n".join(offenders)
