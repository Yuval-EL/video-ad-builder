"""Review pages for the gates. Each is one self-contained HTML file inside the ad folder.

Usage: python tools/review.py <ad-folder> script|concept|kit

  script    review-script.html   body script, hook variants side by side, cutdown lines, timing bars, claims, ad text
  concept   review-concept.html  stills in all three shapes and the silent master
  kit       index.html           every finished file, the campaign plan, uploads, flags

Also updates state.json in the ad folder with the gate that is now waiting.
"""
import datetime, glob, html, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build  # noqa: E402

CSS = """
body{font-family:system-ui,Segoe UI,Arial,sans-serif;margin:0;background:#f4f5f9;color:#141822}
.wrap{max-width:1180px;margin:0 auto;padding:36px 24px 80px} h1{font-size:26px;margin:0 0 4px} h2{font-size:18px;margin:34px 0 12px} .muted{color:#6b7280}
.box{background:#fff;border-radius:16px;padding:20px 24px;box-shadow:0 4px 18px rgba(0,0,0,.05);margin:12px 0}
table{width:100%;border-collapse:collapse;font-size:14px} th,td{text-align:left;padding:9px 10px;border-bottom:1px solid #eef0f4;vertical-align:top} th{color:#6b7280;font-weight:600}
.hooks{display:grid;grid-template-columns:repeat(3,1fr);gap:14px} .hook{background:#fff;border-radius:16px;padding:18px;box-shadow:0 4px 18px rgba(0,0,0,.05)}
.hook .tag{display:inline-block;background:#eef0ff;color:#3b3fb8;border-radius:999px;padding:3px 10px;font-size:12px;font-weight:600;margin-bottom:8px}
.hook .line{font-size:17px;font-weight:600;margin:6px 0} .hook img{width:100%;border-radius:10px;margin-top:10px}
.bar{position:relative;height:14px;background:#e5e7eb;border-radius:7px;overflow:hidden;margin:6px 0} .bar i{position:absolute;left:0;top:0;bottom:0;background:#4f46e5;border-radius:7px}
.bar b{position:absolute;top:0;bottom:0;width:2px;background:#ef4444} .ok{color:#15803d;font-weight:600} .warn{color:#b45309;font-weight:600} .bad{color:#b91c1c;font-weight:600}
.row{display:flex;gap:10px;overflow-x:auto;padding-bottom:8px} .row img{height:150px;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,.12)}
video{width:100%;border-radius:12px;background:#000} .cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px}
.card{background:#fff;border-radius:16px;padding:14px;box-shadow:0 4px 18px rgba(0,0,0,.05)} .card small{color:#6b7280}
.gate{background:#141822;color:#fff;border-radius:16px;padding:18px 24px;margin:0 0 20px} .gate b{color:#c7d2fe}
code{background:#eef0f4;padding:2px 6px;border-radius:5px;font-size:13px}
"""


def page(title, body, sub=""):
    return (f'<!doctype html><html><head><meta charset="utf-8"><title>{html.escape(title)}</title><style>{CSS}</style></head>'
            f'<body><div class="wrap"><h1>{html.escape(title)}</h1><div class="muted">{html.escape(sub)}</div>{body}</div></body></html>')


def md_to_html(md):
    out, in_ul, in_tbl = [], False, False
    for line in md.splitlines():
        s = line.rstrip()
        if s.startswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            if set("".join(cells)) <= set("-: "): continue
            if not in_tbl: out.append("<table>"); in_tbl = True; out.append("<tr>" + "".join(f"<th>{html.escape(c)}</th>" for c in cells) + "</tr>"); continue
            out.append("<tr>" + "".join(f"<td>{html.escape(c)}</td>" for c in cells) + "</tr>"); continue
        if in_tbl: out.append("</table>"); in_tbl = False
        if s.startswith("- "):
            if not in_ul: out.append("<ul>"); in_ul = True
            out.append(f"<li>{html.escape(s[2:])}</li>"); continue
        if in_ul: out.append("</ul>"); in_ul = False
        if s.startswith("# "): out.append(f"<h1>{html.escape(s[2:])}</h1>")
        elif s.startswith("## "): out.append(f"<h2>{html.escape(s[3:])}</h2>")
        elif s.startswith("### "): out.append(f"<h3>{html.escape(s[4:])}</h3>")
        elif s: out.append(f"<p>{html.escape(s)}</p>")
    if in_ul: out.append("</ul>")
    if in_tbl: out.append("</table>")
    return "\n".join(out).replace("**", "")


