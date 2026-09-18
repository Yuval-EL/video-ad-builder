"""Try the demo. Builds one finished file for the bundled sample product so a new user sees a result in minutes.

Usage: python tools/demo.py
With a voice key: the 30 second widescreen master with voice, about 4 minutes.
Without a key:    the 30 second silent vertical version, about 2 minutes, no account needed.
"""
import functools, os, shutil, subprocess, sys
print = functools.partial(print, flush=True)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import ROOT, WORKSPACE, ensure_workspace, voice_key  # noqa: E402


def main():
    ensure_workspace()
    src = os.path.join(ROOT, "examples", "sample-ad")
    dst = os.path.join(WORKSPACE, "output", "sample", "demo")
    os.makedirs(dst, exist_ok=True)
    shutil.copy(os.path.join(src, "ad.json"), os.path.join(dst, "ad.json"))
    build = [sys.executable, os.path.join(ROOT, "tools", "build.py"), dst]
    review = [sys.executable, os.path.join(ROOT, "tools", "review.py"), dst]
    if voice_key():
        print("Demo: 30 second widescreen master with voice. About 4 minutes.\n")
        steps = [build + ["check"], build + ["voice", "--only", "30s-hookA"], build + ["kit", "--only", "30s-hookA:16x9"]]
    else:
        print("Demo: 30 second silent vertical version. No voice key needed. About 2 minutes.\n")
        steps = [build + ["check"], build + ["kit", "--only", "30s-silent:9x16"]]
    for s in steps:
        if subprocess.run(s).returncode != 0: sys.exit("The demo stopped. Run python tools/doctor.py to see what is missing.")
    subprocess.run(review + ["kit"])
    print(f"\nDone. Open {os.path.join(dst, 'index.html')} to watch it.")


if __name__ == "__main__":
    main()
