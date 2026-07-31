# patch_manager.py — README

### How We Move Our Firefox Tweaks From An Old Build To A New One Without Breaking Everything

---

> **UPDATE 2026-07-17 — command changes (read first).**
> - **`port` was RETIRED.** It migrated old *full-file* tweaks from `old.patches/` into git
>   commits — a one-time job that is done. Its output is the diff stack in `new.patches/`.
> - **`apply` is NEW and is the current workflow.** `patch_manager.py apply` git-applies the
>   `new.patches/**/*.patch` unified-diff stack onto the source tree (idempotent — skips
>   already-applied). The diffs carry real source paths, so no path map is needed.
> - Live workflow now: **`init` → `apply` → `build` → (next version) `upgrade`**.
> - This tool now lives at `FIrefox.154.Work/patches/scripts/` and is invoked as
>   `gorilla patch-mgr <cmd>` (or directly). Default source tree: `~/firefox-main`.
> - Sections below that describe `port`/`old.patches` are historical.

---

> *"Imagine you have a recipe notebook. You've been cooking the same dish for months, and you've scribbled notes in the margins of every page — a pinch more salt here, a lower oven temperature there. Now someone hands you a brand new edition of the same cookbook. The recipes have changed slightly. The publisher renamed a few ingredients, reorganised some chapters, and removed a technique you used to rely on. You can't just tear the pages out of your old notebook and staple them into the new book — the page numbers don't match anymore, and some of your margin notes reference things that no longer exist in the same form. You need to go page by page, understand what changed in the new edition, and carefully re-write each of your margin notes into the new book so they make sense in their new context. That is exactly what this tool does for Firefox source code."*

---

## PART ONE: THE PROBLEM THIS TOOL SOLVES

### For The Non-Technical Reader

The Gorilla Unleashed project takes the Firefox web browser's source code and modifies it — about 158 files across 12 categories — to make Firefox run better on a specific laptop. These modifications are called **patches** or **tweaks**. They do things like:

- Force Firefox to use the graphics hardware for video decoding instead of software (which is slower)
- Lock down all telemetry so the browser doesn't phone home with usage data
- Customise the visual theme so it looks like "Gorilla Unleashed" instead of stock Firefox
- Disable remote automation features that could be used to control the browser externally

Every few months, a new version of Firefox is released. The Firefox source code changes — hundreds of thousands of lines are added, removed, renamed, and restructured. Our 158 tweaks were written against an *older* version of this code. When we download the *new* version, we need to re-apply our 158 tweaks to it.

**The problem:** some of the files we modified have changed upstream. A function we relied on might have been renamed. An argument we passed to it might have been removed. An enum we referenced might have moved to a different namespace. If we just copy our old tweaked files over the new tree, the compiler will reject our code because it was written for the old version of the surrounding code. This is called **API churn** and it is the single most painful part of maintaining a custom build of any large software project.

**What happened last time:** in July 2026, we tried to copy our old patched files over a fresh Firefox 154 download and run the build. The compiler produced 18+ errors in the networking subsystem alone. A 16-hour debugging session followed, during which an AI assistant made the same mistake repeatedly — editing a file, then editing it again based on a stale memory of what the file looked like before the first edit, effectively undoing its own work without realising it. The build never succeeded. The session ended with the assistant producing a corrupted, massively-repeated text dump and then going silent. (This is documented in `session_timeline_report.txt`.)

**The solution:** use **git** — a version control system — to track every single change we make, one file at a time, with a checkpoint after each. If a change breaks the build, we know exactly which change did it. If a change conflicts with upstream, we resolve it for that one file, not 158 files blind. When the next Firefox version lands (155, 156, ...), git can automatically replay our tweaks onto the new code using a process called **rebase**, handling non-conflicting changes automatically and only pausing for the ones that genuinely need human attention.

This tool, `patch_manager.py`, automates that entire workflow.

---

## PART TWO: THE MENTAL MODEL

### An Analogy: The Annotated Novel

Think of the Firefox source code as a novel — a very long one, about 500,000 pages. The publisher releases new editions regularly. You are an editor who has produced a custom annotated edition called "Gorilla Unleashed" — you've changed about 158 pages of the novel to fix typos, improve pacing, and add your own commentary.

