#!/usr/bin/env python3
"""Generate reviewable, verifiable .patch files for the AI excision + adjacent work,
by diffing the vanilla vault against the live (excised) tree.

WHY THIS IS TRUSTWORTHY: firefox-main has no VCS, but the vanilla vault
(/home/gorilla/.../SafetyVault.Firefox/firefox-main) is a pristine full tree. Every
patch here is `git diff --no-index vault live`, and the generator then PROVES each
group by applying it to a fresh copy of the vault files and diffing against live —
so a patch that would not reproduce the tree is caught, not shipped.

Universe = (files touched by the mozambique_/customize_ scripts, via AST) UNION
(files whose vault->live diff body mentions an AI symbol) UNION (explicit adjacent
files found during AI GUI testing). firefox.js is emitted whole but labelled (it also
carries non-AI baked prefs). Deleted files and the moved aiwindow/genai/theme dirs
appear as deletion hunks.
"""
import ast, glob, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
VAULT = "/home/gorilla/Documents/FIREFOX.WORK/Firefox.Scripts.Vault.Docs/SafetyVault.Firefox/firefox-main"
LIVE = "/home/gorilla/firefox-main"
OUT = os.path.join(HERE, "patches")
WORK = "/tmp/claude-1000/-home-gorilla-Documents-FIREFOX-WORK-FIrefox-154-Work--claude-worktrees-bold-lamport-02c654/ad78c415-8eb2-43bc-9218-8109ac3e8373/scratchpad/patchgen"

AI_KW = re.compile(r"aiwindow|AIWindow|genai|GenAI|\bml\b|llama|mozinference|smartwindow|"
                   r"SmartWindow|SmartTab|smart\.tab|LinkPreview|AIFeature|semanticHistory|"
                   r"EmbeddingsGenerator|ModelHub|about:inference|MLEngine|MLSuggest|"
                   r"UrlbarProviderAiChat|ChatStore|Smartbar|aiControl|isAIWindow|ai-window", re.I)

# adjacent files edited inline during AI/GUI work that may lack an AI keyword in-diff
ADJACENT = [
    "browser/themes/shared/customizableui/customizeMode.css",   # phantom-panel fix
    "browser/base/content/browser.xhtml",                       # genai.ftl <link> removed
    "browser/components/sidebar/sidebar-customize.html",        # genai.ftl <link> removed
    "browser/components/tabbrowser/content/tabgroup-menu.js",   # dead-code + model-optin
]
# dirs removed wholesale (present in vault, gone from live)
REMOVED_DIRS = [
    "browser/components/aiwindow",
    "browser/components/genai",
    "browser/themes/addons/aiwindow",
    "browser/themes/addons/aiwindow-nova",
]
# tree roots to scan for keyword-matched diffs (keeps it fast; where our edits live)
SCAN = ["browser", "toolkit", "dom", "docshell", "config", "modules"]

def sh(*a, **k):
    return subprocess.run(a, capture_output=True, text=True, **k)

# ---- 1. AST: files the scripts touched ----
script_files = set()
for s in sorted(glob.glob(os.path.join(HERE, "mozambique_*.py")) + glob.glob(os.path.join(HERE, "customize_*.py"))):
    for node in ast.walk(ast.parse(open(s).read())):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
           and node.func.id in ("rep", "remove_object", "delete_file") and node.args:
            a0 = node.args[0]
            if isinstance(a0, ast.Constant) and isinstance(a0.value, str) and a0.value.endswith(
                    (".mjs", ".js", ".jsm", ".css", ".html", ".xhtml", ".json", ".build", ".py",
                     ".manifest", ".mn", ".yaml", ".svg", ".in")):
                script_files.add(a0.value)

