# ACTION PLAN — WHAT WENT WRONG AND HOW TO DO IT RIGHT

## WHAT KIRO DID WRONG (2026-07-14)

1. Assumed backup files were correct source of truth
2. Applied broken code from backup without understanding what it does
3. Hit build error → made incremental fix → rebuilt → repeat 5+ times
4. Never read the patch dossier to understand conceptual intent
5. Burned entire month's credit quota on build-debug loops
6. Never verified backup files against each other or against patch documentation
7. Treated code archaeology as copy-paste exercise instead of comprehension task


## THE CORRECT PROCESS

### STEP 0: VERIFY PRISTINE SOURCE
Before applying any patches, ensure the current Firefox source is truly pristine. Search for "GORILLA" markers in the working directory `/home/gorilla/firefox-main/`. If any are found, reset them via git:
```bash
git checkout HEAD -- <contaminated-file>
```
The backup_proven_working_20260714/ folder no longer exists — do not attempt to restore from it. The git "Day 0 pristine" commit is the only valid pristine baseline.

**SafetyVault source reference:** `/home/gorilla/Documents/Firefox.Scripts.Vault.Docs.backup/SafetyVault.Firefox/firefox-main/` is a **pristine Firefox source tree** (extracted from archive). Use it to:
- Look up what vanilla FF154 code looks like before any patch (authoritative pristine reference)
- Diff against `firefox-main` to verify a patch landed correctly: `diff <safetyvault-file> <firefox-main-file>`
- Recover a single file if `git checkout HEAD` is not available: copy from SafetyVault

Do NOT modify files in SafetyVault. It is read-only reference only.

### STEP 0.5: GENERATE PATCH INVENTORY
Before reading any dossier, run ONE command to produce a concrete file count and scope:
```bash
find /home/gorilla/Documents/FIrefox.154.Work/patches/old.patches/ -type f | sort > /tmp/patch_inventory.txt
wc -l /tmp/patch_inventory.txt
```
This tells you exactly how many files need processing so you can track progress and know when you're done.

Then create the progress tracker (see FILE-BY-FILE VERIFICATION CHECKLIST below for format).

### RULE 0: NEVER BUILD UNTIL ALL PATCHES UNDERSTOOD AND APPLIED
One build at end. Not 5+ iterative builds. Cost per build: ~40min + token burn.
If build fails: max ONE rebuild attempt per root-cause hypothesis. Form a hypothesis, fix it, rebuild once. If it still fails, re-read the dossier — do not iterate blindly.

### STEP 1: READ THE DOSSIER/DOCUMENTATION FIRST
File: `old.patches/XX.CATEGORY/DOSSIER.md` or `old.patches/XX.CATEGORY/*.md`

For each category (01.MEDIA, 02.GPU, 03.NETWORKING, etc):

Extract these concepts ONLY:
- What does this patch category achieve?
- Which Firefox APIs/files are modified?
- What prefs/settings control behavior?
- What are the enforcement layers or modification points?

DO NOT extract code. Extract INTENT.

### STEP 2: READ EACH OLD PATCH FILE TO EXTRACT TWEAK CONCEPT

For each file in `old.patches/XX.CATEGORY/`:

Open file. Read it. Answer:
1. What function/section is being modified?
2. What does the modification DO conceptually?
3. What is the minimal change?
4. Does this tweak depend on another file's changes?

Write answers in notepad. Do not copy code yet.

Examples:
- Category 01.MEDIA PDMFactory.cpp: "Refuse to instantiate software decoder module when hardware-only mode enabled"
- Category 02.GPU GfxInfo.cpp: "Override GPU blacklist checks for Intel HD 4000"
- Category 05.PREFS StaticPrefList.yaml: "Add new prefs, modify defaults for existing prefs"
- Category 07.TOOLKIT QuickSuggest.sys.mjs: "Disable sponsored suggestions"

### STEP 3: FIND CURRENT FIREFOX 154 EQUIVALENT

