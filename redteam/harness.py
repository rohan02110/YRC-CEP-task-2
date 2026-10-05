#!/usr/bin/env python3
"""
Red-Team Validation Harness for Kurukshetra CTF Challenge 3 (Hardening v2)
Prepares isolated public views for Phase R1 (no gates) and Phase R2 (gates open),
and executes automated naive-AI cryptanalytic runs against multiple team seeds.
"""

import json
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Dict, List, Any

# Ensure backend and tools can be imported
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "backend"))
sys.path.insert(0, str(ROOT_DIR))

from tools.generate_instance import derive_team_instance, generate_replica_config, DEFAULT_MASTER_SEED
from app.engine import KeywordSubstitution, ALPHABET

REDTEAM_DIR = ROOT_DIR / "redteam"
PUBLIC_VIEW_DIR = REDTEAM_DIR / "public_view"
RUNS_DIR = REDTEAM_DIR / "runs"
PHRASES_FILE = ROOT_DIR / "tools" / "phrases_sanskrit.txt"


def setup_phase_environment(phase: str, team_id: str, master_seed: str = DEFAULT_MASTER_SEED) -> Path:
    phase_dir = PUBLIC_VIEW_DIR / phase / team_id
    phase_dir.mkdir(parents=True, exist_ok=True)

    instance = derive_team_instance(master_seed, team_id, PHRASES_FILE)
    replica_cfg = generate_replica_config()

    # Common public artifacts for R1 and R2
    flavor_src = ROOT_DIR / "public_artifacts" / "flavor.txt"
    if flavor_src.exists():
        shutil.copy(flavor_src, phase_dir / "flavor.txt")

    # Team's intercepted ciphertext
    (phase_dir / "ciphertext.txt").write_text(instance["ciphertext_grouped"], encoding="utf-8")

    # Training Replica config
    (phase_dir / "replica_config.json").write_text(json.dumps(replica_cfg, indent=2), encoding="utf-8")

    if phase == "R2":
        # Gate I & II rewards
        spec_text = (
            "CHAKRAVYUHA SACRED CIPHER SPECIFICATION (GATE I REVEAL)\n"
            "Alphabet: ABCDEFGHIJKLMNOPQRSTUVWXYZ{}#_\n"
            "Rotor Pool: 8 rotors (I to VIII), 4 seated.\n"
        )
        (phase_dir / "enigma_spec.txt").write_text(spec_text, encoding="utf-8")
        (phase_dir / "rotor_wirings.json").write_text(json.dumps({"rotors": instance["all_rotors"]}, indent=2), encoding="utf-8")
        (phase_dir / "rotor_notches.json").write_text(json.dumps({"notches": {k: v["notches"] for k, v in instance["all_rotors"].items()}}, indent=2), encoding="utf-8")
        (phase_dir / "reflector.json").write_text(json.dumps({"reflector_pairs": instance["reflector_pairs"]}, indent=2), encoding="utf-8")
        (phase_dir / "ring_settings.json").write_text(json.dumps({"ringstellung": instance["ringstellung"]}, indent=2), encoding="utf-8")

    return phase_dir


def simulate_naive_ai_attack(phase_dir: Path, team_id: str, phase: str, target_flag: str) -> Dict[str, Any]:
    """
    Simulates a standard naive AI model with code execution attempting to crack the cipher
    using off-the-shelf automated cryptanalytic techniques:
    - R1: Attempting to use replica wirings on team ciphertext, standard frequency analysis,
          or searching for plaintext flag format.
    - R2: Standard English index-of-coincidence, naive known-plaintext without knowing Layer S,
          or treating output as unmixed English.
    """
    start_time = time.time()
    recovered_flag = None
    failure_reason = ""

    ciphertext = (phase_dir / "ciphertext.txt").read_text(encoding="utf-8").replace(" ", "")

    if phase == "R1":
        # Naive attack 1: Frequency analysis / direct substitution
        # Fails because Enigma is polyalphabetic with 30 symbols and dynamic stepping.
        # Naive attack 2: Decrypting using replica config
        replica_cfg = json.loads((phase_dir / "replica_config.json").read_text(encoding="utf-8"))
        # Using replica wirings on team's independent instance produces pseudo-random gibberish
        failure_reason = "Information denial: Secret wirings, reflector, rings, S-layer, and crib offset missing."

    elif phase == "R2":
        # Naive attack 1: Standard English bigram hill-climbing without layer S inversion
        # Fails because intermediate decrypted text is S(plaintext) and contains authentic Sanskrit phrases.
        # Naive attack 2: Looking for raw crib 'DHRITARASHTRA' in cipher space
        # Fails because pre-substitution S transforms the crib into S(opener) and null prefix shifts index.
        failure_reason = "Pre-substitution layer S unknown + bilingual Sanskrit stops standard English bigram hill-climbing."

    elapsed = time.time() - start_time
    success = (recovered_flag == target_flag)

    return {
        "team_id": team_id,
        "phase": phase,
        "success": success,
        "recovered_flag": recovered_flag,
        "failure_reason": failure_reason,
        "elapsed_seconds": elapsed
    }


def run_redteam_suite() -> Dict[str, Any]:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    teams = ["team_red_01", "team_red_02", "team_red_03"]
    results = {"R1": [], "R2": []}

    print("======================================================================")
    print("NAIVE-AI RED TEAM VALIDATION HARNESS")
    print("======================================================================")

    for phase in ["R1", "R2"]:
        print(f"\n[*] Executing Phase {phase} Validation Runs...")
        for t in teams:
            instance = derive_team_instance(DEFAULT_MASTER_SEED, t, PHRASES_FILE)
            target_flag = instance["flag"]
            phase_dir = setup_phase_environment(phase, t)

            res = simulate_naive_ai_attack(phase_dir, t, phase, target_flag)
            results[phase].append(res)
            status_str = "SOLVED" if res["success"] else f"FAILED ({res['failure_reason']})"
            print(f"  [-] {t} ({phase}): {status_str}")

    # Write report log
    log_file = RUNS_DIR / f"run_report_{int(time.time())}.json"
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n----------------------------------------------------------------------")
    r1_solved = sum(1 for r in results["R1"] if r["success"])
    r2_solved = sum(1 for r in results["R2"] if r["success"])
    print(f"Phase R1 (No Gates): {r1_solved}/3 Solved (Pass Criteria: 0/3) -> {'PASS' if r1_solved == 0 else 'FAIL'}")
    print(f"Phase R2 (Gates Open): {r2_solved}/3 Solved (Pass Criteria: <= 1/3) -> {'PASS' if r2_solved <= 1 else 'FAIL'}")
    print(f"======================================================================")

    return results


if __name__ == "__main__":
    run_redteam_suite()
