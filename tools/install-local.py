"""Install the skill into a workspace without a marketplace.

Usage: python tools/install-local.py [workspace-folder]
Writes <workspace>/.claude/skills/video-ad-builder/ with the plugin path filled in, so /video-ad-builder works
in that folder from Claude Code, the desktop app, or the IDE extension. Run it again after updating the plugin.
"""
import os, shutil, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import ROOT, ensure_workspace  # noqa: E402

ws = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.getcwd()
os.environ["VAB_WORKSPACE"] = ws
dst = os.path.join(ws, ".claude", "skills", "video-ad-builder")
try:
    if os.path.exists(dst): shutil.rmtree(dst)
except PermissionError:
    pass  # a synced folder may hold a lock for a moment; copying over the top is fine
os.makedirs(dst, exist_ok=True)
shutil.copy(os.path.join(ROOT, "SKILL.md"), dst)
for d in ("references", "templates"):
    shutil.copytree(os.path.join(ROOT, d), os.path.join(dst, d), dirs_exist_ok=True)
skill = os.path.join(dst, "SKILL.md")
text = open(skill, encoding="utf-8").read().replace("${CLAUDE_PLUGIN_ROOT}", ROOT.replace("\\", "/"))
open(skill, "w", encoding="utf-8").write(text)
for d in ("products", "output"):
    os.makedirs(os.path.join(ws, d), exist_ok=True)
env = os.path.join(ws, ".env")
if not os.path.exists(env):
    open(env, "w", encoding="utf-8").write("ELEVENLABS_API_KEY=paste_your_key_here\n")
print(f"Installed. Open Claude Code in {ws} and run /video-ad-builder")
