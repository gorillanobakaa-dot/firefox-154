# Retuning Firefox's Network Plumbing to Match a Custom Linux Kernel — Plain Language Guide

> Generated 2026-08-04 from `03.NETWORKING`

---

## Should You Run This?

Yes, if you are running this build on the target hardware — it is low-risk network tuning with a graceful-degradation safety net, and nothing here touches your data. The one caveat is memory on very low-RAM machines during heavy simultaneous transfers; watch that if you have far less than the 16 GB reference machine. If you are on a fast, unmetered local connection you may not notice much, but nothing here will hurt you.

## Worst Case, Honestly

The realistic worst case is wasted memory, not danger. On a busy browsing session with many video/QUIC connections open at once, Firefox asks the kernel for a 64 MB receive buffer and a 4 MB send buffer per connection. If dozens are open, that memory adds up. On the 16 GB reference machine that is comfortable; on a low-RAM (~4 GB) target machine it is the main thing to watch. The code is written to degrade gracefully — if the kernel refuses the large size, Firefox keeps going with a smaller buffer instead of failing — so the bad outcome is 'slower on a huge transfer', not 'crash' or 'data leak'.

## What Data This Touches

These four changes send nothing anywhere. They set connection sizes and timers on your own machine. No data about you is collected, stored, or transmitted by any line in this topic. If you are worried about tracking, this is not the code to worry about — and an earlier draft that claimed this room 'severs telemetry' was mistaken. That claim was checked against the actual code on 2026-08-03 and removed: the telemetry-blocking work was reverted here and lives instead in the build's locked settings and in a separate topic (13.TELEMETRY.KILL).

## Before You Trust It

You are about to run a browser build a stranger tuned. You cannot audit C++, but you can confirm the headline numbers in this guide are actually the numbers in the code. If they match, the guide is honest about what it changed.

**Step 1:** Open the file patches/new.patches/03.NETWORKING/netwerk_protocol_http_HttpConnectionUDP.cpp.patch in any text viewer.
  - Look for: You should see the number 67108864 (that is 64 MB) for the receive buffer and 4194304 (that is 4 MB) for the send buffer, each with a comment saying 'graceful degradation' / 'Do not abort'.
**Step 2:** Open netwerk_dns_nsHostResolver.cpp.patch in the same folder.
  - Look for: You should see NEGATIVE_RECORD_LIFETIME set to 3, SetThreadLimit(16) and SetIdleThreadLimit(12). If those match, the DNS claims in this guide are accurate.
**Step 3:** Open netwerk_base_nsSocketTransport2.cpp.patch and look at the keepalive block.
  - Look for: keepIdle = 15, keepIntvl = 5, keepCnt = 3. These are the three keepalive numbers this guide describes.
**Step 4:** Confirm this room contains exactly four .patch files and no telemetry file.
  - Look for: The folder should list four patch files (nsSocketTransport2, nsHostResolver, HttpConnectionUDP, nsHttpTransaction). If you see a patch touching HttpChannelParent, Http3Session or nsUDPSocket, your copy is out of date — those were removed on 2026-08-03.

## The Big Picture

This is four small changes to the part of Firefox that talks to the internet (Mozilla calls it Necko). None of them add a feature you click. They change the numbers Firefox uses when it opens a connection: how big its incoming and outgoing buffers are, how often it checks that an idle connection is still alive, how many name-lookups it can do at once, and how long it waits before retrying a lookup that just failed.

Why bother? Because the computer this build targets runs a custom Linux kernel (version 7.1.2) that was hand-tuned for two modern traffic algorithms called BBR and FQ-CoDel. Firefox's stock numbers assume a fast, cheap, always-on broadband line. On a slow or shared connection those stock numbers fight the kernel instead of cooperating with it. These four patches change Firefox's numbers so the browser and the kernel pull in the same direction.

There is one thing this topic is NOT, and it is worth saying plainly because an earlier version of these notes got it wrong: this room does not touch telemetry or tracking. It is pure network tuning. The privacy work lives in other parts of the build.

## Key Concepts

| Name | What It Means | Real-World Comparison |
|------|--------------|------------------------|
| `Necko` | Firefox's networking code — everything that sends or receives data over the internet passes through it. | The mail room of a large office: every letter in or out goes through it. |
| `Buffer` | A holding area in memory where data waits to be processed or sent. | The counter space at a shipping desk. Too small and parcels pile up on the floor; too big and the desk hogs the whole room. |
| `BBR` | A congestion-control method from Google that measures how fast the connection really is and sends at that pace. | A driver who watches the road and keeps a steady speed, instead of flooring it until they rear-end the car ahead. |
| `FQ-CoDel` | A queueing method that stops one heavy download from freezing everyone else's traffic on a shared line. | A shop that opens an express lane the moment one giant trolley starts blocking the till. |
| `TCP keepalive` | A tiny 'are you still there?' packet Firefox sends on an idle connection so a router does not quietly kill it. | Saying 'you still on the line?' when the other person has gone quiet for a while. |
| `DNS` | The internet's phonebook — it turns names like example.com into the numeric address a computer dials. | The receptionist who looks up an extension. If she is slow, the whole call feels slow. |

