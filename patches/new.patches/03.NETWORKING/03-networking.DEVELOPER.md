# Necko Socket / DNS / Buffer Tuning for the Custom 7.1.2 BBR + FQ-CoDel Kernel

> Generated 2026-08-04 | Source: `03.NETWORKING`

---

## Purpose

Four Necko-layer patches that re-tune existing kernel-facing knobs so Firefox 154 cooperates with the target machine's custom Linux 7.1.2 kernel (BBR congestion control, FQ-CoDel queue discipline, raised socket-buffer ceilings). No new mechanism is introduced; each patch changes numeric values or adds one setsockopt path. Trust level is unchanged from upstream: the code runs in the parent/socket process it already ran in, and every buffer request is still bounded by the kernel's net.core.*_max ceilings. This topic contains no telemetry, tracking, or experimentation code — a prior claim to the contrary was reverted and is documented as corrected below.

## Design Rationale

The values are co-designed with the 7.1.2 kernel and must not be read in isolation. The 64 MB HTTP/3 receive buffer is the browser-side half of the kernel's bandwidth-delay-product analysis (Debian.Kernel.Work/Reports/06-MATHEMATICAL-DERIVATIONS.md 6.2: transoceanic 1 Gbps x 150 ms = 18.75 MB in flight, socket buffer ceiling set to 64 MiB). The 4 MB send buffer is derived in this project's master log Part 4 (1 Gbps x 32 ms = 4 MB BDP; 16 concurrent QUIC streams x 4 MB = 64 MB bounded commit). The keepalive triple, the 16/12 DNS pool, the 3 s negative-cache TTL, and the 256 KB upload chunk are operational choices justified in the in-source comments (NAT dead-peer detection, multi-domain concurrency, dynamic-host DNS recovery, BBR pacing-clock drain) but have no located formal derivation in the kernel reports. A deliberate departure from upstream: HttpConnectionUDP now degrades gracefully (log + continue) where vanilla aborted (Close + return rv) on a buffer-size failure — correct for the distribution fleet whose ~4 GB machines may run an untuned kernel.

## Architecture

- **Pattern:** Numeric re-tuning of existing knobs plus one added setsockopt path (TCP keepalive). No new abstraction, no runtime feature flag. Cross-layer contract with the kernel via /etc/sysctl.d/99-gorilla-network.conf.
- **Trust boundary:** Necko sits between content/render processes and the kernel socket layer. Firefox cannot exceed the kernel's net.core.*_max ceilings; it can only request a size, which the kernel grants or clamps. The sysctl file is the trust artifact shared between Firefox and the kernel. Content-process code is not more trusted than before — these patches only change sizes and timers on connections the browser already opens.
- **Attack surface:** Unchanged entry points. A remote peer can influence how much of a requested receive buffer is filled, so the 64 MB receive request marginally widens a memory-consumption angle, but the kernel's net.core.rmem_max bounds it — same ceiling as any other high-throughput app on the host. No new parser, no new deserialization, no new network-reachable code path is added.
- **Dependencies:** `Custom Linux 7.1.2 kernel with BBR compiled in and FQ-CoDel as default qdisc (per POR_2026-08-03_room_clearing.md and the kernel reports; not re-measured in this pass)`, `/etc/sysctl.d/99-gorilla-network.conf raising net.core.rmem_max/wmem_max to 67108864 (verified present on the reference machine)`, `NSPR PR_GetIdentitiesLayer / PR_FileDesc2NativeHandle to reach the native TCP socket fd (nsSocketTransport2.cpp)`, `Linux TCP socket options TCP_KEEPIDLE / TCP_KEEPINTVL / TCP_KEEPCNT (guarded by #if defined)`, `nsIThreadPool (SetThreadLimit / SetIdleThreadLimit) in nsHostResolver.cpp`, `nsISocketTransport SetRecvBufferSize / SetSendBufferSize in HttpConnectionUDP.cpp`