Now the publisher releases a new edition. Most pages are identical to the old edition, but about 20 of your 158 annotated pages have been changed by the publisher too. You need to produce a new "Gorilla Unleashed" edition based on the publisher's new edition, keeping all 158 of your annotations, but adapting the ones that fall on pages the publisher changed.

**The old approach (copy everything):**
You take your 158 annotated pages from the old edition and paste them over the new edition. For the ~138 pages that didn't change upstream, this works fine — your annotation is pasted over an identical page. But for the ~20 pages the publisher also changed, you've just pasted your old page over the publisher's new page, destroying their changes. Your annotation may reference something the publisher removed. The book is now internally inconsistent.

**The new approach (git, one page at a time):**
You lay the publisher's new edition on your desk. You photograph every single page and file those photos in a folder called "pristine" — this is your baseline, your record of what the publisher gave you before you touched anything. You tag this baseline "firefox-154-upstream" so you can always return to it.

Then you pick up page 1 of your annotations. You compare it to the corresponding page in the new edition. If the publisher didn't change that page, your annotation applies cleanly — you make the edit and photograph the result (git commit). If the publisher *did* change the page, you read both versions carefully, understand what the publisher changed and what you changed, and write a new version that incorporates both. You photograph the result.

After all 158 pages, you have a complete annotated edition where every page is internally consistent. And you have a photo after every single page, so if page 73 introduced a typo, you can look at photo 72 (which was fine) and photo 73 (which has the typo) and know exactly what went wrong.

**When the publisher releases edition 155:**
You don't start from scratch. You take the new edition, photograph it all ("firefox-155-upstream"), and then ask git to replay your 158 annotations, one at a time, onto the new edition. For each annotation:

- If the page hasn't changed between editions 154 and 155, git applies your annotation automatically. No human intervention needed.
- If the page *has* changed, git pauses and says: "I can't apply this annotation automatically — the page is different. Here's what the page looks like now, here's your old annotation, please tell me how to adapt it." You resolve that one page, then tell git to continue.

This is called a **rebase** and it is the single most powerful feature of using git for this workflow. It means that upgrading to a new Firefox version is no longer a 16-hour ordeal where you re-do everything from scratch. It's a 16-minute review of the conflicts, followed by a coffee.

---

## PART THREE: WHAT EACH COMMAND DOES

### For The Non-Technical Reader (Plain English)

#### `init` — Start A New Project

**What it does:** You downloaded a fresh Firefox source tree. This command turns that folder into a git repository, takes a "photograph" of every file as it came from Mozilla (so you always have a record of what the original looked like), labels that photograph "firefox-154-upstream" (a **tag**), and then creates a separate workspace called "my-patches" where you'll do your work.

**Analogy:** Imagine you just bought a new house. Before moving in your furniture, you photograph every room empty. Those photos go in a binder labelled "empty house." Then you start a separate notebook called "my furniture plan" where you'll track what you put where and when. If you ever need to know what a room looked like before you touched it, you flip to the binder.

**When to use it:** Once, at the very beginning, after downloading a fresh Firefox source tree. Never again unless you're starting over with a completely new tree.

---

#### `status` — Where Am I?

**What it does:** Shows you a summary of the current state: which workspace you're on, how many tweaks you've committed so far, which files have changes that aren't saved yet, and whether your last build attempt succeeded or failed.

**Analogy:** The dashboard of your car. It doesn't drive the car, but it tells you the speed, fuel level, and whether the engine is on. You check it frequently to orient yourself.

**When to use it:** Anytime you're not sure what state things are in, or between operations.

---

#### `port` — Move One Tweak To The New Tree

**What it does:** This is the core operation. You tell it: "take my old tweak for file X in category Y and apply it to the new tree." It:

1. Finds your old tweaked version of the file in `old.patches/CATEGORY/FILE`
2. Finds the corresponding fresh file in the Firefox source tree
3. Copies your old tweak over the fresh file
4. Stages it in git (like putting a document on your desk for review before filing it)
5. Optionally commits it (files it permanently) if you add `--commit`

**Analogy:** You're renovating a house one room at a time. You bring in your old furniture (the tweak), place it in the new room, and step back to look at it. Does it fit? Does it match the new paint colour? If yes, you screw it down (`--commit`). If the room layout changed, you might need to rearrange the furniture before committing.

**Important:** For files where the upstream code changed (like the networking files in our case), you don't want to just copy the old file over. You need to manually edit the new file to re-apply the *intent* of your old tweak, adapting it to the new code around it. `port` gets the old tweak into your working tree so you can review and adjust it before committing.

