# MASTER PROJECT LOG — FIREFOX 154 NETWORKING PATCHES

---

## Part 1: History, Roadmap & Overview
*(Originally from 00_NETWORKING_HISTORY_AND_ROADMAP.md)*

### Document Control
- **Category:** Necko Telemetry Scouring & Socket Tuning
- **Last Updated:** 2026-07-08
- **Status:** Active Development
- **Verification Required:** Yes (see Validation section)
- **Related Documents:**
  - `../DOCUMENTATION_TEMPLATES.md` (IBM format guide)
  - `../01.MEDIA/MASTER_PROJECT_LOG_FIREFOX_154_MEDIA_PATCHES.md` (VA-API buffers - COMPANION)
  - `../02.GPU/MASTER_PROJECT_LOG_FIREFOX_154_GPU_PATCHES.md` (WebRender overrides)
  - `../10.OVERRIDES/user.js` (preference layer)

---

### Executive Summary

**What This Does (Plain Language):**
This folder alters Firefox's networking layer (Necko) to match our custom Linux kernel settings. It:
1. Shuts down backend telemetry connections (Glean metrics) that spy on browser connection events.
2. Expands the internal network buffers to handle high-speed video transfers over UDP.
3. Increases the number of simultaneous DNS resolution tasks from 8 to 16.
4. Keeps active TCP connections alive aggressively to prevent idle timeouts.

**Technical Summary:**
Necko telemetry excision and socket tuning for Sony VAIO SVE14A3AJ (Intel Core i7-3632QM, Debian 13 Wayland + custom Linux 7.x-unleashed.gorilla kernel). Deletes telemetry hooks (`GLEAN_DISABLED 1` and `MOZ_TELEMETRY_REPORTING 0` preprocessors) from Necko modules, scales DNS thread resolver pools to 16, overrides socket send/recv windows up to 64 MB for HTTP/3 UDP channels, and forces aggressive TCP keepalive timings (15s idle, 5s interval, 3 probes).

---

### System Architecture & Logic

```
Necko Socket Thread / DNS Worker Thread Pool / Parent Channel
        |
        +-- nsHostResolver.cpp: SetThreadLimit(16) / SetIdleThreadLimit(12)
        |   Increases DNS worker concurrency for responsive page load
        v
+-----------------------------+
| nsSocketTransport2.cpp      |  Overrides TCP keepalive defaults unconditionally:
| (TCP Socket Layer)          |  - TCP_KEEPIDLE = 15s (forces active keepalive early)
+-----------------------------+  - TCP_KEEPINTVL = 5s (rapid probe intervals)
        |                        - TCP_KEEPCNT = 3 (fast drops for dead routes)
        v
+-----------------------------+
| HttpConnectionUDP.cpp       |  Scales HTTP/3 UDP buffer properties dynamically:
| (UDP / QUIC Socket Layer)   |  - SetRecvBufferSize(64MB)
+-----------------------------+
        |
        v
+-----------------------------+  Glean / Telemetry metrics disabled via compile-time
| HttpChannelParent.cpp       |  preprocessor blocks (#ifndef GLEAN_DISABLED):
| nsHttpConnectionMgr.cpp     |  - Gated: back_pressure_suspension_rate
| Http3Session.cpp            |  - Gated: back_pressure_suspension_delay_time
+-----------------------------+  - Gated: http3_session_version metrics
```

**Kernel Configuration Contract:**
These socket buffer sizes expect cooperating system limits configured in `/etc/sysctl.d/99-gorilla-network.conf`:
```ini
# Maximum socket buffer sizes (64 MB)
net.core.rmem_max = 67108864
net.core.wmem_max = 67108864
# Enable BBR congestion control and FQ-CoDel queueing
net.ipv4.tcp_congestion_control = bbr
net.core.default_qdisc = fq_codel
```

---

### Component Documentation

#### 1. nsHostResolver.cpp — Concurrency Expansion
- **Deploy Path:** `netwerk/dns/nsHostResolver.cpp`
- **Tuning:** Thread pool limit raised to 16, idle thread limit raised to 12.
- **Verification:** Confirm thread limits in constructor output log.

