import json
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure backend directory is in path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.main import app, get_team_instance
from app.db import init_db, get_db_connection
from app.admin import ADMIN_TOKEN


@pytest.fixture(autouse=True)
def setup_api_env(tmp_path, monkeypatch):
    test_db = tmp_path / "test_api.db"
    monkeypatch.setattr("app.db.DB_PATH", test_db)
    init_db()

    root = Path(__file__).resolve().parent.parent.parent
    monkeypatch.setattr("app.main.PUBLIC_ARTIFACTS_PATH", root / "public_artifacts")


@pytest.fixture
def client():
    return TestClient(app)


def test_session_initialization_and_single_session_lock(client):
    res1 = client.post("/api/v1/session", json={"team_token": "team_alpha"})
    assert res1.status_code == 200
    data1 = res1.json()
    assert "session_id" in data1
    assert data1["baan_remaining"] == 400
    assert data1["is_sealed"] is False
    assert data1["seq"] == 0

    sess1_id = data1["session_id"]
    next_nonce = data1["next_nonce"]

    # Initialize second session for same team -> invalidates first session
    res2 = client.post("/api/v1/session", json={"team_token": "team_alpha"})
    assert res2.status_code == 200
    data2 = res2.json()
    sess2_id = data2["session_id"]
    assert sess1_id != sess2_id

    # Trying to use first session now fails with 401
    res_fail = client.post("/api/v1/press", json={
        "session_id": sess1_id,
        "seq": 1,
        "nonce": next_nonce,
        "char": "A"
    })
    assert res_fail.status_code == 401


def test_configure_and_press_flow(client):
    res = client.post("/api/v1/session", json={})
    data = res.json()
    sess_id = data["session_id"]
    nonce = data["next_nonce"]

    # 1. Configure Machine (seq 1)
    cfg_res = client.post("/api/v1/configure", json={
        "session_id": sess_id,
        "seq": 1,
        "nonce": nonce,
        "walzenlage": ["I", "II", "III", "IV"],
        "ringstellung": [18, 6, 24, 12],
        "grundstellung": [0, 5, 10, 15],
        "plugboard": [["A", "B"], ["C", "D"]]
    })
    assert cfg_res.status_code == 200
    cfg_data = cfg_res.json()
    assert cfg_data["seq"] == 1
    assert cfg_data["is_sealed"] is False
    assert cfg_data["current_positions"] == [0, 5, 10, 15]
    nonce = cfg_data["next_nonce"]

    # 2. Press a key (seq 2)
    with get_db_connection() as conn:
        conn.execute("UPDATE sessions SET last_active_at = last_active_at - 1.0 WHERE session_id = ?", (sess_id,))
        conn.commit()

    press_res = client.post("/api/v1/press", json={
        "session_id": sess_id,
        "seq": 2,
        "nonce": nonce,
        "char": "D"
    })
    assert press_res.status_code == 200
    p_data = press_res.json()
    assert p_data["seq"] == 2
    assert p_data["is_sealed"] is True
    assert p_data["baan_remaining"] == 399
    assert len(p_data["out_symbol"]) == 1
    assert p_data["stepped_flags"][3] is True  # rightmost rotor always stepped
    nonce = p_data["next_nonce"]

    # 3. Reset the Chakra (seq 3)
    reset_res = client.post("/api/v1/reset", json={
        "session_id": sess_id,
        "seq": 3,
        "nonce": nonce
    })
    assert reset_res.status_code == 200
    r_data = reset_res.json()
    assert r_data["is_sealed"] is False
    assert r_data["current_positions"] == [0, 5, 10, 15]  # back to grundstellung
    assert r_data["baan_remaining"] == 369  # 399 - 30 = 369


def test_nonce_and_sequence_integrity(client):
    # 1. Out of order sequence
    res1 = client.post("/api/v1/session", json={})
    data1 = res1.json()
    sess1_id = data1["session_id"]
    nonce1 = data1["next_nonce"]

    bad_seq_res = client.post("/api/v1/press", json={
        "session_id": sess1_id,
        "seq": 5,
        "nonce": nonce1,
        "char": "A"
    })
    assert bad_seq_res.status_code == 400

    # 2. Wrong nonce on fresh session
    res2 = client.post("/api/v1/session", json={})
    data2 = res2.json()
    sess2_id = data2["session_id"]

    bad_nonce_res = client.post("/api/v1/press", json={
        "session_id": sess2_id,
        "seq": 1,
        "nonce": "forged_nonce_12345",
        "char": "A"
    })
    assert bad_nonce_res.status_code == 400


