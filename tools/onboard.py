"""Add a product from its public website.

Usage: python tools/onboard.py <url> <product-slug> [--name "Display Name"]

Reads the public home page and writes products/<slug>/:
  brand.json        machine-readable brand: colors by role, font, logo files
  brand-spec.md     the same in prose, with the claims the site makes and the page's call to action
  branding/*.svg    the wordmark and icon if the page has them inline or linked
  brand-card.html   a one-page card for the user to approve

Role assignment is a best guess from color frequency. The card is where the user corrects it.
"""
import colorsys, json, os, re, sys, urllib.request
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import WORKSPACE, ensure_workspace  # noqa: E402
UA = {"User-Agent": "Mozilla/5.0"}


def get(url, binary=False):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=25) as r:
        data = r.read()
    return data if binary else data.decode("utf-8", "ignore")


def hsl(hexv):
    r, g, b = (int(hexv[i:i + 2], 16) / 255 for i in (1, 3, 5))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return h, s, l


def assign_roles(counter):
    """Pick brand roles from the most used hex colors on the page."""
    cols = [(c, n) for c, n in counter.most_common(40) if c not in ("#ffffff", "#000000")]
    sat = [(c, n) for c, n in cols if hsl(c)[1] > 0.35 and 0.25 < hsl(c)[2] < 0.75]
    dark = [(c, n) for c, n in cols if hsl(c)[2] < 0.18]
    tints = [(c, n) for c, n in cols if hsl(c)[2] > 0.8 and hsl(c)[1] > 0.2]
    primary = sat[0][0] if sat else "#3B82F6"
    accent = next((c for c, n in sat if abs(hsl(c)[0] - hsl(primary)[0]) > 0.12), None) or next((c for c, n in tints), None) or "#FBBF24"
    return {"dark": dark[0][0] if dark else "#0F172A", "primary": primary, "accent": accent,
            "soft1": tints[0][0] if tints else "#E0E7FF", "soft2": tints[1][0] if len(tints) > 1 else (tints[0][0] if tints else "#E0F2FE"),
            "card": "#FFFFFF", "ink": dark[0][0] if dark else "#111827", "light": "#FFFFFF", "ok": "#22C55E"}


