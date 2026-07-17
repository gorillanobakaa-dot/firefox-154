# 🧍 The Networking Overhaul — Matching Firefox to a Custom Kernel and a Slow Internet Line — Plain English Guide

> *Topic `03-networking` of the Gorilla Unleashed Firefox 154 build · Written for everyone · 2026-07-16*

---

## 🌍 The Big Picture

Every web page you load is a conversation between your browser and a server on the other side of the world. That conversation happens in tiny packets that travel across dozens of routers, each one deciding when to pass your packet on and when to make it wait in a queue. The rules that govern this — how big the queues are, how long to wait before giving up, how many things to ask about at once — are set in a hundred different places, from your kernel to your browser to the router in your bedroom. When those settings match, the internet feels fast. When they fight each other, the same connection feels sluggish and unreliable.

This patch group re-tunes Firefox's network stack (the part of the browser called *Necko*) so it stops fighting our custom Linux kernel and starts collaborating with it. The kernel was built for two modern algorithms — **BBR** and **FQ-CoDel** — that squeeze the best possible speed out of any given connection, especially a slow or unreliable one. Firefox's stock settings assume a fast broadband line at the client end, so a lot of its behaviour is subtly wrong for the machine and the network it is running on. This is the corrective.

At the same time, every place where Firefox was quietly opening a background connection to phone home telemetry — even in the *networking* layer, the last place you'd expect it — was found and severed. Those connections cost you: bandwidth you paid for, battery to run the radio, and (on metered mobile data in the developing world) actual money per megabyte.

### 🌍 Who this is really for

Same audience as the other topics: **the person on old hardware, and now especially on a slow or expensive internet connection.** In a rural village on a 3G tower, or on a wired connection where the whole neighbourhood shares one flaky uplink, the difference between a browser that respects BBR's pacing and one that dumps traffic in giant bursts is the difference between a webpage that loads and one that gives up. The default 60-second DNS negative cache — where a single failed lookup makes Firefox refuse to try again for a full minute — is a first-world assumption; on a mobile network where addresses shift every few seconds, it is a wall between the user and the internet. This patch group knocks that wall down.

And every telemetry connection removed is one less byte off the user's monthly data cap. **Mozilla's diagnostics were not free.** They were paid for, out of pocket, by whoever was on the other end of an expensive megabyte.

## 🎭 The Main Characters

| Name | What It Is | Real-World Comparison |
|---|---|---|
| **Necko** | Firefox's networking stack — the code that speaks TCP, UDP, HTTP, DNS, everything net-facing | The mail room of a giant office building — every letter in or out passes through it |
| **BBR** | A modern congestion-control algorithm (developed at Google) that senses the actual bottleneck bandwidth and paces packets to it, instead of just crashing traffic into the queue until it drops packets | A driver who watches the road ahead and adjusts speed smoothly, versus one who floors the accelerator until they rear-end the car in front |
| **FQ-CoDel** | A queueing algorithm that stops any single connection from hogging the shared internet pipe — even when the pipe is small and shared | A supermarket that opens a new express lane whenever one shopper's giant cart starts blocking everyone else |
| **TCP Keepalive** | A tiny 'you still there?' packet the browser sends every so often to keep a connection from being killed by an idle timer on a router | The 'are we still on the line?' you say into the phone when the other person has been quiet for too long |
| **DNS** | The phonebook of the internet — turns names like 'youtube.com' into numeric addresses. Slow DNS = slow-feeling browser, even when everything else is fast. | The receptionist who looks up the extension for the person you're trying to call — if she's slow, the whole call feels slow |
| **UDP / QUIC / HTTP/3** | The newer, faster way to load web pages — used by YouTube, Cloudflare, and increasingly everyone. Runs over UDP instead of TCP, which needs its own tuning | Sending letters as individually-addressed postcards (UDP) instead of waiting for a fully-sealed envelope to arrive intact (TCP) — faster if handled right, chaotic if not |
| **Buffer Bloat** | The disease where routers hold onto packets for too long, thinking they're being helpful. Feels like lag and stutter to the user. | A restaurant that seats you but then holds all the orders in the kitchen 'to batch them up efficiently' — you wait forever for a burger |

## 🔢 How It Works — Step by Step

### Step 1: Bigger receive buffers for video (64 MB)

When you watch a high-definition video, the server sends packets faster than Firefox can process them into pixels. If Firefox's incoming buffer is too small, packets get dropped and the video stutters. The receive buffer is now sized up to 64 megabytes — enough to swallow a big burst of video without dropping a frame. The kernel's own limit (`net.core.rmem_max`) has to be raised to match, which is done in `/etc/sysctl.d/99-gorilla-network.conf`. Firefox and the kernel now agree on how big the incoming pipe can be.

### Step 2: A matching UDP send buffer for uploads (with a safety cap)

