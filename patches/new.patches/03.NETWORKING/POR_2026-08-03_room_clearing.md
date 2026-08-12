# POR — 03.NETWORKING room clearing (2026-08-03)

Per `patches/SOP.room-clearing-and-poison-audit.md`. Method: every claim verified against
the LIVE tree (`/home/gorilla/firefox-main`) and the vanilla vault, never against the docs.

## Friendlies (kept — verified real)

| Claim | Ground truth | Evidence |
|---|---|---|
| 4 surviving .patch files are true records | **vanilla + patch == live, byte-exact**, all 4 | staged vault copy, `patch -p1`, `cmp` (nsSocketTransport2, nsHostResolver, HttpConnectionUDP, nsHttpTransaction) |
| NEGATIVE_RECORD_LIFETIME 60→3 s | present | nsHostResolver.cpp:69 (GORILLA v2 marker) |
| DNS pool 16 threads / 12 idle | present | nsHostResolver.cpp:190–191 |
| TCP keepalive 15/5/3 unconditional | present | nsSocketTransport2.cpp ~1520 |
| Upload pacing 256 KB gated >10 MB | present | nsHttpTransaction.cpp:79, :847 |
| UDP send buffer explicitly sized (HIGH-001 closed) | present, 4 MB | HttpConnectionUDP.cpp:311 |
| sysctl contract | conf present (64 MB); **live kernel 128 MB, bbr, fq_codel** — exceeds contract | `/etc/sysctl.d/99-gorilla-network.conf`; `/proc/sys/net/{core,ipv4}/…` |
| `network.gorilla.tuning_enabled` | a labelled RECOMMENDATION, not a claim — no action | master log §Phase 2 / §LOW |

## Tango neutralised (1)

**False-VERIFIED telemetry claims in the master log.** The log marks "Telemetry Lobotomy"
and "Parent Backpressure Telemetry" as ✅ VERIFIED in
HttpChannelParent / nsHttpConnectionMgr / Http3Session / nsUDPSocket. Ground truth: all
four files are **byte-identical to the vanilla vault**; their four .patch files were deleted
in the 2026-08-01/02 reconciliation. The Necko Glean fencing was deliberately reverted when
compile-time excision was abandoned (Prime Directive 0 → 13.TELEMETRY.KILL stub doctrine),
but the log was never corrected. Caught via the log's own falsifiable check
(`grep -l GLEAN_DISABLED netwerk/…` → no matches today).
**Action:** dated correction appended to the master log (append-only); fortress atom
`Necko_Glean_Fencing_REVERTED_Room_Clearing_2026_08_03` supersedes the stale
Telemetry_Lobotomy claims and closes OPEN_ITEM_necko_glean (resolution: reverted by design).
**Do NOT re-apply the guards.**

## Housekeeping flags (not poison)

- `AUDIT_REPORT_03.NETWORKING.md` (2026-07-10, "PASS") is a **stale generation-1 audit** —
  historical record only; this POR supersedes it as the room's status.
- Fortress dir `Firefox.154.Lessons/03.NETWORKING/` contains **misfiled**
  `agy_credentials_deconstruction.xml` (Antigravity binary forensics, not networking) and
  several `Dir_*`/raw capture XMLs — relocation/curation owed when that corpus gets its own
  room-clearing pass.

## What this POR does NOT claim

Values were verified to EXIST as documented; they were **not re-validated against Mozilla
documentation for optimality** (the human 2-month-style doc pass). Contamination-screened;
values not doc-validated — per the SOP's honest-label rule.

**Room status: CLEARED (1 tango neutralised, 0 open items).**