def main():
    url = sys.argv[1]; slug = sys.argv[2]
    name = sys.argv[sys.argv.index("--name") + 1] if "--name" in sys.argv else None
    html = get(url)
    text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text); text = re.sub(r"\s+", " ", text)
    title = re.search(r"<title>([^<]*)", html); title = title.group(1).strip() if title else slug
    desc = re.search(r'name="description" content="([^"]*)"', html); desc = desc.group(1) if desc else ""
    name = name or re.split(r"\s[|\-:]\s", title)[0].strip() or slug

    hexes = Counter(c.lower() for c in re.findall(r"#[0-9a-fA-F]{6}\b", html))
    colors = assign_roles(hexes)
    fonts = Counter(re.findall(r"font-family:\s*(?:var\(--font-)?([A-Za-z][A-Za-z0-9 -]{2,30})", html))
    skip = ("inherit", "monospace", "sans", "system", "ui", "mono", "default", "var", "sans-serif", "serif")
    font = next((f.strip().split(",")[0].strip().title() for f, n in fonts.most_common(8) if f.strip().split(",")[0].strip().lower() not in skip), "Inter")
    ctas = Counter(m.strip() for m in re.findall(r">\s*((?:Book|Get|Request|Schedule|See|Start|Talk|Try)[^<]{2,30}?)\s*<", html))
    claims = sorted({s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if re.search(r"\d+\s?%|\d+\+|\b\d{2,}\b", s) and 20 < len(s) < 160})[:12]

    # Capability candidates: section headings on the page, cleaned. The user confirms which to feature at question 6.
    heads = [re.sub(r"<[^>]+>", " ", h) for h in re.findall(r"<h[23][^>]*>(.*?)</h[23]>", html, flags=re.S)]
    heads = [re.sub(r"\s+", " ", h).strip(" .:") for h in heads]
    seen, capabilities = set(), []
    for h in heads:
        k = h.lower()
        if 3 <= len(h.split()) <= 9 and 12 < len(h) < 80 and k not in seen and not re.search(r"pricing|customer|blog|faq|contact|about|career|login|sign|cookie|privacy|terms|trusted", k):
            seen.add(k); capabilities.append(h)
    capabilities = capabilities[:8]

    ensure_workspace()
    pdir = os.path.join(WORKSPACE, "products", slug); os.makedirs(os.path.join(pdir, "branding"), exist_ok=True)
    os.makedirs(os.path.join(pdir, "screenshots"), exist_ok=True); os.makedirs(os.path.join(pdir, "product-knowledge"), exist_ok=True)
    wordmark = icon = None
    m = re.search(r'<svg[^>]*aria-label="[^"]*"[^>]*>.*?</svg>', html, re.S)
    if m and (name.split()[0].lower() in m.group(0).lower()):
        wordmark = m.group(0)
    if not wordmark:
        m = re.search(r'<img[^>]+src="([^"]+\.svg)"[^>]*alt="([^"]*)"', html)
        if m and name.split()[0].lower() in m.group(2).lower():
            src = m.group(1); src = src if src.startswith("http") else url.rstrip("/") + "/" + src.lstrip("/")
            try: wordmark = get(src)
            except Exception: wordmark = None
    if not wordmark:
        wordmark = (f'<svg viewBox="0 0 400 48" xmlns="http://www.w3.org/2000/svg"><text x="0" y="36" font-family="inherit" font-size="36" '
                    f'font-weight="700" fill="currentColor">{name}</text></svg>')
        logo_note = "No logo found on the page. A typographic wordmark is used. Replace branding/wordmark.svg with the real one."
    else:
        wordmark = re.sub(r'fill="#(?!none)[0-9a-fA-F]{6}"', 'fill="currentColor"', wordmark)
        logo_note = "Wordmark taken from the page header."
    icon = re.sub(r'viewBox="[^"]*"', 'viewBox="0 0 48 48"', wordmark, count=1)   # crude: the left square of the wordmark
    open(os.path.join(pdir, "branding", "wordmark.svg"), "w", encoding="utf-8").write(wordmark)
    open(os.path.join(pdir, "branding", "icon.svg"), "w", encoding="utf-8").write(icon)

    brand = {"name": name, "source": url, "note": f"Built from the public site on request. {logo_note}", "font": font,
             "fontUrl": f"https://fonts.googleapis.com/css2?family={font.replace(' ', '+')}:wght@400;500;600;700&display=block",
             "colors": colors, "wordmark_file": "branding/wordmark.svg", "icon_file": "branding/icon.svg",
             "cta": ctas.most_common(1)[0][0] if ctas else "Book a demo", "tagline": desc, "capabilities": capabilities}
    json.dump(brand, open(os.path.join(pdir, "brand.json"), "w", encoding="utf-8"), indent=2)
    rows = "\n".join(f"| {k} | {v} |" for k, v in colors.items())
    spec = (f"# Brand Spec: {name}\n\n## Source\nPublic website {url}. {logo_note}\n\n## What the site says\n{desc}\n\n## Colors\n| Role | Hex |\n|---|---|\n{rows}\n\n"
            f"## Typography\n{font}, fallback system sans-serif.\n\n## Fixed copy\n- Call to action: {brand['cta']}\n- Web address on closer: {re.sub(r'^https?://(www\\.)?', '', url).strip('/')}\n\n"
            f"## Public claims found on the page\n" + "\n".join(f"- {c}" for c in claims) + "\n\n## Do not\n- Do not invent customer results.\n- Do not show logos of tools not listed as integrations.\n")
    open(os.path.join(pdir, "brand-spec.md"), "w", encoding="utf-8").write(spec)

    sw = "".join(f'<div class="sw"><div class="c" style="background:{v}"></div><b>{k}</b><span>{v}</span></div>' for k, v in colors.items())
    cl = "".join(f"<li>{c}</li>" for c in claims) or "<li>None found with numbers in them.</li>"
    card = f"""<!doctype html><html><head><meta charset="utf-8"><title>Brand card: {name}</title>
<link href="{brand['fontUrl']}" rel="stylesheet"><style>
body{{font-family:{font},system-ui,sans-serif;margin:0;background:#f6f7fb;color:#111}} .wrap{{max-width:980px;margin:40px auto;padding:0 24px}}
.hero{{background:{colors['dark']};color:#fff;border-radius:24px;padding:40px;display:flex;align-items:center;gap:40px}} .hero .wm{{width:260px}} .hero svg{{width:100%;height:auto}}
h1{{margin:0 0 6px;font-size:28px}} .muted{{opacity:.75}} .grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin:28px 0}}
.sw{{background:#fff;border-radius:16px;padding:14px;display:flex;align-items:center;gap:12px;box-shadow:0 4px 16px rgba(0,0,0,.06)}} .sw .c{{width:44px;height:44px;border-radius:12px;border:1px solid rgba(0,0,0,.08)}} .sw span{{margin-left:auto;font-family:monospace;opacity:.7}}
.box{{background:#fff;border-radius:16px;padding:22px 26px;margin:16px 0;box-shadow:0 4px 16px rgba(0,0,0,.06)}} .btn{{display:inline-block;background:{colors['accent']};color:{colors['dark']};padding:12px 24px;border-radius:999px;font-weight:700}}
</style></head><body><div class="wrap">
<div class="hero"><div class="wm">{wordmark}</div><div><h1>{name}</h1><div class="muted">{desc}</div><p style="margin:18px 0 0"><span class="btn">{brand['cta']}</span></p></div></div>
<div class="grid">{sw}</div>
<div class="box"><b>Font</b><br>{font}</div>
<div class="box"><b>Capabilities found on the page</b> (proposed at question 6, you confirm)<ul>{"".join(f"<li>{c}</li>" for c in capabilities) or "<li>None found. The builder will ask.</li>"}</ul></div>
<div class="box"><b>Claims the ad may use</b> (all from the page, each needs a human eye)<ul>{cl}</ul></div>
<div class="box"><b>Logo</b><br>{logo_note}</div>
<div class="box"><b>Screenshots</b><br>None yet. Drop PNGs into <code>products/{slug}/screenshots/</code> to switch the builder to screenshot mode.</div>
</div></body></html>"""
    open(os.path.join(pdir, "brand-card.html"), "w", encoding="utf-8").write(card)
    print(json.dumps({"product": slug, "name": name, "font": font, "colors": colors, "cta": brand["cta"], "claims_found": len(claims), "capabilities": capabilities, "logo": logo_note,
                      "card": os.path.join(pdir, "brand-card.html")}, indent=1))


if __name__ == "__main__":
    main()
