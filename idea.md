# 🏹 Kurukshetra CTF — Challenge Design Document (`idea.md`)

> **Event Theme:** The Mahabharata  
> **Flag Format:** `KCTF{...}`  
> **Challenges:** 3 (Easy → Medium → Hard)  
> **Duration:** 8-hour single event  
> **Status:** Design blueprint — pre-production

---

> *"यदा यदा हि धर्मस्य ग्लानिर्भवति भारत।*  
> *अभ्युत्थानमधर्मस्य तदात्मानं सृजाम्यहम्॥"*  
> *(Whenever righteousness fades and unrighteousness rises, I manifest myself — Bhagavad Gita 4.7)*

---

## Table of Contents

1. [Challenge 1 (Easy) — Gandiva's Secret](#challenge-1-easy--gandivas-secret)
2. [Challenge 2 (Medium) — The Fractured Battlefield](#challenge-2-medium--the-fractured-battlefield)
3. [Challenge 3 (Hard) — Chakravyuha Cipher](#challenge-3-hard--the-chakravyuha-cipher)
4. [Open Decisions Log](#open-decisions-log)
5. [Pre-Production Checklist](#pre-production-checklist)

---

---

# Challenge 1 (Easy) — Gandiva's Secret

---

## 1. Challenge Title & Details

### Title
**"Gandiva's Secret"**  
*"The bow speaks only to those who know its true name."*

### Difficulty
🟢 Easy

### Flavor Text / Storyline

> The war of Kurukshetra stands at a precipice. Before the first conch shell sounded, Arjuna — the unparalleled archer and son of Kunti — stood paralyzed on the battlefield, his mighty bow *Gandiva* silent in his trembling hands. Lord Krishna, in His infinite wisdom, did not hand Arjuna the answer outright. Instead, He embedded the truth within a sacred grid — a *vyuha* of words, arranged as the warriors arranged themselves: vertical spears forming the body, a hidden horizontal line carrying the dharmic secret.
>
> A message was carved into this grid by the Kavi of the Kuru court. Only one who reads **upward**, fills each answer with devotion, and knows the name of Kunti's son's *divine bow* shall decode the line that no mortal eye can perceive at first glance.
>
> Solve the crossword. Find the hidden row. Speak the name of the bow, and the secret of Dharma shall be yours.

---

## 2. Proposed Encryption & Cryptography Method

### Primary Cipher: **Vigenère Cipher** (with Autokey variant as difficulty toggle)

**Rationale:**
- The Vigenère cipher requires a *keyword* — perfectly mapped to the thematic mechanic where the key is the name of Arjuna's bow: **`GANDIVA`**.
- It is approachable for an Easy challenge yet non-trivial if the key is not given outright.
- Autokey Vigenère (where the plaintext feeds back as the key after the keyword) is available as a harder variant without changing the theme.

### Cipher Specifics

| Parameter         | Value                                                                 |
|-------------------|-----------------------------------------------------------------------|
| **Cipher**        | Vigenère Cipher                                                       |
| **Key**           | `GANDIVA` (derived from crossword, not given explicitly)              |
| **Alphabet**      | Standard A–Z (26 chars), uppercase                                   |
| **Ciphertext**    | The letters of a specific horizontal row in the crossword grid        |
| **Key Discovery** | Shaded cells / first-letters of certain answers spell `GANDIVA`       |
| **Decoy Option**  | One additional row decrypts to `KCTF{WRONG_PATH}` as a red herring   |

### Difficulty Escalation Options (Choose One)

```
Level 1 (Base):     Standard Vigenère, key = GANDIVA (hinted by sloka)
Level 2 (Medium):   Autokey Vigenère, same key seed — breaks standard solvers
Level 3 (Hard-Easy):Beaufort cipher — same key, inverse operation confuses players
```

---

## 3. Flow of the Challenge

### Files Given to Participant

```
gandivas_secret/
├── kurukshetra_crossword.pdf      # Printable/renderable crossword grid
├── kurukshetra_crossword.html     # Interactive web version (optional)
├── crossword_clues.txt            # List of all across/down clues
└── flavor.txt                     # Storyline + sloka clues (in English)
```

### Step-by-Step Participant Experience

**Step 1 — Solve the Crossword**
- The grid contains ~15–20 themed Mahabharata clues (characters, weapons, places, events).
- Answers are filled **vertically** (DOWN entries only, no ACROSS entries in the primary grid).
- Example clues:
  - *"Pandava who could shoot with both hands"* → `ARJUNA`
  - *"Sacred field of the great war"* → `KURUKSHETRA`
  - *"The blind king of Hastinapura"* → `DHRITARASHTRA`
  - *"Krishna's discourse to Arjuna"* → `GITOPADESHA`

**Step 2 — Identify the Hidden Row**
- One horizontal row (e.g., Row 7) is subtly marked — perhaps with a faint background color, a symbol, or discovered via a meta-clue.
- This row, read left-to-right, spells a sequence of letters: the **ciphertext**.
- Example ciphertext row: `TLMZRGDVIJKPQAEF` (placeholder)

**Step 3 — Extract the Key**
- Certain grid cells are shaded (or certain DOWN answers have their **first letters** highlighted).
- Reading the first letters of DOWN answers in a specific order spells: **`GANDIVA`**.
- The flavor text sloka provides the thematic nudge: *"The name of Kunti's son's bow is the key."*

**Step 4 — Decrypt**
- Apply Vigenère decryption with key `GANDIVA` to the ciphertext row.
- The result is a readable English string containing the flag.
- Example output: `ARCHERY_IS_DHARMA` → flag: `KCTF{ARCHERY_IS_DHARMA}`

**Step 5 — Validate**
- Submit the flag to the CTF platform.

### Hidden Mechanism
> The participant must realize that the crossword is **not** just trivia — the grid itself **is** the cryptographic artifact. The horizontal row is the ciphertext; the vertical answers hide the key.

---

## 4. Efficient Solving Method (Intended Solution)

### Solve Path

```
1. Complete all DOWN crossword answers using Mahabharata knowledge.
2. Read Row N (the target row) horizontally → extract ciphertext string C.
3. Identify shaded/first-letter cells → extract key string K = "GANDIVA".
4. Apply Vigenère decryption:
      P[i] = (C[i] - K[i mod len(K)]) mod 26   [where letters are 0-indexed A=0]
5. Read plaintext P → locate KCTF{...} flag within it.
```

### Vigenère Decryption — Quick Python Script

```python
def vigenere_decrypt(ciphertext: str, key: str) -> str:
    key = key.upper()
    plaintext = []
    key_len = len(key)
    j = 0
    for ch in ciphertext.upper():
        if ch.isalpha():
            shift = ord(key[j % key_len]) - ord('A')
            decrypted = chr((ord(ch) - ord('A') - shift) % 26 + ord('A'))
            plaintext.append(decrypted)
            j += 1
        else:
            plaintext.append(ch)
    return ''.join(plaintext)

# Usage
ciphertext = "TLMZRGDV..."   # read from the target crossword row
key = "GANDIVA"
print(vigenere_decrypt(ciphertext, key))
```

### Useful Tools

| Tool       | Use                                                         |
|------------|-------------------------------------------------------------|
| CyberChef  | Vigenère decode → `Vigenère Decode` recipe, key = GANDIVA   |
| dCode.fr   | Online Vigenère solver with key input                       |
| Python     | Script above for clean automation                           |
| quipqiup   | If participant tries frequency analysis first (dead end)    |

### Common Wrong Paths (Traps to Design For)

- Trying Caesar shift on the ciphertext row → garbage output.
- Trying ROT13 → garbage.
- Attempting to decode decoy row → fake flag `KCTF{WRONG_PATH}`.

---

## 5. Clues

### 🔵 Clue 1 — Thematic Nudge (Sloka)

> **Sanskrit:**  
> *"कुन्तीपुत्रस्य धनुषः नाम एव कुञ्जिका भवेत्।*  
> *तेन एव भिद्यते सा पङ्क्तिः या गुप्ता आसीत्॥"*
>
> **Translation:**  
> *"The name of Kunti's son's bow itself becomes the key;*  
> *by that alone is the hidden row broken."*
>
> **Nudge:** Which son of Kunti is most associated with a bow? What is the name of that bow? The answer is your key.

### 🔴 Clue 2 — Technical Hint

> The hidden row contains letters that have been **shifted** cyclically using a repeating keyword. The keyword is 7 letters long. Each letter of the ciphertext is shifted **backward** in the alphabet by the corresponding letter of the keyword (repeating).  
> This is not ROT-13. Try a tool like **CyberChef** → `Vigenère Decode` and experiment with keywords related to Arjuna's weapons.

---

---

# Challenge 2 (Medium) — The Fractured Battlefield

---

## 1. Challenge Title & Details

### Title
**"The Fractured Battlefield"**  
*"Only when every warrior stands in their rightful place does the truth of Kurukshetra emerge."*

### Difficulty
🟡 Medium

### Flavor Text / Storyline

> The great battle of Kurukshetra lasted eighteen days. On the fourteenth night, in the chaos of torchlit warfare, the battle-painters of the Kuru court captured the magnificent and terrible scene — warriors locked in combat, elephants falling like mountains, the sky lit with flaming arrows. But the painting was shattered. A cunning saboteur from the Kaurava side fragmented the sacred image into sixteen tiles and scrambled them, hoping to erase the record of Pandava valor forever.
>
> The painting holds a secret: the Kuru court's spy has embedded a hidden message within the very *atoms* of the image — invisible to the naked eye, perceivable only by those who look *beneath* the surface.
>
> But the hidden message only reveals itself when the image is **whole**. Restore each tile to its rightful place, and then look within the picture's invisible depths. The battle's true secret awaits.

---

## 2. Proposed Encryption & Cryptography Method

### Primary Method: **Image Steganography** (LSB embedding via `steghide` or custom LSB)

**Rationale:**
- The puzzle restoration step makes steganography *mandatory* — a participant who tries to run `steghide` on scrambled tiles gets garbage output, because the embedded payload spans tile boundaries.
- This elegantly enforces the "solve the puzzle first" mechanic.

### Steganography Specifics

| Parameter              | Value                                                                 |
|------------------------|-----------------------------------------------------------------------|
| **Embedding Method**   | `steghide` with a lore-derived passphrase                            |
| **Host Image**         | 4×4 tile sliding puzzle (15-puzzle) of a Kurukshetra battle scene     |
| **Payload**            | Base64-encoded string containing the flag                            |
| **Passphrase**         | Lore-derived (e.g., `SANJAYAUVACHA`) — not a dict word               |
| **Decoy Layer**        | A visible watermark or obvious metadata that is a red herring         |
| **Payload Placement**  | Embeds across tile-boundary pixels → broken if tiles are scrambled    |

### Difficulty Escalation Options

```
Level 1 (Base):     steghide with hinted passphrase, base64 payload → direct flag
Level 2 (Medium):   steghide payload is XOR-encrypted; XOR key hinted via lore
Level 3 (Hard-Med): Custom LSB in Blue channel bit-plane 1 only; no standard tool
```

### Payload Encoding Chain (Recommended)

```
FLAG → Base64 encode → XOR with key → steghide embed with passphrase
                                  ↑
                        (Key hidden in exif/metadata of a provided hint image)
```

---

## 3. Flow of the Challenge

### Files Given to Participant

```
fractured_battlefield/
├── tiles/
│   ├── tile_00.png  ...  tile_15.png    # 16 scrambled tiles (4×4)
├── tile_numbers.txt                     # Scrambled tile order (1D array)
├── flavor.txt                           # Storyline + sloka clues
└── hint_scroll.jpg                      # Bonus image with metadata clue (optional)
```

### Step-by-Step Participant Experience

**Step 1 — Verify Puzzle Solvability**
- The 16 tiles represent a 4×4 sliding puzzle (15-puzzle + one blank).
- The scrambled configuration is guaranteed to be **solvable** (even permutation parity).
- Participant may verify parity: count inversions → must be even for a 4×4 puzzle with blank in the correct row.

**Step 2 — Solve the Sliding Puzzle**
- Solve using A\* algorithm, or manually if the image has distinctive artwork.
- The solved order is a permutation array, e.g., `[0, 1, 2, 3, 7, 4, 5, 6, ...]`.
- Reassemble the image by placing tiles in correct positions using PIL/Pillow.

```python
from PIL import Image

TILE_SIZE = 128  # pixels per tile
GRID = 4         # 4x4 grid

solution_order = [0, 1, 2, 3, 7, 4, 5, 6, ...]  # participant derives this
tiles = [Image.open(f"tile_{i:02d}.png") for i in range(16)]

output = Image.new("RGB", (GRID * TILE_SIZE, GRID * TILE_SIZE))
for idx, tile_id in enumerate(solution_order):
    row, col = divmod(idx, GRID)
    output.paste(tiles[tile_id], (col * TILE_SIZE, row * TILE_SIZE))

output.save("restored_battlefield.png")
```

**Step 3 — Steganalysis on Restored Image**
- Run standard steganalysis tools on `restored_battlefield.png`.
- `steghide extract` prompts for passphrase.
- The passphrase is found via thematic deduction: *"Sanjaya always begins with the same phrase"* → `SANJAYAUVACHA`.

```bash
steghide extract -sf restored_battlefield.png -p "SANJAYAUVACHA"
# Outputs: hidden_payload.txt
```

**Step 4 — Decode the Payload**
- `hidden_payload.txt` contains a Base64-encoded string.
- Decode it to reveal the flag (optionally XOR-decrypt first if difficulty-up is applied).

```bash
base64 -d hidden_payload.txt
# Output: KCTF{THE_BATTLEFIELD_REVEALS_ITS_TRUTH}
```

**Step 5 — Validate**
- Submit the flag.

### Hidden Mechanism
> The steganographic payload **intentionally spans tile boundaries**. Running `steghide extract` on any individual scrambled tile or on the wrongly assembled image produces either an error or garbage — forcing participants to fully and correctly solve the puzzle first.

---

## 4. Efficient Solving Method (Intended Solution)

### Solve Path

```
1. Load tile_numbers.txt → parse scrambled grid state.
2. Verify parity (count inversions) → confirm solvability.
3. Apply A* solver OR manually solve the 15-puzzle → get solution_order[].
4. Use PIL to reconstruct full image → save as restored_battlefield.png.
5. Run: steghide extract -sf restored_battlefield.png -p "SANJAYAUVACHA"
6. Read extracted file → base64 decode → retrieve flag.
```

### A\* Solver (Python)

```python
import heapq

def solve_15_puzzle(start_state):
    """
    A* search for 15-puzzle.
    state: tuple of 16 integers (0 = blank tile)
    heuristic: Manhattan distance
    """
    goal = tuple(range(16))

    def manhattan(state):
        dist = 0
        for i, val in enumerate(state):
            if val != 0:
                goal_r, goal_c = divmod(val, 4)
                curr_r, curr_c = divmod(i, 4)
                dist += abs(goal_r - curr_r) + abs(goal_c - curr_c)
        return dist

    heap = [(manhattan(start_state), 0, start_state, [])]
    visited = set()

    while heap:
        f, g, state, path = heapq.heappop(heap)
        if state == goal:
            return path
        if state in visited:
            continue
        visited.add(state)
        blank = state.index(0)
        br, bc = divmod(blank, 4)
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = br+dr, bc+dc
            if 0 <= nr < 4 and 0 <= nc < 4:
                ni = nr*4 + nc
                new_state = list(state)
                new_state[blank], new_state[ni] = new_state[ni], new_state[blank]
                new_state = tuple(new_state)
                if new_state not in visited:
                    heapq.heappush(heap, (
                        g+1+manhattan(new_state), g+1, new_state, path+[ni]
                    ))
    return None
```

### Useful Tools

| Tool          | Use                                                                  |
|---------------|----------------------------------------------------------------------|
| `steghide`    | Extract hidden payload with passphrase                               |
| `zsteg`       | If steghide fails, check LSB channels in PNG                         |
| `exiftool`    | Check metadata for passphrase hints (hint_scroll.jpg)                |
| `binwalk`     | Check for appended data or hidden files                              |
| `PIL/Pillow`  | Reconstruct image from solved tile order                             |
| CyberChef     | Base64 decode of extracted payload                                   |
| `stegsolve`   | Visual channel analysis (Java tool)                                  |

### Common Wrong Paths

- Running `steghide` directly on scrambled tiles → error/garbage.
- Trying `zsteg` on individual tiles → no payload found (it spans boundaries).
- Using `rockyou.txt` / `stegseek` → passphrase `SANJAYAUVACHA` is not in wordlists.

---

## 5. Clues

### 🔵 Clue 1 — Thematic Nudge (Sloka)

> **Sanskrit:**  
> *"छिन्नानि अङ्गानि यदा सर्वाणि स्वस्थाने संयोजितानि भवन्ति।*  
> *तदा एव सम्पूर्णं दृश्यं जायते तस्य रणभूमेः चित्रम्॥"*
>
> **Translation:**  
> *"When all severed limbs are rejoined in their rightful place, only then does the full picture of that battlefield appear."*
>
> **Nudge:** The image must be **complete** before the secret reveals itself. Every tile in its correct place. Do not attempt to extract anything from a broken image.

### 🔴 Clue 2 — Technical Hint

> The secret is hidden **inside** the restored image using a steganography tool. The tool requires a password to extract. The password is a phrase that a famous narrator of the Mahabharata war always used to begin his accounts to the blind king. It is two Sanskrit words joined together.  
> Try running: `steghide extract -sf restored_battlefield.png -p <YOUR_GUESS>`

---

---

# Challenge 3 (Hard) — The Chakravyuha Cipher

---

## 1. Challenge Title & Details

### Title
**"The Chakravyuha Cipher"**  
*"To enter the spiral formation is easy. To find the key within it — that is the trial of Abhimanyu."*

### Difficulty
🔴 Hard

### Flavor Text / Storyline

> On the thirteenth day of the Kurukshetra War, Drona — the unparalleled master of military science — arranged the Kaurava forces in the dreaded *Chakravyuha*: a seven-layered, ever-rotating spiral formation impossible to penetrate or escape without knowing its deepest secrets.
>
> The young Abhimanyu knew how to enter. But the knowledge of how to *exit* — the key to the innermost ring — was never taught to him.
>
> Now, the Kuru war council has devised a cipher of the same design: a machine of spinning wheels, plugs, and reflections — seven layers deep. Every letter that enters is transformed through five rotating cipher-wheels (called *chakras*), bounced off a secret reflector, and scrambled further by a plugboard of thirteen symbol-swaps.
>
> Sanjaya, the divine narrator, always begins his message with the same sacred salutation. Eighteen is the number of days, of armies, of chapters — and eighteen is the secret embedded within the ring itself.
>
> You are Abhimanyu. You have the wheel designs. You have the opening phrase. You know the number eighteen. Find the key. Break the Chakravyuha. Recover the message.

---

## 2. Proposed Encryption & Cryptography Method

### Primary Method: **Custom Enigma-Style Polyalphabetic Rotor Cipher**

**Rationale:**
- A custom Enigma machine maps perfectly to the *Chakravyuha* (rotating spiral formation).
- The rotating rotors mirror the ever-turning layers of the military formation.
- The extended 30-symbol alphabet breaks all off-the-shelf Enigma tools, ensuring participants must engage with the mathematics and implement their own simulator.

### Cipher Specifications

| Component          | Specification                                                                          |
|--------------------|----------------------------------------------------------------------------------------|
| **Alphabet**       | 30 symbols: `A-Z` + `{`, `}`, `_`, `#` (or similar non-letter markers)               |
| **Rotors**         | 5 custom rotors (all wirings published); 4 used per session (order is secret)         |
| **Notches**        | Each rotor has **2 notches** (double-stepping, non-standard positions)                |
| **Reflector**      | Rewirable/secret; only its *property* disclosed (involutory: maps every symbol to another) |
| **Plugboard**      | 13 pairs of symbol swaps from the 30-symbol alphabet (Steckerbrett)                   |
| **Ring Settings**  | Derived via the **"18" lore rule** (see below)                                        |
| **Crib**           | Every message begins with: `DHRITARASHTRAUVACHA` (19 chars)                          |
| **Keyspace**       | ~10^46–10^47 (infeasible by raw brute force)                                          |

### The "18" Lore Rule — Ring Setting Derivation

This is the core fair-crack mechanism:

```
The ring settings (Ringstellung) for the 4 active rotors are derived as follows:

Let the rotor slots be numbered 1, 2, 3, 4 (left to right).
The ring setting for each rotor = (slot_number × 18) mod 30

Slot 1: (1 × 18) mod 30 = 18
Slot 2: (2 × 18) mod 30 = 36 mod 30 = 6
Slot 3: (3 × 18) mod 30 = 54 mod 30 = 24
Slot 4: (4 × 18) mod 30 = 72 mod 30 = 12
```

> **Design Note:** This formula must be documented precisely in the answer key. The sloka clue points toward 18 as the multiplier. Players who know *what* 18 does but not *how exactly* should be guided by Clue 2.

### Intended Attack Path (Fair Cracks)

The challenge is designed so that brute force on the full keyspace is impossible, but the following **deliberate vulnerabilities** make it tractable:

1. **Crib-drag attack** — known plaintext `DHRITARASHTRAUVACHA` at position 0.
2. **Ring setting reduction** — the "18" formula reduces the ring-setting search space from 30^4 = 810,000 to exactly 1 candidate.
3. **Rotor wiring published** — no need to guess wiring, only order (5P4 = 120 permutations).
4. **Hill-climbing** — after fixing ring settings and candidate rotor orders, use Index of Coincidence (IoC) or bigram scoring to find plugboard pairs and rotor order.

---

## 3. Flow of the Challenge

### Files Given to Participant

```
chakravyuha_cipher/
├── ciphertext.txt              # The encrypted message (30-symbol alphabet)
├── rotor_wirings.json          # All 5 rotor wiring tables (published)
├── rotor_notches.json          # Notch/turnover positions for each rotor
├── enigma_spec.txt             # Machine specification (alphabet, rules, stepping)
├── flavor.txt                  # Storyline + sloka clues (English)
└── simulator_skeleton.py       # Optional: empty Enigma simulator skeleton
```

### `rotor_wirings.json` Format (Example)

```json
{
  "rotors": {
    "I":   {"wiring": "BDFHJLCPRTXVZNYEIWGAKMUSQO##_{}",  "notches": [4, 21]},
    "II":  {"wiring": "AJDKSIRUXBLHWTMCQGZNPYFVOE{}#_",  "notches": [8, 17]},
    "III": {"wiring": "EKMFLGDQVZNTOWYHXUSPAIBRCJ{}_#",  "notches": [2, 25]},
    "IV":  {"wiring": "RVHIAQNJXLBZFGUOMEDSWKPTCY_{}#",  "notches": [13, 0]},
    "V":   {"wiring": "JPGVOUMFYQBENHZRDKASXLICTW{#}_",  "notches": [6, 19]}
  },
  "alphabet": "ABCDEFGHIJKLMNOPQRSTUVWXYZ{}#_"
}
```

### Step-by-Step Participant Experience

**Step 1 — Understand the Machine**
- Read `enigma_spec.txt` and `rotor_wirings.json`.
- Understand the 30-symbol alphabet and the custom stepping/notch behavior.
- Realize that standard Enigma tools do **not** support a 30-symbol alphabet — must write or adapt a simulator.

**Step 2 — Build a Custom Enigma Simulator**
- Implement the rotor cipher in Python (or SageMath).
- Key components: alphabet mapping, rotor stepping with double-notch, plugboard swap, reflector involution.

**Step 3 — Apply the "18" Rule**
- From the sloka clue, participants identify that the number 18 is key.
- They derive ring settings using: `ring[slot] = (slot × 18) mod 30`.
- This collapses the ring-setting search space to exactly 1 possibility.

**Step 4 — Crib-Drag Attack**
- The crib `DHRITARASHTRAUVACHA` is known to appear at position 0.
- For each of the 120 rotor orders (5P4): encrypt the crib and check if output matches first 19 chars of ciphertext.
- This narrows rotor order candidates dramatically.

**Step 5 — Hill-Climbing for Plugboard**
- With rotor order fixed, perform hill-climbing using bigram/trigram frequency scores to find all 13 plugboard pairs.
- Tools: custom Python script with a pre-loaded English bigram table.

**Step 6 — Decrypt & Extract Flag**
- Full decrypt of `ciphertext.txt` yields a readable plaintext sentence.
- The flag `KCTF{...}` is embedded within the plaintext.

---

## 4. Efficient Solving Method (Intended Solution)

### Solve Path Overview

```
1. Build 30-symbol Enigma simulator in Python.
2. Compute ring settings: ring[i] = (i × 18) mod 30  for i in [1,2,3,4].
3. Loop over all 120 rotor order permutations (5 choose 4, ordered).
4. For each order: encrypt crib "DHRITARASHTRAUVACHA" at position 0.
5. Check if encryption matches ciphertext[0:19] → identify candidate orders.
6. For each candidate: run hill-climbing over plugboard pairs using IoC/bigram score.
7. Optimal plugboard + rotor order → decrypt full ciphertext.
8. Extract KCTF{...} from plaintext.
```

### Python Enigma Simulator

```python
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ{}#_"   # 30 symbols
N = len(ALPHABET)

def char_to_idx(c): return ALPHABET.index(c)
def idx_to_char(i): return ALPHABET[i]

class Rotor:
    def __init__(self, wiring: str, notches: list, ring_setting: int = 0):
        self.forward = [char_to_idx(c) for c in wiring]
        self.backward = [0] * N
        for i, j in enumerate(self.forward):
            self.backward[j] = i
        self.notches = notches
        self.ring = ring_setting
        self.position = 0

    def at_notch(self) -> bool:
        return self.position in self.notches

    def step(self):
        self.position = (self.position + 1) % N

    def encode_forward(self, signal: int) -> int:
        shifted = (signal + self.position - self.ring) % N
        encoded = self.forward[shifted]
        return (encoded - self.position + self.ring) % N

    def encode_backward(self, signal: int) -> int:
        shifted = (signal + self.position - self.ring) % N
        encoded = self.backward[shifted]
        return (encoded - self.position + self.ring) % N

class Reflector:
    def __init__(self, wiring: str):
        self.pairs = [char_to_idx(c) for c in wiring]

    def reflect(self, signal: int) -> int:
        return self.pairs[signal]

class Plugboard:
    def __init__(self, pairs: list):
        self.mapping = list(range(N))
        for a, b in pairs:
            ia, ib = char_to_idx(a), char_to_idx(b)
            self.mapping[ia] = ib
            self.mapping[ib] = ia

    def swap(self, signal: int) -> int:
        return self.mapping[signal]

class EnigmaMachine:
    def __init__(self, rotors: list, reflector: Reflector, plugboard: Plugboard):
        self.rotors = rotors      # list of Rotor objects, left to right
        self.reflector = reflector
        self.plugboard = plugboard

    def _step_rotors(self):
        # Double-notch stepping (accounts for middle rotor anomaly)
        r = self.rotors
        if r[-2].at_notch():
            r[-2].step()
            r[-3].step()
        elif r[-1].at_notch():
            r[-2].step()
        r[-1].step()

    def encrypt_char(self, ch: str) -> str:
        self._step_rotors()
        signal = char_to_idx(ch)
        signal = self.plugboard.swap(signal)
        for rotor in reversed(self.rotors):
            signal = rotor.encode_forward(signal)
        signal = self.reflector.reflect(signal)
        for rotor in self.rotors:
            signal = rotor.encode_backward(signal)
        signal = self.plugboard.swap(signal)
        return idx_to_char(signal)

    def encrypt(self, plaintext: str) -> str:
        return ''.join(self.encrypt_char(c) for c in plaintext if c in ALPHABET)

# --- Ring Setting Derivation (The "18" Rule) ---
ring_settings = [(slot * 18) % N for slot in range(1, 5)]  # [18, 6, 24, 12]
print(f"Ring settings: {ring_settings}")

# --- Crib-Drag Attack Loop (pseudocode skeleton) ---
from itertools import permutations
import json

with open("rotor_wirings.json") as f:
    data = json.load(f)

rotor_defs = data["rotors"]
crib       = "DHRITARASHTRAUVACHA"

with open("ciphertext.txt") as f:
    ciphertext = f.read().strip()

candidates = []
for rotor_order in permutations(["I","II","III","IV","V"], 4):
    rotors = [
        Rotor(
            rotor_defs[r]["wiring"],
            rotor_defs[r]["notches"],
            ring_settings[i]
        )
        for i, r in enumerate(rotor_order)
    ]
    # TODO: load reflector, set up EnigmaMachine, encrypt crib, compare to ciphertext[:19]
    # If match → add rotor_order to candidates → proceed to hill-climbing
    pass
```

### Hill-Climbing for Plugboard

```python
def score_text(text: str, bigrams: dict) -> float:
    """Score using bigram log-probability."""
    score = 0
    for i in range(len(text) - 1):
        pair = text[i:i+2]
        score += bigrams.get(pair, -10)  # penalty for unknown bigrams
    return score

def hill_climb_plugboard(machine_factory, ciphertext, bigrams, iterations=5000):
    best_plugboard = []
    best_score = float('-inf')

    for _ in range(iterations):
        # Mutate: swap one plugboard pair randomly
        candidate = best_plugboard.copy()
        # ... mutation logic ...
        machine = machine_factory(candidate)
        plaintext = machine.encrypt(ciphertext)
        score = score_text(plaintext, bigrams)
        if score > best_score:
            best_score = score
            best_plugboard = candidate

    return best_plugboard
```

### Useful Tools

| Tool             | Use                                                                  |
|------------------|----------------------------------------------------------------------|
| Python 3         | Build the custom Enigma simulator                                    |
| SageMath         | Group theory / permutation analysis                                  |
| `itertools`      | Enumerate rotor order permutations                                   |
| Bigram tables    | Score candidate decryptions (English bigram/trigram frequency)       |
| CyberChef        | Base64/hex decode of final flag if needed                            |
| Jupyter Notebook | Interactive hill-climbing and scoring visualization                  |

### Key Insight Summary

> The challenge is **not** about brute force. It is about:
> 1. **Knowing the "18" formula** → eliminates ring-setting search entirely.
> 2. **Using the crib** → reduces rotor order candidates from 120 to ~1–5.
> 3. **Hill-climbing** → finds plugboard pairs efficiently.
> 4. **Understanding Enigma's reciprocal property** → `encrypt(encrypt(X)) = X` means decryption = re-encryption.

---

## 5. Clues

### 🔵 Clue 1 — Thematic Nudge (Sloka)

> **Sanskrit:**  
> *"यथा सञ्जयः प्रतिवचनम् आरभते एकेन एव वाक्येन नित्यम्,*  
> *तथा एव सन्देशः आरभ्यते तेन एव शब्देन सर्वदा॥"*
>
> **Translation:**  
> *"As Sanjaya always begins his reply with the same one sentence, so too does the message always begin with that very word."*
>
> **Nudge:** Every encrypted message in this challenge begins with the same known phrase. In World War II cryptanalysis, this was called a "crib." Sanjaya's opening salutation in the Mahabharata is your crib.

### 🔴 Clue 2 — Technical Hint

> The ring settings of the four cipher-wheels are not random. They follow a mathematical pattern rooted in the sacred number of this war — **eighteen**. For each wheel position *n* (starting from 1), the ring setting is: `(n × 18) mod 30`.  
> Once you have the ring settings, enumerate all possible wheel orders (there are only 120), use your known opening phrase as a crib, and score each decryption attempt using letter frequency analysis.  
> Tools needed: Python, `itertools.permutations`, a bigram frequency table.

---

---

# Open Decisions Log

| # | Decision                           | Options                              | Status       |
|---|------------------------------------|--------------------------------------|--------------|
| 1 | Exact cipher for crossword row     | Vigenère / Autokey / Beaufort        | ⚠️ Pending   |
| 2 | Grid size + delivery format        | Web page / PDF / tile files          | ⚠️ Pending   |
| 3 | Stego tool/format choice           | steghide / zsteg / custom LSB        | ⚠️ Pending   |
| 4 | Payload encryption for Chal. 2     | Base64 only / Base64 + XOR           | ⚠️ Pending   |
| 5 | Challenge chaining vs. independent | Flag-relay / standalone              | ⚠️ Pending   |
| 6 | Exact "18" ring formula            | `(n×18) mod 30` (proposed above)     | ⚠️ Needs lock|
| 7 | Scoring / hint policy              | Points per challenge / partial credit| ⚠️ Pending   |
| 8 | Event logistics                    | On-site / online / hybrid            | ⚠️ Pending   |

---

---

# Pre-Production Checklist

### Challenge 1 — Gandiva's Secret
- [ ] Design final crossword grid (15–20 clues, themed)
- [ ] Choose target row number and confirm it is non-obvious
- [ ] Generate ciphertext for that row using Vigenère + key `GANDIVA`
- [ ] Verify decoy row decrypts to `KCTF{WRONG_PATH}`
- [ ] Build HTML interactive crossword (or finalize PDF)
- [ ] Write full answer key with Vigenère solve walkthrough
- [ ] Set final flag: `KCTF{_______________}`

### Challenge 2 — The Fractured Battlefield
- [ ] Commission/generate Kurukshetra battle scene artwork
- [ ] Slice into 4×4 tile grid (16 tiles, one blank)
- [ ] Scramble tiles respecting 15-puzzle parity
- [ ] Embed payload with `steghide`, passphrase = `SANJAYAUVACHA`
- [ ] Verify payload is corrupted on scrambled/mis-assembled image
- [ ] Create decoy metadata in `hint_scroll.jpg`
- [ ] Write solve script (A\* + steghide + base64)
- [ ] Set final flag: `KCTF{_______________}`

### Challenge 3 — The Chakravyuha Cipher
- [ ] Finalize 30-symbol alphabet (confirm `{}#_` or alternative)
- [ ] Generate 5 custom rotor wirings (valid permutations of 30 symbols)
- [ ] Choose 4-rotor order for the event key
- [ ] Choose starting positions (ground settings)
- [ ] Generate reflector wiring (must be involutory / self-inverse)
- [ ] Choose 13 plugboard pairs
- [ ] Lock ring settings using `(n×18) mod 30` formula
- [ ] Encrypt flag message using built simulator
- [ ] Publish `rotor_wirings.json`, `enigma_spec.txt`, `ciphertext.txt`
- [ ] Write hill-climbing solver script (internal answer key)
- [ ] Verify solver recovers correct plaintext
- [ ] Set final flag: `KCTF{_______________}`

---

> *"कर्मण्येवाधिकारस्ते मा फलेषु कदाचन।"*  
> *"You have the right to action alone, never to its fruits." — Bhagavad Gita 2.47*  
>
> Let the challengers do the work. Build fair puzzles. May Dharma prevail. 🏹

---

*Document generated for internal CTF design use. Version 0.1 — Pre-production draft.*
