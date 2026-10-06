#!/usr/bin/env python3
"""
Instance and Artifact Generator for Kurukshetra CTF Challenge 3 (Hardening v2)
Implements per-team HMAC-DRBG derivation, 8-rotor pool, keyword pre-substitution (S),
bilingual Sanskrit plaintext, null prefixing, and Training Replica generation.
"""

import argparse
import base64
import hashlib
import hmac
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any

# Ensure backend can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
from app.engine import (
    ALPHABET, N, char_to_idx, idx_to_char,
    HMAC_DRBG, KeywordSubstitution,
    Rotor, Reflector, Plugboard, EnigmaMachine
)

DEFAULT_MASTER_SEED = os.environ.get("MASTER_SEED", "0x9F82A4C6E1D3B5792468ACE013579BDF2468ACE013579BDF2468ACE013579BDF")
UNIVERSAL_FLAG = os.environ.get("CHALLENGE_FLAG", os.environ.get("FLAG", "KCTF{DRONA_CHAKRAVYUHA_SEAL_UNBROKEN_TRUTH}")).strip().upper()
REPLICA_SEED = "REPLICA_SEED_CHAKRAVYUHA_TRAINING_2026"
ROTOR_NAMES = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"]

FLAG_PHRASE_LIST = [
    "DRONA_SEAL_UNBROKEN_VICTORY",
    "CHAKRA_SEVENTH_TIER_BREACH",
    "GANDIVA_TWANG_RESONATES_TRUTH",
    "KURUKSHETRA_DHARMA_TRIUMPHS",
    "ABHIMANYU_VALOR_ETERNAL",
    "SARATHI_DIVINE_GUIDANCE",
    "BRAHMASTRA_CONTAINED_LIGHT",
    "SANJAYA_VISION_UNVEILED"
]

DEFAULT_DECOYS = [
    "KCTF{ABHIMANYU_NEVER_LEARNED_TO_EXIT}",
    "KCTF{WRONG_FORMATION_PATH_TRY_AGAIN}",
    "KCTF{THE_EIGHTEEN_RULES_ARE_LIES}",
    "KCTF{BHISHMA_FELL_ON_DAY_TEN}",
    "KCTF{KARNA_CHARIOT_WHEEL_STUCK}",
    "KCTF{DRONA_LAID_DOWN_HIS_ARMS}",
    "KCTF{ASHWATTHAMA_HATHA_KUNJARA}",
    "KCTF{SHAKUNI_DICE_WAS_LOADED}"
]


def derive_team_seed(master_seed: str, team_id: str) -> bytes:
    if master_seed.startswith("0x"):
        try:
            key = bytes.fromhex(master_seed[2:])
        except ValueError:
            key = master_seed.encode("utf-8")
    else:
        key = master_seed.encode("utf-8")
    return hmac.new(key, f"team:{team_id}".encode("utf-8"), hashlib.sha256).digest()


def generate_flag_tag(master_seed: str, team_id: str, phrase: str) -> str:
    if master_seed.startswith("0x"):
        try:
            key = bytes.fromhex(master_seed[2:])
        except ValueError:
            key = master_seed.encode("utf-8")
    else:
        key = master_seed.encode("utf-8")
    mac = hmac.new(key, f"{team_id}:{phrase}".encode("utf-8"), hashlib.sha256).digest()
    # 6 uppercase letters guaranteed to belong to the 30-symbol machine alphabet
    tag = "".join(chr(65 + (b % 26)) for b in mac[:6])
    return tag


def generate_8_rotors(drbg: HMAC_DRBG) -> Dict[str, Dict[str, Any]]:
    rotors = {}
    for name in ROTOR_NAMES:
        wiring = drbg.permutation(ALPHABET)
        notches = sorted(drbg.sample(range(N), 2))
        rotors[name] = {
            "wiring": wiring,
            "notches": notches
        }
    return rotors


def generate_reflector(drbg: HMAC_DRBG) -> List[Tuple[str, str]]:
    symbols = list(ALPHABET)
    drbg.shuffle(symbols)
    pairs = []
    for i in range(0, N, 2):
        a, b = symbols[i], symbols[i + 1]
        pairs.append((min(a, b), max(a, b)))
    return pairs


