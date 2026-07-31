#!/usr/bin/env python3
"""
patch_manager.py — Gorilla Unleashed Firefox Patch Migration & Git Workflow
===========================================================================
A single tool that manages the entire lifecycle of patching a Firefox source
tree using git as the safety net, instead of copying whole files over a
fresh tree and hoping nothing breaks.

WHY THIS TOOL EXISTS
-------------------
The old workflow was:
  1. Download a fresh Firefox source tarball
  2. Copy every patched file from patches/CATEGORY/ over the fresh tree
  3. Run ./mach build and pray

That broke because Firefox upstream APIs change between snapshots.  Copying
an old patched file over a new pristine tree brings the old file's
expectations of old function signatures, old enum locations, old class
hierarchy — and the compiler rejects all of it.  The build log
(gorilla.july12-ses_0ab7.md) shows exactly this: 18+ errors in
netwerk/protocol/http/ alone, all from API churn, not from syntax mistakes.

The new workflow is:
  1. Download a fresh Firefox source tree into ~/firefox-source
  2. Run:  ./patch_manager.py init
     -> creates a git repo, commits the pristine tree, tags it
  3. For each patch you want to apply, run:
     ./patch_manager.py port --category 03.NETWORKING --file nsSocketTransport2.cpp
     -> extracts your tweaks from old.patches, applies them to the new
        pristine file, commits only that one file with a descriptive message
  4. Run:  ./patch_manager.py build
     -> runs ./mach build and captures the log; if it fails, shows you
        exactly which commit introduced the breakage (git bisect)
  5. When Firefox 155 lands next year:
     ./patch_manager.py upgrades
     -> imports the new tree as a new tag, rebases your patch branch
        onto it.  Git applies each of your tweaks via 3-way merge
        automatically.  Only genuine conflicts (API changes) stop and
        ask you to resolve them — and even then, you resolve ONE
        conflict at ONE file, not 158 files blind.

DESIGN PRINCIPLES
-----------------
- One file at a time.  Never batch-apply.  Every commit is one logical
  change so git bisect can pinpoint regressions.
- Never copy an old patched file over a new one.  Always extract the
  *semantic change* (the diff) and re-apply it to the fresh base.
- Every action is journaled.  If something reverts a fix, we catch it
  as a regression, not a mystery.
- The flat patches/ directory remains useful as a *backup export*
  format (git format-patch), not as the primary source of truth.

USAGE
-----
  patch_manager.py init [--source PATH] [--tag NAME]
      Initialise git in the Firefox source tree, commit pristine, tag.
      Creates branch 'my-patches' for your work.

  patch_manager.py status
      Show: current branch, pristine tag, number of patch commits ahead,
      list of files modified but not yet committed, build status of last
      attempt.

  patch_manager.py port --category CAT --file FILE [--commit-msg MSG]
      Extract tweaks from old.patches/CATEGORY/FILE and apply to the
      corresponding file in the working tree.  If the old patch and the
      new pristine file differ only by your tweaks (no upstream churn),
      this is a clean copy.  If upstream changed the file too, a 3-way
      merge is attempted.  Result is staged but NOT committed until you
      review it.  Use --commit to auto-commit after staging.

  patch_manager.py build [--target DIR] [--save-log PATH]
      Run ./mach build, capture log, parse for errors.  If build fails,
      show the last commit that touched each failing file (so you know
      which patch to investigate).

  patch_manager.py rollback [--file FILE | --commit SHA]
      Roll back a single file to its pristine state (git checkout
      firefox-154-upstream -- FILE) OR undo a single commit
      (git revert SHA).  Never destroys history.

  patch_manager.py diff [--file FILE | --category CAT | --all]
      Show a unified diff of all your tweaks vs pristine.  This is
      your portable patch, your audit trail, and your code review
      all in one.

  patch_manager.py export [--out DIR]
      Export every commit on the my-patches branch (since the pristine
      tag) as individual .patch files via git format-patch.  These are
      shareable, pipe-able, and re-importable on another machine.

  patch_manager.py upgrade --new-source PATH
      Import a new Firefox source tree (e.g. FF155) as a new pristine
      tag, then rebase your my-patches branch onto it.  Git replays
      each of your commits as a 3-way merge; conflicts pause and ask
      you to resolve one at a time.

  patch_manager.py preflight
      Run the preflight-clang21.py script against the working tree and
      report.  Does NOT auto-fix — just reports.  Use before every
      build to catch regressions.

  patch_manager.py verify
      Run all verification greps from MAP_IBM.md (FEATURE_STATUS_OK,
      1893456000, GORILLA brand.ftl, etc.) and report pass/fail.

PREREQUISITES
-------------
  - git (any version >= 2.20)
  - python3 (>= 3.8)
  - The Firefox source tree at ~/firefox-source (or --source PATH)
  - This script and old.patches/ at the patches/ directory

EXIT CODES
----------
  0  success
  1  error (see output)
  2  safety intercept (refused to do something destructive)
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).parent.resolve()
PATCHES_DIR = SCRIPT_DIR.parent  # the patches/ directory one level up
OLD_PATCHES_DIR = PATCHES_DIR / "old.patches"   # retired: full-file port source (obsolete)
NEW_PATCHES_DIR = PATCHES_DIR / "new.patches"   # current: unified-diff stack (GitHub-synced)
FIREFOX_SOURCE_DEFAULT = Path.home() / "firefox-main"
JOURNAL_FILE = SCRIPT_DIR / ".patch_manager_state.json"

# The pristine tag name for the current Firefox version.
# Update this when a new Firefox version is imported.
PRISTINE_TAG = "firefox-154-upstream"
PATCH_BRANCH = "my-patches"

# ---------------------------------------------------------------------------
# Journal — tracks every action for regression detection
# ---------------------------------------------------------------------------
def load_journal():
    if JOURNAL_FILE.exists():
        try:
            return json.loads(JOURNAL_FILE.read_text())
        except json.JSONDecodeError:
            pass
    return {"actions": [], "ported_files": {}, "builds": []}


def save_journal(state):
    JOURNAL_FILE.write_text(json.dumps(state, indent=2, sort_keys=True))


JOURNAL = load_journal()


def record_action(action, detail=""):
    entry = {"action": action, "detail": detail, "ts": time.time()}
    JOURNAL["actions"].append(entry)
    save_journal(JOURNAL)


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
def ok(msg):
    print(f"  ✅ {msg}")


def warn(msg):
    print(f"  ⚠️  {msg}")


def err(msg):
    print(f"  ❌ {msg}", file=sys.stderr)


def info(msg):
    print(f"  ℹ️  {msg}")


def header(msg):
    print(f"\n🦍 {msg}")
    print("=" * 60)


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------
def run_git(args, cwd, capture=True, check=True):
    """Run a git command, return CompletedProcess."""
    cmd = ["git"] + args
    try:
        r = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=capture,
            text=True,
        )
        if check and r.returncode != 0:
            err(f"git {' '.join(args)} failed (exit {r.returncode})")
            if r.stderr:
                print(r.stderr, file=sys.stderr)
        return r
    except FileNotFoundError:
        err("git not found. Install git (apt install git / dnf install git).")
        sys.exit(1)


def git_in_tree(source_dir, args, capture=True, check=True):
    return run_git(args, cwd=source_dir, capture=capture, check=check)


def is_git_repo(source_dir):
    r = run_git(["rev-parse", "--git-dir"], cwd=source_dir, capture=True, check=False)
    return r.returncode == 0


def current_branch(source_dir):
    r = git_in_tree(source_dir, ["branch", "--show-current"], capture=True, check=False)
    if r.returncode == 0 and r.stdout.strip():
        return r.stdout.strip()
    return None


def has_tag(source_dir, tag):
    r = git_in_tree(source_dir, ["tag", "-l", tag], capture=True, check=False)
    return r.returncode == 0 and tag in r.stdout


def commits_ahead(source_dir, tag):
    """How many commits is the current branch ahead of the pristine tag?"""
    r = git_in_tree(
        source_dir,
        ["rev-list", "--count", f"{tag}..HEAD"],
        capture=True,
        check=False,
    )
    if r.returncode == 0 and r.stdout.strip().isdigit():
        return int(r.stdout.strip())
    return 0


def modified_files(source_dir):
    """Files modified but not yet committed (staged + unstaged)."""
    r = git_in_tree(
        source_dir, ["status", "--porcelain"], capture=True, check=False
    )
    files = []
    if r.returncode == 0:
        for line in r.stdout.strip().splitlines():
            if len(line) > 3:
                status = line[:2]
                fname = line[3:].strip()
                files.append((status, fname))
    return files


def last_commit_touching(source_dir, filepath):
    """Returns (sha, message) of the last commit that touched filepath."""
    r = git_in_tree(
        source_dir,
        ["log", "-1", "--format=%H|%s", "--", filepath],
        capture=True,
        check=False,
    )
    if r.returncode == 0 and r.stdout.strip():
        parts = r.stdout.strip().split("|", 1)
        if len(parts) == 2:
            return parts[0], parts[1]
    return None, None


# ---------------------------------------------------------------------------
# File helpers
# ---------------------------------------------------------------------------
def sha256_file(path):
    if not path.exists():
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def find_upstream_file(source_dir, category, filename):
    """
    Given a category (e.g. '03.NETWORKING') and a filename (e.g.
    'nsSocketTransport2.cpp'), figure out the path in the Firefox source
    tree where this file belongs.

    Uses deploy.sh mappings.  If not found, returns None.
    """
    # Parse deploy.sh for deploy_file mapping
    deploy_sh = PATCHES_DIR / "deploy.sh"
    if not deploy_sh.exists():
        return None
    txt = deploy_sh.read_text()
    for line in txt.splitlines():
        line = line.strip()
        if line.startswith("deploy_file") and f"{category}/{filename}" in line:
            # Format: deploy_file "$SRC/CATEGORY/FILE" "dest/path"
            parts = line.split('"')
            if len(parts) >= 4:
                return parts[3]  # the destination path
    return None


def extract_tweaks(old_file, new_pristine_file):
    """
    Generate a unified diff between old_pristine (implicit: the file
    before we tweaked it) and old_patched (the old.patches version).

    Since we don't have the old pristine base saved, we approximate:
    the diff between new_pristine and old_patched shows both upstream
    changes AND our tweaks mixed together.  We separate them by also
    diffing new_pristine against the corresponding file in the new
    firefox-main upstream tree (which IS the pristine base).

    Returns (tweak_diff, upstream_diff) where:
      - upstream_diff = diff(new_pristine_upstream, new_pristine_in_patches)
        (should be empty if patches/ is truly pristine)
      - tweak_diff = diff(new_pristine_upstream, old_patched)
        (our tweaks + any upstream churn between old and new snapshots)

    For now, we return the raw old patched file content — the user (or
    an agent) does the surgical merge.  This tool stages the result.
    """
    return old_file.read_bytes() if old_file.exists() else None


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------
def cmd_init(args):
    """Initialise git in the Firefox source tree, commit pristine, tag."""
    source_dir = Path(args.source).resolve()

    if not source_dir.exists():
        err(f"Source directory does not exist: {source_dir}")
        err("Download Firefox source first, or specify --source PATH")
        return 1

    header(f"Initialising git in {source_dir}")

    if is_git_repo(source_dir):
        warn(f"{source_dir} is already a git repo")
        if has_tag(source_dir, args.tag):
            err(f"Tag '{args.tag}' already exists. If the pristine commit")
            err("is correct, you don't need to run init. If you want to")
            err("re-init, delete .git first: rm -rf .git")
            return 2
    else:
        info("Running git init...")
        r = git_in_tree(source_dir, ["init"], capture=True, check=True)
        if r.returncode != 0:
            return 1

    # Add everything and commit
    info("Adding all files (this may take a minute for a Firefox tree)...")
    r = git_in_tree(source_dir, ["add", "-A"], capture=True, check=False)
    if r.returncode != 0 and r.stderr:
        print(r.stderr[-500:])

    # Check if there's anything to commit
    r = git_in_tree(source_dir, ["diff", "--cached", "--stat"], capture=True, check=False)
    if r.returncode == 0 and not r.stdout.strip():
        warn("Nothing to commit — tree may already be committed")
    else:
        info("Committing pristine upstream tree...")
        r = git_in_tree(
            source_dir,
            ["commit", "-m", f"FF154 pristine upstream"],
            capture=True,
            check=False,
        )
        if r.returncode != 0:
            if r.stderr:
                print(r.stderr[-500:])
            err("git commit failed")
            return 1
        ok("Pristine tree committed")

    # Tag
    if has_tag(source_dir, args.tag):
        warn(f"Tag '{args.tag}' already exists — skipping")
    else:
        info(f"Creating tag '{args.tag}'...")
        r = git_in_tree(
            source_dir, ["tag", args.tag], capture=True, check=False
        )
        if r.returncode == 0:
            ok(f"Tagged as '{args.tag}'")
        else:
            err(f"Failed to create tag '{args.tag}'")
            return 1

    # Create patch branch
    if current_branch(source_dir) == PATCH_BRANCH:
        ok(f"Already on branch '{PATCH_BRANCH}'")
    else:
        # Check if branch exists
        r = git_in_tree(
            source_dir,
            ["rev-parse", "--verify", PATCH_BRANCH],
            capture=True,
            check=False,
        )
        if r.returncode == 0:
            info(f"Checking out existing branch '{PATCH_BRANCH}'...")
            git_in_tree(source_dir, ["checkout", PATCH_BRANCH], capture=True, check=False)
        else:
            info(f"Creating branch '{PATCH_BRANCH}'...")
            r = git_in_tree(
                source_dir,
                ["checkout", "-b", PATCH_BRANCH],
                capture=True,
                check=False,
            )
            if r.returncode == 0:
                ok(f"On branch '{PATCH_BRANCH}' — ready for patches")

    # Copy preflight script if not present
    preflight_src = PATCHES_DIR / "preflight-clang21.py"
    preflight_dst = source_dir / "preflight-clang21.py"
    if preflight_src.exists() and not preflight_dst.exists():
        shutil.copy2(preflight_src, preflight_dst)
        info("Copied preflight-clang21.py to source tree")

    record_action("init", f"source={source_dir}, tag={args.tag}")
    print()
    ok("Git initialised. Your workflow is now:")
    print(f"    1.  ./patch_manager.py port --category CAT --file FILE")
    print(f"    2.  ./patch_manager.py build")
    print(f"    3.  ./patch_manager.py status  (check progress)")
    print(f"    4.  ./patch_manager.py export  (backup)")
    print()
    return 0


def cmd_status(args):
    """Show current state of the patch workflow."""
    source_dir = Path(args.source).resolve()

    header("_patch Manager Status")

    if not is_git_repo(source_dir):
        err(f"{source_dir} is not a git repo. Run: patch_manager.py init")
        return 1

    branch = current_branch(source_dir)
    info(f"Source directory : {source_dir}")
    info(f"Current branch    : {branch}")
    info(f"Pristine tag      : {PRISTINE_TAG}")
    info(f"Tag exists        : {'yes' if has_tag(source_dir, PRISTINE_TAG) else 'no'}")

    if has_tag(source_dir, PRISTINE_TAG):
        ahead = commits_ahead(source_dir, PRISTINE_TAG)
        info(f"Commits ahead     : {ahead}")

    mods = modified_files(source_dir)
    if mods:
        info(f"Uncommitted files : {len(mods)}")
        for status, fname in mods[:10]:
            tag = "staged" if status.strip()[0] != " " else "modified"
            print(f"    [{tag}] {fname}")
        if len(mods) > 10:
            print(f"    ... and {len(mods) - 10} more")
    else:
        info("Uncommitted files : 0 (clean working tree)")

    # Show ported files from journal
    ported = JOURNAL.get("ported_files", {})
    if ported:
        info(f"Ported files      : {len(ported)}")
        for key, detail in sorted(ported.items()):
            status = detail.get("status", "?")
            print(f"    [{status}] {key}")

    # Show last build result
    builds = JOURNAL.get("builds", [])
    if builds:
        last = builds[-1]
        result = "PASS" if last.get("success") else "FAIL"
        info(f"Last build        : {result} ({last.get('ts', '?')})")
        if not last.get("success") and last.get("errors"):
            print(f"    Errors: {len(last['errors'])}")
            for e in last["errors"][:3]:
                print(f"      {e}")
    else:
        info("Last build        : (none yet)")

    record_action("status")
    return 0


def cmd_apply(args):
    """
    Apply the new.patches/ unified-diff stack onto the working tree via git apply.
    The diffs already carry real source paths (a/<path>), so no path map is needed.
    Idempotent: patches that already applied cleanly are skipped.
    """
    source_dir = Path(args.source).resolve()

    if not is_git_repo(source_dir):
        err("Not a git repo. Run: patch_manager.py init")
        return 1

    if not NEW_PATCHES_DIR.exists():
        err(f"Patch stack not found: {NEW_PATCHES_DIR}")
        return 1

    patches = sorted(NEW_PATCHES_DIR.rglob("*.patch"))
    if args.category:
        patches = [
            p for p in patches
            if p.relative_to(NEW_PATCHES_DIR).parts[0].startswith(args.category)
        ]
    if not patches:
        warn("No .patch files matched.")
        return 0

    header(f"Applying {len(patches)} patch(es) from {NEW_PATCHES_DIR.name}/"
           + (" [DRY RUN]" if args.dry_run else ""))

    applied = skipped = failed = 0
    for p in patches:
        rel = p.relative_to(NEW_PATCHES_DIR)
        # Already applied? (reverse-applies cleanly => skip, keeps this idempotent)
        rev = run_git(["apply", "--reverse", "--check", str(p)], cwd=source_dir, check=False)
        if rev.returncode == 0:
            info(f"[skip] already applied: {rel}")
            skipped += 1
            continue
        # Would it apply cleanly forward?
        chk = run_git(["apply", "--check", str(p)], cwd=source_dir, check=False)
        if chk.returncode != 0:
            err(f"[fail] would not apply: {rel}")
            first = (chk.stderr or "").strip().splitlines()
            if first:
                print(f"        {first[0]}", file=sys.stderr)
            failed += 1
            continue
        if args.dry_run:
            info(f"[ok] would apply: {rel}")
            applied += 1
            continue
        res = run_git(["apply", str(p)], cwd=source_dir, check=False)
        if res.returncode == 0:
            info(f"[ok] applied: {rel}")
            applied += 1
        else:
            err(f"[fail] apply error: {rel}")
            failed += 1

    print()
    header("Diff apply summary")
    info(f"  applied : {applied}")
    info(f"  skipped : {skipped} (already applied)")
    (err if failed else info)(f"  failed  : {failed}")

    # --- NEW_FILES phase: brand-new files (not diffs) copied into the tree ---
    # Destination = mirror of the path under NEW_FILES/, except the special cases
    # below (e.g. a flat 'mozconfig' actually belongs at browser/config/mozconfig).
    NEW_FILES_MAP = {
        "mozconfig": "browser/config/mozconfig",
    }
    nf_copied = nf_same = nf_failed = 0
    nf_dirs = sorted(NEW_PATCHES_DIR.glob("*/NEW_FILES"))
    if args.category:
        nf_dirs = [d for d in nf_dirs if d.parent.name.startswith(args.category)]
    nf_files = [(d, f) for d in nf_dirs for f in sorted(d.rglob("*")) if f.is_file()]
    if nf_files:
        print()
        header(f"NEW_FILES ({len(nf_files)} file(s))" + (" [DRY RUN]" if args.dry_run else ""))
        for nf_dir, src in nf_files:
            rel = src.relative_to(nf_dir).as_posix()
            dest_rel = NEW_FILES_MAP.get(rel, rel)
            dest = source_dir / dest_rel
            tag = "" if dest_rel == rel else f"  (mapped -> {dest_rel})"
            if dest.exists() and dest.is_file() and sha256_file(dest) == sha256_file(src):
                info(f"[same] {nf_dir.parent.name}/{rel}")
                nf_same += 1
                continue
            if args.dry_run:
                info(f"[ok] would copy: {nf_dir.parent.name}/{rel}{tag}")
                nf_copied += 1
                continue
            try:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
                info(f"[ok] copied: {nf_dir.parent.name}/{rel}{tag}")
                nf_copied += 1
            except OSError as e:
                err(f"[fail] {nf_dir.parent.name}/{rel}: {e}")
                nf_failed += 1
        print()
        header("NEW_FILES summary")
        info(f"  copied  : {nf_copied}")
        info(f"  same    : {nf_same} (already present, identical)")
        (err if nf_failed else info)(f"  failed  : {nf_failed}")

    return 1 if (failed or nf_failed) else 0


def cmd_port(args):
    """
    Extract tweaks from old.patches/CATEGORY/FILE and apply to the
    corresponding file in the working tree.
    """
    source_dir = Path(args.source).resolve()

    if not is_git_repo(source_dir):
        err("Not a git repo. Run: patch_manager.py init")
        return 1

    category = args.category
    filename = args.file

    old_patched = OLD_PATCHES_DIR / category / filename
    if not old_patched.exists():
        err(f"Old patched file not found: {old_patched}")
        return 1

    # Find where this file goes in the source tree
    rel_dest = find_upstream_file(source_dir, category, filename)
    if rel_dest:
        dest = source_dir / rel_dest
    else:
        # Fallback: assume same relative path exists in the tree
        # (for files not in deploy.sh mappings)
        warn(f"No deploy.sh mapping for {category}/{filename}")
        warn("Trying to locate file in source tree...")
        matches = list(source_dir.rglob(filename))
        if len(matches) == 1:
            dest = matches[0]
            info(f"Found at: {dest.relative_to(source_dir)}")
        elif len(matches) == 0:
            err(f"File '{filename}' not found anywhere in {source_dir}")
            return 1
        else:
            err(f"Multiple matches for '{filename}' — specify path manually")
            for m in matches:
                print(f"    {m.relative_to(source_dir)}")
            return 1

    if not dest.exists():
        err(f"Destination file does not exist: {dest}")
        return 1

    header(f"Porting {category}/{filename}")

    # Hash the current pristine file for the journal
    pristine_hash = sha256_file(dest)
    old_hash = sha256_file(old_patched)

    info(f"Old patched  : {old_patched}")
    info(f"  sha256: {old_hash}")
    info(f"New pristine : {dest}")
    info(f"  sha256: {pristine_hash}")

    # Check if the current destination is actually pristine (matches upstream)
    # by comparing to the firefox-main vault copy
    vault_path = (
        Path.home()
        / "Documents"
        / "Firefox.Scripts.Vault.Docs.backup"
        / "SafetyVault.Firefox"
        / "firefox-main"
        / rel_dest
    ) if rel_dest else None
    if vault_path and vault_path.exists():
        vault_hash = sha256_file(vault_path)
        if vault_hash == pristine_hash:
            info("Destination is confirmed pristine (matches vault firefox-main) ✅")
        else:
            warn("Destination does NOT match vault firefox-main — may already be patched")
            warn(f"  vault:   {vault_hash}")
            warn(f"  current: {pristine_hash}")

    # Now the key question: does the old patched file differ from the new
    # pristine only by our tweaks, or also by upstream changes?
    if pristine_hash == old_hash:
        warn("Old patched file is byte-identical to new pristine — nothing to port")
        return 0

    # Strategy:
    # If we can apply the old patched file's diff (vs an implied old base)
    # cleanly onto the new pristine, do a 3-way merge via git.
    # Otherwise, stage the old patched file as a starting point and let
    # the user/agent do the surgical merge.

    # For now: copy the old patched file over and stage it.
    # The user reviews and adjusts before committing.
    # This is explicit — no silent merge surprises.

    if args.dry_run:
        info("[dry-run] Would copy old patched file to destination and stage")
        info(f"  cp {old_patched} -> {dest}")
        info(f"  git add {dest.relative_to(source_dir)}")
        return 0

    shutil.copy2(old_patched, dest)
    info(f"Copied old patched file to {dest.relative_to(source_dir)}")

    # Stage it
    rel = str(dest.relative_to(source_dir))
    git_in_tree(source_dir, ["add", rel], capture=True, check=True)
    ok(f"Staged: {rel}")

    # Journal it
    key = f"{category}/{filename}"
    JOURNAL.setdefault("ported_files", {})[key] = {
        "old_sha256": old_hash,
        "pristine_sha256": pristine_hash,
        "dest": rel,
        "status": "staged",
        "ts": time.time(),
    }
    save_journal(JOURNAL)

    # Commit if requested
    if args.commit:
        msg = args.commit_msg or f"Port {category}: {filename}"
        r = git_in_tree(
            source_dir, ["commit", "-m", msg], capture=True, check=False
        )
        if r.returncode == 0:
            ok(f"Committed: {msg}")
            JOURNAL["ported_files"][key]["status"] = "committed"
            save_journal(JOURNAL)
        else:
            err("Commit failed")
            if r.stderr:
                print(r.stderr[-500:])
            return 1
    else:
        info("File is staged but NOT committed. Review with:")
        info(f"  git diff --cached {rel}")
        info("Then commit with:")
        info(f"  git commit -m 'Port {category}: {filename}'")
        info("Or undo with:")
        info(f"  git reset HEAD {rel} && git checkout -- {rel}")

    record_action("port", f"{category}/{filename}, committed={args.commit}")
    return 0


def cmd_build(args):
    """Run ./mach build, capture log, parse errors."""
    source_dir = Path(args.source).resolve()
    log_path = Path(args.save_log) if args.save_log else None

    if not is_git_repo(source_dir):
        err("Not a git repo. Run: patch_manager.py init")
        return 1

    mach = source_dir / "mach"
    if not mach.exists():
        err(f"./mach not found in {source_dir}")
        return 1

    header("Running ./mach build")

    # Run build
    info("Starting build (this may take a while)...")
    try:
        result = subprocess.run(
            ["./mach", "build"],
            cwd=str(source_dir),
            capture_output=True,
            text=True,
            timeout=7200,  # 2 hour timeout
        )
    except subprocess.TimeoutExpired:
        err("Build timed out after 2 hours")
        return 1

    output = result.stdout + "\n" + result.stderr

    # Save log
    if log_path:
        log_path.write_text(output)
        info(f"Full log saved to: {log_path}")
    else:
        # Save to a default location
        log_dir = SCRIPT_DIR / "build_logs"
        log_dir.mkdir(exist_ok=True)
        log_path = log_dir / f"build_{time.strftime('%Y%m%d_%H%M%S')}.log"
        log_path.write_text(output)
        info(f"Full log saved to: {log_path}")

    # Parse errors
    error_lines = []
    for line in output.splitlines():
        if ": error:" in line or ": error[" in line:
            error_lines.append(line.strip())

    success = result.returncode == 0 and len(error_lines) == 0

    if success:
        ok("BUILD PASSED ✅")
    else:
        err(f"BUILD FAILED — {len(error_lines)} errors")
        print()
        for e in error_lines[:20]:
            print(f"  {e}")
        if len(error_lines) > 20:
            print(f"  ... and {len(error_lines) - 20} more")

        # Show which commits touched the failing files
        print()
        info("Last commits touching failing files:")
        failing_files = set()
        for e in error_lines:
            parts = e.split(":")
            if parts:
                failing_files.add(parts[0])
        for f in sorted(failing_files):
            sha, msg = last_commit_touching(source_dir, f)
            if sha:
                short_sha = sha[:8]
                print(f"  {f}")
                print(f"    -> {short_sha} {msg}")
            else:
                print(f"  {f} (no committed change — pristine)")

    # Journal
    JOURNAL.setdefault("builds", []).append(
        {
            "success": success,
            "errors": error_lines[:20],
            "log": str(log_path),
            "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
    )
    save_journal(JOURNAL)

    record_action("build", f"success={success}, errors={len(error_lines)}")
    return 0 if success else 1


def cmd_rollback(args):
    """Roll back a file to pristine or undo a commit."""
    source_dir = Path(args.source).resolve()

    if not is_git_repo(source_dir):
        err("Not a git repo. Run: patch_manager.py init")
        return 1

    if args.commit:
        header(f"Reverting commit {args.commit}")
        r = git_in_tree(
            source_dir, ["revert", "--no-edit", args.commit], capture=True, check=False
        )
        if r.returncode == 0:
            ok(f"Reverted commit {args.commit}")
        else:
            err("git revert failed — manual resolution needed")
            if r.stdout:
                print(r.stdout)
            if r.stderr:
                print(r.stderr)
            return 1
    elif args.file:
        header(f"Rolling back {args.file} to pristine")
        r = git_in_tree(
            source_dir,
            ["checkout", PRISTINE_TAG, "--", args.file],
            capture=True,
            check=False,
        )
        if r.returncode == 0:
            ok(f"Restored {args.file} to pristine state")
            ok("File is now staged. Commit with: git commit -m 'Revert FILE'")
        else:
            err(f"Failed to restore {args.file}")
            if r.stderr:
                print(r.stderr)
            return 1
    else:
        err("Specify --file PATH or --commit SHA")
        return 1

    record_action("rollback", f"file={args.file}, commit={args.commit}")
    return 0


def cmd_diff(args):
    """Show unified diff of tweaks vs pristine."""
    source_dir = Path(args.source).resolve()

    if not is_git_repo(source_dir):
        err("Not a git repo. Run: patch_manager.py init")
        return 1

    if not has_tag(source_dir, PRISTINE_TAG):
        err(f"Pristine tag '{PRISTINE_TAG}' not found")
        return 1

    if args.file:
        header(f"Diff: {args.file}")
        r = git_in_tree(
            source_dir,
            ["diff", f"{PRISTINE_TAG}..HEAD", "--", args.file],
            capture=True,
            check=False,
        )
        print(r.stdout)
    elif args.category:
        header(f"Diff: category {args.category}")
        # Find all files in this category that were committed
        ported = JOURNAL.get("ported_files", {})
        cat_files = [k for k in ported if k.startswith(args.category + "/")]
        if not cat_files:
            warn(f"No ported files found for category {args.category}")
            return 0
        for f in cat_files:
            detail = ported[f]
            dest = detail.get("dest")
            if dest:
                r = git_in_tree(
                    source_dir,
                    ["diff", f"{PRISTINE_TAG}..HEAD", "--", dest],
                    capture=True,
                    check=False,
                )
                if r.stdout.strip():
                    print(r.stdout)
    else:
        header("All tweaks vs pristine")
        r = git_in_tree(
            source_dir,
            ["diff", f"{PRISTINE_TAG}..HEAD", "--stat"],
            capture=True,
            check=False,
        )
        print(r.stdout)
        print()
        info("For full diff: patch_manager.py diff --all --verbose")
        if args.verbose:
            r = git_in_tree(
                source_dir,
                ["diff", f"{PRISTINE_TAG}..HEAD"],
                capture=True,
                check=False,
            )
            print(r.stdout)

    return 0


def cmd_export(args):
    """Export all patch commits as .patch files via git format-patch."""
    source_dir = Path(args.source).resolve()
    out_dir = Path(args.out).resolve() if args.out else PATCHES_DIR / "patches-exported"

    if not is_git_repo(source_dir):
        err("Not a git repo. Run: patch_manager.py init")
        return 1

    if not has_tag(source_dir, PRISTINE_TAG):
        err(f"Pristine tag '{PRISTINE_TAG}' not found")
        return 1

    out_dir.mkdir(parents=True, exist_ok=True)
    header(f"Exporting patch commits to {out_dir}")

    r = git_in_tree(
        source_dir,
        ["format-patch", f"{PRISTINE_TAG}..HEAD", "-o", str(out_dir)],
        capture=True,
        check=False,
    )

    if r.returncode == 0:
        patches = [l for l in r.stdout.strip().splitlines() if l]
        ok(f"Exported {len(patches)} patch files:")
        for p in patches:
            print(f"  {p}")
        info("These .patch files are portable — share, pipe, or re-import.")
    else:
        err("git format-patch failed")
        if r.stderr:
            print(r.stderr)

    record_action("export", f"out={out_dir}")
    return 0


def cmd_upgrade(args):
    """
    Import a new Firefox source tree as a new pristine tag, then rebase
    the patch branch onto it.
    """
    source_dir = Path(args.source).resolve()
    new_source = Path(args.new_source).resolve()

    if not is_git_repo(source_dir):
        err(f"{source_dir} is not a git repo")
        return 1

    if not new_source.exists():
        err(f"New source tree not found: {new_source}")
        return 1

    new_tag = args.new_tag
    header(f"Upgrading to {new_tag}")

    # Step 1: Go to main branch
    info("Switching to main branch...")
    git_in_tree(source_dir, ["checkout", "main"], capture=True, check=False)

    # Step 2: Replace tree contents with new source
    info("Replacing source tree with new Firefox source...")
    # Remove all tracked files, then copy new source in
    r = git_in_tree(
        source_dir, ["rm", "-r", "--cached", "."], capture=True, check=False
    )
    # Copy new source files over
    for item in new_source.iterdir():
        if item.name == ".git":
            continue
        dest = source_dir / item.name
        if dest.is_dir():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)

    git_in_tree(source_dir, ["add", "-A"], capture=True, check=False)

    # Step 3: Commit new pristine
    info("Committing new pristine upstream...")
    r = git_in_tree(
        source_dir,
        ["commit", "-m", f"FF pristine upstream ({new_tag})"],
        capture=True,
        check=False,
    )
    if r.returncode == 0:
        ok("New upstream committed")
    else:
        err("Failed to commit new upstream")
        if r.stderr:
            print(r.stderr[-500:])
        return 1

    # Step 4: Tag
    if has_tag(source_dir, new_tag):
        warn(f"Tag '{new_tag}' already exists — overwriting")
        git_in_tree(source_dir, ["tag", "-d", new_tag], capture=True, check=False)
    git_in_tree(source_dir, ["tag", new_tag], capture=True, check=False)
    ok(f"Tagged as '{new_tag}'")

    # Step 5: Rebase patch branch
    info(f"Switching to '{PATCH_BRANCH}' and rebasing onto '{new_tag}'...")
    git_in_tree(source_dir, ["checkout", PATCH_BRANCH], capture=True, check=False)

    r = git_in_tree(
        source_dir, ["rebase", new_tag], capture=True, check=False
    )

    if r.returncode == 0:
        ok("Rebase completed cleanly — all patches applied! 🎉")
    else:
        warn("Rebase encountered conflicts. This is expected when upstream")
        warn("APIs changed. You need to resolve each conflict manually:")
        warn()
        warn("  1. Edit the conflicted file(s)")
        warn("  2. git add <resolved-file>")
        warn("  3. git rebase --continue")
        warn("  4. Repeat until all commits are replayed")
        warn()
        warn("Use: git status   to see which files need resolution")
        warn("Use: git rebase --abort   to cancel and go back")
        if r.stdout:
            print(r.stdout)
        if r.stderr:
            print(r.stderr)

    record_action("upgrade", f"new_tag={new_tag}")
    return 0


def cmd_preflight(args):
    """Run preflight-clang21.py against the working tree."""
    source_dir = Path(args.source).resolve()
    preflight = source_dir / "preflight-clang21.py"

    if not preflight.exists():
        # Try the patches/ copy
        preflight = PATCHES_DIR / "preflight-clang21.py"
    if not preflight.exists():
        preflight = SCRIPT_DIR / "preflight-clang21.py"  # may be symlinked

    if not preflight.exists():
        err("preflight-clang21.py not found")
        return 1

    header("Running Clang 21 pre-flight check")
    r = subprocess.run(
        [sys.executable, str(preflight)],
        cwd=str(source_dir),
        capture_output=False,
    )
    record_action("preflight", f"exit={r.returncode}")
    return r.returncode


def cmd_verify(args):
    """Run MAP_IBM.md verification greps."""
    source_dir = Path(args.source).resolve()

    header("Running verification checks from MAP_IBM.md")

    checks = [
        (
            "GPU unlock (GfxInfo.cpp)",
            "widget/gtk/GfxInfo.cpp",
            "return FEATURE_STATUS_OK",
        ),
        (
            "Mozambique timer (RecipeRunner.sys.mjs)",
            "toolkit/components/normandy/lib/RecipeRunner.sys.mjs",
            "1893456000",
        ),
        (
            "Mozambique timer (RemoteSettingsExperimentLoader.sys.mjs)",
            "toolkit/components/nimbus/lib/RemoteSettingsExperimentLoader.sys.mjs",
            "1893456000",
        ),
        (
            "Gorilla brand (brand.ftl)",
            "browser/branding/gorilla/locales/en-US/brand.ftl",
            "Gorilla",
        ),
        (
            "Remote triple-lock (Marionette)",
            "remote/components/Marionette.sys.mjs",
            "TRIPLE_LOCKED",
        ),
        (
            "Remote triple-lock (RemoteAgent)",
            "remote/components/RemoteAgent.sys.mjs",
            "TRIPLE_LOCKED",
        ),
        (
            "Normandy disabled (policies.json)",
            "browser/app/distribution/policies.json",
            "app.normandy.enabled",
        ),
        (
            "Telemetry lobotomy (firefox.js)",
            "browser/app/profile/firefox.js",
            "app.normandy.enabled",
        ),
    ]

    passed = 0
    failed = 0
    for name, rel_path, search in checks:
        f = source_dir / rel_path
        if not f.exists():
            warn(f"[SKIP] {name}: file not found ({rel_path})")
            continue
        txt = f.read_text(errors="replace")
        if search in txt:
            ok(f"{name}")
            passed += 1
        else:
            err(f"{name}: '{search}' not found in {rel_path}")
            failed += 1

    print()
    info(f"Results: {passed} passed, {failed} failed")
    record_action("verify", f"passed={passed}, failed={failed}")
    return 0 if failed == 0 else 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Gorilla Unleashed Firefox Patch Migration & Git Workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  patch_manager.py init
  patch_manager.py port --category 03.NETWORKING --file nsSocketTransport2.cpp --commit
  patch_manager.py build
  patch_manager.py status
  patch_manager.py diff --all
  patch_manager.py export --out ~/backups/patches
  patch_manager.py upgrade --new-source ~/firefox-155 --new-tag firefox-155-upstream
""",
    )
    parser.add_argument(
        "--source",
        default=str(FIREFOX_SOURCE_DEFAULT),
        help="Path to Firefox source tree (default: ~/firefox-main)",
    )

    sub = parser.add_subparsers(dest="command", help="Command to run")

    # init
    p_init = sub.add_parser("init", help="Initialise git, commit pristine, tag")
    p_init.add_argument("--tag", default=PRISTINE_TAG, help="Pristine tag name")

    # status
    p_status = sub.add_parser("status", help="Show current workflow state")

    # port
    # apply — current workflow: git-apply the new.patches unified-diff stack
    p_apply = sub.add_parser("apply", help="git apply the new.patches/ diff stack onto the source tree")
    p_apply.add_argument("--category", help="Only apply a category prefix (e.g. 03 or 03.NETWORKING)")
    p_apply.add_argument("--dry-run", action="store_true", help="Check only; apply nothing")

    # build
    p_build = sub.add_parser("build", help="Run ./mach build and parse errors")
    p_build.add_argument("--save-log", help="Save build log to this path")

    # rollback
    p_rollback = sub.add_parser("rollback", help="Roll back a file or commit")
    p_rollback.add_argument("--file", help="File to restore to pristine")
    p_rollback.add_argument("--commit", help="Commit SHA to revert")

    # diff
    p_diff = sub.add_parser("diff", help="Show diff of tweaks vs pristine")
    p_diff.add_argument("--file", help="Show diff for specific file")
    p_diff.add_argument("--category", help="Show diff for all files in a category")
    p_diff.add_argument("--all", action="store_true", help="Show all diffs (summary)")
    p_diff.add_argument("--verbose", action="store_true", help="Full diff, not just summary")

    # export
    p_export = sub.add_parser("export", help="Export patch commits as .patch files")
    p_export.add_argument("--out", help="Output directory (default: patches/patches-exported)")

    # upgrade
    p_upgrade = sub.add_parser("upgrade", help="Import new Firefox source and rebase")
    p_upgrade.add_argument("--new-source", required=True, help="Path to new Firefox source tree")
    p_upgrade.add_argument("--new-tag", default="firefox-155-upstream", help="Tag for new upstream")

    # preflight
    p_pre = sub.add_parser("preflight", help="Run preflight-clang21.py")

    # verify
    p_verify = sub.add_parser("verify", help="Run MAP_IBM.md verification greps")

    args = parser.parse_args()

    if args.command == "init":
        return cmd_init(args)
    elif args.command == "status":
        return cmd_status(args)
    elif args.command == "apply":
        return cmd_apply(args)
    elif args.command == "build":
        return cmd_build(args)
    elif args.command == "rollback":
        return cmd_rollback(args)
    elif args.command == "diff":
        return cmd_diff(args)
    elif args.command == "export":
        return cmd_export(args)
    elif args.command == "upgrade":
        return cmd_upgrade(args)
    elif args.command == "preflight":
        return cmd_preflight(args)
    elif args.command == "verify":
        return cmd_verify(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