## How It Works — Step by Step

### Step 1: Ask for a big incoming buffer, but do not insist

When Firefox opens an HTTP/3 (QUIC) connection, the code in HttpConnectionUDP.cpp asks the kernel for a 64 MB receive buffer (the exact number 67108864). That is room to swallow a big burst of video without dropping packets. The important part: if the kernel says no (because its own limit is lower), Firefox writes a note to its log and carries on with whatever it can get. It does not abort the connection. The stock Firefox code did the opposite — it closed the socket and gave up. This 'keep going' behaviour is what makes the change safe to ship to machines whose kernel was never tuned.

### Step 2: Set a matching outgoing buffer for uploads

Right after, the same code asks for a 4 MB send buffer (the number 4194304). For years the download side was widened while the upload side was left tiny, so video calls and file uploads bottlenecked on the way out. 4 MB is deliberately modest: big enough to keep a fast uplink full, small enough that many open connections do not eat hundreds of megabytes of memory. Same rule as step 1 — if the kernel refuses, Firefox continues with a smaller buffer instead of failing.

### Step 3: Keep every TCP connection on a short leash

In nsSocketTransport2.cpp, for every TCP connection Firefox opens, the code tells the operating system: check if this connection is still alive after 15 seconds of silence, then probe every 5 seconds, and give up after 3 failed probes. Cheap home routers and mobile-carrier equipment often kill a quiet connection without telling anyone; this makes Firefox notice within about half a minute and reconnect, instead of hanging when you reload the page.

### Step 4: Do more name-lookups at once, and forget failures faster

In nsHostResolver.cpp two things change. Firefox can now run 16 DNS lookups in parallel (and keep 12 lookup workers warm), instead of the smaller stock number. A modern web page pulls resources from dozens of different domains, so more parallel lookups means the page stops waiting in a queue. Separately, when a lookup fails, Firefox now forgets that failure after 3 seconds instead of 60. On a mobile network where addresses change quickly, a 60-second memory of a failure is a wall between you and a site that has already come back.

### Step 5: Feed big uploads to the network in small, steady bites

In nsHttpTransaction.cpp, when you upload something larger than 10 MB, Firefox now hands the data to the network in 256 KB pieces instead of one giant shove. BBR (in the custom kernel) works by measuring how packets get through; a giant shove distorts that measurement and makes pacing worse. Small uploads are left alone — the extra bookkeeping is not worth it below 10 MB. Only big uploads, where BBR's pacing actually matters, are chunked.

## Quirky Things Worth Knowing

### The 64 MB number only works if the kernel agrees

Firefox asking for a 64 MB buffer means nothing unless the kernel is willing to grant it. On this build the kernel setting net.core.rmem_max is raised to match (in the file /etc/sysctl.d/99-gorilla-network.conf). Two halves of one machine have to agree. If you copy just the Firefox side to an untuned computer, the request is simply trimmed down — which is fine, because of the 'keep going' design in steps 1 and 2.

### Every number is arithmetic, not a hunch

The 64 MB receive buffer comes from a bandwidth-delay calculation in the kernel project's own math notes: a 1 Gbps link across an ocean (150 ms round trip) can have about 18.75 MB of data in flight, and 64 MB leaves comfortable headroom. The 4 MB send buffer comes from a smaller version of the same sum (a 1 Gbps uplink at 32 ms is about 4 MB). Those two are written down. The keepalive timings, the 16 lookup workers, and the 256 KB chunk size are engineering judgements explained in the code comments, but they do not have a formal written derivation — this guide does not pretend they do.

### An earlier version of these notes overstated things

The previous documentation for this room claimed the receive buffer size came from a Firefox preference and that Firefox 'fails visibly' if the kernel is untuned, and it claimed the network code blocks telemetry. All three statements are now false in the actual code: the size is hard-coded to 64 MB, Firefox degrades gracefully rather than failing, and the telemetry-blocking was removed from this room. This is exactly why open documentation with dates and line numbers matters — a mistake can be caught and corrected in public.

## What This Means For You

### Battery, Processor & Memory

