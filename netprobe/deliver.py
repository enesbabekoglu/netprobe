from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

from .config import PROJECT_ROOT


INCLUDE_ROOTS = [
    "netprobe",
    "web",
    "docs",
    "tests",
    "data/sample_files",
    "outputs/analysis",
    "outputs/experiments",
    "outputs/logs",
]
INCLUDE_FILES = [
    "README.md",
    "requirements.txt",
    "pyproject.toml",
    "package.json",
    "package-lock.json",
    "tailwind.config.js",
]
EXCLUDED_PARTS = {"__pycache__", ".pytest_cache", "node_modules"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".DS_Store"}


def _should_include(path: Path) -> bool:
    if any(part in EXCLUDED_PARTS for part in path.parts):
        return False
    if path.suffix in EXCLUDED_SUFFIXES or path.name in EXCLUDED_SUFFIXES:
        return False
    return True


def build_deliverable(output: str | Path = PROJECT_ROOT / "dist" / "netprobe-deliverable.zip") -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file_name in INCLUDE_FILES:
            path = PROJECT_ROOT / file_name
            if path.exists():
                archive.write(path, path.relative_to(PROJECT_ROOT))
        for root_name in INCLUDE_ROOTS:
            root = PROJECT_ROOT / root_name
            if not root.exists():
                continue
            for path in root.rglob("*"):
                if path.is_file() and _should_include(path):
                    archive.write(path, path.relative_to(PROJECT_ROOT))
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the NetProbe delivery zip")
    parser.add_argument("--output", default=str(PROJECT_ROOT / "dist" / "netprobe-deliverable.zip"))
    args = parser.parse_args()
    path = build_deliverable(args.output)
    print(f"deliverable written to {path}")


if __name__ == "__main__":
    main()