## Flags & Configuration

| Name | Type | Default | Effect | Notes |
|------|------|---------|--------|-------|
| `NEGATIVE_RECORD_LIFETIME` | `int (compile-time const, seconds)` | `3 (upstream 60)` | Lifetime of a cached failed DNS lookup before retry is permitted. | netwerk/dns/nsHostResolver.cpp:69, consumed at :1306 rec->SetExpiration(..., NEGATIVE_RECORD_LIFETIME, 0). More aggressive than the 2026-07-10 audit's recommended 15 s. |
| `DNS thread limit` | `int` | `16 (upstream MaxResolverThreads(), pref-driven, defaults to 8)` | Maximum concurrent DNS resolver threads. | nsHostResolver.cpp:190 SetThreadLimit(16) replaces SetThreadLimit(MaxResolverThreads()); MaxResolverThreads() = network.dns.max_any_priority_threads + network.dns.max_high_priority_threads (nsHostResolver.h:47). Hardcoding removes the pref path. |
| `DNS idle thread limit` | `int` | `12 (upstream 8)` | Warm resolver threads kept alive between bursts. | nsHostResolver.cpp:191 SetIdleThreadLimit(12). |
| `TCP keepalive idle/intvl/cnt` | `int (seconds/seconds/count)` | `15 / 5 / 3, forced unconditionally` | Dead-peer detection ~30 s (15 + 5x3) on every TCP socket. | nsSocketTransport2.cpp:1527-1529 + setsockopt at :1531/:1536/:1541. Replaces Firefox's per-socket opt-in keepalive with an unconditional path. Exact prior effective idle value not traced this pass (in-source comment cites 300 s; Linux default is 7200 s). |
| `HTTP/3 UDP receive buffer` | `int (bytes)` | `67108864 (64 MB), hardcoded` | SO_RCVBUF request on each QUIC socket. | HttpConnectionUDP.cpp:301. Replaces vanilla SetRecvBufferSize(StaticPrefs::network_http_http3_recvBufferSize()) — the pref is no longer consulted. |
| `HTTP/3 UDP send buffer` | `int (bytes)` | `4194304 (4 MB), hardcoded` | SO_SNDBUF request on each QUIC socket (new; upstream set none). | HttpConnectionUDP.cpp:311. |
| `kGorillaUploadChunkSize` | `uint32_t (bytes)` | `262144 (256 KB)` | Caps ReadSegments read count per iteration for uploads over 10 MB. | nsHttpTransaction.cpp:79, gated at :847-848 (mRequestSize > 10*1024*1024). |

## API Surface

| Symbol | Description | Side Effects |
|--------|-------------|--------------|
| `nsHttpTransaction::ReadSegments()` | Reads request-body segments to send; now clamps readCount to 256 KB for >10 MB uploads before delegating to mRequestStream->ReadSegments. | Emits data to the send path in smaller chunks for large uploads; no behavioural change below 10 MB. |
| `HttpConnectionUDP::InitCommon()` | Sizes SO_RCVBUF (64 MB) and SO_SNDBUF (4 MB), continuing on failure. | Requests large kernel socket buffers; logs and proceeds if the kernel clamps or refuses. |
| `nsHostResolver::Init()` | Sets DNS thread pool to 16 workers, 12 idle. | Higher concurrent DNS fan-out; more warm threads resident. |
| `nsSocketTransport2 socket-attach path` | Applies TCP keepalive triple to every TCP socket via setsockopt. | One keepalive probe per ~15 s of idle per TCP socket. |

## Kill Switches

### `netwerk/dns/nsHostResolver.cpp:190-191 (SetThreadLimit/SetIdleThreadLimit)`
- **Condition:** Always, at resolver init.
- **Effect:** DNS worker pool sized 16/12 instead of MaxResolverThreads()/8. Reverting means editing the literals back.
- reversible
- No runtime pref gates this; it is a hardcoded value. Idle 12 keeps threads warm without unbounded growth.

