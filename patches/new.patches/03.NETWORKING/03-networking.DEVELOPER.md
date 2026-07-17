# Necko Tuning + Telemetry Excision — BBR/FQ-CoDel Alignment for the Custom Kernel — Developer Track

> **Topic:** `03-networking` · **Files:** `netwerk/base/nsSocketTransport2.cpp`, `netwerk/base/nsUDPSocket.cpp`, `netwerk/dns/nsHostResolver.cpp`, `netwerk/protocol/http/Http3Session.cpp`, `netwerk/protocol/http/HttpChannelParent.cpp`, `netwerk/protocol/http/HttpConnectionUDP.cpp`, `netwerk/protocol/http/nsHttpConnectionMgr.cpp`, `netwerk/protocol/http/nsHttpTransaction.cpp`
> **Generated:** 2026-07-16

---

## Module Summary

Necko-layer re-tuning for coherence with the custom Linux `7.x-unleashed.gorilla` kernel's BBR congestion control and FQ-CoDel queue discipline, plus compile-time excision of Necko-internal Glean/telemetry metrics. DNS worker pool doubled (8→16, idle-warm 12); TCP keepalive hardcoded aggressive (15 s idle / 5 s probe / 3 count); HTTP/3 UDP receive buffer sized to `StaticPrefs::network_http_http3_recvBufferSize()` (up to 64 MB); UDP send buffer explicitly set (closes prior HIGH-001); upload pacing via `kGorillaUploadChunkSize` (256 KB) active only for `mRequestSize > 10 MB` in `nsHttpTransaction::ReadSegments` (closes prior MED-001); DNS negative-cache TTL cut 60→3 s (closes and exceeds LOW-001, which recommended 15 s). Every buffer size assumes matching kernel ceilings from `/etc/sysctl.d/99-gorilla-network.conf` (`net.core.rmem_max=67108864`, `net.core.wmem_max=67108864`, `tcp_congestion_control=bbr`, `default_qdisc=fq_codel`) — the Firefox side fails visibly (buffer allocation clamps) if the sysctl is missing rather than silently degrading.

## Architecture

- **Pattern:** Two layered strategies: (1) numeric re-tuning of existing knobs to co-operate with kernel-side BBR/FQ-CoDel — no new mechanism, just correct values; (2) compile-time preprocessor excision of Necko-internal Glean metrics via `MOZ_TELEMETRY_REPORTING 0` + `GLEAN_DISABLED 1`, coherent with topic 13.TELEMETRY.KILL's methodology.
- **Trust Boundary:** Necko sits between the render/content processes and the kernel socket layer. All buffer-size requests go through the kernel's `net.core.*_max` ceilings — Firefox cannot exceed what the kernel permits, but must ask for the right value or it clamps to defaults. The `/etc/sysctl.d/99-gorilla-network.conf` file is the contract between the two layers.
- **Attack Surface:** Larger receive buffers slightly widen the surface for buffer-based DoS (an attacker could try to send many large UDP packets to consume RAM), but only up to the kernel's `net.core.rmem_max` ceiling — same as any other high-throughput application on the system. Telemetry excision reduces the outbound-data attack surface (no metric channel to exfiltrate through).
- **Dependencies:** `Linux kernel with BBR + FQ-CoDel compiled in (custom `7.x-unleashed.gorilla` kernel provides these)`, ``/etc/sysctl.d/99-gorilla-network.conf` with matching rmem_max/wmem_max/BBR/fq_codel settings`, `StaticPrefs consumers must actually read `network_http_http3_recvBufferSize` — verified in current build`

## Kill Switches

### `netwerk/dns/nsHostResolver.cpp — DNS thread pool sizing` — HARD ⚠️

- **Condition:** Always at Necko init.
- **Effect:** `MOZ_ALWAYS_SUCCEEDS(threadPool->SetThreadLimit(16))` + `SetIdleThreadLimit(12)`. Doubles concurrent DNS lookup capacity vs upstream default of 8. Modern web pages routinely touch 30+ hostnames; at 8 workers, DNS becomes a serialisation point.
- **Reversibility:** reversible
- **Notes:** Idle limit of 12 keeps threads warm (avoids thread-creation cost on burst) without unbounded resource growth.

