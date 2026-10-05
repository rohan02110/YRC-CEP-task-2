# Security Architecture & Threat Model Notes
## Kurukshetra CTF Challenge 3: "The Chakravyuha Cipher"

---

## 1. Core Architectural Boundary

> **The browser is an untrusted keyboard and display. The server is the machine.**

In accordance with Section 3 of the Build Brief, the security of Challenge 3 rests entirely on **server-side validation and secrets isolation**. No cryptographic secrets, algorithms, or shortcuts are ever present on the client.

### Server-Enforced Invariants:
1. **Zero Client Secrets:** The rotor wirings, start positions, reflector mapping, plugboard pairs, and plaintext flag reside exclusively on the server and in the SQLite database.
2. **Deterministic Mechanical Stepping:** The server steps the machine on every valid keypress and returns only the resulting output symbol, new positions, and stepped flags.
3. **Token Bucket & Lifetime Cap:** Rate limits (capacity 400, refill 400/hr, lifetime 2000 arrows) are calculated and enforced atomically in the database.
4. **Nonce & Sequence Chains:** Out-of-order, duplicate, or replayed requests are rejected without advancing the machine state.
5. **Lockout Ladders & Strikes:** All penalties, lockouts, and bans are managed server-side.

---

## 2. Client-Side Deterrent Layers

Client-side protections are **speed bumps** designed to raise the barrier to inspection during live play:

1. **Capture-Phase Keyboard Blocker:** Intercepts shortcut combinations (`Ctrl+C`, `Ctrl+V`, `Ctrl+Shift+I`, `F12`, etc.) in the capture phase before default handlers can trigger.
2. **Clipboard Poisoning:** Copy/cut events automatically overwrite the system clipboard with registered decoy flags (`KCTF{ABHIMANYU_NEVER_LEARNED_TO_EXIT}`), penalizing automated scraper scripts.
3. **Multi-layer Debugger Traps:** Jittered debugger loops on the main thread and dedicated Web Worker threads create continuous pause cycles when DevTools is active.
4. **Code Obfuscation:** `javascript-obfuscator` applies control flow flattening, dead code injection, and string encryption (`rc4`), rendering decompiled client logic opaque.

---

## 3. Accepted Browser Limitations (Unblockable by Design)

Modern web browsers enforce strict security sandboxes that intentionally prevent JavaScript from overriding certain OS-level and browser-level actions:

| Mechanism | Browser / OS Behavior | Architectural Countermeasure |
|---|---|---|
| **`Ctrl + W` / `Ctrl + T` / `Ctrl + N`** | Handled directly by browser process; JavaScript cannot prevent tab closing or new window creation. | Single-session locking on the server; opening new tabs invalidates previous session state. |
| **Browser Native Menu / Address Bar** | User can access DevTools via browser menu (`More Tools -> Developer Tools`). | Main thread and Web Worker timing traps fire within milliseconds of DevTools attaching, triggering tamper beacons. |
| **Local Overrides / Request Interception** | DevTools Local Overrides and tools like Burp Suite can modify client JS or craft raw HTTP requests. | The client holds zero secrets. Raw HTTP requests must still satisfy sequence numbers, rolling nonces, and arrow token budgets. |
| **OS Shortcuts (`Alt+Tab`, `Win+D`)** | Handled directly by OS window manager. | Window focus loss / blur is **explicitly not penalized**, allowing participants to legitimately run external scripts and solvers. |
