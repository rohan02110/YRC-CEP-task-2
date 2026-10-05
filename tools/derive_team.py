#!/usr/bin/env python3
"""
Organizer Tool: Derive Team Answer Key on Demand (v2)
Reproduces any team's exact parameters, wirings, crib offset, S-layer, and Flag from master seed.
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Ensure backend and tools can be imported
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "backend"))
sys.path.insert(0, str(root))
from tools.generate_instance import derive_team_instance, DEFAULT_MASTER_SEED


def main():
    parser = argparse.ArgumentParser(description="Derive team instance secrets for organizers")
    parser.add_argument("--team", required=True, help="Team ID (e.g. team_12345)")
    parser.add_argument("--master-seed", default=DEFAULT_MASTER_SEED, help="Master seed (hex or string)")
    parser.add_argument("--save", action="store_true", help="Save answer key to organizer/ANSWER_KEY_<team>.json")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    phrases_file = root / "tools" / "phrases_sanskrit.txt"

    instance = derive_team_instance(args.master_seed, args.team, phrases_file)

    answer_key = {
        "team_id": instance["team_id"],
        "flag": instance["flag"],
        "null_prefix_length": instance["null_prefix_len"],
        "null_prefix_symbols": instance["null_prefix"],
        "walzenlage": instance["walzenlage"],
        "ringstellung": instance["ringstellung"],
        "grundstellung": instance["grundstellung"],
        "reflector_pairs": instance["reflector_pairs"],
        "plugboard_pairs": instance["plugboard"],
        "pre_sub_keyword": instance["pre_sub_keyword"],
        "raw_plaintext": instance["raw_plaintext"],
        "ciphertext": instance["ciphertext"]
    }

    if args.save:
        org_dir = root / "organizer"
        org_dir.mkdir(parents=True, exist_ok=True)
        out_file = org_dir / f"ANSWER_KEY_{args.team}.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(answer_key, f, indent=2)
        print(f"[+] Saved answer key to: {out_file}")
    else:
        print(json.dumps(answer_key, indent=2))


if __name__ == "__main__":
    main()
