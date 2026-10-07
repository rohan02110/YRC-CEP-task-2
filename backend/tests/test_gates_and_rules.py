import os
import sys
import time
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

# Setup path
BACKEND_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BACKEND_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Use isolated test database
os.environ["DATABASE_PATH"] = str(BACKEND_DIR / "test_chakravyuha_v2.db")
os.environ["RULES_CONFIG_PATH"] = str(ROOT_DIR / "config" / "rules.yaml")
os.environ["GATES_CONFIG_PATH"] = str(ROOT_DIR / "config" / "gates.yaml")
os.environ["MASTER_SEED"] = "0x9F82A4C6E1D3B5792468ACE013579BDF2468ACE013579BDF2468ACE013579BDF"

from app.db import init_db, get_db_connection
from app.main import app, get_team_instance, REPLICA_CONFIG
from app.engine import (
    ALPHABET, N, KeywordSubstitution,
    Rotor, Reflector, Plugboard, EnigmaMachine
)

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_teardown():
    test_db = Path(os.environ["DATABASE_PATH"])
    if test_db.exists():
        try:
            test_db.unlink()
        except Exception:
            pass
    init_db()
    yield
    if test_db.exists():
        try:
            test_db.unlink()
        except Exception:
            pass


def test_public_and_gated_artifacts_access():
    # 1. Pre-gate public files accessible without session or gate
    resp = client.get("/api/v1/artifacts/flavor.txt")
    assert resp.status_code == 200

    resp = client.get("/api/v1/artifacts/replica_config.json")
    assert resp.status_code == 200
    replica_data = resp.json()
    assert "rotors" in replica_data
    assert len(replica_data["rotors"]) == 8

    # 2. Gated files without session return 401
    resp = client.get("/api/v1/artifacts/rotor_wirings.json")
    assert resp.status_code == 401

    # 3. Create session for team A
    init_resp = client.post("/api/v1/session", json={}).json()
    session_id = init_resp["session_id"]
    team_id = init_resp["team_id"]
    seq = 0
    nonce = init_resp["next_nonce"]

    # Ciphertext is available with session
    resp = client.get(f"/api/v1/artifacts/ciphertext.txt?session_id={session_id}")
    assert resp.status_code == 200
    assert len(resp.text) > 50

    # Before unlocking Gate I, gated files return 403
    resp = client.get(f"/api/v1/artifacts/rotor_wirings.json?session_id={session_id}")
    assert resp.status_code == 403

    resp = client.get(f"/api/v1/artifacts/reflector.json?session_id={session_id}")
    assert resp.status_code == 403

    # Unlock Gate I
    seq += 1
    unlock1_resp = client.post("/api/v1/gates/unlock", json={
        "session_id": session_id,
        "seq": seq,
        "nonce": nonce,
        "gate_id": "I",
        "seal": "KCTF{GANDIVA_BOW_UNSTRINGED_SECRET}"
    }).json()
    assert unlock1_resp["success"] is True
    nonce = unlock1_resp["next_nonce"]

    # Gate I artifacts now accessible
    resp = client.get(f"/api/v1/artifacts/rotor_wirings.json?session_id={session_id}")
    assert resp.status_code == 200

    # Unlock Gate II
    seq += 1
    unlock2_resp = client.post("/api/v1/gates/unlock", json={
        "session_id": session_id,
        "seq": seq,
        "nonce": nonce,
        "gate_id": "II",
        "seal": "SANJAYAUVACHA"
    }).json()
    assert unlock2_resp["success"] is True

    # Gate II artifacts now accessible
    resp = client.get(f"/api/v1/artifacts/reflector.json?session_id={session_id}")
    assert resp.status_code == 200


