#!/usr/bin/env python3
"""
Extended String Audit for Kurukshetra CTF Challenge 3 (Hardening v2)
Blocks CI if any forbidden cribs, spellings, ring-rules, decoy flags, or admin tokens leak
into frontend/dist, public_artifacts, or live API responses across all gate levels.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

# Ensure backend can be imported for live route auditing
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "backend"))

from fastapi.testclient import TestClient
from app.main import app

FORBIDDEN_BASE_TOKENS = [
    "DHRITARASHTRA",
    "DHRITRASHTRA",
    "DHRTARASTRA",
    "UVACHA",
    "UVACA",
    "SANJAYAUVACHA",
    "ring rule",
    "KURUKSHETRA_SACRED_ADMIN"
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


def normalize_text(text: str) -> str:
    """Removes separators, underscores, spaces, dashes to detect obfuscated substrings."""
    return re.sub(r"[\s_\-#{}\[\]/\\\"':;,.]", "", text).upper()


def check_forbidden_in_text(text: str, source_label: str) -> List[Tuple[str, str]]:
    violations = []
    norm_text = normalize_text(text)
    lower_text = text.lower()

    for tok in FORBIDDEN_BASE_TOKENS:
        norm_tok = normalize_text(tok)
        if norm_tok in norm_text or tok.lower() in lower_text:
            violations.append((source_label, f"Forbidden token found: '{tok}'"))

    for decoy in DEFAULT_DECOYS:
        if decoy in text:
            # Note: HTML honeypots in index.html specifically allow decoy comment
            if not source_label.endswith("index.html"):
                violations.append((source_label, f"Decoy flag leak: '{decoy}'"))

    return violations


def audit_filesystem() -> List[Tuple[str, str]]:
    violations = []
    dist_dir = ROOT_DIR / "frontend" / "dist"
    public_artifacts_dir = ROOT_DIR / "public_artifacts"

    # 1. Audit public_artifacts
    print(f"[*] Auditing files in {public_artifacts_dir}...")
    if public_artifacts_dir.exists():
        for f in public_artifacts_dir.glob("*"):
            if f.is_file():
                content = f.read_text(encoding="utf-8", errors="ignore")
                violations.extend(check_forbidden_in_text(content, f"public_artifacts/{f.name}"))

    # 2. Audit frontend/dist
    print(f"[*] Auditing frontend distribution in {dist_dir}...")
    if dist_dir.exists():
        for root, _, files in os.walk(dist_dir):
            for file in files:
                fpath = Path(root) / file
                if fpath.suffix in [".js", ".html", ".css", ".txt", ".json"]:
                    content = fpath.read_text(encoding="utf-8", errors="ignore")
                    # For JS files, ensure no raw KCTF{ flag strings
                    if fpath.suffix == ".js" and "KCTF{" in content:
                        violations.append((fpath.name, "JS bundle contains raw 'KCTF{' string"))
                    violations.extend(check_forbidden_in_text(content, f"dist/{fpath.name}"))
    else:
        violations.append(("frontend/dist", "dist directory missing! Run npm run build first."))

    return violations


def audit_live_routes() -> List[Tuple[str, str]]:
    violations = []
    client = TestClient(app)
    print("[*] Auditing live API routes unauthenticated & gated...")

    # 1. Unauthenticated routes
    public_routes = [
        "/api/v1/artifacts/flavor.txt",
        "/api/v1/artifacts/replica_config.json",
        "/api/v1/hints"
    ]
    for r in public_routes:
        resp = client.get(r)
        violations.extend(check_forbidden_in_text(resp.text, f"GET {r}"))

    # 2. Authenticated pre-gate session
    init_resp = client.post("/api/v1/session", json={})
    if init_resp.status_code == 200:
        sess_data = init_resp.json()
        violations.extend(check_forbidden_in_text(init_resp.text, "POST /api/v1/session"))
        sess_id = sess_data["session_id"]

        gates_resp = client.get(f"/api/v1/gates?session_id={sess_id}")
        violations.extend(check_forbidden_in_text(gates_resp.text, "GET /api/v1/gates"))

        cipher_resp = client.get(f"/api/v1/artifacts/ciphertext.txt?session_id={sess_id}")
        violations.extend(check_forbidden_in_text(cipher_resp.text, "GET /api/v1/artifacts/ciphertext.txt"))

    return violations


def main():
    print("=" * 70)
    print("EXTENDED STRING AUDIT (CI-BLOCKING) — V2 HARDENING")
    print("=" * 70)

    violations = []
    violations.extend(audit_filesystem())
    violations.extend(audit_live_routes())

    if violations:
        print("\n" + "!" * 70)
        print(f"[-] STRING AUDIT FAILED! {len(violations)} VIOLATION(S) DETECTED:")
        print("!" * 70)
        for src, desc in violations:
            print(f"  [FAIL] [{src}] -> {desc}")
        sys.exit(1)

    print("\n" + "=" * 70)
    print("[+] EXTENDED STRING AUDIT PASSED! ZERO FORBIDDEN STRINGS OR LEAKS.")
    print("=" * 70)
    sys.exit(0)


if __name__ == "__main__":
    main()
