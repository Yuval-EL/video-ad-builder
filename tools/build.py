"""Ad builder tool chain. One ad spec in, a full asset kit out.

Usage: python tools/build.py <ad-folder> <stage> [options]

Stages, in the order the builder runs them:
  check    Validate ad.json. Word budgets, claims of length, text limits, scene references. No network.
  plan     Estimated timeline for every deliverable. No network, no voice quota.
  player   Write working/player.html, a self-contained page that plays any deliverable in any format.
  stills   Review stills. Options: --d <deliverable> --fmt <16x9|9x16|1x1>. Default: first kit entry.
  master   Silent render of the first kit entry, for the concept review gate.
  voice    Generate the voice, re-time every deliverable to the real speech, write captions.
  kit      Render and finish every kit entry. Options: --only <deliverable>:<fmt> to build one, --audio-only to re-mix without re-rendering.

The voice key is read from .env and never printed.
"""
import base64, hashlib, json, os, re, subprocess, sys, urllib.error, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import ROOT, WORKSPACE, product_dir, voice_key  # noqa: E402

PLAN_WPS = 2.1                       # measured pace of generated voices, pauses included
SCENE_TYPES = {"hook-text", "text-card", "pivot", "conversation", "workflow", "pills", "number", "shield", "closer"}
FORMATS = {"16x9": (1920, 1080), "9x16": (1080, 1920), "1x1": (1080, 1080)}
HEADLINE_MAX, DESCRIPTION_MAX = 40, 35
SKIP_POINT = 5.0


# ---------------------------------------------------------------- loading
def load(ad_dir):
    ad = json.load(open(os.path.join(ad_dir, "ad.json"), encoding="utf-8"))
    pdir = product_dir(ad["product"])
    brand = json.load(open(os.path.join(pdir, "brand.json"), encoding="utf-8"))
    for key, f in (("wordmark", "wordmark_file"), ("icon", "icon_file")):
        svg = open(os.path.join(pdir, brand[f]), encoding="utf-8").read()
        brand[key] = re.sub(r'\s(width|height)="[^"]*"', "", svg, count=2)
    ad["brand"] = brand
    ad["_pdir"] = pdir
    return ad


def work(ad_dir, *p):
    d = os.path.join(ad_dir, "working"); os.makedirs(d, exist_ok=True)
    return os.path.join(d, *p)


def timing_params(duration):
    if duration <= 8:   return dict(lead_in=0.2, hold=0.8, min_gap=0.12, max_gap=0.4)
    if duration <= 20:  return dict(lead_in=0.4, hold=1.5, min_gap=0.18, max_gap=0.5)
    if duration <= 40:  return dict(lead_in=0.5, hold=2.5, min_gap=0.2, max_gap=0.6)
    return dict(lead_in=0.5, hold=3.0, min_gap=0.2, max_gap=0.7)


# ---------------------------------------------------------------- timeline
def plain(text):
    """The words that are actually spoken: delivery tags such as [confident] removed."""
    return re.sub(r"\s{2,}", " ", re.sub(r"\[[^\]]*\]", "", text or "")).strip()


def estimate_spoken(text):
    text = plain(text)
    words = len(text.split()); stops = max(0, len(re.findall(r"[.?!]", text)) - 1)
    return max(0.7, words / 2.3 + 0.35 * stops)


def cue_offset(scene, word, spoken, alignment):
    i = scene["vo"].lower().find(word.lower())
    if i < 0: raise ValueError(f"cue word '{word}' is not in the line: {scene['vo']}")
    if alignment: return alignment["character_start_times_seconds"][i]
    return spoken * i / max(1, len(scene["vo"]))


def voice_for(ad, name):
    """The voice config a deliverable uses. Deliverables may name one of ad['voices']; otherwise ad['voice']."""
    key = ad["deliverables"][name].get("voice")
    return ad.get("voices", {}).get(key, ad.get("voice")) if key else ad.get("voice")