### `netwerk/dns/nsHostResolver.cpp:69 (NEGATIVE_RECORD_LIFETIME)`
- **Condition:** Compile-time constant; effective on every negative-cache expiry.
- **Effect:** Failed lookups retried after 3 s instead of 60 s.
- reversible
- Kernel-independent; safe to revert to 60 without touching sysctl.

### `netwerk/base/nsSocketTransport2.cpp:1527-1541 (keepalive block)`
- **Condition:** Every TCP socket creation where the native fd is obtainable.
- **Effect:** Forces TCP_KEEPIDLE=15 / TCP_KEEPINTVL=5 / TCP_KEEPCNT=3 unconditionally.
- reversible
- Delete the block to restore per-socket opt-in keepalive. setsockopt failures are logged via SOCKET_LOG and ignored (non-fatal).

### `netwerk/protocol/http/HttpConnectionUDP.cpp:301,311 (buffer sizing)`
- **Condition:** At InitCommon for each QUIC socket.
- **Effect:** Requests 64 MB recv + 4 MB send; on NS_FAILED, logs and continues (graceful degradation).
- reversible
- Remove SetSendBufferSize line and/or restore the pref-driven recv size and the abort branch to return to upstream behaviour. The graceful-degradation branch is the operative safety net for untuned kernels.

### `netwerk/protocol/http/nsHttpTransaction.cpp:847-851 (upload pacing gate)`
- **Condition:** mRequestSize > 10 MB and readCount > 256 KB.
- **Effect:** Clamps per-iteration ReadSegments read count to 256 KB.
- reversible
- Below 10 MB the original count is used unchanged; deleting the gate restores unpaced reads.

## Dead Code

- **`None in the four patches.`** — kGorillaUploadChunkSize is defined at nsHttpTransaction.cpp:79 and used at :847-848 — it is live, not the unused constant the 2026-07-10 audit flagged as MED-001. (risk: N/A — removing it would break the pacing gate that references it.)

## Performance

- **CPU:** Not measured for this topic. Qualitatively: negligible added CPU (one keepalive probe per idle socket per ~15 s; a bounded compare in ReadSegments). No before/after CPU number is claimed.
- **MEMORY:** Up to 64 MB SO_RCVBUF + 4 MB SO_SNDBUF requested per QUIC socket, bounded by kernel ceilings. Master log Part 4 caps the design at ~16 concurrent QUIC streams (4 MB send x 16 = 64 MB send commit); receive worst case is larger and is the primary watch item on ~4 GB distribution targets. Comfortable on the 16 GiB (UMA-shared) reference machine. Not empirically measured.
- **IO:** Larger receive buffers absorb burst arrivals without loss; explicit send buffer removes upload head-of-line blocking; 16-way DNS parallelism removes lookup serialization on multi-domain pages; 256 KB upload chunking keeps BBR's RTT estimate clean on large uploads.
- **NOTES:** Every buffer figure is contingent on the kernel granting it; graceful degradation means the Firefox side never fails when the kernel is untuned, it only under-performs.

## Security

- **Remote execution:** None introduced. No new parser, deserializer, or executable path.
- **Data handling:** No user data is read, stored, or transmitted by any line in this topic. This is pure socket/DNS/buffer configuration.
- **Attack surface:** Marginally wider memory-consumption angle from the 64 MB receive request, bounded by net.core.rmem_max — no unbounded growth. No change to authentication, TLS, or origin handling.
- **Notes:** Prior documentation claimed Necko-layer Glean/telemetry excision (GLEAN_DISABLED / MOZ_TELEMETRY_REPORTING) in HttpChannelParent/nsHttpConnectionMgr/Http3Session/nsUDPSocket. That is FALSE for the current tree: those four files are byte-identical to vanilla and their patches were removed in the 2026-08-01/02 reconciliation; grep for GLEAN_DISABLED across the netwerk files returns zero matches (verified 2026-08-04). Telemetry containment for the build lives in locked prefs (datareporting.glean.uploadEnabled=false, toolkit.telemetry.enabled=false — 05.PREFS) and topic 13.TELEMETRY.KILL, not here.

