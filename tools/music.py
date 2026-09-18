"""Build a music library in the workspace from Mixkit's free stock music.

Usage: python tools/music.py [--per-mood N]

Downloads a few tracks per mood into <workspace>/music/ and writes music/library.json.
Mixkit's free license allows use in commercial video, no attribution. The tracks are not part of
this plugin and are fetched by the user; see https://mixkit.co/license/#musicFree.
Safe to run again: tracks already on disk are kept.
"""
import json, os, re, sys, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import WORKSPACE, ensure_workspace  # noqa: E402

UA = {"User-Agent": "Mozilla/5.0"}
# mood -> Mixkit tag pages, in order of preference
MOODS = {
    "calm":      ["ambient", "chill"],
    "confident": ["corporate", "technology"],
    "upbeat":    ["upbeat", "pop"],
    "warm":      ["acoustic", "guitar", "happy", "inspirational"],
    "tense":     ["cinematic", "epic"],
}


def get(url, binary=False):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
        data = r.read()
    return data if binary else data.decode("utf-8", "ignore")


def tracks_on(tag):
    html = get(f"https://mixkit.co/free-stock-music/tag/{tag}/")
    out = []
    for m in re.finditer(r'"name":"([^"]+)","genre":"([^"]*)","byArtist":"([^"]*)","duration":"PT(?:(\d+)M)?(?:(\d+)S)?","url":"(https://assets\.mixkit\.co/music/[^"]+\.mp3)"', html):
        name, genre, artist, mins, secs, url = m.groups()
        dur = int(mins or 0) * 60 + int(secs or 0)
        out.append({"title": name, "genre": genre, "artist": artist, "seconds": dur, "url": url})
    return out


def main():
    per = int(sys.argv[sys.argv.index("--per-mood") + 1]) if "--per-mood" in sys.argv else 2
    ensure_workspace()
    mdir = os.path.join(WORKSPACE, "music"); os.makedirs(mdir, exist_ok=True)
    libf = os.path.join(mdir, "library.json")
    lib = json.load(open(libf, encoding="utf-8")) if os.path.exists(libf) else {"source": "Mixkit free stock music, https://mixkit.co/license/#musicFree", "tracks": []}
    have = {t["url"] for t in lib["tracks"]}
    for mood, tags in MOODS.items():
        got = sum(1 for t in lib["tracks"] if t["mood"] == mood)
        for tag in tags:
            if got >= per: break
            try:
                cands = [t for t in tracks_on(tag) if t["seconds"] >= 60 and t["url"] not in have]
            except Exception as e:
                print(f"  {mood}: could not read the {tag} page ({e})"); continue
            for t in cands:
                if got >= per: break
                slug = re.sub(r"[^a-z0-9]+", "-", t["title"].lower()).strip("-")
                fname = f"{mood}-{slug}.mp3"
                path = os.path.join(mdir, fname)
                try:
                    open(path, "wb").write(get(t["url"], binary=True))
                except Exception as e:
                    print(f"  skipped {t['title']} ({e})"); continue
                lib["tracks"].append({"file": fname, "mood": mood, "title": t["title"], "artist": t["artist"], "genre": t["genre"], "seconds": t["seconds"], "url": t["url"], "license": "Mixkit Stock Music Free License"})
                have.add(t["url"]); got += 1
                print(f"  {mood:<10} {t['title']} ({t['seconds']} s)")
    json.dump(lib, open(libf, "w", encoding="utf-8"), indent=1)
    print(f"\n{len(lib['tracks'])} tracks in {mdir}")


if __name__ == "__main__":
    main()
