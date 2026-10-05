# Kurukshetra CTF — Organizer Runbook (Hardening v2)
## Challenge 3 (Hard): "The Chakravyuha Cipher: Sealed Machine"

---

## 1. Quick Start & Architecture Overview

In v2, all team configurations, wirings, rings, reflectors, null-prefix lengths, and flags are derived dynamically on demand from `MASTER_SEED` using `HMAC-DRBG`. No per-team secret is stored at rest or written to disk.

### Running in Production via Docker
```bash
# 1. Set environment master seed (or use default)
export MASTER_SEED="0x9F82A4C6E1D3B5792468ACE013579BDF2468ACE013579BDF2468ACE013579BDF"

# 2. Build and start containers
docker compose up -d --build

# 3. Check container logs
docker compose logs -f
```

### Running Locally without Docker
```bash
# 1. Install dependencies
python -m venv .venv
.\.venv\Scripts\pip install fastapi uvicorn pydantic pyyaml pytest httpx
cd frontend && npm install && npm run build && cd ..

# 2. Start Uvicorn server
.\.venv\Scripts\python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

---

## 2. Progressive Gate Seals & Challenge Chaining

- **Gate I (Seal of Gandiva):** Reward for solving Challenge 1.
  - Default Flag: `KCTF{GANDIVA_BOW_UNSTRINGED_SECRET}`
  - Unlocks: `enigma_spec.txt`, `rotor_wirings.json`, `rotor_notches.json`.
- **Gate II (Seal of Sanjaya):** Reward for solving Challenge 2.
  - Default Passphrase: `SANJAYAUVACHA`
  - Unlocks: `reflector.json`, `ring_settings.json`, and engages the **Original Celestial Machine**.
  - *Crucial note:* `SANJAYAUVACHA` doubles as the pre-substitution keyword $S$.

*Note on Per-Team Seals:* Challenge 1 and 2 flags are global by default in `config/gates.yaml`. If the competition platform supports per-team flags for Challenges 1 and 2, you can pass custom hashes or configure environment overrides `GATEI_SEAL_SHA256` and `GATEII_SEAL_SHA256`.

---

## 3. Deriving Team Secrets & Verifying Answers

To inspect or verify any team's deterministic instance without exposing secrets to participants:

```bash
# Display answer key in terminal
python tools/derive_team.py --team team_alpha

# Save answer key to organizer/ANSWER_KEY_team_alpha.json
python tools/derive_team.py --team team_alpha --save
```

The output contains:
- Team's specific flag: `KCTF{<WORDS>_<TAG>}`
- Seated 4 wheels from pool of 8
- Start positions (Grundstellung) & Ring settings
- True Reflector pairs & Plugboard pairs
- Null prefix length ($0..11$) & Plaintext

---

## 4. Live Difficulty Dial (Hint Release Schedule)

The Admin API enables organizers to release progressive hints in real time:

```bash
# List all hints and their release status
curl -H "X-Admin-Token: KURUKSHETRA_SACRED_ADMIN_TOKEN_2026" http://localhost:8000/admin/hints

# Release Hint 1
curl -X POST -H "X-Admin-Token: KURUKSHETRA_SACRED_ADMIN_TOKEN_2026" http://localhost:8000/admin/hints/1/release

# Withdraw Hint 1 (if needed)
curl -X POST -H "X-Admin-Token: KURUKSHETRA_SACRED_ADMIN_TOKEN_2026" http://localhost:8000/admin/hints/1/withdraw
```

Released hints immediately appear in all participants' Seven Gates modal dialog.

---

## 5. Collusion Detection & Administrative Operations

### Collusion Detection
If Team A submits Team B's flag, the server immediately:
1. Applies a hard strike to Team A.
2. Imposes a 60-minute lockout (capped at 5 minutes in UI).
3. Logs a `COLLUSION_ALERT` in the audit logs indicating both team IDs.

### Common Admin Tasks

1. **List All Teams and Live Quotas:**
   ```bash
   curl -H "X-Admin-Token: KURUKSHETRA_SACRED_ADMIN_TOKEN_2026" http://localhost:8000/admin/teams
   ```

2. **Pardon a Team (Clear Lockout & Strikes):**
   ```bash
   curl -X POST -H "Content-Type: application/json" \
        -H "X-Admin-Token: KURUKSHETRA_SACRED_ADMIN_TOKEN_2026" \
        -d '{"team_id": "team_xxxxx"}' \
        http://localhost:8000/admin/pardon
   ```

3. **Reset Arrow Budget (Tokens & Lifetime Cap):**
   ```bash
   curl -X POST -H "Content-Type: application/json" \
        -H "X-Admin-Token: KURUKSHETRA_SACRED_ADMIN_TOKEN_2026" \
        -d '{"team_id": "team_xxxxx"}' \
        http://localhost:8000/admin/reset-budget
   ```

4. **Tail Audit Log:**
   ```bash
   curl -H "X-Admin-Token: KURUKSHETRA_SACRED_ADMIN_TOKEN_2026" http://localhost:8000/admin/audit?limit=50
   ```

---

## 6. LAN HTTP vs. HTTPS Notes

- When hosted over plain HTTP on an isolated LAN without TLS certificates, `crypto.subtle` and `navigator.keyboard` will be unavailable in modern browsers.
- The challenge includes an automatic pure-JS SHA-256 / HMAC-SHA256 cryptographic fallback in `frontend/src/net/cryptoFallback.ts`, ensuring zero disruption during on-site LAN operations.
- Security headers (CSP, X-Frame-Options, Cache-Control) and 64KB payload limits are actively enforced by the backend middleware.
