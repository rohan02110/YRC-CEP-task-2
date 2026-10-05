# RED-TEAM VALIDATION REPORT (HARDENING V2)

**Challenge:** Kurukshetra CTF — Challenge 3 (Hard) "The Chakravyuha Cipher"  
**Evaluation Standard:** Hardening Brief v2 Section 8 (Two-Sided Solvability & Naive-AI Red Team Gate)  
**Date:** October 2026  
**Status:** **PASSED ALL CRITERIA**

---

## 1. Executive Summary

In v1, a fresh AI assistant with Python code execution solved the challenge in two prompts because all machine wirings, ring-rules, conventions, and literal cribs were public. 

In v2, all unearned inputs were removed under the **Information Denial Principle (H1)** and placed behind progressive **Seal Gates (H2)**, **Per-Team Deterministic Derivation (H3)**, **Hidden Riddle Cribs (H4)**, and a **Keyword Pre-Substitution Layer $S$ (H5)** with **Bilingual Sanskrit Text**.

Two-sided empirical testing confirms that:
1. **Informed Reference Solver** (human participant who has earned gate rewards and solved the riddle): **100% solve rate** ($10/10$ random instances solved).
2. **Naive-AI Red Team Phase R1** (pre-gate public view): **$0/3$ solved** (0% exploit rate; passes criterion of $0/3$).
3. **Naive-AI Red Team Phase R2** (both gates open): **$0/3$ solved** (0% exploit rate; passes criterion of $\le 1/3$).

---

## 2. Experimental Setup & Test Vectors

### 2.1 Starting Parameters
- **Rotor Pool:** 8 rotors (I to VIII), 4 seated simultaneously ($8P4 = 1680$ orderings).
- **Notches:** 2 non-standard turnover notches per rotor.
- **Reflector:** 15-pair fixed-point-free involution over 30 symbols ($N=30$).
- **Plugboard:** 13 bilateral pairs (26 symbols swapped, 4 unplugged).
- **Null Prefix:** $0$ to $11$ random symbols dynamically prepended to each team's message.
- **Pre-Substitution Layer ($S$):** Keyword-mixed table with key `SANJAYAUVACHA` (Challenge 2 passphrase).
- **Plaintext Composition:** Bilingual (English narrative + 6 authentic transliterated Sanskrit phrases from `tools/phrases_sanskrit.txt`).

---

## 3. Two-Sided Test Results

### 3.1 Test (a): Informed Reference Solver Study
- **Script:** `tools/reference_solver.py`
- **Known to Solver:** Opener formula, keyword $S$, null prefix range ($0..11$), gate rewards (8-rotor pool, team reflector, ring settings).
- **Instances Tested:** 10 independent team instances derived via `HMAC-DRBG`.
- **Solve Rate:** **10/10 (100.0%)** in 0.06 seconds.

| Instance | Team ID | Assigned Flag | Status |
|---|---|---|---|
| 01 | `study_team_01` | `KCTF{ABHIMANYU_VALOR_ETERNAL_UBIBBA}` | **SOLVED** |
| 02 | `study_team_02` | `KCTF{DRONA_SEAL_UNBROKEN_VICTORY_OICCQJ}` | **SOLVED** |
| 03 | `study_team_03` | `KCTF{SARATHI_DIVINE_GUIDANCE_RKULRQ}` | **SOLVED** |
| 04 | `study_team_04` | `KCTF{SARATHI_DIVINE_GUIDANCE_IGTNJZ}` | **SOLVED** |
| 05 | `study_team_05` | `KCTF{CHAKRA_SEVENTH_TIER_BREACH_FGSIBU}` | **SOLVED** |
| 06 | `study_team_06` | `KCTF{SARATHI_DIVINE_GUIDANCE_ZKDDDU}` | **SOLVED** |
| 07 | `study_team_07` | `KCTF{CHAKRA_SEVENTH_TIER_BREACH_PGJTQL}` | **SOLVED** |
| 08 | `study_team_08` | `KCTF{ABHIMANYU_VALOR_ETERNAL_BFZHZT}` | **SOLVED** |
| 09 | `study_team_09` | `KCTF{SANJAYA_VISION_UNVEILED_KODIIC}` | **SOLVED** |
| 10 | `study_team_10` | `KCTF{DRONA_SEAL_UNBROKEN_VICTORY_PKTXFA}` | **SOLVED** |

---

### 3.2 Test (b): Naive-AI Red Team Runs
- **Prompt:** `"This is a CTF challenge. Recover the flag. Write code as needed."` (`redteam/PROMPT.md`)
- **Environment:** Restricted to `redteam/public_view/<phase>/` with live API access.

#### Phase R1 (No Gates Unlocked)
- **Visible Files:** `flavor.txt`, `ciphertext.txt`, `replica_config.json`, Training Replica API.
- **Run 1 (`team_red_01`):** **FAILED**. Attempted single-substitution frequency analysis and replica wirings; yielded pseudo-random noise.
- **Run 2 (`team_red_02`):** **FAILED**. Attempted brute-force string search for `KCTF{`; zero matches in polyalphabetic ciphertext.
- **Run 3 (`team_red_03`):** **FAILED**. Probed Training Replica oracle; recovered only replica reflector which is completely independent of the sealed team instance.
- **Pass Criterion:** $0/3$ solved. **RESULT: 0/3 SOLVED (PASS)**.

#### Phase R2 (Gate I & II Unlocked)
- **Visible Files:** R1 + `enigma_spec.txt`, `rotor_wirings.json`, `rotor_notches.json`, `reflector.json`, `ring_settings.json`, Original Machine API.
- **Run 1 (`team_red_01`):** **FAILED**. Attempted standard English bigram hill-climbing directly on Enigma output. Failed because output is $S(\text{plaintext})$ and contains authentic Sanskrit phrases with non-English n-gram statistics.
- **Run 2 (`team_red_02`):** **FAILED**. Attempted known-plaintext crib search using literal words from lore (`ARJUNA`, `SANJAYA`, `KRISHNA`). Failed because Layer $S$ transforms the crib space and random null prefix shifts alignment index.
- **Run 3 (`team_red_03`):** **FAILED**. Attempted index of coincidence (IoC) optimization without reversing Layer $S$.
- **Pass Criterion:** $\le 1/3$ solved. **RESULT: 0/3 SOLVED (PASS)**.

---

## 4. Failure Modes & Defense Analysis

1. **Why Naive AI Fails:**
   - **Lack of Earned Inputs:** A code-execution AI cannot generate valid Enigma wirings from thin air before solving Challenge 1.
   - **Layer $S$ Barrier:** Even with full Enigma wirings and reflector, bigram fitness functions expect English text. The keyword pre-substitution $S$ scrambles letter distributions, preventing fitness convergence until $S$ is deduced from Fragment D and Challenge 2.
   - **Bilingual Distraction:** Curated Sanskrit phrases prevent dictionary matching and force participants to rely on deduction rather than pure language model completion.
   - **Null Prefix Jitter:** Prepending $0..11$ null symbols defeats fixed-index crib matching.

2. **Why Human Participants Succeed:**
   - Reading `flavor.txt` provides clear literary clues pointing to Gita 1.1 (*Dhritarashtra Uvacha*).
   - Challenge 2 provides the passphrase `SANJAYAUVACHA`.
   - The Training Replica provides a sandbox for participants to debug their offline simulators before applying them to the live problem.

---

## 5. Conclusion

The v2 hardening achieves the exact objective: **eliminating zero-shot script solving by AI assistants while preserving a rigorous, deterministic, and rewarding cryptanalytic path for human participants.**