## Error Conditions

| Error | Cause | Remedy |
|-------|-------|--------|
| `HttpConnectionUDP::InitCommon SetRecvBufferSize failed ... Continuing with default kernel receive buffers.` | Kernel net.core.rmem_max lower than 64 MB (untuned kernel). | Non-fatal by design; throughput on very high-BDP links is reduced. Install /etc/sysctl.d/99-gorilla-network.conf and reload sysctl to grant the full size. |
| `HttpConnectionUDP::InitCommon SetSendBufferSize failed ... Continuing with default kernel send buffers.` | Kernel net.core.wmem_max lower than 4 MB. | Non-fatal; upload pacing falls back to kernel default send buffer. Same remedy as above. |
| `nsSocketTransport: TCP_KEEPIDLE/INTVL/CNT failed` | setsockopt rejected on the platform (e.g. option unsupported). | Logged via SOCKET_LOG and ignored; connection proceeds with platform-default keepalive. No action required. |

## Tasks

### Verify the four patches match the live tree

Confirm the documented values are the values in netwerk before trusting this doc.

**Prerequisites:**
- FF_SRC points at the patched tree (/home/gorilla/firefox-main)

**Step 1:** grep -n 'NEGATIVE_RECORD_LIFETIME\|SetThreadLimit\|SetIdleThreadLimit' $FF_SRC/netwerk/dns/nsHostResolver.cpp
  - Expected: NEGATIVE_RECORD_LIFETIME = 3 (:69), SetThreadLimit(16) (:190), SetIdleThreadLimit(12) (:191).
**Step 2:** grep -n 'keepIdle\|keepIntvl\|keepCnt\|TCP_KEEPIDLE' $FF_SRC/netwerk/base/nsSocketTransport2.cpp
  - Expected: keepIdle=15 (:1527), keepIntvl=5 (:1528), keepCnt=3 (:1529), setsockopt at :1531/:1536/:1541.
**Step 3:** grep -n 'SetRecvBufferSize\|SetSendBufferSize\|graceful' $FF_SRC/netwerk/protocol/http/HttpConnectionUDP.cpp
  - Expected: SetRecvBufferSize(67108864) (:301), SetSendBufferSize(4194304) (:311), two 'graceful degradation' comments (:306/:316).
**Step 4:** grep -n 'kGorillaUploadChunkSize\|mRequestSize > 10' $FF_SRC/netwerk/protocol/http/nsHttpTransaction.cpp
  - Expected: constant at :79 (256*1024), gate at :847, applied at :851.

**After this task:** All four values reproduce the patch files byte-for-byte (already confirmed by POR_2026-08-03 and re-checked 2026-08-04).

### Confirm the telemetry-fencing revert is still in effect

Guard against a stale re-application of the reverted Glean fencing.

**Prerequisites:**
- FF_SRC set

**Step 1:** grep -rln 'GLEAN_DISABLED\|MOZ_TELEMETRY_REPORTING 0' $FF_SRC/netwerk/protocol/http/HttpChannelParent.cpp $FF_SRC/netwerk/protocol/http/nsHttpConnectionMgr.cpp $FF_SRC/netwerk/protocol/http/Http3Session.cpp $FF_SRC/netwerk/base/nsUDPSocket.cpp
  - Expected: No output. Any match means the reverted fencing was re-introduced and must be removed again (do NOT re-apply it).

**After this task:** Zero matches; the four files remain vanilla.

### Confirm the kernel-side contract

The buffer sizes are meaningless unless the kernel grants them.

**Prerequisites:**
- Root or read access to /etc/sysctl.d and /proc/sys