def silent_timeline(ad, name):
    """Scenes hold for their 'hold' seconds, scaled so the whole thing fills the duration exactly."""
    dv = ad["deliverables"][name]; D = float(dv["duration"]); ids = dv["scenes"]; sc = ad["scenes"]
    holds = [float(sc[i].get("hold", 3)) for i in ids]; k = D / sum(holds)
    sched = {"duration": D, "source": "silent", "scenes": [], "cues": {}}; t = 0.0; lines = []
    for i, h in zip(ids, holds):
        sched["scenes"].append({"id": i, "t": round(t, 3)})
        lines.append({"id": i, "start": round(t, 2), "end": round(t + h * k, 2), "text": sc[i].get("text", sc[i].get("label", ""))}); t += h * k
    info = {"deliverable": name, "duration": D, "words": 0, "word_budget": 0, "spoken": 0, "gap": 0, "voice_ends": 0,
            "closer_hold": round(holds[-1] * k, 2), "over_by": 0.0, "brand_spoken_at": None, "silent": True, "lines": lines}
    return sched, info


def timeline(ad, name, clips=None):
    """clips: {scene_id: {"spoken": seconds, "alignment": {...}}} from the real voice, or None to estimate."""
    dv = ad["deliverables"][name]
    if dv.get("silent"): return silent_timeline(ad, name)
    D = float(dv["duration"]); tp = timing_params(D)
    ids = dv["scenes"]; sc = ad["scenes"]
    spoken = {i: (clips[i]["spoken"] if clips else estimate_spoken(sc[i]["vo"])) for i in ids}
    total = sum(spoken.values()); gaps = max(1, len(ids) - 1)
    spare = D - tp["lead_in"] - total - tp["hold"]
    gap = spare / gaps
    over = 0.0
    if gap < tp["min_gap"]:
        over = tp["min_gap"] * gaps - spare; gap = tp["min_gap"]
    gap = min(gap, tp["max_gap"])
    t = tp["lead_in"]; starts = {}
    for i in ids:
        starts[i] = t; t += spoken[i] + gap
    voice_end = starts[ids[-1]] + spoken[ids[-1]]
    sched = {"duration": D, "source": "voice" if clips else "estimate", "scenes": [], "cues": {}}
    for n, i in enumerate(ids):
        sched["scenes"].append({"id": i, "t": 0.0 if n == 0 else round(starts[i] - 0.12, 3)})
        for cue, word in sc[i].get("cues", {}).items():
            sched["cues"][f"{i}.{cue}"] = round(starts[i] + cue_offset(sc[i], word, spoken[i], clips[i]["alignment"] if clips else None), 3)
    brand = ad["brand"]["name"].lower().split()[0]
    brand_at = next((round(starts[i] + cue_offset(sc[i], brand, spoken[i], clips[i]["alignment"] if clips else None), 2)
                     for i in ids if brand in sc[i]["vo"].lower()), None)
    words = sum(len(plain(sc[i]["vo"]).split()) for i in ids)
    info = {"deliverable": name, "duration": D, "words": words, "word_budget": int((D - tp["lead_in"] - tp["hold"] - tp["min_gap"] * gaps) * PLAN_WPS),
            "spoken": round(total, 2), "gap": round(gap, 2), "voice_ends": round(voice_end, 2), "closer_hold": round(D - voice_end, 2),
            "over_by": round(over, 2), "brand_spoken_at": brand_at,
            "lines": [{"id": i, "start": round(starts[i], 2), "end": round(starts[i] + spoken[i], 2), "text": plain(sc[i]["vo"])} for i in ids]}
    return sched, info


