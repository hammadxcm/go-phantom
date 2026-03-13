#!/usr/bin/env python3
"""Bump version across all project files.

Usage:
    python scripts/bump_version.py 0.2.0       # set explicit version
    python scripts/bump_version.py --patch      # 0.0.1 → 0.0.2
    python scripts/bump_version.py --minor      # 0.0.1 → 0.1.0
    python scripts/bump_version.py --major      # 0.0.1 → 1.0.0
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def get_current_version() -> str:
    init = ROOT / "phantom" / "__init__.py"
    match = re.search(r'__version__\s*=\s*"([^"]+)"', init.read_text())
    if not match:
        sys.exit("Could not find __version__ in phantom/__init__.py")
    return match.group(1)


def bump(current: str, part: str) -> str:
    major, minor, patch = (int(x) for x in current.split("."))
    if part == "major":
        return f"{major + 1}.0.0"
    if part == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def replace_in_file(path: Path, pattern: str, replacement: str) -> bool:
    if not path.exists():
        return False
    text = path.read_text()
    new_text = re.sub(pattern, replacement, text, flags=re.MULTILINE)
    if text != new_text:
        path.write_text(new_text)
        return True
    return False


def update_json_version(path: Path, old: str, new: str) -> bool:
    if not path.exists():
        return False
    text = path.read_text()
    new_text = text.replace(f'"version": "{old}"', f'"version": "{new}"')
    new_text = new_text.replace(f"/v{old}/", f"/v{new}/")
    if text != new_text:
        path.write_text(new_text)
        return True
    return False


def main():
    parser = argparse.ArgumentParser(description="Bump version across all project files")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("version", nargs="?", help="Explicit version (e.g. 0.2.0)")
    group.add_argument("--patch", action="store_true", help="Bump patch version")
    group.add_argument("--minor", action="store_true", help="Bump minor version")
    group.add_argument("--major", action="store_true", help="Bump major version")
    args = parser.parse_args()

    old = get_current_version()

    if args.version:
        new = args.version
    elif args.patch:
        new = bump(old, "patch")
    elif args.minor:
        new = bump(old, "minor")
    else:
        new = bump(old, "major")

    if new == old:
        print(f"Version is already {old}")
        return

    print(f"Bumping version: {old} → {new}\n")

    updates = [
        (
            "phantom/__init__.py",
            lambda: replace_in_file(
                ROOT / "phantom" / "__init__.py",
                r'__version__\s*=\s*"[^"]+"',
                f'__version__ = "{new}"',
            ),
        ),
        (
            "pyproject.toml",
            lambda: replace_in_file(
                ROOT / "pyproject.toml",
                r'^version\s*=\s*"[^"]+"',
                f'version = "{new}"',
            ),
        ),
        (
            "README.md",
            lambda: replace_in_file(
                ROOT / "README.md",
                rf"phantom-v{re.escape(old)}-",
                f"phantom-v{new}-",
            ),
        ),
        (
            "README.md (.deb reference)",
            lambda: replace_in_file(
                ROOT / "README.md",
                rf"phantom_{re.escape(old)}_amd64\.deb",
                f"phantom_{new}_amd64.deb",
            ),
        ),
        (
            "Formula/phantom.rb",
            lambda: any([
                replace_in_file(
                    ROOT / "Formula" / "phantom.rb",
                    rf"/v{re.escape(old)}\.tar\.gz",
                    f"/v{new}.tar.gz",
                ),
                replace_in_file(
                    ROOT / "Formula" / "phantom.rb",
                    r'sha256 "[^"]+"',
                    'sha256 "PLACEHOLDER_SHA256"',
                ),
            ]),
        ),
        (
            "snap/snapcraft.yaml",
            lambda: replace_in_file(
                ROOT / "snap" / "snapcraft.yaml",
                r"version:\s*'[^']+'",
                f"version: '{new}'",
            ),
        ),
        (
            "packaging/chocolatey/go-phantom.nuspec",
            lambda: replace_in_file(
                ROOT / "packaging" / "chocolatey" / "go-phantom.nuspec",
                r"<version>[^<]+</version>",
                f"<version>{new}</version>",
            ),
        ),
        (
            "packaging/scoop/go-phantom.json",
            lambda: update_json_version(
                ROOT / "packaging" / "scoop" / "go-phantom.json", old, new
            ),
        ),
        (
            "packaging/winget/hammadxcm.go-phantom.yaml",
            lambda: replace_in_file(
                ROOT / "packaging" / "winget" / "hammadxcm.go-phantom.yaml",
                rf"PackageVersion:\s*{re.escape(old)}",
                f"PackageVersion: {new}",
            ),
        ),
        (
            "packaging/winget/hammadxcm.go-phantom.installer.yaml",
            lambda: (
                replace_in_file(
                    ROOT / "packaging" / "winget" / "hammadxcm.go-phantom.installer.yaml",
                    rf"PackageVersion:\s*{re.escape(old)}",
                    f"PackageVersion: {new}",
                ),
                replace_in_file(
                    ROOT / "packaging" / "winget" / "hammadxcm.go-phantom.installer.yaml",
                    rf"/v{re.escape(old)}/",
                    f"/v{new}/",
                ),
            )[0],
        ),
        (
            "packaging/winget/hammadxcm.go-phantom.locale.en-US.yaml",
            lambda: replace_in_file(
                ROOT / "packaging" / "winget" / "hammadxcm.go-phantom.locale.en-US.yaml",
                rf"PackageVersion:\s*{re.escape(old)}",
                f"PackageVersion: {new}",
            ),
        ),
        # Astro landing page components
        (
            "docs/Downloads.astro",
            lambda: replace_in_file(
                ROOT / "docs" / "src" / "components" / "Downloads.astro",
                rf'const version = "{re.escape(old)}";',
                f'const version = "{new}";',
            ),
        ),
        (
            "docs/Hero.astro",
            lambda: replace_in_file(
                ROOT / "docs" / "src" / "components" / "Hero.astro",
                rf'const version = "{re.escape(old)}";',
                f'const version = "{new}";',
            ),
        ),
        (
            "docs/Footer.astro",
            lambda: replace_in_file(
                ROOT / "docs" / "src" / "components" / "Footer.astro",
                rf'const version = "{re.escape(old)}";',
                f'const version = "{new}";',
            ),
        ),
        # macOS native app
        (
            "phantom-macos/Info.plist",
            lambda: replace_in_file(
                ROOT / "phantom-macos" / "Phantom" / "Info.plist",
                rf"<string>{re.escape(old)}</string>",
                f"<string>{new}</string>",
            ),
        ),
        (
            "phantom-macos/project.pbxproj",
            lambda: replace_in_file(
                ROOT / "phantom-macos" / "Phantom.xcodeproj" / "project.pbxproj",
                rf"MARKETING_VERSION = {re.escape(old)};",
                f"MARKETING_VERSION = {new};",
            ),
        ),
    ]

    for name, update_fn in updates:
        result = update_fn()
        status = "updated" if result else "skipped (no change or missing)"
        print(f"  {'OK' if result else '--'}  {name} ... {status}")

    print(f"\nVersion bumped to {new}")
    print(f"\nNext steps:")
    print(f"  1. Update CHANGELOG.md with a new [{new}] section")
    print(f'  2. git add -A && git commit -m "Release v{new}"')
    print(f"  3. git tag v{new}")
    print(f"  4. git push && git push --tags")


if __name__ == "__main__":
    main()
