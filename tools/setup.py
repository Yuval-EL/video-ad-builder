"""One-time setup. Installs the browser engine, checks ffmpeg, prepares the workspace, then runs the check.

Usage: python tools/setup.py
Safe to run again. Nothing is downloaded twice.
"""
import functools, os, subprocess, sys
print = functools.partial(print, flush=True)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import ROOT, WORKSPACE, ensure_workspace  # noqa: E402


def run(cmd, cwd=None):
    print("  " + " ".join(cmd))
    return subprocess.run(cmd, cwd=cwd, shell=(os.name == "nt")).returncode == 0


def main():
    print("Video Ad Builder setup\n")
    print("1. Browser engine")
    if not os.path.isdir(os.path.join(ROOT, "node_modules", "playwright")):
        if not run(["npm", "install", "--no-audit", "--no-fund"], cwd=ROOT):
            sys.exit("npm install failed. Is Node.js installed? Get it from nodejs.org and run this again.")
    else:
        print("  already installed")
    run(["npx", "playwright", "install", "chromium"], cwd=ROOT)
    print("\n2. Workspace")
    ensure_workspace()
    print(f"  {WORKSPACE}")
    print("  products/ for your saved products, output/ for finished ads, .env for the voice key")
    print("\n3. Music library")
    run([sys.executable, os.path.join(ROOT, "tools", "music.py")])
    print("\n4. Check")
    subprocess.run([sys.executable, os.path.join(ROOT, "tools", "doctor.py")])
    print("\nNext: open Claude Code in this folder and run /video-ad-builder")


if __name__ == "__main__":
    main()