def print_plan(infos):
    print(f"{'deliverable':<14}{'len':>5}{'words':>7}{'budget':>8}{'voice ends':>12}{'hold':>7}{'brand at':>10}  status")
    ok = True
    for x in infos:
        flags = []
        if x.get("silent"):
            print(f"{x['deliverable']:<14}{x['duration']:>5.0f}{'silent':>7}{'':>8}{'':>12}{x['closer_hold']:>7}{'':>10}  ok, text-driven"); continue
        if x["over_by"] > 0: flags.append(f"TOO LONG by {x['over_by']}s, cut about {int(x['over_by'] * PLAN_WPS) + 1} words")
        if x["duration"] >= 15 and (x["brand_spoken_at"] is None or x["brand_spoken_at"] > SKIP_POINT): flags.append("brand spoken after the skip point")
        target = timing_params(x["duration"])["hold"]
        if x["closer_hold"] > target * 1.8: flags.append(f"closer holds {x['closer_hold']}s, room for about {int((x['closer_hold'] - target) * PLAN_WPS)} more words")
        ok = ok and not x["over_by"] > 0
        print(f"{x['deliverable']:<14}{x['duration']:>5.0f}{x['words']:>7}{x['word_budget']:>8}{x['voice_ends']:>12}{x['closer_hold']:>7}{str(x['brand_spoken_at']):>10}  {'; '.join(flags) or 'ok'}")
    return ok


# ---------------------------------------------------------------- stages
def stage_check(ad, ad_dir):
    problems = []
    for sid, s in ad["scenes"].items():
        if s.get("type") not in SCENE_TYPES: problems.append(f"scene {sid}: unknown type {s.get('type')}")
        if not s.get("vo") and not s.get("hold"): problems.append(f"scene {sid}: no voice line and no hold time")
        if s.get("bg") not in ad["brand"]["colors"]: problems.append(f"scene {sid}: background role '{s.get('bg')}' is not in the brand colors")
        for cue, word in s.get("cues", {}).items():
            if word.lower() not in s.get("vo", "").lower(): problems.append(f"scene {sid}: cue word '{word}' is not in the voice line")
    for name, dv in ad["deliverables"].items():
        for sid in dv["scenes"]:
            if sid not in ad["scenes"]: problems.append(f"deliverable {name}: scene {sid} does not exist")
        if ad["scenes"].get(dv["scenes"][-1], {}).get("type") != "closer": problems.append(f"deliverable {name}: last scene is not a closer")
    for k in ad["kit"]:
        if k["d"] not in ad["deliverables"]: problems.append(f"kit: deliverable {k['d']} does not exist")
        if k["fmt"] not in FORMATS: problems.append(f"kit: format {k['fmt']} is not supported")
    for hline in ad.get("ad_text", {}).get("headlines", []):
        if len(hline) > HEADLINE_MAX: problems.append(f"headline over {HEADLINE_MAX} characters: {hline}")
    for dline in ad.get("ad_text", {}).get("descriptions", []):
        if len(dline) > DESCRIPTION_MAX: problems.append(f"description over {DESCRIPTION_MAX} characters: {dline}")
    for role, hexv in ad["brand"]["colors"].items():
        if not re.fullmatch(r"#[0-9A-Fa-f]{6}", hexv): problems.append(f"brand color {role} is not a hex value")
    shots = os.path.join(ad["_pdir"], "screenshots")
    mode = "screenshot" if os.path.isdir(shots) and any(f.lower().endswith((".png", ".jpg", ".jpeg", ".webp")) for f in os.listdir(shots)) else "illustrated"
    hooks = [n for n, d in ad["deliverables"].items() if d.get("hook_pattern")]
    concepts = sorted({d.get("concept", "main") for d in ad["deliverables"].values()})
    voices = sorted({(voice_for(ad, n) or {}).get("voice_name", "none") for n, d in ad["deliverables"].items() if not d.get("silent")})
    print(f"product: {ad['brand']['name']} | material mode: {mode} | scenes: {len(ad['scenes'])} | deliverables: {len(ad['deliverables'])} | concepts: {', '.join(concepts)} | voices: {', '.join(voices)} | hook variants: {len(hooks)} | kit files: {len(ad['kit'])}")
    for p in problems: print("  PROBLEM:", p)
    if not problems: print("  spec is valid")
    ok = print_plan([timeline(ad, n)[1] for n in ad["deliverables"]])
    return not problems and ok