# ---- 2. keyword-matched: everything different vault->live whose diff mentions AI ----
kw_files = set()
for root in SCAN:
    r = sh("diff", "-rq", f"{VAULT}/{root}", f"{LIVE}/{root}")
    for line in r.stdout.splitlines():
        # "Files A/x and B/x differ"  OR  "Only in A: x" (deleted in live)
        m = re.match(r"Files .* and .* differ", line)
        if m:
            rel = line.split(" and ", 1)[1].rsplit(" differ", 1)[0]
            rel = os.path.relpath(rel, LIVE)
            d = sh("diff", "-u", f"{VAULT}/{rel}", f"{LIVE}/{rel}")
            if AI_KW.search(d.stdout):
                kw_files.add(rel)

# ---- 3. deleted individual files (in vault, absent from live, script-known) ----
universe = set(f for f in (script_files | kw_files | set(ADJACENT))
               if os.path.exists(f"{VAULT}/{f}"))
# only keep files that actually differ or are deleted
def differs(rel):
    v, l = f"{VAULT}/{rel}", f"{LIVE}/{rel}"
    if not os.path.exists(l):
        return True   # deleted
    return sh("diff", "-q", v, l).returncode != 0
universe = sorted(f for f in universe if differs(f))

# enumerate removed-dir files from the vault
removed_dir_files = []
for d in REMOVED_DIRS:
    for dp, _, fns in os.walk(f"{VAULT}/{d}"):
        for fn in fns:
            rel = os.path.relpath(os.path.join(dp, fn), VAULT)
            if not os.path.exists(f"{LIVE}/{rel}"):
                removed_dir_files.append(rel)

print(f"script_files={len(script_files)} kw_files={len(kw_files)} "
      f"adjacent={len(ADJACENT)}  -> universe(differing)={len(universe)}  "
      f"removed_dir_files={len(removed_dir_files)}")

# ---- 4. grouping (tier-aligned, matches the chronicle) ----
def group_of(rel):
    if rel == "browser/app/profile/firefox.js":
        return "07-prefs-firefox-js-FULL"      # whole file; AI subset is a labelled part
    if rel in removed_dir_files:
        return "09-removed-dirs-aiwindow-genai"
    if not os.path.exists(f"{LIVE}/{rel}"):
        return "08-deleted-files"
    if rel in ADJACENT:
        return "06-tabgroups-customize-adjacent"
    b = rel.rsplit("/", 1)[-1]
    if any(k in rel for k in ("metrics_index", ".manifest", "moz.build", "jar.mn",
           "session.schema", "ActorManagerParent", "DesktopActorRegistry", "package-manifest")):
        return "01-native-unwire"
    if any(k in b for k in ("SessionStore", "NewTabPagePreloading", "UrlbarUtils", "UrlbarInput",
           "browser-sidebar", "UITour", "SpecialMessageActions", "ASRouter", "Onboarding",
           "FeatureCallout", "PanelTest", "BrowserContentHandler", "Sanitizer",
           "ProfileDataUpgrader", "LightweightTheme", "sidebar-main", "storybook")):
        return "03-module-seams"
    if any(k in b for k in ("GenAI", "LinkPreview", "Translations", "PlacesSemantic",
           "preferences", "tabs-browsing", "tab-context-menu", "nsContextMenu")):
        return "04-genai-translations"
    if b.endswith((".xhtml", ".inc", ".html", ".ftl")) or "firefoxview" in rel:
        return "05-ftl-l10n-markup"
    return "02-window-chrome-seams"

groups = {}
for rel in universe:
    groups.setdefault(group_of(rel), []).append(rel)