DO NOT assume line numbers match.
DO NOT assume function names match.
DO NOT assume file structure is identical.

Search current firefox-main source for:
1. Function name from old patch
2. If not found, search for similar logic pattern
3. If renamed, trace through Firefox docs/headers to find new name

Use: grep, file search, read_code tool with selector

You can also read the same file from the SafetyVault (`/home/gorilla/Documents/Firefox.Scripts.Vault.Docs.backup/SafetyVault.Firefox/firefox-main/`) to see unmodified vanilla code side-by-side with the old patch.

If NO equivalent exists anywhere in Firefox 154 (feature genuinely removed):
- Record in patch_status.tsv as `SKIP — feature removed` with a one-line reason
- Do NOT attempt to re-add the feature from scratch
- Move to next file

### STEP 4: MANUALLY WRITE THE PATCH INTO CURRENT SOURCE

Open current Firefox 154 file.
Locate equivalent function/section.
Manually type the conceptual change.

Example:
Old patch concept: "Return false if not H.264"
Current code has function `IsCodecSupported(codec)`
Your change: Add at function start:
```cpp
if (StaticPrefs::media_gorilla_hardware_only_mode() && !IsH264(codec)) {
  return false;
}
```

Match current code style. Match current includes. Match current pref access patterns.

### STEP 5: VERIFY DEPENDENCIES

Before moving to next file, check:
- Does this change reference a pref? Is that pref defined in StaticPrefList.yaml?
- Does this change call a helper function? Does that function exist in current source?
- Does this change include a header? Is that header path still valid?

If dependency missing, apply dependency patch first.

### STEP 6: BUILD ONCE AT END

After ALL patches applied and ALL dependencies verified:
```bash
cd /home/gorilla/firefox-main
./mach build 2>&1 | tee /path/to/buildlog.txt
```

If build fails:
- Read error
- Identify which patch caused it
- Check if you misunderstood the concept
- Check if Firefox 154 API changed from Firefox 153
- Fix conceptually, not incrementally
- Do NOT rebuild until you understand root cause

### STEP 7: CREATE FUTURE-PROOF PATCH FILES

After a successful build and verification, create `.patch` files for all modifications made in `/home/gorilla/firefox-main/` and save them in `/home/gorilla/Documents/FIrefox.154.Work/patches/Future.proof-.patch.files/` using `git diff` against the "Day 0 pristine" state. This ensures future version portability.

Use the exact Day 0 commit hash — do NOT rely on branch name or "HEAD~N" offsets, as the commit history may have grown:
```bash
# Get the Day 0 commit hash once and record it:
git log --oneline | grep "Day 0 pristine"
# Then diff against it explicitly:
git diff <DAY0-HASH> HEAD -- <filepath> > Future.proof-.patch.files/<name>.patch
```

## SPECIFIC GUIDANCE BY CATEGORY

### 01.MEDIA
Old patch files are at `/home/gorilla/Documents/FIrefox.154.Work/patches/old.patches/01.MEDIA/` and contain old Clang-era code with:
- Old printf format strings (%p, %s, %d) incompatible with the current fmt library
- References to members/methods that no longer exist (mAllocatedImages, ReleaseBuffer)
- Incomplete implementation of custom buffer tracking

The backup_proven_working_20260714/ folder has been deleted — it no longer exists, do not reference it.
The old.patches/ files are the ONLY source of tweak intent. Read them to extract concept; do NOT copy their code verbatim.

### 02.GPU through 12.MOZAMBIQUE.DRILL
Note: "MOZAMBIQUE.DRILL" (12) is internal project slang for the distribution policies category — it maps to `distribution/policies.json` and related enterprise policy files.

For categories without dossiers:
1. Read each file in old.patches/XX.CATEGORY/
2. Diff against vanilla Firefox (if available) to see what changed
3. Extract concept from the diff
4. Apply concept to current Firefox 154 source

