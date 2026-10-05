# ORGANIZER HINTS SCHEDULE & LIVE DIAL

The following 6 progressive hints can be released live during the CTF using the Admin API:
- `POST /admin/hints/{id}/release`
- `POST /admin/hints/{id}/withdraw`

Released hints automatically appear in real-time in all participants' Seven Gates panel via `GET /api/v1/hints`.

---

### Hint 1 (Difficulty: Low)
- **Title:** The Opening Utterance
- **Text:** *"The scroll's first words are a speaker's name followed by an ancient word meaning 'spoke'."*
- **Purpose:** Clarifies Fragment A if teams are unfamiliar with epic Sanskrit literary formatting.

---

### Hint 2 (Difficulty: Low-Medium)
- **Title:** The Blind King's Inquiry
- **Text:** *"The speaker is the first one to speak in the great song's very first verse (Gita 1.1)."*
- **Purpose:** Nudges teams to Gita 1.1 (*Dhritarashtra Uvacha*).

---

### Hint 3 (Difficulty: Medium)
- **Title:** Idle Strokes of the Scribe
- **Text:** *"Some idle symbols (null prefix) come before the first word to steady the hand."*
- **Purpose:** Nudges teams to test offsets $k \in \{0, 1, \dots, 11\}$ for the crib alignment.

---

### Hint 4 (Difficulty: Medium-High)
- **Title:** The Rearranged Tongue
- **Text:** *"The wheels are not the first lock on the speech: a rearranged tongue lies in front of them."*
- **Purpose:** Clarifies that the Enigma stage decrypts to $S(\text{plaintext})$ rather than directly to raw English/Sanskrit.

---

### Hint 5 (Difficulty: High)
- **Title:** The Narrator's Key
- **Text:** *"The rearranging uses the narrator's name and formula as a keyword, with the unused symbols following in their usual order."*
- **Purpose:** Reveals the exact keyword substitution construction formula using the narrator's formula (`SANJAYAUVACHA`, the Challenge 2 passphrase).

---

### Hint 6 (Difficulty: Direct Nudge)
- **Title:** Testing the Wheels
- **Text:** *"The final wheel order is among those you can test with a good crib in your offline simulator."*
- **Purpose:** Confirms that offline search over seated permutations against $S(\text{opener})$ will isolate the true rotor order.

---

## Admin API Quick Reference

```bash
# Release Hint 1
curl -X POST http://localhost:8000/admin/hints/1/release \
     -H "X-Admin-Token: KURUKSHETRA_SACRED_ADMIN_TOKEN_2026"

# List All Hints & Status
curl http://localhost:8000/admin/hints \
     -H "X-Admin-Token: KURUKSHETRA_SACRED_ADMIN_TOKEN_2026"
```
