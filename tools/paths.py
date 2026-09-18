"""Where things live.

ROOT       the plugin: engine, tools, examples. Never written to by a run.
WORKSPACE  the user's folder: products/, output/, .env. Set with VAB_WORKSPACE, otherwise the current folder.
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKSPACE = os.path.abspath(os.environ.get("VAB_WORKSPACE") or os.getcwd())

if os.environ.get("LOCALAPPDATA"):
    os.environ["PATH"] = os.path.join(os.environ["LOCALAPPDATA"], "Microsoft", "WinGet", "Links") + os.pathsep + os.environ["PATH"]


def ensure_workspace():
    for d in ("products", "output"):
        os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)
    env = os.path.join(WORKSPACE, ".env")
    if not os.path.exists(env):
        open(env, "w", encoding="utf-8").write("ELEVENLABS_API_KEY=paste_your_key_here\n")
    return WORKSPACE


def product_dir(name):
    """A product in the workspace, or a bundled example product."""
    for base in (os.path.join(WORKSPACE, "products"), os.path.join(ROOT, "examples", "products")):
        p = os.path.join(base, name)
        if os.path.exists(os.path.join(p, "brand.json")):
            return p
    raise SystemExit(f"No product named '{name}'. Saved products live in {os.path.join(WORKSPACE, 'products')}.")


def list_products():
    out = []
    for base in (os.path.join(WORKSPACE, "products"), os.path.join(ROOT, "examples", "products")):
        if os.path.isdir(base):
            out += [p for p in os.listdir(base) if os.path.exists(os.path.join(base, p, "brand.json")) and p not in out]
    return out


def voice_key():
    """The voice key, from the environment or the workspace .env. Never printed."""
    k = os.environ.get("ELEVENLABS_API_KEY")
    if k and "paste" not in k:
        return k
    for base in (WORKSPACE, ROOT):
        f = os.path.join(base, ".env")
        if os.path.exists(f):
            for line in open(f, encoding="utf-8"):
                if line.startswith("ELEVENLABS_API_KEY=") and "paste" not in line:
                    return line.split("=", 1)[1].strip()
    return None