**Step 1:** grep -E 'rmem_max|wmem_max|congestion_control' /etc/sysctl.d/99-gorilla-network.conf
  - Expected: net.core.rmem_max = 67108864, net.core.wmem_max = 67108864, net.ipv4.tcp_congestion_control = bbr.
**Step 2:** cat /proc/sys/net/core/rmem_max /proc/sys/net/ipv4/tcp_congestion_control /proc/sys/net/core/default_qdisc
  - Expected: rmem_max at least 67108864; tcp_congestion_control 'bbr'; default_qdisc 'fq_codel'. NOTE: fq_codel is the custom kernel's compiled-in default — the .conf file ships bbr but does NOT contain a default_qdisc line.

**After this task:** Kernel grants at least the requested buffer sizes and runs bbr + fq_codel.

## Troubleshooting

**Symptom:** High-BDP transfers do not reach expected throughput.
**Cause:** Kernel net.core.rmem_max below 64 MB, so the receive-buffer request was clamped.
**Remedy:** Install and reload /etc/sysctl.d/99-gorilla-network.conf.
**Verify:** cat /proc/sys/net/core/rmem_max returns at least 67108864.

**Symptom:** Large uploads still burst instead of pacing.
**Cause:** Upload below the 10 MB gate, or the gate was reverted.
**Remedy:** Confirm the payload exceeds 10 MB; re-check the gate at nsHttpTransaction.cpp:847.
**Verify:** grep -n 'mRequestSize > 10' nsHttpTransaction.cpp returns the gate.

**Symptom:** Idle TCP connections still die on cheap NAT gear.
**Cause:** setsockopt keepalive was rejected on the platform (logged, ignored).
**Remedy:** Check SOCKET_LOG output for 'TCP_KEEPIDLE failed'; confirm the platform supports the options.
**Verify:** MOZ_LOG=nsSocketTransport:5 shows the keepalive path executing without the failure log.

**Symptom:** A doc or patch references HttpChannelParent/Http3Session/nsUDPSocket telemetry fencing.
**Cause:** Stale material from before the 2026-08-03 revert.
**Remedy:** Ignore/remove it; do not re-apply. Telemetry is handled by locked prefs and topic 13.
**Verify:** grep for GLEAN_DISABLED in those files returns nothing.

## Technical Debt

🟡 **LOW** — DNS thread limit and NEGATIVE_RECORD_LIFETIME are hardcoded literals, bypassing the pref path (MaxResolverThreads() and the negative-TTL constant). → Acceptable for a fixed-hardware build; if a runtime A/B is ever wanted, route through a network.gorilla.* pref instead of literals.
🟡 **LOW** — The 10 MB upload-pacing threshold is a magic number inline in the gate. → Extract to a named constexpr adjacent to kGorillaUploadChunkSize with a comment on why pacing overhead is not worth it below that size.
🟠 **MEDIUM** — No preflight assertion that /etc/sysctl.d/99-gorilla-network.conf is installed and active; buffer requests silently clamp on a fresh/untuned install. → Add a build/preflight check that /proc/sys/net/core/rmem_max >= 67108864 and warns loudly otherwise.
🟡 **LOW** — Master log's 'Kernel Configuration Contract' lists net.core.default_qdisc = fq_codel as shipped in the .conf, but the on-disk .conf contains no default_qdisc line (fq_codel is the kernel's compiled-in default). → Correct the master log's contract block to reflect that fq_codel comes from the kernel build, not this sysctl file, to avoid a false verification expectation.

## Impact If Removed

