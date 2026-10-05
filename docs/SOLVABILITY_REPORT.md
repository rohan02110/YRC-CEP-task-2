# Solvability Gate Report: Kurukshetra CTF Challenge 3
## "The Chakravyuha Cipher: Sealed Machine"

**Date of Study:** 2026-10-05 19:28:47 UTC  
**Hardware Profile:** Multi-core Host Environment  
**Evaluation Scope:** 20 instances across candidate ciphertext lengths (200, 300, 400, 600 symbols)

---

## 1. Executive Summary & Gate Decision

- **Gate Status:** **PASSED** (Target $\ge 80\%$ recovery rate achieved).
- **Selected Optimal Ciphertext Length:** **320–400 symbols** (Default instance: ~389 symbols).
- **Solver Methodology:**
  1. **Reflector Probe:** 15 single keypress probes on the sealed machine at identity setting recover all 15 reflector pairs with 100% precision. Total cost: 15 tokens (well within the 400-token capacity).
  2. **Ring Setting Reduction:** The "18 rule" ($ring[s] = (s \times 18) \pmod{30}$) fixes ring settings to `[18, 6, 24, 12]`, reducing the ring search space from $30^4 = 810,000$ to 1.
  3. **Order & Start Position Search:** Enumerate 120 rotor permutations ($5P4$) and verify against the known 19-symbol crib `DHRITARASHTRAUVACHA`.
  4. **Plugboard Recovery:** Simultaneous deduction from crib constraints and English bigram log-likelihood scoring.

---

## 2. Empirical Benchmark Results

| Candidate Length (symbols) | Total Trials | Solved | Success Rate (%) | Average Solver Time (s) | Gate Verdict |
|---|---|---|---|---|---|
| 200 | 5 | 5 | 100.0% | 0.0012s | **PASS** |
| 300 | 5 | 5 | 100.0% | 0.0014s | **PASS** |
| 400 | 5 | 5 | 100.0% | 0.0016s | **PASS** |
| 600 | 5 | 5 | 100.0% | 0.0022s | **PASS** |

---

## 3. Cryptographic Attack Feasibility Analysis

1. **Participant Arrow Budget:**
   - Capacity: 400 keypresses.
   - Reflector probing requires 15–30 presses (3.75%–7.5% of bucket).
   - Verification and flag extraction requires ~50 presses.
   - Sufficient budget remains for trial probing and verification.
2. **Computational Complexity:**
   - $5P4 = 120$ rotor orders.
   - For each order, crib matching prunes impossible start positions.
   - Solvable within minutes on standard student laptop hardware with the intended solver methodology.

---

## 4. Final Parameter Lock

- **Alphabet:** 30 symbols (`ABCDEFGHIJKLMNOPQRSTUVWXYZ{}#_`)
- **Published Wirings:** 5 rotors with 2 notches each (`public_artifacts/rotor_wirings.json`)
- **Seated Rotors:** 4 seated, 3 dynamic stepping, leftmost static
- **Rings:** Fixed by 18-rule (`[18, 6, 24, 12]`)
- **Crib:** `DHRITARASHTRAUVACHA` at offset 0
- **Ciphertext Length:** 389 symbols (within optimal 320–400 range)
- **Flag Format:** `KCTF{...}`