**When to use it:** One file at a time. NEVER in bulk. The whole point of this tool is to avoid bulk operations.

---

#### `build` — Test The Build

**What it does:** Runs `./mach build` (Firefox's build command), captures the output to a log file, and parses the result for errors. If the build fails, it shows you each error AND tells you which git commit last touched the file where the error occurred — so you know immediately which of your tweaks caused the problem.

**Analogy:** After renovating each room, you flip the circuit breaker for that room to make sure the lights work. If they don't, the error message tells you which room has the problem, and you can check your renovation notebook to see exactly what you changed in that room.

**When to use it:** After committing a batch of tweaks (or even after a single one if it's a risky C++ file). Build incrementally — don't wait until all 158 files are done to discover the build is broken.

---

#### `rollback` — Undo A Mistake

**What it does:** Two modes:
- `--file PATH`: restores a single file to its pristine upstream state (as if you never touched it)
- `--commit SHA`:undoes a specific commit (creates a new commit that reverses the changes)

Neither mode destroys history. Git always keeps a record of everything that happened, so you can always see what was rolled back and when.

**Analogy:** You painted a wall the wrong colour. You can either repaint it white (restore file to pristine) or paint over your new colour with the previous colour (revert commit). Either way, the original wrong-colour paint is still visible under a microscope — the history is preserved, the wall just looks correct now.

**When to use it:** When a tweak breaks the build and you can't fix it quickly. Roll back, build again to confirm the rest is clean, then come back to that file later with more time.

---

#### `diff` — Show What You've Changed

**What it does:** Shows a unified diff (a side-by-side comparison) of everything you've changed compared to the pristine upstream code. Can show all files, one category, or a single file.

**Analogy:** A "before and after" photo comparison. On the left, the original room. On the right, the renovated room. The differences are highlighted so you can see exactly what you changed and what you didn't. This is your code review, your audit trail, and your portable patch file all in one.

**When to use it:** Before committing a tweak (to review your work), or anytime you want to see the cumulative effect of all your changes.

---

#### `export` — Backup Your Work

**What it does:** Takes every commit you've made on the "my-patches" branch and exports each one as a standalone `.patch` file. These files are:

- **Portable**: you can email them, put them on a USB stick, put them in Google Drive
- **Standard format**: any git user in the world can apply them with `git am` or `patch -p1`
- **Re-importable**: on another machine, they can be applied to a fresh Firefox tree
- **Human-readable**: they contain the diff and your commit message, so you can read them in any text editor

**Analogy:** After finishing renovations, you write up a renovation report: "I changed the kitchen, I changed the bathroom, I changed the living room." Each page of the report describes one room's changes. You can hand this report to another renovator working on a similar house, and they can replicate your work.

**When to use it:** Periodically as a backup. Definitely before trying an upgrade or rebase. Also when sharing your work with others.

---

#### `upgrade` — Move To A New Firefox Version

**What it does:** This is the most powerful command. When Firefox 155 comes out:

1. You download the new source tree
2. Run `upgrade --new-source ~/firefox-155 --new-tag firefox-155-upstream`
3. The tool imports the new source as a new pristine baseline
4. Then it **rebases** your patch branch onto the new baseline

The rebase is where the magic happens. Git takes your 158 commits, one at a time, and tries to apply each one to the new code. Three things can happen:

| Situation | What git does | What you do |
|-----------|---------------|-------------|
| The file hasn't changed upstream | Applies your tweak automatically | Nothing |
| The file changed upstream but your tweak is in a different part | Applies your tweak automatically (3-way merge) | Nothing |
| The file changed upstream AND your tweak is in the same area | Pauses and asks you to resolve | Edit the conflicted file, `git add`, `git rebase --continue` |

**Analogy:** You're a translator who translated a novel into another language. The author releases a new edition with some chapters rewritten. Instead of retranslating the whole novel from scratch, you feed your translation and the new edition into a smart assistant that copies your translations for unchanged chapters automatically, and only brings the changed chapters to your desk for re-translation. You handle them one at a time while the assistant holds the rest.

**When to use it:** Once per new Firefox version (quarterly, annually — however often Mozilla releases).

---

#### `preflight` — Check For Known Issues

**What it does:** Runs `preflight-clang21.py`, which is a separate script that checks for known breakage patterns specific to building Firefox with Clang 21 (the compiler we use). It doesn't fix anything — it just reports what it finds.

**Analogy:** Before starting your car, you walk around it and check: are the tires inflated? Are there any puddles underneath? Is the windshield cracked? The preflight check does this for your source tree.

**When to use it:** Before every `build` command. It catches issues in seconds that would otherwise take hours to diagnose from build errors.

---

#### `verify` — Confirm Everything Is In Place

**What it does:** Runs a series of checks from `MAP_IBM.md` that confirm all the critical tweaks are present in the built tree. For example:

- GPU unlock: checks that `GfxInfo.cpp` contains `return FEATURE_STATUS_OK`
- Telemetry kill: checks that the 60-year timer (`1893456000`) is present in the Normandy and Nimbus files
- Branding: checks that `brand.ftl` contains "Gorilla"
- Remote locks: checks that `TRIPLE_LOCKED` is present in Marionette and RemoteAgent

**Analogy:** After renovation, you walk through the house with a checklist: kitchen faucet works? Bathroom door locks? Living room lights on? This is that checklist.

**When to use it:** After a successful build, before declaring the migration complete.

---

## PART FOUR: THE WORKFLOW IN PRACTICE

### A Step-By-Step Walkthrough

Here is the complete process from start to finish, with every command you would run:

#### Step 0: Prepare (one-time)

```bash
# Download fresh Firefox 154 source
# ... (download to ~/firefox-source)

# Verify the tree exists
ls ~/firefox-source/mach    # should show the mach build script
```

#### Step 1: Initialise git

```bash
cd ~/Documents/FIrefox.154.Work/patches/FIrefox154.work.scripts
python3 patch_manager.py --source ~/firefox-source init
```

**Output:**
```
🦍 Initialising git in /home/gorilla/firefox-source
============================================================
  ℹ️  Running git init...
  ℹ️  Adding all files (this may take a minute for a Firefox tree)...
  ℹ️  Committing pristine upstream tree...
  ✅ Pristine tree committed
  ℹ️  Creating tag 'firefox-154-upstream'...
  ✅ Tagged as 'firefox-154-upstream'
  ℹ️  Creating branch 'my-patches'...
  ✅ On branch 'my-patches' — ready for patches
  ℹ️  Copied preflight-clang21.py to source tree
```

#### Step 2: Start porting files (one at a time)

Start with the safe categories (CSS, JSON, static assets) and work up to the risky ones (C++ with API churn):

```bash
# Safe: static assets (CSS, PNG, TTF — no compilation risk)
python3 patch_manager.py --source ~/firefox-source port \
  --category 08.Look --file master-redirect.css --commit
python3 patch_manager.py --source ~/firefox-source port \
  --category 08.Look --file activity-stream.css --commit
# ... one file at a time

# Then: JS modules (no compilation, but functional logic)
python3 patch_manager.py --source ~/firefox-source port \
  --category 09.REMOTE --file Marionette.sys.mjs --commit

# Then: low-risk C++ (GPU — 4 files, small)
python3 patch_manager.py --source ~/firefox-source port \
  --category 02.GPU --file GfxInfo.cpp --commit

# Build after each C++ category to catch errors early:
python3 patch_manager.py --source ~/firefox-source build

# Finally: high-risk C++ (networking — API churn landmine)
python3 patch_manager.py --source ~/firefox-source port \
  --category 03.NETWORKING --file nsSocketTransport2.cpp
# ^ NOTE: no --commit here — review first, because this file has API churn
# Edit the file manually to adapt your tweak to the new upstream APIs
git diff                    # review your changes
git add netwerk/base/nsSocketTransport2.cpp
git commit -m "Port nsSocketTransport2.cpp: 64MB socket buffer (adapt to new upstream)"
```

#### Step 3: Check progress

```bash
python3 patch_manager.py --source ~/firefox-source status
```

**Output:**
```
🦍 _patch Manager Status
============================================================
  ℹ️  Source directory : /home/gorilla/firefox-source
  ℹ️  Current branch    : my-patches
  ℹ️  Pristine tag      : firefox-154-upstream
  ℹ️  Tag exists        : yes
  ℹ️  Commits ahead     : 42
  ℹ️  Uncommitted files : 0 (clean working tree)
  ℹ️  Ported files      : 42
    [committed] 08.Look/master-redirect.css
    [committed] 08.Look/activity-stream.css
    [committed] 09.REMOTE/Marionette.sys.mjs
    [committed] 02.GPU/GfxInfo.cpp
    ...
  ℹ️  Last build        : PASS (2026-07-12 14:30:00)
```

#### Step 4: Build and iterate

```bash
python3 patch_manager.py --source ~/firefox-source build
```

If the build fails, the output tells you which file has the error and which commit last touched it:

```
❌ BUILD FAILED — 4 errors
  HttpChannelParent.cpp:731:8: error: no matching function for call to 'NS_LinkRedirectChannels'
  ...

  Last commits touching failing files:
  netwerk/protocol/http/HttpChannelParent.cpp
    -> a3b2c1d9 Port 03.NETWORKING: HttpChannelParent.cpp (adapt to new NS_LinkRedirectChannels signature)
```

If you can't fix it quickly, roll back and move on:

```bash
python3 patch_manager.py --source ~/firefox-source rollback \
  --file netwerk/protocol/http/HttpChannelParent.cpp
# come back to it later
```

#### Step 5: Verify

```bash
python3 patch_manager.py --source ~/firefox-source verify
```

```
🦍 Running verification checks from MAP_IBM.md
============================================================
  ✅ GPU unlock (GfxInfo.cpp)
  ✅ Mozambique timer (RecipeRunner.sys.mjs)
  ✅ Mozambique timer (RemoteSettingsExperimentLoader.sys.mjs)
  ✅ Gorilla brand (brand.ftl)
  ✅ Remote triple-lock (Marionette)
  ✅ Remote triple-lock (RemoteAgent)
  ✅ Normandy disabled (policies.json)
  ✅ Telemetry lobotomy (firefox.js)

  ℹ️  Results: 8 passed, 0 failed
```

#### Step 6: Export backups

```bash
python3 patch_manager.py --source ~/firefox-source export --out ~/backups/gorilla-patches-2026-07-12
```

```
🦍 Exporting patch commits to /home/gorilla/backups/gorilla-patches-2026-07-12
============================================================
  ✅ Exported 158 patch files:
  0001-Port-08.Look-master-redirect.css.patch
  0002-Port-08.Look-activity-stream.css.patch
  ...
  0158-Port-01.MEDIA-AudioStream.cpp.patch
  ℹ️  These .patch files are portable — share, pipe, or re-import.
```

#### Step 7: When Firefox 155 lands (next year)

```bash
# Download Firefox 155 to ~/firefox-155
# ...

python3 patch_manager.py --source ~/firefox-source upgrade \
  --new-source ~/firefox-155 \
  --new-tag firefox-155-upstream
```

```
🦍 Upgrading to firefox-155-upstream
============================================================
  ℹ️  Switching to main branch...
  ℹ️  Replacing source tree with new Firefox source...
  ℹ️  Committing new pristine upstream...
  ✅ New upstream committed
  ✅ Tagged as 'firefox-155-upstream'
  ℹ️  Switching to 'my-patches' and rebasing onto 'firefox-155-upstream'...
  ⚠️  Rebase encountered conflicts. This is expected when upstream
  APIs changed. You need to resolve each conflict manually:

    1. Edit the conflicted file(s)
    2. git add <resolved-file>
    3. git rebase --continue
    4. Repeat until all commits are replayed
```

Git replays your 158 commits onto the new code. For the ~140 files that didn't change upstream, this is automatic. For the ~18 files that changed, git pauses and asks you to resolve each one. You resolve them one at a time, then continue. No more blind guessing about what went wrong.

---

## PART FIVE: WHY THIS IS BETTER THAN WHAT WE DID BEFORE

| Aspect | Old Approach (copy everything) | New Approach (git + patch_manager) |
|--------|--------------------------------|-----------------------------------|
| Failure granularity | All 158 files or nothing | One file at a time |
| Rollback | Restore original (if you kept it) | `git revert` or `git checkout pristine -- file` |
| Audit trail | "Which file did I change and when?" — you guess | `git log` shows every commit with timestamp and message |
| Build debugging | "18 errors? Where do I start?" | Last commit touching each failing file is shown |
| Upgrade to new FF | Start from scratch every time | Rebase replays most patches automatically |
| Stale-view re-edit bug | The exact bug that caused the 16-hour disaster | `git diff` always shows the true current state |
| Collaboration | "Trust me, I changed the right files" | Export `.patch` files, anyone can review and apply |
| Backup | "I hope my patches/ directory is safe" | `git format-patch` exports to a portable, format-independent backup |

---

## PART SIX: COMMON PITFALLS AND HOW TO AVOID THEM

### 1. The Stale-View Re-Edit Bug

**What happened:** In the 16-hour session, an AI assistant read a file, edited it, then edited it again based on its *memory* of what the file looked like before the first edit — not based on a fresh read. This silently reverted the first edit. The assistant then re-applied the same fix 3 more times throughout the session, each time believing it was new work.

**How this tool prevents it:** Every edit is a git commit. Before editing, run `git diff` to see the *actual* current state. After editing, commit immediately. If you re-read the file, you're reading the committed version, not a stale mental model.

### 2. The No-Op Edit

**What happened:** The assistant attempted an edit where the "before" text and the "after" text were byte-identical. The tool applied nothing. The assistant believed it had made a change and ran a build, wasting a full build cycle.

**How this tool prevents it:** `git diff` after staging shows whether anything actually changed. If the diff is empty, nothing was applied. Don't commit nothing.

### 3. The False "FIXED" Claim

**What happened:** The assistant wrote in a changelog that it had fixed a problem, then built, found the same error, and "fixed" it again — four times — without realising the first three "fixes" had never actually been applied to the source file.

**How this tool prevents it:** The journal (`.patch_manager_state.json`) records every `port` action with SHA-256 hashes before and after. If a file is "ported" but its hash doesn't change, that's flagged. The verify command checks the *actual file content* for expected patterns, not a changelog's claims about what was done.

### 4. Building Everything Before Testing Anything

**What happened:** The assistant applied dozens of changes, then built once. The build produced 18 errors across 4 files, with no way to know which change caused which error.

**How this tool prevents it:** The `build` command shows the last commit that touched each failing file. You build after each category (or each file for risky ones), so errors are isolated to one change.

### 5. Destroying History To "Fix" A Mistake

**What happened:** Various attempts to "undo" changes were made by overwriting files with old versions, making it impossible to know what the real state of the tree was at any point.

**How this tool prevents it:** `rollback --file` and `rollback --commit` both create new commits that *reverse* changes. The original is still in history. You can always see what was done, when, and by whom, and you can undo an undo.

---

## PART SEVEN: FILE LOCATIONS

| File | Location | Purpose |
|------|----------|---------|
| `patch_manager.py` | `patches/FIrefox154.work.scripts/` | This tool |
| `preflight-clang21.py` | `patches/FIrefox154.work.scripts/` | Clang 21 pre-flight checker |
| `old.patches/` | `patches/old.patches/` | Your old tweaked files (read-only reference) |
| `patches/` categories | `patches/01.MEDIA/`, `patches/02.GPU/`, etc. | Pristine upstream files (new copies) |
| `deploy.sh` | `patches/deploy.sh` | Original deployment script (legacy, kept for path mappings) |
| `.patch_manager_state.json` | `patches/FIrefox154.work.scripts/` | Journal of all actions |
| `build_logs/` | `patches/FIrefox154.work.scripts/build_logs/` | Saved build logs |

---

## PART EIGHT: TECHNICAL REFERENCE

### For The Developer

#### Architecture

`patch_manager.py` is a single-file Python 3 script (~700 lines) with no external dependencies beyond the standard library and git. It uses subcommands via `argparse` and communicates with git via `subprocess.run`.

The tool maintains a JSON journal (`.patch_manager_state.json`) recording every action taken, with timestamps. This journal is the regression-detection mechanism — if a file was previously "ported" and committed, but its current SHA-256 doesn't match the committed version, that's flagged as a regression.

#### Git Workflow

```
main ──────●─ firefox-154-upstream (tag)
            \
my-patches   ●──●──●──●──●──●  (one commit per ported file)
                            └── HEAD

main ──────●─ firefox-154-upstream
            \           \
my-patches   ●──●──●──●──●──    (rebased onto 155-upstream)
             \           \
              ────────────●─ firefox-155-upstream (tag)
```

Each "●" is a commit. The tag pins the pristine state. `my-patches` diverges from it one commit at a time. On upgrade, `my-patches` is rebased onto the new tag.

#### Deploy.sh Path Mappings

The tool parses `deploy.sh` to resolve category/filename to a path in the Firefox source tree. The parsing is line-based, looking for `deploy_file "$SRC/CATEGORY/FILE" "dest/path"`. This means `deploy.sh` remains the source of truth for file mappings, and any changes to it are automatically picked up.

#### State Journal Schema

```json
{
  "actions": [
    {"action": "init", "detail": "...", "ts": 1720800000},
    {"action": "port", "detail": "...", "ts": 1720800100}
  ],
  "ported_files": {
    "03.NETWORKING/nsSocketTransport2.cpp": {
      "old_sha256": "abc123...",
      "pristine_sha256": "def456...",
      "dest": "netwerk/base/nsSocketTransport2.cpp",
      "status": "committed",
      "ts": 1720800100
    }
  },
  "builds": [
    {
      "success": false,
      "errors": ["HttpChannelParent.cpp:731: error: ..."],
      "log": "/path/to/build.log",
      "ts": "2026-07-12 14:30:00"
    }
  ]
}
```

#### Known Limitations

1. **Port does not do semantic 3-way merge.** It copies the old patched file over the new pristine file and stages it. For files with upstream API churn, the user (or an AI agent) must manually adapt the tweaks before committing. A future version could use `git merge-file` for a proper 3-way merge, but this requires the old pristine base (which we don't have saved — only the old patched version).

2. **The `upgrade` command replaces the entire source tree.** If the new Firefox source has a different directory structure, the rebase will produce many conflicts. This is by design — it forces you to review each affected file rather than silently producing a broken tree.

3. **No parallel porting.** The tool is designed for sequential, one-file-at-a-time operation. This is intentional. Bulk operations are what caused the original disaster.

4. **No automatic Clang 21 fix-up during port.** The `preflight` command reports issues but does not auto-fix. Run it separately. Auto-fixing during port would mask merge errors.

---

## PART NINE: PREREQUISITES

- **Python 3.8+** (standard library only)
- **git 2.20+** (`apt install git` or `dnf install git`)
- **~20GB free disk space** for the Firefox source tree + git history
- **The Firefox source tree** downloaded and extracted
- **This tool and old.patches/** in the patches/ directory

---

## PART TEN: FAQ

### Q: Can I use this for a different browser (Chromium, etc.)?

A: Yes, with modifications. The path mappings in `deploy.sh` are Firefox-specific, but the git workflow (init, port, build, diff, export, upgrade) is generic. Replace the deploy.sh mappings with your project's file paths and it works.

### Q: What if I accidentally delete .git?

A: Your pristine tag is gone, but your patches are still in `old.patches/`. Re-run `init` to recreate the git repo. Your commits are lost, but you can re-port from `old.patches/`. This is why `export` exists — export your patches frequently so you have a backup outside the git repo.

### Q: The build is failing and I don't know why. Can this tool help?

A: Run `build` — it shows you the last commit that touched each failing file. Use `diff --file` to see exactly what that commit changed. Use `rollback --file` to restore the pristine version, build again, and confirm the rest is clean. Then come back to the problematic file.

### Q: Can I use this without the old.patches directory?

A: `init`, `status`, `build`, `diff`, `export`, `upgrade`, `preflight`, and `verify` all work without `old.patches/`. Only `port` requires it. If you're starting fresh and want to write your tweaks from scratch, you don't need `old.patches/` at all — just edit files in the source tree and commit directly with git.

### Q: Why not just use git directly without this script?

A: You can. This script is a convenience that:
- Parses `deploy.sh` for file mappings
- Runs preflight and verify checks
- Journals every action for regression detection
- Parses build output and maps errors to commits
- Provides a single entry point with help text

If you're comfortable with git, you can do everything this script does manually. The script exists because the disaster we're trying to prevent happened precisely because someone was *not* systematically using git.

### Q: What about the `06.QUOTA` category?

A: `06.QUOTA` is listed as an empty placeholder in `MAP_IBM.md`. If you add files to it in the future, `port` will work as long as the file mapping exists in `deploy.sh` or the file can be found in the source tree.

---

## DOCUMENT HISTORY

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-12 | Gorilla | Initial version, written to support the patch_manager.py workflow |

---

*This document is written in the spirit of the Gorilla Open Source Philosophy: dual-track documentation that is complete and honest for both the layperson and the developer. If something in this document is unclear to you, that is a bug in this document, not a deficiency in your knowledge. Report it.*

---

**END OF DOCUMENT**
