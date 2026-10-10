# 🏹 Kurukshetra CTF — Challenge 3: "The Chakravyuha Cipher"
## Master Technical Specification & Architecture Report

> **Event Name:** Kurukshetra CTF  
> **Challenge Title:** The Chakravyuha Cipher (Hard)  
> **Theme:** The Mahabharata  
> **Flag Format:** `KCTF{...}`  
> **Status:** Production-Ready & Hardened (v2)  
> **Deployment Target:** Render Docker Web Service / Docker Compose  

---

## 1. Executive Summary

**The Chakravyuha Cipher** is a custom, hard-tier cryptography challenge designed for competent Computer Science students and CTF competitors. Based on the 18-day battle of Kurukshetra, the challenge features a web-hosted, 8-rotor Enigma-style cipher machine with double-notch stepping, dynamic plugboards, reciprocal reflectors, a keyword substitution layer $S$, and progressive seal gates.

The v2 Hardening update introduces strict **Information Denial (H1)** to prevent AI code-execution models from solving the challenge autonomously via public telemetry, requiring human intuition to solve riddles, isolate cribs, and execute targeted cryptanalysis.

---

## 2. Technical Architecture & Cryptographic Engine

### 2.1 Cipher Alphabet
The cipher operates over a custom **30-symbol alphabet**:
```
Alphabet (N=30): "ABCDEFGHIJKLMNOPQRSTUVWXYZ{}#_"
```

### 2.2 Master Seed & Deterministic Instance Derivation
To prevent hardcoded solutions, every team receives a unique machine configuration derived from a global `MASTER_SEED` using **HMAC-DRBG (SHA-256)**:
* **Rotor Pool:** 8 distinct 30-symbol rotors ($8P4 = 1,680$ possible ordered 4-rotor permutations).
* **Reflector:** Reciprocal involution over 30 symbols (15 disjoint swap pairs).
* **Plugboard:** 13 disjoint symbol pairs (4 unswapped symbols).
* **Ring Settings:** Derived via the sacred "18" formula:
  $$\text{ring}[n] = (n \times 18) \bmod 30 \quad \text{for } n \in \{1, 2, 3, 4\} \implies [18, 6, 24, 12]$$
* **Pre-Substitution Layer ($S$):** Keyword substitution constructed using `SANJAYAUVACHA` followed by remaining unused alphabet symbols.
* **Null Prefix Padding:** $0 \dots 11$ pseudorandom null symbols prepended to plaintext.

### 2.3 Double-Notch Stepping Mechanism
The 4-rotor machine implements authentic double-notch stepping (middle rotor anomaly):
```python
if rotors[2].at_notch():       # Slot 3 (middle-left)
    rotors[2].step()
    rotors[1].step()
elif rotors[3].at_notch():     # Slot 4 (fast rightmost)
    rotors[2].step()
rotors[3].step()
```

---

## 3. Seven Seal Gates & Information Denial

The challenge employs progressive seal gates to ensure information denial on public surfaces:

| Gate | Requirement | Wrong Answer Penalty | Unlocked Assets & Surface |
| :---: | :--- | :--- | :--- |
| **Gate 0** | Public Access | None | Training Replica endpoint (`/api/machine/replica`), static public config (`replica_config.json`), `enigma_spec.txt`. |
| **Gate I** | Submit `KCTF{GANDIVA_BOW_UNSTRINGED_SECRET}` | **3 Minutes (180s) Lockout** | Unlocks Fragment A in `flavor.txt` (the opening salutation riddle). |
| **Gate II** | Submit `SANJAYAUVACHA` | **5 Minutes (300s) Lockout** | Unlocks `ciphertext.txt`, `rotor_wirings.json`, `rotor_notches.json`, and Original Machine live endpoints (`/api/machine/step`). |

---

## 4. Rate Limiting, Budgets & Anti-Bruteforce Defenses

To enforce offline cryptanalysis over brute-force server hammering, strict budgets are enforced:

* **Token Bucket:** 400 token capacity, refilling at 400 tokens/hour.
* **Lifetime Keypress Cap:** Hard ceiling of 2,000 keypresses per team.
* **Chakra Reset:** Deducts 30 tokens to reset machine position to initial state.
* **Gate Wrong Answer Penalties:**
  * **Gate I:** 3-minute (180s) lockout on wrong seal submission.
  * **Gate II:** 5-minute (300s) lockout on wrong seal submission.
  * **Active Penalty Denial:** During the lockout penalty, the server rejects all flag submissions and seal offerings (HTTP 423 Locked).
* **Strike System & Lockouts:** Incorrect flag submissions ladder up to a maximum of **300 seconds (5 minutes)**.
* **Client Lockdown & Honeypots:** Includes infinite loop debugger traps, console clearing, shortcut blocks (`F12`, `Ctrl+Shift+I`), and honeypot routes (`/tactical_dispatch.txt`, `/robots.txt`).

---

## 5. Intended Solve Path & Reference Solver