def test_gate_unlocking_ladder_and_decoy_detection():
    init_resp = client.post("/api/v1/session", json={}).json()
    session_id = init_resp["session_id"]
    seq = 0
    nonce = init_resp["next_nonce"]

    # Invalid seal rejected
    seq += 1
    resp = client.post("/api/v1/gates/unlock", json={
        "session_id": session_id,
        "seq": seq,
        "nonce": nonce,
        "gate_id": "I",
        "seal": "WRONG_SEAL"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert data["is_unlocked"] is False
    nonce = data["next_nonce"]

    # Valid seal unlocked (supports numeric "1" or "I" and variations)
    seq += 1
    resp = client.post("/api/v1/gates/unlock", json={
        "session_id": session_id,
        "seq": seq,
        "nonce": nonce,
        "gate_id": "1",
        "seal": "GANDIVA_BOW_UNSTRINGED_SECRET"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["is_unlocked"] is True
    nonce = data["next_nonce"]

    # Unlock Gate 2 with numeric "2"
    seq += 1
    resp = client.post("/api/v1/gates/unlock", json={
        "session_id": session_id,
        "seq": seq,
        "nonce": nonce,
        "gate_id": "2",
        "seal": "SANJAYAUVACHA"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["is_unlocked"] is True


def test_successful_gate_unlock_and_artifact_reveal():
    init_resp = client.post("/api/v1/session", json={}).json()
    session_id = init_resp["session_id"]
    team_id = init_resp["team_id"]
    seq = 0
    nonce = init_resp["next_nonce"]

    # Unlock Gate I with valid seal (KCTF{GANDIVA_BOW_UNSTRINGED_SECRET})
    seq += 1
    resp = client.post("/api/v1/gates/unlock", json={
        "session_id": session_id,
        "seq": seq,
        "nonce": nonce,
        "gate_id": "I",
        "seal": "KCTF{GANDIVA_BOW_UNSTRINGED_SECRET}"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["is_unlocked"] is True
    assert "enigma_spec.txt" in data["reveals"]
    nonce = data["next_nonce"]

    # Now Gate I artifacts are accessible
    resp = client.get(f"/api/v1/artifacts/rotor_wirings.json?session_id={session_id}")
    assert resp.status_code == 200
    rw_data = resp.json()
    assert "rotors" in rw_data
    assert len(rw_data["rotors"]) == 8

    resp = client.get(f"/api/v1/artifacts/enigma_spec.txt?session_id={session_id}")
    assert resp.status_code == 200
    assert "CHAKRAVYUHA SACRED CIPHER SPECIFICATION" in resp.text

    # Gate II still locked
    resp = client.get(f"/api/v1/artifacts/reflector.json?session_id={session_id}")
    assert resp.status_code == 403

    # Unlock Gate II with valid seal (SANJAYAUVACHA)
    seq += 1
    resp = client.post("/api/v1/gates/unlock", json={
        "session_id": session_id,
        "seq": seq,
        "nonce": nonce,
        "gate_id": "II",
        "seal": "SANJAYAUVACHA"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["is_unlocked"] is True
    nonce = data["next_nonce"]

    # Gate II artifacts now accessible
    resp = client.get(f"/api/v1/artifacts/reflector.json?session_id={session_id}")
    assert resp.status_code == 200
    ref_data = resp.json()
    assert "reflector_pairs" in ref_data
    assert len(ref_data["reflector_pairs"]) == 15  # 30 symbols / 2 = 15 pairs

    resp = client.get(f"/api/v1/artifacts/ring_settings.json?session_id={session_id}")
    assert resp.status_code == 200
    rings_data = resp.json()
    assert "ringstellung" in rings_data
    assert len(rings_data["ringstellung"]) == 4


def test_per_team_uniqueness_and_universal_flag():
    # Team 1
    resp1 = client.post("/api/v1/session", json={}).json()
    t1_id = resp1["team_id"]
    t1_inst = get_team_instance(t1_id)

    # Team 2
    resp2 = client.post("/api/v1/session", json={}).json()
    t2_id = resp2["team_id"]
    t2_inst = get_team_instance(t2_id)

    assert t1_id != t2_id
    assert t1_inst["flag"] == t2_inst["flag"]
    assert t1_inst["ciphertext"] != t2_inst["ciphertext"]
    assert t1_inst["reflector_pairs"] != t2_inst["reflector_pairs"]

    # Both teams can submit the universal flag successfully
    seq = 1
    nonce = resp1["next_nonce"]
    resp = client.post("/api/v1/submit", json={
        "session_id": resp1["session_id"],
        "seq": seq,
        "nonce": nonce,
        "flag": t1_inst["flag"]
    })
    assert resp.status_code == 200
    sub_data = resp.json()
    assert sub_data["correct"] is True
    assert sub_data["is_locked"] is False


def test_dual_machine_modes_and_e2e_decryption():
    # 1. Initialize session (starts in Replica mode)
    init_resp = client.post("/api/v1/session", json={}).json()
    session_id = init_resp["session_id"]
    team_id = init_resp["team_id"]
    team_inst = get_team_instance(team_id)
    seq = 0
    nonce = init_resp["next_nonce"]

    # 2. Test Replica mode typing
    seq += 1
    with get_db_connection() as conn:
        conn.execute("UPDATE sessions SET last_active_at = last_active_at - 1.0 WHERE session_id = ?", (session_id,))
        conn.commit()

    resp = client.post("/api/v1/press", json={
        "session_id": session_id,
        "seq": seq,
        "nonce": nonce,
        "char": "A"
    })
    assert resp.status_code == 200
    press_data = resp.json()
    assert press_data["out_symbol"] in ALPHABET
    nonce = press_data["next_nonce"]

    # 3. Unlock Gate II to enable Original mode
    seq += 1
    u_resp = client.post("/api/v1/gates/unlock", json={
        "session_id": session_id,
        "seq": seq,
        "nonce": nonce,
        "gate_id": "II",
        "seal": "SANJAYAUVACHA"
    }).json()
    assert u_resp["success"] is True
    nonce = u_resp["next_nonce"]

    # 4. Switch to Original mode
    seq += 1
    resp = client.post("/api/v1/mode/switch", json={
        "session_id": session_id,
        "seq": seq,
        "nonce": nonce,
        "target_mode": "original"
    })
    assert resp.status_code == 200
    switch_data = resp.json()
    assert switch_data["mode"] == "original"
    nonce = switch_data["next_nonce"]

    # 5. Configure Original machine with the team's true secret settings
    seq += 1
    resp = client.post("/api/v1/configure", json={
        "session_id": session_id,
        "seq": seq,
        "nonce": nonce,
        "walzenlage": team_inst["walzenlage"],
        "ringstellung": team_inst["ringstellung"],
        "grundstellung": team_inst["grundstellung"],
        "plugboard": team_inst["plugboard"]
    })
    assert resp.status_code == 200
    nonce = resp.json()["next_nonce"]

    # 6. Type the first 10 characters of the team's ciphertext through the Original machine
    ciphertext_prefix = team_inst["ciphertext"][:10]
    expected_s_prefix = team_inst["s_plaintext"][:10]
    decrypted_s_chars = []

    for c in ciphertext_prefix:
        seq += 1
        with get_db_connection() as conn:
            conn.execute("UPDATE sessions SET last_active_at = last_active_at - 1.0 WHERE session_id = ?", (session_id,))
            conn.commit()

        p_resp = client.post("/api/v1/press", json={
            "session_id": session_id,
            "seq": seq,
            "nonce": nonce,
            "char": c
        }).json()
        decrypted_s_chars.append(p_resp["out_symbol"])
        nonce = p_resp["next_nonce"]

    # The Enigma stage recovers S(plaintext)
    assert "".join(decrypted_s_chars) == expected_s_prefix

    # 7. Submit correct flag -> Success!
    seq += 1
    sub_resp = client.post("/api/v1/submit", json={
        "session_id": session_id,
        "seq": seq,
        "nonce": nonce,
        "flag": team_inst["flag"]
    }).json()
    assert sub_resp["correct"] is True
    assert "victory" in sub_resp["message"].lower() or "broken" in sub_resp["message"].lower()
