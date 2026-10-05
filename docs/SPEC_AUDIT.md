# Specification Audit: Kurukshetra CTF Challenge 3 (Hard) — Hardening v2
## "The Chakravyuha Cipher: Denied Inputs & Progressive Gates"

This document records the cryptographic, mechanical, and architectural audit of Challenge 3 as hardened in v2.

---

## 1. Hardening v2 Corrections & Overrides

| Ref # | Item in v1 | Issue in v1 (AI Two-Prompt Exploit) | Hardening v2 Enforcement (Information Denial) |
|---|---|---|---|
| **H1** | Public Artifacts & Slokas | Provided crib `DHRITARASHTRA UVACHA`, symbol conventions `_`/`#`, and ring hints in `flavor.txt` and public spec files. | **Strict Denial:** Only `flavor.txt`, `ciphertext.txt`, and `replica_config.json` exist pre-gate. The crib is replaced with 4 subtle riddle fragments (epithets only, zero literal names). |
| **H2** | Monolithic Public Spec | Machine wirings, notches, and spec were completely public. | **Progressive Seal Gates:** Gate I (Seal of Gandiva, Challenge 1 flag) unlocks `enigma_spec.txt`, `rotor_wirings.json`, `rotor_notches.json`. Gate II (Seal of Sanjaya, Challenge 2 flag) unlocks `reflector.json`, `ring_settings.json`, and unlocks Original mode. Served per-team via authenticated endpoints. |
| **H3** | Shared Instance & 5-Rotor Pool | All teams shared the same ciphertext and 5-rotor pool ($5P4 = 120$). | **Per-Team CSPRNG Derivation (`HMAC-DRBG`):** Each team gets unique 8-rotor pool ($8P4 = 1680$), random rings, random reflector, random null-prefix ($0..11$), and per-team flag `KCTF{<WORDS>_<TAG>}`. Anti-collusion penalty on flag collision. |
| **H4** | Known-Plaintext Opener at Index 0 | Known crib aligned at index 0 allowed instant crib dragging. | **Hidden Opener & Random Null Prefix:** Opener is hidden behind riddle fragments; preceded by $0..11$ random null symbols unknown to the player. |
| **H5** | Mono-Language Plaintext | Pure English text allowed standard n-gram hill-climbing on raw Enigma output. | **Pre-Substitution Layer ($S$) & Bilingual Plaintext:** Keyword-mixed monoalphabetic cipher ($S$) using keyword `SANJAYAUVACHA` applied before Enigma: $\text{Plaintext} \to S \to \text{Enigma} \to \text{Ciphertext}$. Plaintext interleaved with authentic Sanskrit phrases. |
| **H6** | Sealed Oracle Reflector Leak | The sealed machine's live oracle allowed extracting the reflector in ~30 keypresses. | **Training Replica vs Original Mode:** Pre-Gate II machine is an independent Training Replica with its own public configuration (`replica_config.json`) and separate budget. Original mode is unlocked only post-Gate II (using team's already-revealed wirings and reflector). |

---

## 2. Bilingual Plaintext Sanskrit Phrase Corpus Review

The plaintext generator combines English military narrative with authentic transliterated Sanskrit phrases from the Mahabharata / Gita (curated in `tools/phrases_sanskrit.txt`):
- `DHARMASHETRE_KURUKSHETRE`
- `YATO_DHARMAH_TATO_JAYAH`
- `KARMASU_KAUSHALAM`
- `SWA_DHARME_NIDHANAM_SHREYAH`
- `NA_DHARMAT_PARAMASTI`
- `PARITRANAYA_SADHUNAM`
- `NIMITTA_MATRAM_BHAVA_SAVYASACHIN`
- `SANJAYASYA_VACHANAM_SHRUTVA`
*(All phrases verified for standard IAST/ASCII transliteration with no duplicate or invalid symbols).*

---

## 3. Cryptographic Pipeline Summary

$$\text{Plaintext} \longrightarrow \text{Opener} + \text{Null Prefix} \longrightarrow S_{\text{SANJAYAUVACHA}} \longrightarrow \text{Enigma}_{4/8} \longrightarrow \text{Ciphertext}$$

$$\text{Ciphertext} \xrightarrow{\text{Enigma}^{-1}} S(\text{Plaintext}) \xrightarrow{S^{-1}} \text{Bilingual Plaintext} \longrightarrow \mathbf{KCTF\{\dots\}}$$