# ---- 5. emit patches via git diff --no-index against clean-named staged trees ----
# stage into vanilla/<rel> and live/<rel>; git diff --no-index vanilla live yields
# a/vanilla/<rel> b/live/<rel>; sed-clean to a/<rel> b/<rel> for -p1 applicability.
if os.path.exists(WORK): shutil.rmtree(WORK)
os.makedirs(OUT, exist_ok=True)
manifest = []
def stage_and_diff(gname, files):
    base = os.path.join(WORK, gname)
    va_root, vb_root = os.path.join(base, "vanilla"), os.path.join(base, "live")
    os.makedirs(va_root, exist_ok=True); os.makedirs(vb_root, exist_ok=True)  # both exist
    for rel in files:
        s, l = f"{VAULT}/{rel}", f"{LIVE}/{rel}"
        if os.path.exists(s):
            os.makedirs(os.path.dirname(f"{va_root}/{rel}"), exist_ok=True); shutil.copy2(s, f"{va_root}/{rel}")
        if os.path.exists(l):
            os.makedirs(os.path.dirname(f"{vb_root}/{rel}"), exist_ok=True); shutil.copy2(l, f"{vb_root}/{rel}")
    r = sh("git", "diff", "--no-index", "vanilla", "live", cwd=base)
    txt = r.stdout.replace("a/vanilla/", "a/").replace("b/live/", "b/") \
                  .replace(" vanilla/", " a/").replace(" live/", " b/")
    patch = os.path.join(OUT, f"ai-excision-{gname}.patch")
    open(patch, "w").write(txt)
    return base, txt

for gname in sorted(groups):
    files = sorted(set(groups[gname]))
    base, txt = stage_and_diff(gname, files)
    manifest.append((f"ai-excision-{gname}.patch", txt.count("diff --git "), len(txt.splitlines())))

# removed dirs -> manifest list (content is Mozilla's, reproducible from vault; the
# DECISION is the moz.build DIRS removal in 01 + these dirs moved to firefox-main.excised-*)
rd = os.path.join(OUT, "ai-excision-09-removed-dirs-MANIFEST.txt")
with open(rd, "w") as g:
    g.write("# Directories removed wholesale (present in vanilla vault, absent from live tree).\n")
    g.write("# Moved (not rm'd) to /home/gorilla/firefox-main.excised-ai-aiwindow-genai.2026-08-02/\n")
    g.write("# The build-level removal is captured in ai-excision-01-native-unwire.patch (moz.build DIRS).\n")
    g.write(f"# {len(removed_dir_files)} files across: {', '.join(REMOVED_DIRS)}\n\n")
    for rel in sorted(removed_dir_files): g.write(rel + "\n")

# ---- 6. VERIFY: apply each patch to a fresh vanilla copy, must equal live ----
print("\n=== VERIFICATION (git apply to vanilla copy -> diff vs live) ===")
allok = True
for gname in sorted(groups):
    base = os.path.join(WORK, gname)
    ver = os.path.join(base, "verify")
    shutil.copytree(f"{base}/vanilla", ver)
    ap = sh("git", "apply", "-p1", f"--directory={os.path.relpath(ver, base)}",
            os.path.join(OUT, f"ai-excision-{gname}.patch"), cwd=base)
    # git apply leaves empty parent dirs after deletions; prune both sides so the
    # comparison is file-content only, not incidental empty directories.
    for d0 in (ver, f"{base}/live"):
        sh("find", d0, "-type", "d", "-empty", "-delete")
        os.makedirs(d0, exist_ok=True)   # re-create roots if pruning emptied them fully
    d = sh("diff", "-r", ver, f"{base}/live")
    ok = ap.returncode == 0 and d.returncode == 0
    allok &= ok
    print(f"  {'OK  ' if ok else 'FAIL'} ai-excision-{gname}.patch"
          + ("" if ok else f"  apply_rc={ap.returncode} diff_rc={d.returncode}\n       {ap.stderr.strip()[:200]}\n       {d.stdout.strip()[:200]}"))

print("\n=== PATCH SET ===")
for name, nf, nl in manifest:
    print(f"  {name}: {nf} files, {nl} lines")
print(f"  ai-excision-09-removed-dirs-MANIFEST.txt: {len(removed_dir_files)} files listed")
print("\nALL VERIFIED — patches reproduce the live tree from vanilla" if allok
      else "\n!!! SOME PATCHES FAILED VERIFICATION")