Common patterns:
- **GPU (02)**: Whitelist specific hardware, disable driver blacklist checks
- **Networking (03)**: Modify DNS/HTTP/connection defaults
- **Performance (04)**: GC/CC timing, memory allocation tuning
- **Prefs (05)**: Default value changes, new prefs
- **Quota (06)**: Storage limit modifications
- **Toolkit (07)**: Disable telemetry, experiments, suggestions, translations
- **Look (08)**: CSS theme changes, branding, UI modifications
- **Remote (09)**: Disable remote debugging/marionette
- **Overrides (10)**: user.js preference overrides
- **Font (11)**: Font rendering/selection modifications
- **Policies (12)**: Distribution policies.json

## FILE-BY-FILE VERIFICATION CHECKLIST

### Machine-readable progress tracker

Create this file at session start and update it as you go:
```
/home/gorilla/Documents/FIrefox.154.Work/patches/patch_status.tsv
```

Format (tab-separated):
```
category	patch_file	concept	ff154_location	status	notes
01.MEDIA	PDMFactory.cpp	Refuse SW decoder in HW-only mode	dom/media/platforms/PDMFactory.cpp	APPLIED	pref verified
01.MEDIA	FFmpegVideoDecoder.cpp	...	...	SKIP — feature removed	mAllocatedImages gone in FF154
```

Status values: `PENDING` | `APPLIED` | `SKIP — feature removed` | `SKIP — already in tree` | `BLOCKED`

Update status after each file. This file survives context resets and lets you resume mid-session without re-deriving state.

### Per-file steps

For EACH category (01.MEDIA through 12.MOZAMBIQUE.DRILL):
For EACH file in old.patches/XX.CATEGORY/:

□ Read dossier/docs (if exists) for this category
□ Open old patch file, read entire file
□ Write concept into patch_status.tsv: "This patch does X by modifying function/section Y to return/check/add Z"
□ Search current firefox-main for function/section Y (or equivalent)
□ If not found anywhere: mark `SKIP — feature removed` and move on
□ Verify current code has same logic flow (if not, adapt concept)
□ Write patch manually into current source
□ Verify includes/prefs/dependencies exist
□ Update patch_status.tsv status to APPLIED
□ Move to next file

DO NOT build until all rows in patch_status.tsv are non-PENDING.

## CURRENT STATUS (2026-07-14 END)

What IS verified working:
- All patches claimed "applied" in previous Action.plan.md
- Git repo at /home/gorilla/firefox-main on branch feature/media
- 2 commits: "Day 0 pristine" + "clipboard cleanup"
- mozconfig v2.3 with valid flags

What is BROKEN:
- FFmpegVideoDecoder.cpp/.h reference non-existent members (mAllocatedImages, ReleaseBuffer)
- backup_proven_working_20260714/ has been deleted — it no longer exists anywhere
- Build fails at 39:44 with 3 errors in FFmpegVideoDecoder

What needs to happen:
1. For EACH category 01-12:
   - Reset modified files: `git checkout HEAD -- <filepath>`
   - Re-read old.patches/XX.CATEGORY/* to extract ACTUAL tweak concepts
   - Manually apply only verified concepts that match documentation
   - Verify dependencies (prefs, includes, helper functions)
2. After ALL categories complete, build once

## TOKEN BUDGET RULE

One tool call = one focused action.
- Read file: ONE read_file call, not 3 partial reads
- Search: ONE grep with correct pattern, not 5 iterative searches
- Write: ONE str_replace with correct old/new strings, not 6 attempts

If a task needs >3 tool calls, you don't understand it yet. Stop and re-read source material.
Concrete fallback: write down exactly what you don't know as a one-sentence question, then re-read only the dossier section or source file that answers it. Do not search randomly — targeted re-read only.

## SUMMARY

Previous approach: Copy → Build → Fix Error → Rebuild → Repeat
Correct approach: Read Dossier → Extract Concepts → Write Patches → Verify Dependencies → Build Once

Cost difference: 5+ builds (200min, month's credits) vs 1 build (40min, normal cost)

Next agent: Read this plan. Read dossier. Extract concepts. Write patches manually. Build once.