```
[ Gate 0 ] --> Submit Gate I Flag --> [ Gate I Unlocked ]
                                              |
                                     Solve Riddle in Fragment A
                                              |
                                              v
[ Gate II Unlocked ] <-- Submit "SANJAYAUVACHA" <-- [ Gate II ]
        |
        +--> Download ciphertext.txt, rotor_wirings.json, rotor_notches.json
        |
        +--> Compute Ring Settings: (n * 18) mod 30 -> [18, 6, 24, 12]
        |
        +--> Perform Crib-Drag Attack over 8P4 (1680) Rotor Orders against crib "DHRITARASHTRAUVACHA"
        |
        +--> Execute Hill-Climbing algorithm for 13 Plugboard Pairs using bigram scoring
        |
        +--> Decrypt Enigma stage -> Invert Layer S -> Obtain Plaintext & Flag
        |
        +--> Submit Flag: KCTF{<WORDS>_<TAG>}
```

Automated verification via [`tools/reference_solver.py`](file:///d:/Kurukshetra/codebase%20C3/tools/reference_solver.py) achieves a **100% solve rate** ($10/10$ test instances solved in under 12 seconds).

---

## 6. Progressive Hints Schedule (2 Hard Cryptic Hints)

The organizers can release 2 progressive text hints live during the CTF competition using the Admin API (`POST /admin/hints/{id}/release`). The hints are intentionally cryptic and embedded in epic Mahabharata lore to prevent direct algorithm disclosure:

### Hint 1: The Unwavering Witness
* **Difficulty:** Hard (Cryptic Lore Nudge)
* **Text:** *"When darkness shrouded the battle of eighteen days, a single narrator was granted divine vision to speak the unfolding truth to the sightless throne. His sacred name and formula bind the tongue before the wheels begin to turn."*
* **Cryptographic Objective:** Cryptically hints at Sanjaya (`SANJAYAUVACHA`, the Gate II passphrase & Keyword Substitution layer $S$) and the opening salutation formula (`DHRITARASHTRAUVACHA`).

### Hint 2: The Harmony of Eighteen
* **Difficulty:** Hard (Mathematical & Cryptanalytic Nudge)
* **Text:** *"Eighteen akshauhinis assembled upon the sacred field, and for eighteen suns the concentric spirals of the Vyuha held firm. Let the sacred count of the war govern the rhythm of each wheel's inner ring, while the narrator's first utterance guides your offline search through the seating of the wheels."*
* **Cryptographic Objective:** Cryptically hints at the 18-based ring setting rule (`ring[n] = (n * 18) mod 30`) and performing an offline 4-rotor permutation search ($8P4 = 1,680$) using the opening crib.

---

## 7. Project Structure & Key Files

```
codebase C3/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI main application & middleware
│   │   ├── engine.py          # Cryptographic Enigma & Layer S engine
│   │   ├── db.py              # SQLite WAL persistence layer
│   │   ├── rules.py           # Token bucket, lockouts, seal gate logic
│   │   ├── admin.py           # Admin API (/admin/*)
│   │   └── honeypots.py       # Decoy endpoints & honeypot flags
│   └── tests/                 # 37 pytest integration & unit tests
├── config/
│   ├── gates.yaml             # Seal gate definitions & SHA-256 hashes
│   ├── hints.yaml             # Progressive hint release configuration (2 Hard Hints)
│   └── rules.yaml             # Rate limits, token bucket, lockout caps
├── frontend/
│   ├── src/                   # Vite / TypeScript obfuscated frontend UI
│   └── obfuscator.config.json # JavaScript Obfuscator rules
├── public_artifacts/          # Public CTF files (ciphertext, flavor, spec)
├── tools/
│   ├── derive_team.py         # Team instance generator
│   ├── generate_instance.py   # Master seed instance generator
│   ├── reference_solver.py    # Automated offline cryptanalysis solver
│   └── audit_strings.py       # Pre-commit CI string leak auditor
├── Dockerfile                 # Multi-stage production container build
├── docker-compose.yml         # Local container orchestration
├── .env.example               # Master environment variable template
├── report.md                  # Master challenge report
└── idea.md                    # Original design blueprint
```

---

## 8. Deployment Quick Reference (Render / Docker)

### Environment Variables
```dotenv
MASTER_SEED=0x9F82A4C6E1D3B5792468ACE013579BDF2468ACE013579BDF2468ACE013579BDF
ADMIN_TOKEN=KURUKSHETRA_SACRED_ADMIN_TOKEN_2026
MAX_LOCKOUT_SECONDS=300
TOKEN_CAPACITY=400
TOKEN_REFILL_PER_HOUR=400
LIFETIME_KEYPRESS_CAP=2000
RESET_CHAKRA_COST=30
DATABASE_PATH=/data/chakravyuha.db
```

### Docker Build & Launch
```bash
# Build & start container
docker compose up -d --build

# Run test suite
pytest backend/tests

# Run pre-push string audit
python tools/audit_strings.py
```