def set_state(ad_dir, gate, extra=None):
    f = os.path.join(ad_dir, "state.json")
    st = json.load(open(f)) if os.path.exists(f) else {}
    st.update({"gate": gate, "updated": datetime.datetime.now().isoformat(timespec="seconds")}); st.update(extra or {})
    json.dump(st, open(f, "w"), indent=1)


def still_for(ad_dir, d, fmt, idx=1):
    m = sorted(glob.glob(os.path.join(ad_dir, "working", "stills", f"{d}-{fmt}-{idx:02d}-*.jpg")))
    return os.path.relpath(m[0], ad_dir).replace("\\", "/") if m else None


def script_page(ad, ad_dir):
    sc = ad["scenes"]; infos = {n: build.timeline(ad, n)[1] for n in ad["deliverables"]}
    hooks = [(n, dv) for n, dv in ad["deliverables"].items() if dv.get("hook_pattern")]
    hk = ""
    for n, dv in hooks:
        first = sc[dv["scenes"][0]]; img = still_for(ad_dir, n, "16x9")
        hk += (f'<div class="hook"><span class="tag">{html.escape(dv["hook_pattern"])}</span><div class="muted">{n} · {first["type"]}</div>'
               f'<div class="line">{html.escape(first["vo"])}</div><div class="muted">{html.escape(dv.get("bet", ""))}</div>' + (f'<img src="{img}">' if img else "") + "</div>")
    concepts = {}
    for n, dv in ad["deliverables"].items(): concepts.setdefault(dv.get("concept", "main"), []).append(n)
    cx = ""
    for c, names in concepts.items():
        dv0 = ad["deliverables"][names[0]]
        voice = "none, text-driven" if dv0.get("silent") else (build.voice_for(ad, names[0]) or {}).get("voice_name", "?")
        lines = "".join(f"<tr><td><b>{n}</b><br><small class='muted'>{ad['deliverables'][n]['duration']} s</small></td><td>" +
                        "<br>".join(html.escape(sc[x].get("vo") or ("[on screen] " + str(sc[x].get("text", sc[x].get("label", ""))))) for x in ad["deliverables"][n]["scenes"]) + "</td></tr>"
                        for n in names if not ad["deliverables"][n].get("hook_pattern"))
        cx += f'<div class="box"><b>{html.escape(c)}</b> <span class="muted">· voice: {html.escape(voice)} · {len(names)} version{"s" if len(names) > 1 else ""}</span>' + (f"<table>{lines}</table>" if lines else "") + "</div>"
    main = hooks[0][1]["scenes"] if hooks else list(ad["deliverables"].values())[0]["scenes"]
    body = "".join(f"<tr><td>{i + 1}</td><td><code>{s}</code><br><small class='muted'>{sc[s]['type']} · {sc[s]['bg']}</small></td><td>{html.escape(sc[s]['vo'])}</td>"
                   f"<td>{html.escape(', '.join(sc[s].get('cues', {}).values()))}</td></tr>" for i, s in enumerate(main))
    cuts = ""
    for n, dv in ad["deliverables"].items():
        if dv.get("hook_pattern"): continue
        cuts += f"<tr><td><b>{n}</b><br><small class='muted'>{dv['duration']} s</small></td><td>" + "<br>".join(html.escape(sc[s].get("vo") or "[on screen] " + str(sc[s].get("text", sc[s].get("label", "")))) for s in dv["scenes"]) + "</td></tr>"
    bars = ""
    for n, x in infos.items():
        if x.get("silent"):
            bars += f'<div><b>{n}</b> <span class="muted">text-driven, no voice. Scenes hold {x["duration"]:.0f} s in total.</span> <span class="ok">fits</span></div>'; continue
        pct = min(100, x["voice_ends"] / x["duration"] * 100); skip = 5 / x["duration"] * 100
        flags = []
        if x["over_by"] > 0: flags.append(f'<span class="bad">too long by {x["over_by"]} s</span>')
        if x["duration"] >= 15 and (x["brand_spoken_at"] is None or x["brand_spoken_at"] > 5): flags.append('<span class="warn">brand after the skip point</span>')
        if not flags: flags.append('<span class="ok">fits</span>')
        bars += (f'<div><b>{n}</b> <span class="muted">{x["words"]} words, budget {x["word_budget"]}. Voice ends at {x["voice_ends"]} s of {x["duration"]:.0f}. '
                 f'Brand spoken at {x["brand_spoken_at"]} s.</span> {" ".join(flags)}<div class="bar"><i style="width:{pct:.0f}%"></i><b style="left:{skip:.1f}%"></b></div></div>')
    claims = "".join(f"<tr><td>{html.escape(c['claim'])}</td><td>{html.escape(c['source'])}</td><td>{html.escape(c['status'])}</td></tr>" for c in ad.get("claims", []))
    t = ad.get("ad_text", {})
    adtext = "<br>".join(html.escape(x) + f" <small class='muted'>({len(x)})</small>" for x in t.get("headlines", [])) + "<br><br>" + \
             "<br>".join(html.escape(x) + f" <small class='muted'>({len(x)})</small>" for x in t.get("descriptions", []))
    mode = "screenshot" if glob.glob(os.path.join(ad["_pdir"], "screenshots", "*.*")) else "illustrated"
    body_html = (f'<div class="gate"><b>Gate 2 of 4: script.</b> Nothing is voiced or rendered until you approve this page. Reply "approve" or say what to change.</div>'
                 f'<div class="box"><b>{html.escape(ad["brand"]["name"])}</b> · {ad.get("playbook", "")} · {mode} mode · {len(ad["kit"])} files planned · patterns {", ".join(ad.get("patterns", []))}</div>'
                 f'<h2>Creative concepts</h2>{cx}'
                 f'<h2>Openings tested on the first concept</h2><div class="hooks">{hk}</div>'
                 f'<h2>The body, scene by scene</h2><div class="box"><table><tr><th>#</th><th>Scene</th><th>Voice line</th><th>Lands on</th></tr>{body}</table></div>'
                 f'<h2>Cutdowns</h2><div class="box"><table>{cuts}</table></div>'
                 f'<h2>Timing</h2><div class="box"><div class="muted">Blue is spoken voice. The red mark is the five second skip point.</div>{bars}</div>'
                 f'<h2>Claims and sources</h2><div class="box"><table><tr><th>Claim in the ad</th><th>Source</th><th>Status</th></tr>{claims}</table></div>'
                 f'<h2>Ad text for the upload fields</h2><div class="box">{adtext}</div>')
    out = os.path.join(ad_dir, "review-script.html"); open(out, "w", encoding="utf-8").write(page(f"Script review: {ad['name']}", body_html, "Gate 2 of 4"))
    set_state(ad_dir, "script"); print(out)


