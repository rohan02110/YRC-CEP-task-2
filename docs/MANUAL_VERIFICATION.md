# Manual Verification Checklist & Protocol
## Kurukshetra CTF Challenge 3: "The Chakravyuha Cipher"

This document specifies the step-by-step human verification checklist for verifying browser lockdown, DevTools traps, and tamper detection across Chromium (Chrome/Edge) and Gecko (Firefox) browsers.

---

## 1. Test 16 — Standard DevTools Inspection Trap
**Objective:** Verify that opening DevTools immediately traps the debugger, halts execution, records a server-side strike, and renders the Dharma violation screen.

### Execution Steps:
1. Open the application in Google Chrome / Microsoft Edge / Mozilla Firefox.
2. Enter fullscreen mode by clicking **ENTER FORMATION**.
3. Attempt to open Developer Tools via:
   - Pressing `F12` (if not intercepted by keyboard lockdown)
   - Browser menu: `Settings -> More Tools -> Developer Tools`
   - Right-clicking (if contextmenu not intercepted) -> Inspect Element
4. **Expected Result:**
   - The debugger immediately pauses on the jittered `debugger` loop in `debuggerTrap.ts`.
   - The scope panel reveals an isolated closure with zero application secrets or state.
   - Resuming the debugger (`F8` or continue button) immediately re-pauses within 15–50 ms across multiple distinct function frames (`a()`, `b()`, `c()`).
   - The DOM is wiped and replaced by the full-screen *"Dharma has been violated"* interstitial.
   - The server audit log records a `HARD_STRIKE` with detector `dbg_main_timing` or `dbg_worker_paused`.

---

## 2. Test 17 — Breakpoints Deactivated Bypass Attempt
**Objective:** Verify that if an attacker toggles "Deactivate breakpoints" (`Ctrl + F8`) to ignore literal debugger statements, secondary detectors catch the session.

### Execution Steps:
1. Open DevTools with "Deactivate breakpoints" enabled prior to navigation.
2. Navigate to the challenge URL.
3. Observe browser behavior over 15 seconds.
4. **Expected Result:**
   - The **Console Probe** fires as soon as the console panel attempts to render the probe object getter, triggering `dbg_console_probe`.
   - If the main thread is suspended/paused, the **Server Watchdog** detects missed 3-second heartbeats after 10 seconds and invalidates the nonce chain, rendering subsequent requests rejected.
   - The server records a hard strike.

---

## 3. Test 18 — Sources Panel Script Blackboxing Attempt
**Objective:** Verify that if an attacker blackboxes `main.js` in the Sources panel, worker and server traps still engage.

### Execution Steps:
1. In DevTools, right-click `main.js` and select "Add script to ignore list" (blackboxing).
2. Reload and interact with the page.
3. **Expected Result:**
   - The **Web Worker Trap** (`w.ts`) continues executing its own dedicated thread debugger loop.
   - The worker ceases responding with `pong` messages within 500 ms, causing the main thread watchdog to detect `dbg_worker_paused` and trigger the tamper beacon.
   - The server enforces the hard strike and locks the session.

---

## 4. Test Verification Summary Matrix

| Verification ID | Browser | Test Case | Expected Behavior | Status |
|---|---|---|---|---|
| **MV-01** | Chrome / Edge | DevTools Open (Docked) | Debugger loop traps; session wiped; strike recorded | Verified |
| **MV-02** | Chrome / Edge | DevTools Open (Undocked) | Window delta heuristic + timing trap fires | Verified |
| **MV-03** | Firefox | Inspector / Console Open | Console getter probe fires; DOM wiped | Verified |
| **MV-04** | All | Deactivate Breakpoints | Console probe / Server watchdog catches session | Verified |
| **MV-05** | All | Script Blackboxing | Dedicated Web Worker trap triggers watchdog | Verified |
| **MV-06** | All | Clipboard Copy/Paste | Decoy flag injected into clipboard; paste blocked | Verified |
| **MV-07** | All | Fullscreen Exit | Machine re-covered without penalty | Verified |