#### 2. nsSocketTransport2.cpp — Keepalive Overrides
- **Deploy Path:** `netwerk/base/nsSocketTransport2.cpp`
- **Tuning:** Hardcodes TCP_KEEPIDLE to 15, TCP_KEEPINTVL to 5, and TCP_KEEPCNT to 3.
- **Verification:** `ss -ie | grep keepalive` on active connections should reflect low timing intervals.

#### 3. HttpConnectionUDP.cpp — Buffer Tuning
- **Deploy Path:** `netwerk/protocol/http/HttpConnectionUDP.cpp`
- **Tuning:** Passes `StaticPrefs::network_http_http3_recvBufferSize()` (typically 64MB) to the socket buffer allocator.
- **Correction:** The UDP send buffer is NOT configured currently; it defaults to system limits.

---

### Chronological History (Recovered)

#### 2026-06-08/09
**Initial Networking Patches Applied:**
DNS thread expansions and socket buffer overrides introduced in Firefox 153. A buggy helper method (`SetIsPrivate`) was mistakenly introduced by a script generator, causing immediate compile failures. It was quickly reverted, restoring Necko build stability.

#### 2026-07-05
**Firefox 154 Rebase:**
Patches migrated and adapted to Firefox 154 codebase.

#### 2026-07-08
**Glean Scouring Phase:**
Scoured Necko files for residual telemetry metrics. Wrapped parent-side backpressure statistics in `HttpChannelParent.cpp` under `#ifndef GLEAN_DISABLED` guards.

---

## Part 2: Audit & Performance Assessment (2026-07-10)

We completed a full verification of the C++ implementations against the claims made in the roadmap.

### 1. Verification Checklist

| Claim / Goal | Status | Details |
| :--- | :--- | :--- |
| **Telemetry Lobotomy** | ✅ VERIFIED | Preprocessor macros (`GLEAN_DISABLED 1` and `MOZ_TELEMETRY_REPORTING 0`) successfully wrap all metrics loops inside `Http3Session.cpp`, `nsHttpConnectionMgr.cpp`, and `nsUDPSocket.cpp`. |
| **64MB UDP Receive Buffers** | ✅ VERIFIED | `mSocket->SetRecvBufferSize` is properly wired to preference metrics in `HttpConnectionUDP.cpp`. |
| **32MB UDP Send Buffers** | ❌ MISSED | **The baseline code lacks UDP send buffer configurations.** Socket send buffers are left to standard kernel defaults. |
| **16 DNS Resolver Threads** | ✅ VERIFIED | Resolvers successfully call `SetThreadLimit(16)` and `SetIdleThreadLimit(12)` in `nsHostResolver.cpp`. |
| **Aggressive TCP Keepalive** | ✅ VERIFIED | `nsSocketTransport2.cpp` sets idle delay to 15s and probe interval to 5s unconditionally. |
| **Parent Backpressure Telemetry** | ✅ VERIFIED | Residual Glean metrics in `HttpChannelParent.cpp` are successfully gated under `#ifndef GLEAN_DISABLED`. |

---

### 2. High-Fidelity Performance Opportunities

The following knobs and changes can be applied to further improve Necko throughput:

#### A. Configure UDP Send Buffer Size
- **Opportunity:** Call `SetSendBufferSize` on UDP sockets in `HttpConnectionUDP.cpp` (inside `InitCommon`) to prevent upload pacing bottlenecks.
- **Tweak:**
  ```cpp
  rv = mSocket->SetSendBufferSize(33554432); // 32MB send window
  ```

#### B. Wire Upload Pacing
- **Opportunity:** Wire the defined constant `kGorillaUploadChunkSize = 256 * 1024` into the upload data stream inside `nsHttpTransaction.cpp::ReadSegments` to pace large uploads against BBR congestion windows.

#### C. Reduce DNS Negative Cache Lifetime
- **Opportunity:** Change `#define NEGATIVE_RECORD_LIFETIME 60` to `15` inside `nsHostResolver.cpp`. This reduces delay when dynamic signaling nodes quickly shift IP configurations.

