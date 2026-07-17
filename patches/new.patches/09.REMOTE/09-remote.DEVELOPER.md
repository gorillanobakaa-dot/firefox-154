# Remote Automation Lockdown — Marionette + Remote Agent Hard Disable — Developer Track

> **Topic:** `09-remote` · **Files:** `remote/components/Marionette.sys.mjs`, `remote/components/RemoteAgent.sys.mjs`
> **Generated:** 2026-07-16

---

## Module Summary

Three-layer dead-code lockdown of both browser-automation channels. Marionette: instance `enabled = false` at construction, `set enabled(value)` setter body removed, `--marionette` CLI flag branch dead-coded. Remote Agent (WebDriver BiDi): identical treatment with `#enabled = false`, `#allowSystemAccess = false`, setters dead-ended, `--remote-debugging-port` branch dead-coded. Trade-off explicit: browser is unusable with Selenium/WebDriver by design.

## Architecture

- **Pattern:** Belt-and-suspenders dead-coding at three independent activation surfaces per channel.
- **Trust Boundary:** Removes a browser-automation channel that would otherwise be a listening socket. Substantial attack-surface reduction for targeted-attack scenarios.
- **Attack Surface:** Two fewer listening TCP sockets in the browser process.

## Kill Switches

### `Marionette.sys.mjs — `enabled` init + setter + CLI parser branch` — HARD ⚠️

- **Condition:** compile-time (source-level dead-coding)
- **Effect:** Marionette cannot be turned on by any means short of source edit + rebuild.
- **Reversibility:** reversible
- **Notes:** Rebuild required.

### `RemoteAgent.sys.mjs — `#enabled` init + `#allowSystemAccess = false` + setters + CLI parser branch` — HARD ⚠️

- **Condition:** compile-time
- **Effect:** WebDriver BiDi Remote Agent cannot be turned on. Same three-layer redundancy.
- **Reversibility:** reversible
- **Notes:** Rebuild required.

## Performance Profile

- **CPU:** Marginal.
- **Memory:** Marginal.
- **I/O:** One or two fewer TCP listeners.
- **Timer Interval:** N/A

## Security Analysis

### User Profiling

N/A

### Targeting

Removes a class of remote-attack surface. If an attacker reaches localhost (via XSS-in-browser, malicious-extension escape) they cannot enable a browser-automation socket.

### Trust Chain

N/A

### Abuse Potential

Substantial reduction: browser-automation-socket abuse is a documented attack pattern for targeted browser exploitation.

## Implementation Flow

1. **`Marionette constructor`** — Sets `this.enabled = false`.
   *Side effects:* Instance starts disabled.
2. **`Marionette setter`** — Setter body dead-ended.
   *Side effects:* External code calling `Marionette.enabled = true` has no effect.
3. **`startup CLI parse for --marionette`** — Flag parses but branch does nothing.
   *Side effects:* No socket bound.
4. **`RemoteAgent equivalent (three sites)`** — Same pattern for WebDriver BiDi.
   *Side effects:* No listening socket.

## Technical Debt

🟢 **ACCEPTED** — Automated-testing capability gone — cannot self-verify with Selenium
  - *Recommendation:* Documented trade-off. Testing lives elsewhere (headless CI on stock Firefox).

## Impact If Removed / Disabled

Selenium/WebDriver/BiDi tooling would work — and so would any attacker who could poke localhost.

## Testing Notes

`ss -tlnp | grep -E ':2828|:9222'` — expect no output. Try `firefox --marionette --remote-debugging-port=9222` — flags accepted, no sockets bound.

## Changelog Notes

Locked down 2026-07-06. Cross-references 12.MOZAMBIQUE.DRILL for parallel Normandy/Nimbus lockdown pattern.

---
*Developer Track. Human Track twin: `09-remote.LAYMAN.md`.*