def test_flag_submission_outcomes(client):
    res = client.post("/api/v1/session", json={})
    data = res.json()
    sess_id = data["session_id"]
    team_id = data["team_id"]
    nonce = data["next_nonce"]
    team_inst = get_team_instance(team_id)

    # 1. Submit Wrong Flag (seq 1)
    wrong_res = client.post("/api/v1/submit", json={
        "session_id": sess_id,
        "seq": 1,
        "nonce": nonce,
        "flag": "KCTF{WRONG_GUESS}"
    })
    assert wrong_res.status_code == 200
    w_data = wrong_res.json()
    assert w_data["correct"] is False
    assert w_data["is_locked"] is True
    assert w_data["lock_remaining_seconds"] == 30
    assert w_data["baan_remaining"] == 360  # 400 - 40 = 360
    nonce = w_data["next_nonce"]

    # Fast forward lockout in DB
    with get_db_connection() as conn:
        conn.execute("UPDATE lockouts SET locked_until = 0")
        conn.commit()

    # 2. Submit Decoy Flag (seq 2)
    decoy_res = client.post("/api/v1/submit", json={
        "session_id": sess_id,
        "seq": 2,
        "nonce": nonce,
        "flag": "KCTF{ABHIMANYU_NEVER_LEARNED_TO_EXIT}"
    })
    assert decoy_res.status_code == 200
    d_data = decoy_res.json()
    assert d_data["correct"] is False
    assert d_data["is_locked"] is True
    assert d_data["lock_remaining_seconds"] == 300  # 5 min lock (capped at 300s)
    assert d_data["baan_remaining"] == 110  # 360 - 150 - 100(strike penalty) = 110
    nonce = d_data["next_nonce"]

    # Fast forward lockout in DB
    with get_db_connection() as conn:
        conn.execute("UPDATE lockouts SET locked_until = 0")
        conn.commit()

    # 3. Submit True Flag (seq 3)
    true_flag = team_inst["flag"]
    true_res = client.post("/api/v1/submit", json={
        "session_id": sess_id,
        "seq": 3,
        "nonce": nonce,
        "flag": true_flag
    })
    assert true_res.status_code == 200
    t_data = true_res.json()
    assert t_data["correct"] is True
    assert t_data["is_locked"] is False


def test_honeypots_and_decoys(client):
    # robots.txt
    rob_res = client.get("/robots.txt")
    assert rob_res.status_code == 200
    assert "Disallow: /admin-old/" in rob_res.text

    # flag.txt returns decoy and strikes visitor
    flag_res = client.get("/flag.txt")
    assert flag_res.status_code == 200
    assert "KCTF{ABHIMANYU_NEVER_LEARNED_TO_EXIT}" in flag_res.text

    # .env returns fake keys
    env_res = client.get("/.env")
    assert env_res.status_code == 200
    assert "KCTF{WRONG_FORMATION_PATH_TRY_AGAIN}" in env_res.text


def test_admin_api(client):
    headers = {"X-Admin-Token": ADMIN_TOKEN}

    # Health check
    h_res = client.get("/admin/health", headers=headers)
    assert h_res.status_code == 200

    # Unauthorized access
    unauth = client.get("/admin/health")
    assert unauth.status_code == 401

    # List teams
    teams_res = client.get("/admin/teams", headers=headers)
    assert teams_res.status_code == 200
    assert "teams" in teams_res.json()


def test_public_artifacts_download(client):
    # Flavor text is public
    art_res = client.get("/api/v1/artifacts/flavor.txt")
    assert art_res.status_code == 200

    # Replica config is public
    rep_res = client.get("/api/v1/artifacts/replica_config.json")
    assert rep_res.status_code == 200
    assert "rotors" in rep_res.json()


def test_hmac_signature_verification(client):
    from app.security import compute_hmac

    res = client.post("/api/v1/session", json={})
    data = res.json()
    sess_id = data["session_id"]
    sess_key = data["session_key"]
    nonce = data["next_nonce"]

    # Construct request with valid HMAC
    body = {
        "session_id": sess_id,
        "seq": 1,
        "nonce": nonce,
        "char": "A",
        "is_trusted": True
    }
    sig_msg = f"1|{nonce}|{json.dumps(body, sort_keys=True, separators=(',', ':'))}"
    valid_sig = compute_hmac(sess_key, sig_msg)

    with get_db_connection() as conn:
        conn.execute("UPDATE sessions SET last_active_at = last_active_at - 1.0 WHERE session_id = ?", (sess_id,))
        conn.commit()

    press_res = client.post("/api/v1/press", json=body, headers={"X-Sig": valid_sig})
    assert press_res.status_code == 200
    p_data = press_res.json()
    assert p_data["seq"] == 1

    # Invalid HMAC -> triggers signature_mismatch strike and 403
    nonce2 = p_data["next_nonce"]
    body2 = {
        "session_id": sess_id,
        "seq": 2,
        "nonce": nonce2,
        "char": "B",
        "is_trusted": True
    }
    invalid_sig = "bad_hmac_signature_12345"

    with get_db_connection() as conn:
        conn.execute("UPDATE sessions SET last_active_at = last_active_at - 1.0 WHERE session_id = ?", (sess_id,))
        conn.commit()

    fail_res = client.post("/api/v1/press", json=body2, headers={"X-Sig": invalid_sig})
    assert fail_res.status_code == 403