---

## Part 3: Detailed Breakdown of Flagged Issues & Buffer Asymmetry

Here is a plain-English and technical breakdown of the flagged issues in the networking audit:

### 1. 🟠 HIGH-001: Missing UDP Send Buffer Sizing
- **What it means (Layman):** Imagine widening a highway to 8 lanes for incoming traffic (64MB UDP receive buffers for video playback) but leaving the exit ramps restricted to a single lane (default kernel send buffers for uploads). If you try to upload data or participate in a high-resolution video call, the outgoing data gets bottlenecked, causing packet loss and lag.
- **Technical details (Developer):** In `HttpConnectionUDP.cpp::InitCommon()`, the code calls `mSocket->SetRecvBufferSize(StaticPrefs::network_http_http3_recvBufferSize())` but completely omits setting `SO_SNDBUF` (`mSocket->SetSendBufferSize(...)`).
- **Why it's a defect:** During high-speed HTTP/3 (QUIC) transmissions, asymmetric buffer sizes conflict with our kernel's **BBR congestion control** and **FQ-CoDel** pacing, leading to buffer starvation on upload streams.
- **The Fix:** Add a line to explicitly pin the send buffer size to 32MB:
  ```cpp
  mSocket->SetSendBufferSize(33554432); // 32 MB send window
  ```

### 2. 🟡 MED-001: Unused Upload Pacing Constant
- **What it means (Layman):** You have calculated the perfect size for package shipments to keep traffic moving smoothly (the `kGorillaUploadChunkSize` limit of 256 KB), but you forgot to tell the shipping clerk to actually split the cargo into those package sizes. The cargo is still shipped in massive blocks, which causes immediate shipping lanes congestion (bufferbloat).
- **Technical details (Developer):** `nsHttpTransaction.cpp` defines a constant:
  ```cpp
  const uint32_t kGorillaUploadChunkSize = 256 * 1024; // 256 KB
  ```
  However, inside `nsHttpTransaction::ReadSegments()`, this constant is never referenced. The transaction reads whatever the stream manager provides in one large block.
- **Why it's a defect:** Without pacing these reads, the browser dumps huge bursts of data into the socket queue at once. This degrades **BBR's** RTT (Round Trip Time) estimations.
- **The Fix:** Gate segment reads inside `ReadSegments()` to read a maximum of 256 KB per cycle when dealing with large uploads.

### 3. 🟢 LOW-001: Excessive Negative DNS Lifetime Cache
- **What it means (Layman):** If you try to call a friend and get a busy signal, you wait 60 seconds before trying their number again, even though they might have hung up and become available in 10 seconds. 
- **Technical details (Developer):** In `nsHostResolver.cpp`, the negative cache record duration is defined as:
  ```cpp
  #define NEGATIVE_RECORD_LIFETIME 60 // 60 seconds
  ```
- **Why it's a defect:** For dynamic servers (like WebRTC signaling hosts that change IP addresses quickly or fall back to relays), a failed lookup is cached for a full minute, blocking reconnection attempts.
- **The Fix:** Change the definition to 15 seconds:
  ```cpp
  #define NEGATIVE_RECORD_LIFETIME 15
  ```

---

## Part 4: Technical Analysis of Buffer Asymmetry & Memory Safety

### Why is the upload window set asymmetrically?

#### 1. The "Web-Consumer" Bias (Upstream Defaults)
Historically, web browser engines are designed under the assumption that clients are primarily **consumers** of data (downloading videos, loading images, fetching pages) rather than massive uploaders. 
- Upstream Firefox allocates large receive buffers (`network.http.http3.recvBufferSize` up to 64MB) to prevent incoming packet loss on high-bandwidth streams (like AV1/VP9 video).
- In contrast, outgoing uploads are treated as short, bursty control messages (HTTP GET/POST API payloads), so upstream simply delegates the send buffer size to the operating system's auto-tuning defaults.

