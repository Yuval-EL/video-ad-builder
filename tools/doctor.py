"""Setup check and status. Says in plain words what is ready, what to fix, and what is in progress.

Usage: python tools/doctor.py [--json]
Exit code 0 when everything needed for a full run is present.
"""
import glob, json, os, shutil, subprocess, sys, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import ROOT, WORKSPACE, ensure_workspace, list_products, voice_key  # noqa: E402


def ver(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=20, shell=(os.name == "nt")).stdout.strip().splitlines()[0]
    except Exception:
        return None


def main():
    as_json = "--json" in sys.argv
    ensure_workspace()
    rows, ok = [], True
    node = ver(["node", "--version"])
    rows.append(("Node.js", node or "missing", None if node else "Install Node.js from nodejs.org, then run this check again."))
    pw = os.path.isdir(os.path.join(ROOT, "node_modules", "playwright"))
    browsers = os.path.join(os.environ.get("LOCALAPPDATA") or os.path.expanduser("~/.cache"), "ms-playwright")
    has_browser = os.path.isdir(browsers) and any(n.startswith("chromium") for n in os.listdir(browsers))
    rows.append(("Browser engine", ("installed" if pw else "missing") + (", with Chromium" if has_browser else ", browser missing"),
                 None if (pw and has_browser) else f"Run: python \"{os.path.join(ROOT, 'tools', 'setup.py')}\""))
    ff = ver(["ffmpeg", "-version"])
    rows.append(("ffmpeg", ff.split(" ")[2] if ff else "missing",
                 None if ff else "Windows: winget install --id Gyan.FFmpeg -e --source winget   Mac: brew install ffmpeg   Then restart the terminal."))
    key = voice_key()
    if key:
        try:
            req = urllib.request.Request("https://api.elevenlabs.io/v1/user/subscription", headers={"xi-api-key": key})
            d = json.load(urllib.request.urlopen(req, timeout=15))
            left = d["character_limit"] - d["character_count"]
            rows.append(("Voice service", f"connected, {d['tier']} plan, {left:,} characters left this month, about {left // 450} thirty-second voiceovers", None))
        except Exception:
            rows.append(("Voice service", "key present but rejected",
                         "At elevenlabs.io open Profile, then API Keys, create a key with Text to Speech, Voices and User permissions, and paste it into .env"))
    else:
        rows.append(("Voice service", "no key yet",
                     f"Optional. Create a free account at elevenlabs.io, make an API key, and put ELEVENLABS_API_KEY=<key> in {os.path.join(WORKSPACE, '.env')}. Silent ads work without it."))
    products = list_products()
    rows.append(("Products", ", ".join(products) or "none yet", None))
    libf = os.path.join(WORKSPACE, "music", "library.json")
    ntracks = len(json.load(open(libf, encoding="utf-8"))["tracks"]) if os.path.exists(libf) else 0
    rows.append(("Music library", f"{ntracks} tracks" if ntracks else "empty, ads will get a placeholder bed",
                 None if ntracks else f"Optional. Run: python \"{os.path.join(ROOT, 'tools', 'music.py')}\"  to fetch free tracks by mood"))
    rows.append(("Workspace", WORKSPACE, None))

    in_progress = []
    for f in glob.glob(os.path.join(WORKSPACE, "output", "*", "*", "state.json")):
        st = json.load(open(f))
        in_progress.append({"ad": os.path.basename(os.path.dirname(f)), "product": os.path.basename(os.path.dirname(os.path.dirname(f))),
                            "gate": st.get("gate"), "updated": st.get("updated"), "files": st.get("files")})

    needed = [r for r in rows if r[2] and r[0] not in ("Voice service", "Music library")]
    ok = not needed
    if as_json:
        print(json.dumps({"ok": ok, "checks": [{"item": r[0], "status": r[1], "fix": r[2]} for r in rows], "ads": in_progress}, indent=1)); sys.exit(0 if ok else 1)
    for name, status, fix in rows:
        print(f"{'ready ' if fix is None else ('note  ' if name in ('Voice service', 'Music library') else 'FIX   ')} {name:<16} {status}")
        if fix: print(f"       {fix}")
    if in_progress:
        print("\nAds on file:")
        for a in in_progress:
            print(f"  {a['product']}/{a['ad']}: {'finished, ' + str(a['files']) + ' files' if a['gate'] == 'done' else 'waiting at ' + str(a['gate'])} ({a['updated']})")
    print("\nAll set." if ok else "\nFix the items marked FIX, then run the check again.")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
