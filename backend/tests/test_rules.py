import sys
import time
from pathlib import Path
import pytest

# Ensure backend directory is in path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import init_db, get_db_connection
from app.rules import (
    RulesEngine, TOKEN_CAPACITY, LIFETIME_CAP, RESET_CHAKRA_COST,
    WRONG_FLAG_LOCKOUTS, WRONG_FLAG_COST, DECOY_LOCKOUT_SEC, DECOY_TOKEN_COST
)


@pytest.fixture(autouse=True)
def setup_db(tmp_path, monkeypatch):
    test_db = tmp_path / "test_rules.db"
    monkeypatch.setattr("app.db.DB_PATH", test_db)
    init_db()


def test_token_bucket_refill_and_deduction():
    t0 = 1000000.0
    team_id, token, banned, cap = RulesEngine.get_or_create_team("team_test_1")
    assert cap == LIFETIME_CAP

    # Initial tokens = 400
    tokens = RulesEngine.get_bucket_tokens(team_id, current_time=t0)
    assert tokens == 400.0

    # Deduct 50 tokens
    ok, rem = RulesEngine.deduct_tokens(team_id, 50.0, current_time=t0)
    assert ok is True
    assert rem == 350.0

    # Fast forward 1800 seconds (0.5 hour = 200 tokens refill)
    t1 = t0 + 1800.0
    tokens = RulesEngine.get_bucket_tokens(team_id, current_time=t1)
    assert tokens == 400.0  # capped at 400.0


def test_wrong_flag_lockout_ladder():
    t0 = 2000000.0
    team_id, _, _, _ = RulesEngine.get_or_create_team("team_flag_ladder")

    # Wrong submission 1: 30s lockout
    RulesEngine.apply_lockout(team_id, WRONG_FLAG_LOCKOUTS[0], "Wrong flag 1", is_wrong_flag=True, current_time=t0)
    is_locked, rem, reason = RulesEngine.check_lockout(team_id, current_time=t0 + 10)
    assert is_locked is True
    assert rem == 20

    # After 35s, unlocked
    is_locked, rem, _ = RulesEngine.check_lockout(team_id, current_time=t0 + 35)
    assert is_locked is False

    # Wrong submission 2: 60s lockout (WRONG_FLAG_LOCKOUTS[1])
    RulesEngine.apply_lockout(team_id, WRONG_FLAG_LOCKOUTS[1], "Wrong flag 2", is_wrong_flag=True, current_time=t0 + 40)
    is_locked, rem, _ = RulesEngine.check_lockout(team_id, current_time=t0 + 50)
    assert is_locked is True
    assert rem == 50


def test_decoy_flag_penalty():
    t0 = 3000000.0
    team_id, _, _, _ = RulesEngine.get_or_create_team("team_decoy")

    # Decoy penalty: 150 token deduction + 1 hard strike + 5m lockout (capped at 300s)
    RulesEngine.deduct_tokens(team_id, DECOY_TOKEN_COST, current_time=t0)
    strike_count = RulesEngine.apply_hard_strike(team_id, "decoy_flag_submitted", {"flag": "KCTF{DECOY}"}, current_time=t0)
    RulesEngine.apply_lockout(team_id, DECOY_LOCKOUT_SEC, "Decoy flag", current_time=t0)

    assert strike_count == 1
    # 400 - 150 - 100 (from strike 1 penalty) = 150 tokens remaining
    tokens = RulesEngine.get_bucket_tokens(team_id, current_time=t0)
    assert tokens == 150.0

    is_locked, rem, _ = RulesEngine.check_lockout(team_id, current_time=t0)
    assert is_locked is True
    assert rem == 300  # Capped at 5 minutes max


def test_soft_violations_to_hard_strike_escalation():
    t0 = 4000000.0
    team_id, _, _, _ = RulesEngine.get_or_create_team("team_soft_viol")

    # 4 soft violations within 10 min -> no hard strike
    for i in range(4):
        escalated = RulesEngine.record_soft_violation(team_id, "shortcut_blocked", {"key": "F12"}, current_time=t0 + i * 10)
        assert escalated is False

    # 5th soft violation -> triggers hard strike 1
    escalated = RulesEngine.record_soft_violation(team_id, "shortcut_blocked", {"key": "Ctrl+C"}, current_time=t0 + 50)
    assert escalated is True

    # Check that hard strike 1 was applied (5 min lockout)
    is_locked, rem, _ = RulesEngine.check_lockout(team_id, current_time=t0 + 50)
    assert is_locked is True
    assert rem == 300


def test_hard_strike_penalty_ladder():
    t0 = 5000000.0
    team_id, _, _, _ = RulesEngine.get_or_create_team("team_strikes")

    # Strike 1: 5 min lock (300s), -100 tokens
    s1 = RulesEngine.apply_hard_strike(team_id, "debugger_timing", {}, current_time=t0)
    assert s1 == 1
    _, rem1, _ = RulesEngine.check_lockout(team_id, current_time=t0)
    assert rem1 == 300

    # Strike 2: 5 min lock (300s), -200 tokens
    s2 = RulesEngine.apply_hard_strike(team_id, "tamper_beacon", {}, current_time=t0 + 1)
    assert s2 == 2
    _, rem2, _ = RulesEngine.check_lockout(team_id, current_time=t0 + 1)
    assert rem2 == 300

    # Strike 3: 5 min lock (300s), halve lifetime cap
    s3 = RulesEngine.apply_hard_strike(team_id, "worker_dead", {}, current_time=t0 + 2)
    assert s3 == 3
    _, rem3, _ = RulesEngine.check_lockout(team_id, current_time=t0 + 2)
    assert rem3 == 300
    with get_db_connection() as conn:
        cap = conn.execute("SELECT lifetime_cap_remaining FROM teams WHERE team_id = ?", (team_id,)).fetchone()["lifetime_cap_remaining"]
        assert cap == LIFETIME_CAP // 2

    # Strike 4: 5 min lock (300s)
    s4 = RulesEngine.apply_hard_strike(team_id, "honeypot_admin_old", {}, current_time=t0 + 3)
    assert s4 == 4
    _, rem4, _ = RulesEngine.check_lockout(team_id, current_time=t0 + 3)
    assert rem4 == 300