def stage_player(ad, ad_dir, schedules=None):
    if schedules is None:
        f = work(ad_dir, "schedules.json")
        schedules = json.load(open(f)) if os.path.exists(f) else {}
        for n in ad["deliverables"]:
            if n not in schedules or (ad["deliverables"][n].get("silent") and schedules[n]["source"] != "silent"): schedules[n] = timeline(ad, n)[0]
        if os.path.exists(f): json.dump(schedules, open(f, "w"), indent=1)
    pub = {k: v for k, v in ad.items() if not k.startswith("_")}
    css = open(os.path.join(ROOT, "engine", "engine.css"), encoding="utf-8").read()
    js = open(os.path.join(ROOT, "engine", "engine.js"), encoding="utf-8").read()
    font = f'<link href="{ad["brand"]["fontUrl"]}" rel="stylesheet">' if ad["brand"].get("fontUrl") else ""
    html = (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{ad["name"]}</title>{font}<style>{css}</style></head><body>'
            f'<script>window.AD={json.dumps(pub)};window.SCHEDULES={json.dumps(schedules)};</script><script>{js}</script></body></html>')
    out = work(ad_dir, "player.html"); open(out, "w", encoding="utf-8").write(html)
    voiced = [n for n, v in schedules.items() if v["source"] == "voice"]
    print(f"player written. Voice-timed: {', '.join(voiced) or 'none yet, all estimated'}")
    return out


def node(script, *args):
    r = subprocess.run(["node", os.path.join(ROOT, "tools", script), *map(str, args)], capture_output=True, text=True)
    print((r.stdout + r.stderr).strip())
    if r.returncode: sys.exit(1)


def stage_stills(ad, ad_dir, d=None, fmt=None):
    player = stage_player(ad, ad_dir)
    first = ad["kit"][0]
    node("stills.js", player, os.path.join(ad_dir, "working", "stills"), d or first["d"], fmt or first["fmt"], "auto")


def stage_master(ad, ad_dir):
    player = stage_player(ad, ad_dir); k = ad["kit"][0]
    node("render.js", player, work(ad_dir, f"concept-{k['d']}-{k['fmt']}.mp4"), k["d"], k["fmt"], k.get("fps", 30))


def api_key():
    k = voice_key()
    if not k: sys.exit(f"No voice key. Put ELEVENLABS_API_KEY=<key> in {os.path.join(WORKSPACE, '.env')}")
    return k