### `netwerk/dns/nsHostResolver.cpp — NEGATIVE_RECORD_LIFETIME` — HARD ⚠️

- **Condition:** Always (compile-time #define).
- **Effect:** `#define NEGATIVE_RECORD_LIFETIME 3` (was 60). Failed DNS lookups are re-attempted after 3 seconds instead of 60. Critical for dynamic mobile networks and WebRTC signaling hosts whose IPs shift on short timescales.
- **Reversibility:** reversible
- **Notes:** This is MORE aggressive than the 2026-07-10 audit's recommended 15 s. The tighter value reflects the target audience: users on mobile networks where address churn is measured in seconds, not minutes.

### `netwerk/base/nsSocketTransport2.cpp — TCP keepalive` — HARD ⚠️

- **Condition:** Every TCP socket creation.
- **Effect:** TCP_KEEPIDLE=15, TCP_KEEPINTVL=5, TCP_KEEPCNT=3 hardcoded unconditionally via `setsockopt(sock, IPPROTO_TCP, TCP_KEEPIDLE, ...)`. Total time-to-detect-dead-connection: ~30 s (15 + 5×3), vs the kernel default of ~2 hours.
- **Reversibility:** reversible
- **Notes:** Aggressive keepalive is what keeps sessions alive across NAT-heavy consumer/mobile networks that silently drop idle connections in 1–2 minutes. Cost: one small probe packet per socket per 15 s of idle — negligible.

### `netwerk/protocol/http/HttpConnectionUDP.cpp — UDP buffer sizing` — RUNTIME_GUARD ⚠️

- **Condition:** At socket InitCommon.
- **Effect:** `mSocket->SetRecvBufferSize(StaticPrefs::network_http_http3_recvBufferSize())` — up to 64 MB from pref. `mSocket->SetSendBufferSize(...)` — closes HIGH-001 defect; the send buffer size is deliberately smaller than 32 MB to avoid a hundreds-of-megabytes-of-buffers scenario (see log's BDP analysis: 16 concurrent QUIC streams × safety-sized buffer → bounded total commit).
- **Reversibility:** reversible
- **Notes:** Log recommends 4 MB based on 1 Gbps × 32 ms BDP; verify actual value in current build against that rationale.

### `netwerk/protocol/http/nsHttpTransaction.cpp — upload pacing` — RUNTIME_GUARD ⚠️

- **Condition:** `mRequestSize > 10 * 1024 * 1024` (10 MB threshold).
- **Effect:** `if (mRequestSize > 10 * 1024 * 1024 && readCount > kGorillaUploadChunkSize) { readCount = kGorillaUploadChunkSize; }` inside ReadSegments. `kGorillaUploadChunkSize = 256 * 1024`. Caps read size per iteration to 256 KB for large uploads, so BBR's RTT-based pacing sees a smooth stream of segments instead of giant bursts.
- **Reversibility:** reversible
- **Notes:** Small uploads (< 10 MB) bypass the pacing — the overhead of gating would exceed the benefit at that size. Closes MED-001. `kGorillaUploadChunkSize` is a pre-existing identifier per the no-brand-spam rule.

### `HttpChannelParent.cpp + nsHttpConnectionMgr.cpp + Http3Session.cpp + nsUDPSocket.cpp — Glean excision` — HARD ⚠️

- **Condition:** Compile-time preprocessor.
- **Effect:** Each translation unit top has `#undef MOZ_TELEMETRY_REPORTING` + `#define MOZ_TELEMETRY_REPORTING 0` + `#define GLEAN_DISABLED 1`. All Glean metric expansions in the file become no-ops that DCE cleanly. Necko-internal metrics (`back_pressure_suspension_*`, `http3_session_version`, etc.) are eliminated.
- **Reversibility:** reversible
- **Notes:** Preprocessor rather than runtime guard so LTO can eliminate the metric-string constants entirely from libxul (verify with `strings libxul.so | grep back_pressure_suspension` — expect 0 matches). Coherent with topic 13.TELEMETRY.KILL methodology.

## Performance Profile

| Component | Before | After | Mechanism |
|---|---|---|---|
| DNS resolution capacity | 8 worker threads (upstream default) | 16 workers + 12 idle-warm | SetThreadLimit(16) + SetIdleThreadLimit(12) in nsHostResolver.cpp |
| TCP dead-connection detection | ~2 hours (kernel default) | ~30 s (15+5×3) | TCP_KEEPIDLE=15 / TCP_KEEPINTVL=5 / TCP_KEEPCNT=3 hardcoded |
| HTTP/3 UDP receive buffer | kernel default (typically 208 KB) | up to 64 MB (from StaticPrefs) | SetRecvBufferSize wired to pref |
| HTTP/3 UDP send buffer | kernel default (~128–256 KB — HIGH-001) | explicit size (log recommends 4 MB per BDP calc) | SetSendBufferSize added — closes HIGH-001 |
| Upload pacing (> 10 MB) | giant bursts (confused BBR — MED-001) | 256 KB chunks per read cycle | kGorillaUploadChunkSize gate in ReadSegments |
| DNS negative-cache retry | 60 s | 3 s | #define NEGATIVE_RECORD_LIFETIME 3 |
| Necko-internal Glean metrics | recorded + eligible for upload | compile-time excised (DCE'd) | GLEAN_DISABLED 1 + MOZ_TELEMETRY_REPORTING 0 preprocessor in 4 files |

- **CPU:** Fewer background metric-recording calls (Necko-internal Glean gone) reduces per-connection CPU overhead. Not measured as a topic-specific number for Necko; the whole-project telemetry win (12.8% parent CPU) captured in topic 13.TELEMETRY.KILL includes this contribution.
- **Memory:** UDP receive buffer up to 64 MB per QUIC socket; send buffer deliberately smaller (log's 4 MB recommendation). Assuming 16 concurrent QUIC streams: worst case ~1 GB receive + ~64 MB send. This is a memory-vs-throughput trade — the log's analysis walks through the kernel-level `net.core.rmem_max` ceiling as the hard cap.
- **I/O:** Larger receive buffers absorb burst arrivals without packet loss; matching send buffer prevents upload-side head-of-line blocking. DNS parallelism (16 threads) removes lookup serialisation as a page-load bottleneck.
- **Timer Interval:** TCP keepalive: 15 s idle + 5 s × 3 probes = ~30 s to detect dead connection (vs kernel default ~2 hours). DNS negative cache: 3 s (vs upstream 60 s).

## Security Analysis

### User Profiling

Necko-internal Glean metrics that reported connection-open/close events, backpressure statistics, and HTTP/3 version negotiation are all excised at compile time. No telemetry channel remains open in the networking layer to profile the user via.

### Targeting

N/A — no experimentation channel in this topic.

### Trust Chain

Kernel socket layer + libc are unchanged; trust boundary is where it always was. The sysctl file is the only new trust artifact — it should be shipped and verified during install.

### Abuse Potential

Larger receive buffers marginally widen a memory-consumption DoS surface, but the kernel's `net.core.rmem_max` ceiling bounds it; no unbounded growth is possible.

## Implementation Flow

1. **`nsHostResolver::Init`** — Sets thread pool limit to 16 and idle limit to 12. Declares `#define NEGATIVE_RECORD_LIFETIME 3`.
   *Side effects:* DNS lookups can proceed in parallel to a much higher fan-out. Failed lookups retried much sooner.
2. **`nsSocketTransport2::InitiateSocket / OnSocketConnected`** — For every TCP socket, immediately setsockopt keepalive triple.
   *Side effects:* TCP connections stay measurable-alive across NAT gear; dead sockets detected in ~30 s.
3. **`HttpConnectionUDP::InitCommon`** — SetRecvBufferSize + SetSendBufferSize for each QUIC socket. Sizes drawn from prefs; kernel ceilings from sysctl.
   *Side effects:* HTTP/3 streams can absorb bursts and pace uploads symmetrically.
4. **`nsHttpTransaction::ReadSegments`** — When mRequestSize > 10 MB, clamps read size to kGorillaUploadChunkSize (256 KB) per iteration.
   *Side effects:* Large uploads stream in paced 256 KB segments; BBR's RTT estimation stays clean.
5. **`HttpChannelParent / nsHttpConnectionMgr / Http3Session / nsUDPSocket TU init`** — Preprocessor asserts GLEAN_DISABLED 1 + MOZ_TELEMETRY_REPORTING 0. All Glean expansions in the TU become no-ops, DCE'd out.
   *Side effects:* Zero Necko-internal metric recording; zero corresponding string constants in the final binary.

## Technical Debt

🟠 **MEDIUM** — The `GLEAN_DISABLED 1` + `MOZ_TELEMETRY_REPORTING 0` preprocessor pair is duplicated at the top of 4 files — drift-vulnerable on rebase
  - *Recommendation:* Extract to a shared `NeckoTelemetryDisable.h` included from each affected file.

🟡 **LOW** — The 10 MB upload-pacing threshold is a magic number
  - *Recommendation:* Extract to a named constexpr adjacent to kGorillaUploadChunkSize with a comment explaining the rationale (below this size, pacing overhead exceeds BBR benefit).

🟠 **MEDIUM** — No toolchain-preflight assertion that `/etc/sysctl.d/99-gorilla-network.conf` is installed and active
  - *Recommendation:* Add a preflight check: `sysctl net.core.rmem_max` must return 67108864, else print a loud warning — otherwise the Firefox-side buffer requests silently clamp to defaults.

🟡 **LOW** — No topic-level master pref (unlike topic 01.MEDIA's `media.gorilla.hardware_only_mode`)
  - *Recommendation:* Consider `network.gorilla.tuning_enabled` gating the Necko custom behaviour — enables runtime A/B testing against upstream.

## Impact If Removed / Disabled

Reverting: (1) DNS becomes a serialisation point on multi-domain pages (perceived slowness); (2) TCP connections silently die at NAT-heavy consumer/mobile networks and Firefox hangs on reload; (3) HTTP/3 video stutters on burst arrivals (receive buffer too small); (4) HTTP/3 uploads bottleneck (send buffer at kernel default); (5) large uploads wreck BBR's RTT estimation; (6) failed DNS lookups wait 60 s before retry, killing mobile-network UX; (7) Necko-internal Glean metrics resume phoning home on every connection open/close.

## Testing Notes

Verify state matches spec: `grep -n 'SetThreadLimit\|NEGATIVE_RECORD_LIFETIME' netwerk/dns/nsHostResolver.cpp` returns 16 / 12 / 3; `grep -n 'TCP_KEEPIDLE' netwerk/base/nsSocketTransport2.cpp` returns 15; `grep -c 'SetSendBufferSize' netwerk/protocol/http/HttpConnectionUDP.cpp` returns ≥ 1. During browser use: `ss -o` on active TCP sockets shows 15/5/3 keepalive; `ss -ie` on QUIC sockets shows large rcv/snd wscale. `strings libxul.so | grep back_pressure_suspension` returns 0 (metric strings DCE'd). Kernel side: `sysctl net.core.rmem_max` returns 67108864, `sysctl net.ipv4.tcp_congestion_control` returns `bbr`, `sysctl net.core.default_qdisc` returns `fq_codel` — mismatches here cause Firefox-side sizes to silently clamp.

## Changelog Notes

History from `MASTER_PROJECT_LOG_FIREFOX_154_NETWORKING_PATCHES.md`: initial FF153 work (2026-06-08/09), FF154 rebase (2026-07-05), Glean scouring phase in HttpChannelParent (2026-07-08), audit performed (2026-07-10) which flagged HIGH-001/MED-001/LOW-001 — all three now closed in the current patch set. NEGATIVE_RECORD_LIFETIME exceeded the audit's recommended fix (3 s vs recommended 15 s). Naming discipline note: `kGorillaUploadChunkSize` is a pre-existing identifier and remains as-is (see project no-brand-spam rule).

---
*Developer Track. Human Track twin: `03-networking.LAYMAN.md`.*