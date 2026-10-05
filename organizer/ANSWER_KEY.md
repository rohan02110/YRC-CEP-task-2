# Kurukshetra CTF — Official Answer Key (Confidential)
## Challenge 3 (Hard): "The Chakravyuha Cipher: Sealed Machine"

> **STRICT CONFIDENTIALITY:** For event organizers and challenge leads only.

---

## 1. Challenge Parameters & Master Configuration

- **Alphabet (30 symbols):** `ABCDEFGHIJKLMNOPQRSTUVWXYZ{}#_`
- **Rotors:** 5 published rotors (I to V) with 2 notches each.
- **Seated Rotors (Slot 1 to 4):** 4 of 5 rotors seated left to right.
- **Ring Settings ("18 Rule"):** `[18, 6, 24, 12]`
- **Reflector:** Secret 15-pair involution without fixed points.
- **Plugboard:** Secret 13-pair involution (4 unplugged symbols).
- **Crib:** `DHRITARASHTRAUVACHA` at offset 0.

---

## 2. Mathematical Solve Path & Cryptanalysis

### Step 1: Recovering the Secret Reflector
When the participant configures the sealed machine to identity:
- Walzenlage = `["I", "II", "III", "IV"]`
- Ringstellung = `[0, 0, 0, 0]`
- Grundstellung = `[0, 0, 0, 0]`
- Plugboard = `[]`

On pressing symbol $c$, rotor 3 steps from 0 to 1.
Let $R_{fwd}$ be the forward permutation of the 4 rotors at positions `[0, 0, 0, 1]` with rings `[0, 0, 0, 0]`.
The input symbol reaches the reflector as $s_{in} = R_{fwd}(c)$.
The machine produces output symbol $c_{out}$.
Inverting the backward rotor pass is equivalent to running $s_{out} = R_{fwd}(c_{out})$.
Therefore, the secret reflector pair $(s_{in}, s_{out})$ is revealed on each press.
Probing at most 15–30 characters yields all 15 pairs of the reflector for a cost of 15–30 arrow tokens.

### Step 2: Applying the 18 Rule
Using Clue 1/2, ring settings are calculated as:
- Slot 1: $(1 \times 18) \bmod 30 = 18$
- Slot 2: $(2 \times 18) \bmod 30 = 6$
- Slot 3: $(3 \times 18) \bmod 30 = 24$
- Slot 4: $(4 \times 18) \bmod 30 = 12$

### Step 3: Enumerate Rotor Orders & Solve Crib Constraints
There are $5P4 = 120$ possible rotor orders.
For each candidate rotor order and candidate start position:
Simulate the internal rotor permutation $E_i$ for each step $i \in [0, 18]$ corresponding to the crib `DHRITARASHTRAUVACHA`.
The plugboard $PB$ satisfies:
$$PB(Ciphertext[i]) = E_i(PB(Crib[i]))$$
Solving this consistency graph or running hill-climbing with English bigram log-likelihood scoring determines the correct start positions and plugboard pairs in seconds.

### Step 4: Full Decryption
Re-encrypting (or decrypting) `ciphertext.txt` with the recovered parameters reveals the full Sanskrit narration in natural English prose and extracts `KCTF{...}`.

---

## 3. Automated Answer Extraction
To run the automated solver and extract the flag for the active instance:
```bash
python tools/reference_solver.py
```
Expected Output:
```text
[+] Recovered reflector with 15 pairs successfully.
[+] Decryption successful!
[+] Flag Extracted: KCTF{DRONA_CHAKRAVYUHA_SEAL_UNBROKEN_TRUTH}
```