Not measured for this topic. The honest expectation: slightly more memory used when many large transfers run at once (bigger buffers), and a negligible amount of CPU for the keepalive probes. No before/after numbers were taken, so none are claimed.

### Speed

Not measured as a number. By design: pages that touch many domains should feel quicker (more parallel DNS), high-bitrate video should stutter less (bigger receive buffer), uploads should stop bottlenecking (send buffer plus paced chunks), and connections that used to silently die on cheap routers should recover. No throughput or page-load measurement was recorded, so no percentage is claimed here.

### Your Privacy

No effect. This topic collects and sends nothing about you. Privacy is handled elsewhere in the build.

### Your Internet

Uses your connection more efficiently, not more heavily. It does not add background traffic. The only extra bytes are the small keepalive probes on idle connections, which are tiny and are what keep a connection from dying.

## The Off Switch

**What it is:** There is no single on/off switch for this topic — the changes are numbers baked into the code, not a feature flag. But each one is independently reversible: change 16 back to the stock lookup count, delete the send-buffer line, restore the failure-lifetime to 60, or remove the keepalive block. The kernel side has its own switch: the file /etc/sysctl.d/99-gorilla-network.conf. Remove it and the kernel goes back to its defaults, and Firefox's large-buffer requests are simply trimmed (thanks to the graceful-degradation design).

**Without it:** Without these changes, on a slow or shared line you get the stock behaviour: video can stutter on bursts, big uploads bottleneck, connections silently die on cheap routers and Firefox hangs on reload, many-domain pages feel sluggish because lookups queue up, and a failed lookup is remembered for a full minute.

**Think of it like:** It is less like one light switch and more like a car service: a wider fuel line (buffers), smoother throttle control (BBR-friendly pacing), a faster restart when the engine stalls (keepalives), and more staff at the parts desk (DNS workers). Each part can be undone on its own; together they make the car actually move.

## How to use this

**Before you start:**
- You are building or running the Gorilla Unleashed Firefox 154 build, not stock Firefox.
- For the full benefit, the companion kernel file /etc/sysctl.d/99-gorilla-network.conf is installed and active (it raises the kernel buffer limits to match).
- The custom 7.1.2 kernel with BBR available is what these numbers were designed against; on a stock kernel the changes still work but do less.

**Step 1:** Build Firefox with these four patches applied (they are part of the standard patch set).
  - You should see: The build completes; the four netwerk source files carry the GORILLA v2 comments.
**Step 2:** Confirm the kernel side is in place if you want the large buffers to actually be granted.
  - You should see: The sysctl file exists with net.core.rmem_max = 67108864 and net.core.wmem_max = 67108864. Without it, Firefox still runs and simply gets smaller buffers.
**Step 3:** Just use the browser normally — there is nothing to switch on.
  - You should see: Multi-domain pages, video, uploads and flaky-router reconnects behave better on slow or shared links than stock Firefox would.

## If Something Goes Wrong

**Firefox uses more memory than you expected during heavy video or many downloads.**
Each HTTP/3 connection can request up to a 64 MB receive buffer; several at once add up.
What to do: This is expected on the 16 GB reference machine. On a low-RAM (~4 GB) machine, close some tabs; or lower the 67108864 figure in HttpConnectionUDP.cpp and rebuild if it is a real problem for you.

**You do not see any speed improvement over stock Firefox.**
The kernel side may not be installed, so your buffer requests are being trimmed; or your connection was never the bottleneck.
What to do: Confirm /etc/sysctl.d/99-gorilla-network.conf is installed and active. The gains are largest on slow, shared, or high-latency links — on a fast local line you may notice little.

**You read an older note claiming this room blocks telemetry and are confused.**
That claim was true of a since-reverted version and was corrected on 2026-08-03.
What to do: Trust the current four patches: they contain no telemetry code. Privacy/telemetry work is in the locked settings and in topic 13.TELEMETRY.KILL.

## Why a Developer Would Do This

A developer makes these choices because the browser and the kernel are two halves of one machine, and stock Firefox assumes a rich-world broadband line that the target user does not have. Matching Firefox's buffer sizes and timers to the custom kernel's BBR/FQ-CoDel design — and making the code degrade gracefully when the kernel is not tuned — is the difference between a page that loads and one that gives up on a slow or shared connection.

## Why It Matters That You Can Read This

You cannot read C++ to check this, and you should not have to. What you can do is check that the claims here match the code, because both are in the same folder with line numbers. This guide points you at HttpConnectionUDP.cpp line 301 for the 64 MB number and line 311 for the 4 MB number; anyone can open those and see the exact figures. A closed browser would ship these numbers with no way to see them, no way to know a past version had a bug, and no way to correct a documentation mistake in public. This room already demonstrates the value: an earlier draft's false claims were caught precisely because the code was open and dated.