For a long time, the download side was widened while the upload side was left at the kernel's tiny default. That created an asymmetric highway: 8 lanes in, 1 lane out. Video calls and file uploads would bottleneck on the exit ramp. The fix is now in: an explicit UDP send buffer is set, sized deliberately for safety. The audit log spelled out the trade-off: a giant 32 MB per socket × 16 concurrent QUIC streams = 512 MB of memory locked up before you even watch anything. So the size chosen is much more modest — enough to saturate a 1 Gbps uplink at typical internet latency, without hogging RAM.

### Step 3: Aggressive TCP keepalives (15 s / 5 s / 3 probes)

Cheap internet gear — home routers, phone-carrier NAT boxes, ISP middleware — often silently drops any TCP connection that has been idle for a minute or two, without telling either end. Firefox then discovers this by hanging when you go to reload the page. The fix is to send a keepalive probe every 15 seconds of idle, and a follow-up every 5 seconds after that, up to 3 probes. Cheap gear now can't silently drop the connection — Firefox notices it's dead and reconnects.

### Step 4: More DNS workers (16 threads, 12 idle-hot)

The default of 8 DNS workers is fine when every page is one domain. Modern pages fetch resources from 50 different domains (ads, CDNs, analytics, fonts, images from 12 different hosts). With only 8 workers, DNS lookups queue up and pages 'feel slow' even when the network is fast. Sixteen workers, twelve of them staying warm, is roughly double the throughput at essentially zero memory cost.

### Step 5: DNS negative cache: 60 → 3 seconds

Historically, if a DNS lookup failed, Firefox remembered that failure for a full minute — refusing to try again in the meantime. On a stable network that's harmless. On a mobile network where cell towers shift addresses, or on a signaling server that just rebooted, that 60-second wall means the user gives up before the network heals. The lifetime is now 3 seconds. A dead lookup is retried almost immediately.

### Step 6: Upload pacing for big files (BBR-aware, ≥ 10 MB)

Uploading a big file? Firefox used to just fire off huge chunks and let the operating system deal with the mess. That confused BBR's pacing logic — it measures the network by watching how packets get through, and giant bursts distort that measurement. Now, for uploads over 10 MB (which is where BBR's pacing actually matters — smaller uploads finish before BBR notices), Firefox reads the outgoing data in 256 KB paced chunks. Small uploads are still fast; big ones no longer wreck BBR's measurement of the connection.

### Step 7: Telemetry connections severed inside the network layer itself

The place you would least expect background telemetry is inside the *networking* code — but there it was. `HttpChannelParent.cpp`, `nsHttpConnectionMgr.cpp`, `Http3Session.cpp`, `nsUDPSocket.cpp` all had Glean metrics buried in them, silently phoning home when connections opened or closed. Every one of those metric hooks is now wrapped in `#ifndef GLEAN_DISABLED` and disabled at compile time. Zero background connections. Zero bytes sent home.

## 🤔 Quirky Things Worth Knowing

### ⚠️ Firefox's default assumptions are shaped by rich internet

The stock Firefox network settings assume you have a fast, unmetered, reliable broadband line. Big buffers everywhere, long timeouts, generous negative caches. On a good line, that's fine. On a slow, laggy, or metered line — the reality for a huge chunk of the world — those defaults amplify every problem: bloated queues, stale caches, unnecessary background traffic. This patch group is that world's rebuttal.

### ⚠️ The kernel had to be re-tuned to match, and vice-versa

The 64 MB receive buffer on the Firefox side is useless if the kernel refuses to grant it. So a companion file `/etc/sysctl.d/99-gorilla-network.conf` sets `net.core.rmem_max`, `net.core.wmem_max`, and enables BBR and FQ-CoDel at the kernel level. Neither piece works without the other — the machine has to think as one thing, not seven arguing pieces.

### ⚠️ The 'web-consumer bias' baked into every browser

As the audit log put it in the developer track: browsers historically assume clients only download. Everything is tuned for download: buffers, congestion, cache. Uploads are treated as bursty afterthoughts, so their pacing is bad. This is exactly the wrong assumption for someone using video calls to see family abroad, or uploading school assignments over a rural connection. The upload path is treated as a first-class citizen here.

### ⚠️ Every knob was measured, not guessed

The 4 MB UDP send buffer size is not arbitrary — it comes from a calculation: 1 Gbps upload × 32 ms latency ≈ 4 MB (this is called the *bandwidth-delay product*). It's the smallest buffer that keeps the pipe full without wasting memory. Sixteen DNS threads is roughly the concurrency needed by a modern web page. The 10 MB pacing threshold is where BBR's benefit exceeds its overhead. This is not vibes — it's arithmetic, and the arithmetic is in the log.

## 💻 What Does This Mean For YOU?

### 🔋 Battery, Speed & Memory

Fewer background connections (telemetry gone) means less radio use, which means less battery drain — especially on laptops on Wi-Fi and phones on cellular. RAM usage is deliberately capped: the upload buffer size was picked to prevent a hundreds-of-megabytes-of-buffers scenario on a heavy browsing session.

### ⚡ Speed