def stage_voice(ad, ad_dir, only=None):
    key = api_key(); vdir = work(ad_dir, "voice"); os.makedirs(vdir, exist_ok=True)
    names = [n for n in ad["deliverables"] if (not only or n == only) and not ad["deliverables"][n].get("silent")]
    clips_by_text, used = {}, 0
    for name in names:
        v = voice_for(ad, name); ids = ad["deliverables"][name]["scenes"]
        for n, sid in enumerate(ids):
            text = ad["scenes"][sid]["vo"]
            h = hashlib.sha1(json.dumps([text, v["voice_id"], v.get("model"), v.get("settings")], sort_keys=True).encode()).hexdigest()[:12]
            mp3, meta = os.path.join(vdir, h + ".mp3"), os.path.join(vdir, h + ".json")
            if not os.path.exists(meta):
                body = {"text": text, "model_id": v.get("model", "eleven_multilingual_v2"), "voice_settings": v.get("settings", {}),
                        "previous_text": " ".join(ad["scenes"][x]["vo"] for x in ids[:n])[-300:], "next_text": " ".join(ad["scenes"][x]["vo"] for x in ids[n + 1:])[:300]}
                body = {k: val for k, val in body.items() if val != ""}
                if str(body["model_id"]).startswith("eleven_v3"):   # v3 does not accept surrounding context yet
                    body.pop("previous_text", None); body.pop("next_text", None)
                req = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{v['voice_id']}/with-timestamps?output_format=mp3_44100_128",
                                             data=json.dumps(body).encode(), method="POST", headers={"xi-api-key": key, "Content-Type": "application/json"})
                try:
                    res = json.load(urllib.request.urlopen(req, timeout=120))
                except urllib.error.HTTPError as e:
                    try: msg = json.load(e).get("detail", {}).get("message", "")
                    except Exception: msg = ""
                    sys.exit(f"The voice service refused the line \"{text[:50]}\" ({e.code}). {msg}".strip())
                open(mp3, "wb").write(base64.b64decode(res["audio_base64"]))
                json.dump({"text": text, "alignment": res["alignment"]}, open(meta, "w")); used += len(text)
            al = json.load(open(meta))["alignment"]
            clips_by_text[(text, v["voice_id"])] = {"spoken": al["character_end_times_seconds"][-1], "alignment": al, "file": mp3}
    schedules = {n: timeline(ad, n)[0] for n in ad["deliverables"]}; infos = []
    os.makedirs(os.path.join(ad_dir, "upload"), exist_ok=True)
    for name in names:
        ids = ad["deliverables"][name]["scenes"]; vid = voice_for(ad, name)["voice_id"]
        clips = {sid: clips_by_text[(ad["scenes"][sid]["vo"], vid)] for sid in ids}
        sched, info = timeline(ad, name, clips); schedules[name] = sched; infos.append(info)
        D = sched["duration"]; cmd = ["ffmpeg", "-y", "-loglevel", "error"]
        for sid in ids: cmd += ["-i", clips[sid]["file"]]
        parts = [f"[{n}:a]adelay={int(l['start'] * 1000)}:all=1[a{n}]" for n, l in enumerate(info["lines"])]
        mix = "".join(f"[a{n}]" for n in range(len(ids))) + f"amix=inputs={len(ids)}:normalize=0,apad=whole_dur={D},atrim=0:{D}[out]"
        subprocess.run(cmd + ["-filter_complex", ";".join(parts) + ";" + mix, "-map", "[out]", "-ar", "48000", work(ad_dir, f"voice-{name}.wav")], check=True)
        with open(os.path.join(ad_dir, "upload", f"captions-{name}.srt"), "w", encoding="utf-8") as f:
            for n, l in enumerate(info["lines"], 1): f.write(f"{n}\n{srt(l['start'])} --> {srt(l['end'])}\n{l['text']}\n\n")
    prev = work(ad_dir, "schedules.json")
    if only and os.path.exists(prev):
        merged = json.load(open(prev)); merged.update({n: schedules[n] for n in names}); schedules = merged
    json.dump(schedules, open(prev, "w"), indent=1)
    json.dump(infos, open(work(ad_dir, "timelines.json"), "w"), indent=1)
    print(f"voice characters used this run: {used}")
    ok = print_plan(infos); stage_player(ad, ad_dir, schedules)
    if not ok: sys.exit("One or more deliverables run long. Shorten the lines and run voice again. Nothing was rendered.")


def srt(t):
    ms = int(round(t * 1000)); hh, ms = divmod(ms, 3600000); mm, ms = divmod(ms, 60000); ss, ms = divmod(ms, 1000)
    return f"{hh:02}:{mm:02}:{ss:02},{ms:03}"


def library_track(want, key=""):
    """A track from <workspace>/music/library.json by mood or by file name.
    Within a mood the pick is fixed by `key` (the concept), so every version of one concept shares a track
    and different concepts get different tracks."""
    libf = os.path.join(WORKSPACE, "music", "library.json")
    if not want or not os.path.exists(libf): return None
    lib = json.load(open(libf, encoding="utf-8"))["tracks"]
    hits = [t for t in lib if t["file"] == want] or [t for t in lib if t["mood"] == want]
    if not hits: return None
    t = hits[sum(ord(c) for c in key) % len(hits)]
    p = os.path.join(WORKSPACE, "music", t["file"])
    return p if os.path.exists(p) else None