def generate_plugboard(drbg: HMAC_DRBG, reflector_pairs: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
    reflector_set = set(reflector_pairs)
    while True:
        symbols = list(ALPHABET)
        drbg.shuffle(symbols)
        plug_symbols = symbols[:26]  # 13 pairs = 26 symbols, 4 unplugged
        pairs = []
        for i in range(0, 26, 2):
            a, b = plug_symbols[i], plug_symbols[i + 1]
            pairs.append((min(a, b), max(a, b)))
        if not set(pairs).intersection(reflector_set):
            return pairs


def load_sanskrit_phrases(phrases_file: Path) -> List[str]:
    if not phrases_file.exists():
        raise FileNotFoundError(f"Sanskrit phrases file not found: {phrases_file}")
    with open(phrases_file, "r", encoding="utf-8") as f:
        lines = [line.strip().upper() for line in f if line.strip() and not line.startswith("#")]
    if len(lines) < 40:
        raise ValueError(f"Expected at least 40 Sanskrit phrases, found {len(lines)}")
    return lines


def build_bilingual_plaintext(drbg: HMAC_DRBG, flag: str, phrases: List[str]) -> Tuple[str, str, int]:
    """
    Constructs bilingual plaintext:
    - Null prefix of 0..11 symbols
    - Opener: DHRITARASHTRAUVACHA#_
    - Interleaved English narrative + 6 Sanskrit phrases
    - Flag embedding
    Returns (raw_plaintext, null_prefix_str, null_prefix_len).
    """
    null_len = drbg.next_int(0, 11)
    null_prefix = "".join(drbg.choice(list(ALPHABET)) for _ in range(null_len))

    opener = "DHRITARASHTRAUVACHA#_"

    selected_phrases = drbg.sample(phrases, 6)

    # Narrative sentences
    p1 = f"{selected_phrases[0]}#_SANJAYA_SAID#_{selected_phrases[1]}#_"
    p2 = f"THE_SEVENTH_TIER_TURNS_UPON_CELESTIAL_AXES#_{selected_phrases[2]}#_"
    p3 = f"VALOR_SHINES_IN_DEFEAT_AND_VICTORY#_{selected_phrases[3]}#_"
    p4 = f"THE_SACRED_SEAL_IS_{flag}#_{selected_phrases[4]}#_"
    p5 = f"DHARMA_ENDURES_BEYOND_ALL_AGES#_{selected_phrases[5]}#"

    body = p1 + p2 + p3 + p4 + p5
    full_text = null_prefix + opener + body

    # Clean characters to ALPHABET
    cleaned = "".join(c for c in full_text if c in ALPHABET)
    return cleaned, null_prefix, null_len


def derive_team_instance(
    master_seed: str,
    team_id: str,
    phrases_file: Path,
    keyword: str = "SANJAYAUVACHA",
    flag_override: str = None
) -> Dict[str, Any]:
    team_seed_bytes = derive_team_seed(master_seed, team_id)
    drbg = HMAC_DRBG(team_seed_bytes)

    # 1. 8-Rotor pool
    all_rotors = generate_8_rotors(drbg)

    # 2. Seated 4 rotors (order 0 to 3)
    seated_names = drbg.sample(ROTOR_NAMES, 4)

    # 3. Random rings & positions
    ring_settings = [drbg.next_int(0, N - 1) for _ in range(4)]
    grundstellung = [drbg.next_int(0, N - 1) for _ in range(4)]

    # 4. Reflector & Plugboard
    reflector_pairs = generate_reflector(drbg)
    plugboard_pairs = generate_plugboard(drbg, reflector_pairs)

    # 5. Universal Flag (Same for all teams)
    flag = (flag_override or UNIVERSAL_FLAG).strip().upper()

    # Flag hash
    flag_salt = os.urandom(8).hex()
    flag_sha256 = f"{flag_salt}:{hashlib.sha256((flag_salt + flag).encode()).hexdigest()}"

    # 6. Bilingual Plaintext
    phrases = load_sanskrit_phrases(phrases_file)
    raw_plaintext, null_prefix, null_len = build_bilingual_plaintext(drbg, flag, phrases)

    # 7. Layer S: Pre-Substitution
    sub = KeywordSubstitution(keyword)
    s_plaintext = sub.encrypt(raw_plaintext)

    # 8. Enigma Stage
    rotors = [
        Rotor(
            wiring=all_rotors[seated_names[i]]["wiring"],
            notches=all_rotors[seated_names[i]]["notches"],
            ring_setting=ring_settings[i],
            position=grundstellung[i]
        )
        for i in range(4)
    ]
    reflector = Reflector(reflector_pairs)
    plugboard = Plugboard(plugboard_pairs)
    machine = EnigmaMachine(rotors, reflector, plugboard)
    ciphertext = machine.encrypt_string(s_plaintext)

    return {
        "team_id": team_id,
        "master_seed": master_seed,
        "flag": flag,
        "flag_sha256": flag_sha256,
        "decoy_flags": DEFAULT_DECOYS,
        "null_prefix_len": null_len,
        "null_prefix": null_prefix,
        "raw_plaintext": raw_plaintext,
        "s_plaintext": s_plaintext,
        "ciphertext": ciphertext,
        "ciphertext_grouped": " ".join([ciphertext[i:i+5] for i in range(0, len(ciphertext), 5)]),
        "all_rotors": all_rotors,
        "walzenlage": seated_names,
        "ringstellung": ring_settings,
        "grundstellung": grundstellung,
        "reflector_pairs": reflector_pairs,
        "plugboard": plugboard_pairs,
        "pre_sub_keyword": keyword
    }


def generate_replica_config() -> Dict[str, Any]:
    """Generates the public Training Replica configuration."""
    drbg = HMAC_DRBG(REPLICA_SEED)
    all_rotors = generate_8_rotors(drbg)
    seated_names = drbg.sample(ROTOR_NAMES, 4)
    ring_settings = [drbg.next_int(0, N - 1) for _ in range(4)]
    grundstellung = [drbg.next_int(0, N - 1) for _ in range(4)]
    reflector_pairs = generate_reflector(drbg)
    plugboard_pairs = generate_plugboard(drbg, reflector_pairs)

    return {
        "name": "Chakravyuha Training Replica",
        "description": "Replica built from captured drawings. Its wheels are not the originals.",
        "alphabet": ALPHABET,
        "alphabet_size": N,
        "rotors": all_rotors,
        "seated_rotors": seated_names,
        "default_ringstellung": ring_settings,
        "default_grundstellung": grundstellung,
        "reflector_pairs": reflector_pairs,
        "default_plugboard": plugboard_pairs
    }


def main():
    parser = argparse.ArgumentParser(description="Generate Kurukshetra CTF Challenge 3 Instances & Artifacts (v2)")
    parser.add_argument("--master-seed", default=DEFAULT_MASTER_SEED, help="Master seed (hex or string)")
    parser.add_argument("--team", default="default_team", help="Team ID to generate instance for")
    parser.add_argument("--flag", default=None, help="Universal flag override (e.g. KCTF{...})")
    parser.add_argument("--out-dir", default="secrets", help="Directory to write team secret instance")
    parser.add_argument("--public-dir", default="public_artifacts", help="Directory to write public artifacts")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    phrases_file = root / "tools" / "phrases_sanskrit.txt"
    public_dir = root / args.public_dir
    secrets_dir = root / args.out_dir
    public_dir.mkdir(parents=True, exist_ok=True)
    secrets_dir.mkdir(parents=True, exist_ok=True)

    # 1. Derive Team instance
    instance = derive_team_instance(args.master_seed, args.team, phrases_file, flag_override=args.flag)
    instance_path = secrets_dir / "challenge_instance.json"
    with open(instance_path, "w", encoding="utf-8") as f:
        json.dump(instance, f, indent=2)
    print(f"[+] Team instance written to: {instance_path}")

    # 2. Write Training Replica config
    replica = generate_replica_config()
    replica_path = public_dir / "replica_config.json"
    with open(replica_path, "w", encoding="utf-8") as f:
        json.dump(replica, f, indent=2)
    print(f"[+] Training replica config written to: {replica_path}")

    # 3. Write public pre-gate ciphertext.txt
    cipher_path = public_dir / "ciphertext.txt"
    with open(cipher_path, "w", encoding="utf-8") as f:
        f.write(instance["ciphertext_grouped"] + "\n")
    print(f"[+] Public ciphertext written to: {cipher_path}")


if __name__ == "__main__":
    main()