Pages that touch many domains (which is most modern pages) feel faster because DNS lookups no longer queue behind each other. Video that used to stutter no longer stutters, because the buffer can absorb a burst. Uploads that used to bottleneck no longer bottleneck. TCP connections that used to silently die at NAT boxes now stay alive.

### 🕵️ Your Privacy

Every background metric that used to be sent to Mozilla from the networking layer is severed. No opening a connection to log that a connection was opened. This is the *networking-layer* telemetry excision; the broader telemetry kill lives in Topic 13.

### 🌐 Your Internet

This is the topic where the internet actually gets faster and cheaper — cheaper because of the bandwidth NOT spent on background telemetry. On a metered mobile plan where every megabyte costs real money, that is not a footnote.

## 🔴 The Kill Switch — Explained

**What it is:** There isn't one master toggle for this topic — the changes are structural (buffer sizes, thread counts, timeouts) rather than an on/off feature. But every change is a specific numeric tuning that can be reverted independently: change 16 back to 8 for DNS threads, remove the SetSendBufferSize call, delete the `GLEAN_DISABLED` defines. Nothing here is welded shut.

**Without it:** Without the tuning: video stutters on high-bitrate content, uploads bottleneck, TCP connections silently die at NAT boxes, DNS lookups queue up, telemetry connections open in the background on every page load, and BBR (in the custom kernel) is confused by giant uncontrolled bursts. In short, the modern web feels like the machine is old — even though the network stack is what's actually the bottleneck.

**Think of it like:** Not one switch but a whole car service: bigger fuel line (buffers), synchronised transmission (BBR pacing), faster restart on stall (keepalives), more mechanics on shift (DNS threads), and the tracking device removed from under the chassis (telemetry excision). Each piece independently valuable; the whole is a car that actually goes.

## 🌐 Open Source & Why It Matters To You

The audit log for this topic — publicly readable, in the same folder as the patches — lists three defects the previous version had, and describes each one in both plain-English and technical form. All three have since been fixed in the code. **A closed browser would have shipped those defects silently and no one outside its company would ever know they existed.** The value of open source here is not abstract: it is a table of past mistakes, published, with fixes tied back to them by line number. If you want to know what changed and why, you can read it. If you disagree with a knob, you can flip it and rebuild. If you find a new bottleneck, you can add it to the list.

## 📖 Glossary (Plain English Dictionary)

**Necko** — Firefox's networking stack. Handles TCP, UDP, HTTP/1/2/3, DNS, sockets — everything net-facing. Name is Mozilla-internal, short for 'network cocoa'.

**TCP** — The most common way computers talk on the internet — a reliable, in-order stream. Every HTTP/1 and HTTP/2 connection uses it.

**UDP / QUIC / HTTP/3** — The newer way — packet-based rather than stream-based, faster to establish and more resilient to lost packets. YouTube, Cloudflare, and Google all use it heavily.

**BBR** — A congestion-control algorithm from Google. Measures the actual bandwidth of the connection and paces packets to match, instead of the older approach of dumping packets until some get dropped and then backing off.

**FQ-CoDel** — A queueing algorithm (Fair Queueing with Controlled Delay). Prevents any single big flow from hogging the whole pipe, and keeps queue lengths short even when the pipe is full.

**Buffer bloat** — The disease of routers holding onto packets for too long, thinking they're being efficient. Manifests as unpredictable lag and stutter.

**Congestion control** — The rules a sender follows to avoid overwhelming the network. Old-school algorithms (Cubic, Reno) drop packets to detect trouble; BBR watches actual throughput instead.

**DNS** — Domain Name System — turns names like `youtube.com` into IP addresses. Every web page load involves several DNS lookups.

**Bandwidth-Delay Product** — How much data can be 'in flight' on a connection at any one time — bandwidth × round-trip delay. A 1 Gbps link with 32 ms latency has a BDP of 4 MB. That's the smallest buffer that can keep the link full.

**TCP Keepalive** — A tiny periodic 'still there?' packet sent on an idle TCP connection to prevent middle-boxes (routers, NATs, firewalls) from silently killing it.

**Negative DNS cache** — When a DNS lookup fails, browsers remember the failure for a while so they don't retry immediately. This build shortens that memory from 60 seconds to 3 seconds — right for dynamic mobile networks, right for signaling servers, right for anyone whose IP changes fast.

**Sysctl** — The Linux command that reads and writes kernel tuning knobs. `sysctl -w net.core.rmem_max=67108864` says 'kernel, please accept sockets requesting up to 64 MB of receive buffer.' This build ships a matching `/etc/sysctl.d/99-gorilla-network.conf` file so the kernel is in the loop.

**Web-consumer bias** — The assumption baked into most browsers that the user is downloading a lot and uploading a little. Convenient for browser-vendors; wrong for anyone doing video calls or uploading assignments over a slow link.

---
*Human Track. Its Developer Track twin (`03-networking.DEVELOPER.md`) covers the same changes in technical detail. Neither is a simplified copy of the other — they are the same truth in two languages.*