def find_music(ad, ad_dir, D, name=None):
    adir = os.path.join(ad["_pdir"], "audio")
    want = (ad["deliverables"][name].get("music") if name else None) or ad.get("music")
    if want:
        t = library_track(want, ad["deliverables"][name].get("concept", "") if name else "")
        if t: return t, False
        p = os.path.join(WORKSPACE, want)
        if os.path.exists(p): return p, False
    if os.path.isdir(adir):
        for f in sorted(os.listdir(adir)):
            if f.lower().endswith((".mp3", ".wav", ".m4a")): return os.path.join(adir, f), False
    out = work(ad_dir, "music-placeholder.wav")
    if not os.path.exists(out):
        chord = "0.22*sin(2*PI*110*t)+0.16*sin(2*PI*164.81*t)+0.16*sin(2*PI*220*t)+0.11*sin(2*PI*277.18*t)+0.10*sin(2*PI*329.63*t)+0.05*sin(2*PI*493.88*t)"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"aevalsrc={chord}:s=48000:d=60",
                        "-af", "tremolo=f=1.83:d=0.30,lowpass=f=1600,aecho=0.8:0.7:90|180:0.35|0.25,afade=t=in:d=0.6", "-ac", "2", out], check=True)
    return out, True


def stage_kit(ad, ad_dir, only=None, audio_only=False):
    f = work(ad_dir, "schedules.json")
    schedules = json.load(open(f)) if os.path.exists(f) else {}
    for n in ad["deliverables"]:
        if n not in schedules: schedules[n] = timeline(ad, n)[0]
    player = stage_player(ad, ad_dir, schedules); report = []
    for k in ad["kit"]:
        if only and only != f"{k['d']}:{k['fmt']}": continue
        silent = ad["deliverables"][k["d"]].get("silent", False)
        if schedules[k["d"]]["source"] not in ("voice", "silent"): sys.exit(f"{k['d']} has no voice timing yet. Run the voice stage first.")
        D = schedules[k["d"]]["duration"]; fps = k.get("fps", 30)
        picture = work(ad_dir, f"silent-{k['d']}-{k['fmt']}.mp4")
        if audio_only and os.path.exists(picture): print("  keeping picture", os.path.basename(picture))
        else: node("render.js", player, picture, k["d"], k["fmt"], fps)
        music, placeholder = find_music(ad, ad_dir, D, k["d"])
        mixed = work(ad_dir, f"mix-{k['d']}.wav")
        if silent and not os.path.exists(mixed):
            fade = min(1.2, D / 5)
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", music, "-filter_complex",
                            f"[0:a]aloop=loop=-1:size=2e9,atrim=0:{D},afade=t=out:st={D - fade}:d={fade},loudnorm=I=-16:TP=-1.5:LRA=7,atrim=0:{D}[out]",
                            "-map", "[out]", "-ar", "48000", mixed], check=True)
        elif not silent and (not os.path.exists(mixed) or os.path.getmtime(mixed) < os.path.getmtime(work(ad_dir, f"voice-{k['d']}.wav"))):
            fade = min(1.2, D / 5)
            pre = (f"[1:a]aloop=loop=-1:size=2e9,atrim=0:{D},volume=0.18,afade=t=out:st={D - fade}:d={fade}[m];[0:a]aformat=channel_layouts=stereo[v];"
                   f"[v][m]amix=inputs=2:normalize=0")
            ins = ["-i", work(ad_dir, f"voice-{k['d']}.wav"), "-i", music]
            m = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", *ins, "-filter_complex", pre + ",loudnorm=I=-14:TP=-1.5:LRA=7:print_format=json[out]",
                                "-map", "[out]", "-f", "null", "-"], capture_output=True, text=True).stderr
            j = json.loads(m[m.rindex("{"):m.rindex("}") + 1])
            second = (f",loudnorm=I=-14:TP=-1.5:LRA=7:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}"
                      f":measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true,atrim=0:{D}[out]")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *ins, "-filter_complex", pre + second, "-map", "[out]", "-ar", "48000", mixed], check=True)
        folder = os.path.join(ad_dir, k["folder"]); os.makedirs(folder, exist_ok=True)
        final = os.path.join(folder, f"{k['d']}-{k['fmt']}.mp4")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", picture, "-i", mixed, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-t", str(D), final], check=True)
        rep = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", final, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
        lufs = re.findall(r"I:\s+(-?[\d.]+) LUFS", rep); peak = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", rep)
        pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,r_frame_rate:format=duration,size",
                                        "-of", "json", final], capture_output=True, text=True).stdout)
        report.append({"file": os.path.relpath(final, ad_dir).replace("\\", "/"), "concept": ad["deliverables"][k["d"]].get("concept", "main"),
                       "voice": "none, text-driven" if silent else voice_for(ad, k["d"]).get("voice_name", "?"), "size": f"{pr['streams'][0]['width']}x{pr['streams'][0]['height']}",
                       "fps": pr["streams"][0]["r_frame_rate"], "duration": round(float(pr["format"]["duration"]), 2), "mb": round(int(pr["format"]["size"]) / 1e6, 2),
                       "lufs": float(lufs[-1]) if lufs else None, "true_peak": float(peak[-1]) if peak else None, "music": "placeholder" if placeholder else os.path.basename(music)})
        print("  finished", report[-1]["file"])
    up = os.path.join(ad_dir, "upload"); os.makedirs(up, exist_ok=True)
    first = ad["kit"][0]; master = os.path.join(ad_dir, first["folder"], f"{first['d']}-{first['fmt']}.mp4")
    if os.path.exists(master):
        D = schedules[first["d"]]["duration"]
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(D - 1), "-i", master, "-frames:v", "1", "-vf", "scale=1280:720", "-q:v", "3", os.path.join(up, "thumbnail.jpg")], check=True)
    t = ad.get("ad_text", {})
    open(os.path.join(up, "ad-text.md"), "w", encoding="utf-8").write(
        "# Ad text\n\n## Headlines (40 characters max)\n" + "\n".join(f"- {x} ({len(x)})" for x in t.get("headlines", [])) +
        "\n\n## Descriptions (35 characters max)\n" + "\n".join(f"- {x} ({len(x)})" for x in t.get("descriptions", [])) + "\n")
    prev = work(ad_dir, "kit-report.json")
    if only and os.path.exists(prev):
        old = [r for r in json.load(open(prev)) if r["file"] not in {x["file"] for x in report}]; report = old + report
    json.dump(report, open(prev, "w"), indent=1)
    print(json.dumps(report, indent=1))
    if not os.path.exists(os.path.join(ad_dir, "CAMPAIGN-PLAN.md")): print("REMINDER: CAMPAIGN-PLAN.md has not been written for this ad.")


def main():
    if len(sys.argv) < 3: sys.exit(__doc__)
    ad_dir, stage = os.path.abspath(sys.argv[1]), sys.argv[2]
    opts = dict(zip(sys.argv[3::2], sys.argv[4::2]))
    ad = load(ad_dir)
    if stage == "check":   sys.exit(0 if stage_check(ad, ad_dir) else 1)
    if stage == "plan":    print_plan([timeline(ad, n)[1] for n in ad["deliverables"]])
    elif stage == "player": stage_player(ad, ad_dir)
    elif stage == "stills": stage_stills(ad, ad_dir, opts.get("--d"), opts.get("--fmt"))
    elif stage == "master": stage_master(ad, ad_dir)
    elif stage == "voice":  stage_voice(ad, ad_dir, opts.get("--only"))
    elif stage == "kit":    stage_kit(ad, ad_dir, opts.get("--only"), "--audio-only" in sys.argv)
    else: sys.exit(__doc__)


if __name__ == "__main__":
    main()