## Glossary

**Necko** — Firefox's internal name for all of its networking code.

**Buffer** — A temporary holding area in memory for data waiting to be sent or processed.

**TCP** — The common, reliable way two computers hold a connection and exchange an ordered stream of data.

**UDP / QUIC / HTTP/3** — A newer, faster way to load pages that sends data as individually addressed packets; used by YouTube, Cloudflare and Google.

**DNS** — The internet's phonebook, which turns a name like example.com into a numeric address.

**BBR** — A congestion-control method that measures the connection's real speed and paces packets to match.

**FQ-CoDel** — A queueing method that keeps one heavy flow from freezing everyone else on a shared line.

**Keepalive** — A tiny periodic packet that keeps an idle connection from being silently killed by a router.

**Negative DNS cache** — Firefox's short memory of a failed name lookup so it does not immediately retry; shortened here from 60 seconds to 3.

**Bandwidth-delay product** — How much data can be in flight on a connection at once — its speed times its round-trip delay; it sets the smallest buffer that keeps the link full.

**sysctl** — The Linux mechanism for reading and setting kernel tuning knobs, such as the maximum socket buffer size.

**Graceful degradation** — Continuing with a smaller/simpler result when the ideal one is not available, instead of failing outright.

## Claim Sources

| Claim | Basis | Evidence |
|-------|-------|----------|
| Topic is four patch files, no telemetry code | 📄 stated in input | Siblings: netwerk_base_nsSocketTransport2.cpp.patch, netwerk_dns_nsHostResolver.cpp.patch, netwerk_protocol_http_HttpConnectionUDP.cpp.patch, netwerk_protocol_http_nsHttpTransaction.cpp.patch |
| Receive buffer hard-coded to 64 MB (67108864) | 📄 stated in input | rv = mSocket->SetRecvBufferSize(67108864);  // 64MB |
| Send buffer set to 4 MB (4194304) | 📄 stated in input | rv = mSocket->SetSendBufferSize(4194304); |
| Buffers degrade gracefully instead of aborting | 📄 stated in input | // Do not abort — graceful degradation. |
| Vanilla aborted on receive-buffer failure | 📄 stated in input | -    mSocket->Close();
-    mSocket = nullptr;
-    return rv; |
| TCP keepalive 15s idle / 5s interval / 3 probes | 📄 stated in input | int32_t keepIdle = 15;
 int32_t keepIntvl = 5;
 int32_t keepCnt = 3; |
| DNS thread limit 16, idle 12 | 📄 stated in input | SetThreadLimit(16)) ... SetIdleThreadLimit(12)) |
| NEGATIVE_RECORD_LIFETIME 60 -> 3 | 📄 stated in input | static const unsigned int NEGATIVE_RECORD_LIFETIME = 3; |
| Upload chunk 256 KB for uploads over 10 MB | 📄 stated in input | if (mRequestSize > 10 * 1024 * 1024 && readCount > kGorillaUploadChunkSize) |
| 64 MB buffer justified by transoceanic BDP ~18.75 MB | 📄 stated in input | BDP = 125 MB/s * 0.150 s = 18.75 MB ... maximum socket buffer is configured at 64 MiB (Reports/06-MATHEMATICAL-DERIVATIONS.md 6.2) |
| 4 MB send buffer justified by 1 Gbps x 32 ms BDP | 📄 stated in input | 1000 Mbps * 0.032 s = 4 MB (master log Part 4) |
| Kernel contract file raises rmem_max/wmem_max to 64 MB | 📄 stated in input | net.core.rmem_max = 67108864 / net.core.wmem_max = 67108864 in /etc/sysctl.d/99-gorilla-network.conf |
| Telemetry fencing was reverted from this room 2026-08-03 | 📄 stated in input | all four files are byte-identical to the vanilla vault; their four .patch files were deleted (POR_2026-08-03_room_clearing.md) |
| No performance numbers were measured for this topic | 🤖 model inference | *(none — model judgment)* |
| keepalive/DNS/chunk values have no formal kernel-side derivation | 🤖 model inference | *(none — model judgment)* |


---
**How to verify this document:**
`📄 stated in input` — the model's phrasing of something your source text said.
Find the matching line in the original to verify.
`🤖 model inference` — the model's own judgment or synthesis. Treat as opinion,
not measurement. Re-run on the same input and check whether specific numbers
stay consistent between runs.

*Human Track. Its Developer Track twin covers the same changes in technical detail. Neither is a simplified copy of the other — they are the same truth in two languages.*