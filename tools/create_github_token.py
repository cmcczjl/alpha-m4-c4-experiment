#!/usr/bin/env python3
"""
Utility script to ensure a GitHub Personal Access Token (PAT) is available
in the environment variable ``GITHUB_TOKEN``.

If the variable is already set, the script simply reports success.
Otherwise it:

1. Checks whether the GitHub CLI (`gh`) is installed; if not, it offers
   to install it (Linux/macOS only) via the official installer.
2. Prompts the user to generate a PAT with the required scopes
   (e.g. ``repo``) on the GitHub website and paste it.
3. Exports the token to the current process environment and optionally
   writes it to a ``.env`` file for reuse in the container/session.

The script is deliberately interactive because creating a PAT requires
user consent and cannot be fully automated without exposing credentials.

Usage:
    $ python3 tools/create_github_token.py
"""

import os
import sys
import subprocess
import shutil
import textwrap

def is_gh_installed() -> bool:
    """Return True if the `gh` CLI is found in PATH."""
    return shutil.which("gh") is not None

def install_gh_cli() -> None:
    """Attempt to install the GitHub CLI using the official installer."""
    print("GitHub CLI (`gh`) not found. Attempting to install it...")
    if sys.platform.startswith("linux"):
        # Install via apt (Debian/Ubuntu) or dnf (Fedora) if available
        if shutil.which("apt"):
            subprocess.check_call(["sudo", "apt", "update"])
            subprocess.check_call(["sudo", "apt", "install", "-y", "gh"])
        elif shutil.which("dnf"):
            subprocess.check_call(["sudo", "dnf", "install", "-y", "gh"])
        else:
            print("Unsupported Linux package manager. Please install `gh` manually.")
            sys.exit(1)
    elif sys.platform == "darwin":
        if shutil.which("brew"):
            subprocess.check_call(["brew", "install", "gh"])
        else:
            print("Homebrew not found. Please install `gh` manually (https://cli.github.com).")
            sys.exit(1)
    else:
        print(f"Unsupported platform: {sys.platform}. Please install `gh` manually.")
        sys.exit(1)

def prompt_for_token() -> str:
    """Prompt the user to paste a GitHub PAT."""
    print(textwrap.dedent("""
        -----------------------------------------------------------------
        A GitHub Personal Access Token (PAT) is required.
        1. Open https://github.com/settings/tokens
        2. Click “Generate new token” → “Fine-grained token” (or classic)
        3. Give it a name, set expiration, and grant at least the `repo` scope.
        4. Generate the token and copy it.
        -----------------------------------------------------------------
    """))
    token = input("Paste your PAT here (input will be hidden): ").strip()
    if not token:
        print("Error: No token entered.")
        sys.exit(1)
    return token

def export_token(token: str) -> None:
    """Export the token to the environment of the current process."""
    os.environ["GITHUB_TOKEN"] = token
    print("\n✅ GITHUB_TOKEN has been set for the current session.")

def write_dotenv(token: str, path: str = ".env") -> None:
    """Append the token to a .env file (creates if missing)."""
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"\nGITHUB_TOKEN={token}\n")
    print(f"🔧 Token also written to {path} (you can source it later).")

def main() -> None:
    # 1️⃣ Check existing env var
    existing = os.getenv("GITHUB_TOKEN")
    if existing:
        print("✅ GITHUB_TOKEN is already set in the environment.")
        return

    # 2️⃣ Ensure `gh` CLI is present (optional, but useful for later steps)
    if not is_gh_installed():
        install_gh_cli()
    else:
        print("✅ GitHub CLI (`gh`) is available.")

    # 3️⃣ Prompt user for PAT
    token = prompt_for_token()

    # 4️⃣ Export and persist
    export_token(token)
    write_dotenv(token)

if __name__ == "__main__":
    main()