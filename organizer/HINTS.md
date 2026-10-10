# ORGANIZER HINTS SCHEDULE & LIVE DIAL

The following **2 progressive hints** can be released live during the CTF using the Admin API:
- `POST /admin/hints/{id}/release`
- `POST /admin/hints/{id}/withdraw`

Released hints automatically appear in real-time in all participants' Seven Gates panel via `GET /api/v1/hints`.

---

### Hint 1 (Difficulty: Hard — Cryptic Lore Nudge)
- **Title:** The Unwavering Witness
- **Text:** *"When darkness shrouded the battle of eighteen days, a single narrator was granted divine vision to speak the unfolding truth to the sightless throne. His sacred name and formula bind the tongue before the wheels begin to turn."*
- **Purpose:** Cryptically hints at Sanjaya (`SANJAYAUVACHA`, Gate II passphrase & Keyword Substitution layer $S$) and the opening salutation formula (`DHRITARASHTRAUVACHA`).

---

### Hint 2 (Difficulty: Hard — Mathematical & Cryptanalytic Nudge)
- **Title:** The Harmony of Eighteen
- **Text:** *"Eighteen akshauhinis assembled upon the sacred field, and for eighteen suns the concentric spirals of the Vyuha held firm. Let the sacred count of the war govern the rhythm of each wheel's inner ring, while the narrator's first utterance guides your offline search through the seating of the wheels."*
- **Purpose:** Cryptically hints at the 18-based ring setting rule (`ring[n] = (n * 18) mod 30`) and performing an offline 4-rotor permutation search ($8P4 = 1,680$) using the opening crib.

---

## Admin API Quick Reference

```bash
# Release Hint 1
curl -X POST http://localhost:8000/admin/hints/1/release \
     -H "X-Admin-Token: KURUKSHETRA_SACRED_ADMIN_TOKEN_2026"

# Release Hint 2
curl -X POST http://localhost:8000/admin/hints/2/release \
     -H "X-Admin-Token: KURUKSHETRA_SACRED_ADMIN_TOKEN_2026"

# List All Hints & Status
curl http://localhost:8000/admin/hints \
     -H "X-Admin-Token: KURUKSHETRA_SACRED_ADMIN_TOKEN_2026"
```