def concept_page(ad, ad_dir):
    k = ad["kit"][0]; d = k["d"]
    rows = ""
    for fmt in ("16x9", "9x16", "1x1"):
        imgs = sorted(glob.glob(os.path.join(ad_dir, "working", "stills", f"{d}-{fmt}-*.jpg")))
        rows += f'<h2>{fmt.replace("x", ":")}</h2><div class="box"><div class="row">' + "".join(f'<img src="{os.path.relpath(i, ad_dir).replace(chr(92), "/")}">' for i in imgs) + "</div></div>"
    vid = f"working/concept-{d}-{k['fmt']}.mp4"
    body_html = (f'<div class="gate"><b>Gate 3 of 4: silent concept.</b> Watch the master without sound and look at the stills in every shape. Reply "approve" or give notes by scene.</div>'
                 f'<h2>Silent master, {d} in {k["fmt"].replace("x", ":")}</h2><div class="box"><video controls muted src="{vid}"></video></div>{rows}')
    out = os.path.join(ad_dir, "review-concept.html"); open(out, "w", encoding="utf-8").write(page(f"Concept review: {ad['name']}", body_html, "Gate 3 of 4"))
    set_state(ad_dir, "concept"); print(out)


def kit_page(ad, ad_dir):
    rep = json.load(open(os.path.join(ad_dir, "working", "kit-report.json"))) if os.path.exists(os.path.join(ad_dir, "working", "kit-report.json")) else []
    groups = {}
    for r in rep: groups.setdefault(r.get("concept", "main"), []).append(r)
    cards = ""
    for g, items in groups.items():
        voices = sorted({r.get("voice", "?") for r in items})
        cards += f"<h2>{html.escape(g)} <span class='muted' style='font-size:14px;font-weight:400'>· voice: {html.escape(', '.join(voices))} · {len(items)} files</span></h2><div class='cards'>" + "".join(
            f'<div class="card"><video controls src="{r["file"]}"></video><div><b>{os.path.basename(r["file"])}</b> <small class="muted">{r["file"].split("/")[0]}</small></div>'
            f'<small>{r["size"]} · {r["fps"].split("/")[0]} fps · {r["duration"]} s · {r["mb"]} MB · {r["lufs"]} LUFS</small></div>' for r in items) + "</div>"
    ups = "".join(f"<li><a href='upload/{f}'>{f}</a></li>" for f in sorted(os.listdir(os.path.join(ad_dir, "upload")))) if os.path.isdir(os.path.join(ad_dir, "upload")) else ""
    flags = []
    if any(r.get("music") == "placeholder" for r in rep): flags.append("Music is a synthesized placeholder. Add a licensed track to the product's audio folder and rerun the kit.")
    for c in ad.get("claims", []):
        if "illustrative" in c["status"].lower(): flags.append(f"Illustrative: {c['claim']}")
    plan_f = os.path.join(ad_dir, "CAMPAIGN-PLAN.md")
    plan = md_to_html(open(plan_f, encoding="utf-8").read()) if os.path.exists(plan_f) else "<p class='warn'>No campaign plan written yet.</p>"
    body_html = (f'<div class="gate"><b>Gate 4 of 4: the kit.</b> {len(rep)} files are finished. Everything below is in this folder.</div>{cards}'
                 f'<h2>Campaign plan</h2><div class="box">{plan}</div>'
                 f'<h2>Uploads</h2><div class="box"><ul>{ups}</ul></div>'
                 f'<h2>Flags</h2><div class="box"><ul>' + "".join(f"<li>{html.escape(f)}</li>" for f in flags) + ("<li>None.</li>" if not flags else "") + "</ul></div>")
    out = os.path.join(ad_dir, "index.html"); open(out, "w", encoding="utf-8").write(page(f"Kit: {ad['name']}", body_html, f"{ad['brand']['name']} · {len(rep)} files"))
    set_state(ad_dir, "done", {"files": len(rep)}); print(out)


if __name__ == "__main__":
    ad_dir, which = os.path.abspath(sys.argv[1]), sys.argv[2]
    ad = build.load(ad_dir)
    {"script": script_page, "concept": concept_page, "kit": kit_page}[which](ad, ad_dir)