#### 2. Safeguarding against RAM Bloat on Socket Creation
Unlike receive buffers which are allocated dynamically per-active-channel, setting a high static `SO_SNDBUF` (like 32MB) on every socket initialization forces the kernel to immediately lock down that memory window for output queues. 
- Since Necko spawns dozens of concurrent connections, statically forcing 32MB buffers on every socket could easily allocate hundreds of megabytes of system memory (RAM) instantly, even if the connection only uploads a 2KB header.
- Leaving it unconfigured was likely an intentional safety choice to prevent memory exhaustion (OOMs) on machines with less RAM.

#### 3. Relying on Linux TCP/UDP Kernel Auto-Tuning
On modern Linux kernels, the socket layer auto-tunes buffer sizes dynamically based on measured RTT (Round Trip Time) and bottleneck bandwidth (especially under TCP). 
- The original author likely assumed the Linux kernel's sysctl properties (`net.ipv4.tcp_wmem` and dynamic socket allocation) would scale the upload window automatically.
- **The Catch:** For UDP (which HTTP/3 / QUIC runs on), Linux kernel auto-tuning is much less aggressive than TCP, meaning the upload buffer remained clamped at the low default baseline (usually 128KB–256KB) while the download buffer scaled up to 64MB.

---

### What's the maximum safety size we can increase to on the UDP side without hogging the memory?

For your VAIO laptop with **16 GB of RAM**, the optimal maximum safety size for the UDP send buffer (`SO_SNDBUF`) is **`4,194,304` bytes (4 MB)**.

#### Why 4 MB is the Sweet Spot:

1. **Prevents Memory Hogging:**
   - In a typical heavy browsing session, Firefox might open up to **16 concurrent UDP/QUIC streams** (for media networks, WebRTC, and HTTP/3).
   - Statically setting **32 MB** per socket could lock up **512 MB** of memory immediately.
   - Statically setting **4 MB** per socket clamps the maximum active UDP upload pool to a highly safe **64 MB** total, which is negligible on a 16 GB machine.

2. **Perfect Pacing for Upstream BBR:**
   - At **4 MB**, the socket buffer is large enough to saturate a **1 Gbps upload link** at **32ms of latency** (Bandwidth-Delay Product: 1000 Mbps * 0.032 s = 4 MB).
   - This provides BBR congestion loops with enough room to pace packets smoothly without buffer starvation, while preventing bufferbloat.

3. **Aligns with FQ-CoDel:**
   - FQ-CoDel handles buffer congestion best when queues are not overly saturated. A 4MB send buffer matches the dynamic queue size of high-speed household uploads perfectly.

#### Recommended Value:

```cpp
mSocket->SetSendBufferSize(4194304); // 4 MB upload window
```

---

## Part 5: Outbound Security & Background Connection Audit

To guarantee Firefox is not leaking data or connecting to background telemetry, dictionaries, translators, AI assistants, PDF telemetry, or dynamic experiments, the following security measures are locked into the build:

### 1. The Mozambique Drill — Dynamic Studies Exclusion
Firefox's Normandy and Nimbus C2 experiment engines are neutralized at the compilation and xpcom layer:
- **`app.normandy.enabled`** is locked to `false` via system policies.
- **`app.normandy.api_url`** is wiped to `""`, triggering initialization aborts.
- **RecipeRunner & RemoteSettingsLoader** fallback loops are dilated to 60 years (`1893456000` seconds). The loader threads are functionally inert and will make no network requests for 60 years.

### 2. Local-Only Translator & Extension Locks
- **`browser.translations.enable`** is set to `false`.
- **`browser.translations.select.enable`** is set to `false`.
- **`extensions.translations.disabled`** is set to `true` to block translations extensions.

### 3. PDF.js & AI Chatbot Shielding
- **`browser.ai.control.pdfjsAltText`** is overridden to `false` in `all.js`, preventing the browser from attempting local or remote AI models to transcribe or parse PDF content.
- Telemetry modules inside PDF.js (`pdfjs.enableTelemetry`) are scoured.

All outbound connections remain locked down, and the browser cannot connect to unauthorized background services.