Reverting the four patches restores upstream Necko behaviour: (1) DNS becomes a serialization point on multi-domain pages (lower concurrency, warmer-thread churn); (2) failed DNS lookups block retry for 60 s instead of 3 s, hurting dynamic-host and mobile UX; (3) TCP connections revert to per-socket opt-in keepalive and silently die on NAT-heavy links, causing reload hangs; (4) HTTP/3 receive buffer reverts to the pref value AND the abort-on-failure branch returns, so a buffer-size failure again tears down the QUIC socket rather than degrading; (5) the explicit 4 MB send buffer disappears and uploads bottleneck at the kernel default; (6) large uploads stream unpaced, distorting BBR's RTT estimation. No security posture is lost by removal — this topic adds none.

## Claim Sources

| Claim | Basis | Evidence |
|-------|-------|----------|
| Receive buffer hardcoded 67108864, not from StaticPrefs | 📄 stated in input | rv = mSocket->SetRecvBufferSize(67108864);  // 64MB |
| Vanilla used the pref and aborted on failure | 📄 stated in input | -  rv = mSocket->SetRecvBufferSize(
-      StaticPrefs::network_http_http3_recvBufferSize()); ... -    mSocket->Close(); |
| Send buffer 4194304 added, graceful degradation | 📄 stated in input | rv = mSocket->SetSendBufferSize(4194304); ... // Do not abort — graceful degradation. |
| Keepalive 15/5/3 unconditional | 📄 stated in input | int32_t keepIdle = 15; int32_t keepIntvl = 5; int32_t keepCnt = 3; |
| DNS 16 threads / 12 idle, replacing MaxResolverThreads()/8 | 📄 stated in input | -  MOZ_ALWAYS_SUCCEEDS(threadPool->SetThreadLimit(MaxResolverThreads())); ... +  SetThreadLimit(16)) ... +  SetIdleThreadLimit(12)) |
| MaxResolverThreads() = any + high priority pref sums | 📄 stated in input | return MaxResolverThreadsAnyPriority() + MaxResolverThreadsHighPriority(); (nsHostResolver.h:47) |
| NEGATIVE_RECORD_LIFETIME 60 -> 3 | 📄 stated in input | static const unsigned int NEGATIVE_RECORD_LIFETIME = 3; |
| Upload chunk 256 KB gated at 10 MB, and is used (not dead) | 📄 stated in input | if (mRequestSize > 10 * 1024 * 1024 && readCount > kGorillaUploadChunkSize) { readCount = kGorillaUploadChunkSize; } |
| 64 MB recv buffer traces to kernel BDP derivation 6.2 | 📄 stated in input | BDP = 125 MB/s * 0.150 s = 18.75 MB ... configured at 64 MiB (Reports/06-MATHEMATICAL-DERIVATIONS.md 6.2) |
| 4 MB send buffer traces to master-log Part 4 BDP | 📄 stated in input | 1000 Mbps * 0.032 s = 4 MB (master log Part 4) |
| Telemetry fencing reverted; files vanilla; patches deleted | 📄 stated in input | all four files are byte-identical to the vanilla vault; their four .patch files were deleted (POR_2026-08-03_room_clearing.md) |
| GLEAN_DISABLED grep returns zero in the four files | 🤖 model inference | *(none — model judgment)* |
| .conf ships bbr + 64 MB but no default_qdisc line | 📄 stated in input | net.core.rmem_max = 67108864 ... net.ipv4.tcp_congestion_control = bbr (no fq_codel/default_qdisc line in /etc/sysctl.d/99-gorilla-network.conf) |
| keepalive/DNS/chunk lack formal kernel derivation | 🤖 model inference | *(none — model judgment)* |
| No CPU/memory/throughput measured for this topic | 🤖 model inference | *(none — model judgment)* |
| Exact prior keepalive idle value not traced | 🤖 model inference | *(none — model judgment)* |


---
**How to verify this document:**
`📄 stated in input` — the model's phrasing of something your source text said.
Find the matching line in the original to verify.
`🤖 model inference` — the model's own judgment or synthesis. Treat as opinion,
not measurement. Re-run on the same input and check whether specific numbers
stay consistent between runs.

*Auto-generated DITA-structured developer documentation.*