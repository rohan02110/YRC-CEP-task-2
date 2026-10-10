"""
Chakravyuha Merciless Rules Engine
Enforces token buckets, lifetime caps, penalty ladders, lockout timers, and strike management.
"""

import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import yaml

from app.db import get_db_connection, log_audit
from app.security import hash_user_agent, verify_flag

CONFIG_PATH = Path(os.environ.get("RULES_CONFIG_PATH", Path(__file__).resolve().parent.parent.parent / "config" / "rules.yaml"))
GATES_CONFIG_PATH = Path(os.environ.get("GATES_CONFIG_PATH", Path(__file__).resolve().parent.parent.parent / "config" / "gates.yaml"))


def load_rules_config() -> Dict[str, Any]:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
            return cfg.get("rules", {})
    return {}


def load_gates_config() -> Dict[str, Any]:
    if GATES_CONFIG_PATH.exists():
        with open(GATES_CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
            return cfg
    return {"chain_mode": "strict", "gates": []}


RULES = load_rules_config()
GATES_CONFIG = load_gates_config()

# Defaults / Overrides
TOKEN_CAPACITY = float(os.environ.get("TOKEN_CAPACITY", RULES.get("token_bucket_capacity", 400)))
REFILL_PER_SECOND = float(os.environ.get("TOKEN_REFILL_PER_HOUR", RULES.get("token_bucket_refill_per_hour", 400))) / 3600.0
LIFETIME_CAP = int(os.environ.get("LIFETIME_KEYPRESS_CAP", RULES.get("lifetime_keypress_cap", 2000)))
RESET_CHAKRA_COST = float(os.environ.get("RESET_CHAKRA_COST", RULES.get("reset_chakra_cost", 30)))
MIN_INTERVAL_SEC = float(RULES.get("min_keypress_interval_ms", 70)) / 1000.0
MAX_SUSTAINED_RATE = int(RULES.get("max_sustained_rate_per_sec", 12))
IDLE_TIMEOUT_SEC = float(RULES.get("idle_timeout_seconds", 480))
WATCHDOG_TIMEOUT_SEC = float(RULES.get("watchdog_timeout_seconds", 10))

MAX_LOCKOUT_SEC = float(os.environ.get("MAX_LOCKOUT_SECONDS", RULES.get("max_lockout_seconds", 300.0)))

WRONG_FLAG_LOCKOUTS = [min(float(x), MAX_LOCKOUT_SEC) for x in RULES.get("wrong_flag_lockouts", [30, 60, 120, 180, 300])]
WRONG_FLAG_COST = float(RULES.get("wrong_flag_token_cost", 40))

DECOY_LOCKOUT_SEC = min(float(RULES.get("decoy_flag_lockout_seconds", 300)), MAX_LOCKOUT_SEC)
DECOY_TOKEN_COST = float(RULES.get("decoy_flag_token_cost", 150))

SOFT_VIOLATION_WINDOW = float(RULES.get("soft_violation_window_seconds", 600))
SOFT_VIOLATIONS_FOR_STRIKE = int(RULES.get("soft_violations_for_strike", 5))


KNOWN_GATE_SEALS = {
    "I": {
        "KCTF{GANDIVA_BOW_UNSTRINGED_SECRET}",
        "GANDIVA_BOW_UNSTRINGED_SECRET",
        "KCTF{ARCHERY_IS_DHARMA}",
        "ARCHERY_IS_DHARMA",
        "KCTF{GANDIVA}",
        "GANDIVA",
        "KCTF{GANDIVAS_SECRET}",
        "GANDIVAS_SECRET",
    },
    "II": {
        "SANJAYAUVACHA",
        "KCTF{SANJAYAUVACHA}",
        "SANJAYA_UVACHA",
        "SANJAYA UVACHA",
        "KCTF{SANJAYA_UVACHA}",
        "KCTF{THE_BATTLEFIELD_REVEALS_ITS_TRUTH}",
        "THE_BATTLEFIELD_REVEALS_ITS_TRUTH",
        "KCTF{SANJAYA}",
        "SANJAYA",
    }
}


def normalize_gate_id(gate_id: Any) -> str:
    s = str(gate_id).strip().upper()
    if s in ("1", "GATE1", "GATE_1", "GATE 1", "I", "GATE_I", "GATE I"):
        return "I"
    if s in ("2", "GATE2", "GATE_2", "GATE 2", "II", "GATE_II", "GATE II"):
        return "II"
    return s


class RulesEngine:
    @staticmethod
    def get_or_create_team(team_token: Optional[str] = None) -> Tuple[str, str, bool, int]:
        """Returns (team_id, team_token, banned, lifetime_cap_remaining)."""
        now = time.time()
        with get_db_connection() as conn:
            if team_token:
                row = conn.execute("SELECT * FROM teams WHERE team_token = ?", (team_token,)).fetchone()
                if row:
                    return row["team_id"], row["team_token"], bool(row["banned"]), row["lifetime_cap_remaining"]

            # Create new team
            import secrets
            team_id = f"team_{secrets.token_hex(6)}"
            token = team_token or f"tok_{secrets.token_hex(12)}"
            conn.execute(
                "INSERT INTO teams (team_id, team_token, banned, lifetime_cap_remaining, created_at) VALUES (?, ?, 0, ?, ?)",
                (team_id, token, LIFETIME_CAP, now)
            )
            conn.execute(
                "INSERT INTO token_buckets (team_id, tokens, last_refill_at) VALUES (?, ?, ?)",
                (team_id, TOKEN_CAPACITY, now)
            )
            conn.commit()
            return team_id, token, False, LIFETIME_CAP

    @staticmethod
    def get_bucket_tokens(team_id: str, current_time: Optional[float] = None) -> float:
        now = current_time or time.time()
        with get_db_connection() as conn:
            row = conn.execute("SELECT tokens, last_refill_at FROM token_buckets WHERE team_id = ?", (team_id,)).fetchone()
            if not row:
                return TOKEN_CAPACITY
            tokens = row["tokens"]
            last_refill = row["last_refill_at"]
            elapsed = max(0.0, now - last_refill)
            new_tokens = min(TOKEN_CAPACITY, tokens + elapsed * REFILL_PER_SECOND)

            conn.execute(
                "UPDATE token_buckets SET tokens = ?, last_refill_at = ? WHERE team_id = ?",
                (new_tokens, now, team_id)
            )
            conn.commit()
            return new_tokens

    @staticmethod
    def deduct_tokens(team_id: str, amount: float, current_time: Optional[float] = None) -> Tuple[bool, float]:
        """Deducts tokens from team bucket. Returns (success, remaining_tokens)."""
        tokens = RulesEngine.get_bucket_tokens(team_id, current_time)
        now = current_time or time.time()
        if tokens < amount:
            return False, tokens
        new_tokens = tokens - amount
        with get_db_connection() as conn:
            conn.execute(
                "UPDATE token_buckets SET tokens = ?, last_refill_at = ? WHERE team_id = ?",
                (new_tokens, now, team_id)
            )
            conn.commit()
        return True, new_tokens

    @staticmethod
    def check_lockout(team_id: str, current_time: Optional[float] = None) -> Tuple[bool, int, Optional[str]]:
        """Returns (is_locked, remaining_seconds, reason)."""
        now = current_time or time.time()
        with get_db_connection() as conn:
            row = conn.execute("SELECT locked_until, reason FROM lockouts WHERE team_id = ?", (team_id,)).fetchone()
            if row and row["locked_until"] > now:
                remaining = int(row["locked_until"] - now)
                return True, remaining, row["reason"]
        return False, 0, None

    @staticmethod
    def apply_lockout(team_id: str, duration_seconds: float, reason: str, is_wrong_flag: bool = False, current_time: Optional[float] = None):
        now = current_time or time.time()
        capped_duration = min(float(duration_seconds), MAX_LOCKOUT_SEC)
        locked_until = now + capped_duration
        with get_db_connection() as conn:
            row = conn.execute("SELECT wrong_flag_count FROM lockouts WHERE team_id = ?", (team_id,)).fetchone()
            wrong_count = (row["wrong_flag_count"] if row else 0) + (1 if is_wrong_flag else 0)
            conn.execute(
                "INSERT INTO lockouts (team_id, locked_until, reason, wrong_flag_count) VALUES (?, ?, ?, ?) "
                "ON CONFLICT(team_id) DO UPDATE SET locked_until = max(locked_until, excluded.locked_until), reason = excluded.reason, wrong_flag_count = excluded.wrong_flag_count",
                (team_id, locked_until, reason, wrong_count)
            )
            conn.commit()
        log_audit(None, team_id, "LOCKOUT_APPLIED", {"duration": capped_duration, "reason": reason})

    @staticmethod
    def apply_hard_strike(team_id: str, detector: str, evidence: Any, ua_string: Optional[str] = None, current_time: Optional[float] = None) -> int:
        """Applies a hard strike and enforces the strike penalty ladder (capped at 5 min max lockout)."""
        now = current_time or time.time()
        ua_hash = hash_user_agent(ua_string)

        with get_db_connection() as conn:
            strike_row = conn.execute("SELECT COUNT(*) as count FROM strikes WHERE team_id = ?", (team_id,)).fetchone()
            strike_count = (strike_row["count"] if strike_row else 0) + 1

            conn.execute(
                "INSERT INTO strikes (team_id, strike_count, detector, evidence, ua_hash, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                (team_id, strike_count, detector, json.dumps(evidence), ua_hash, now)
            )

            # Penalty actions performed within same transaction
            if strike_count in (1, 2):
                # Wipe machine state
                conn.execute(
                    "UPDATE machine_state SET is_sealed = 0, current_positions = grundstellung WHERE team_id = ?",
                    (team_id,)
                )
            elif strike_count >= 3:
                conn.execute(
                    "UPDATE teams SET lifetime_cap_remaining = lifetime_cap_remaining / 2 WHERE team_id = ?",
                    (team_id,)
                )

            conn.commit()

        # Deduct tokens and apply lockout (capped at 5 mins / 300 seconds max)
        if strike_count == 1:
            RulesEngine.deduct_tokens(team_id, 100, now)
            RulesEngine.apply_lockout(team_id, 300, f"Hard strike 1: {detector} (5 min lockout, -100 arrows)", current_time=now)
        elif strike_count == 2:
            RulesEngine.deduct_tokens(team_id, 200, now)
            RulesEngine.apply_lockout(team_id, 300, f"Hard strike 2: {detector} (5 min lockout, -200 arrows)", current_time=now)
        elif strike_count == 3:
            RulesEngine.apply_lockout(team_id, 300, f"Hard strike 3: {detector} (5 min lockout, lifetime cap halved)", current_time=now)
        else:
            RulesEngine.apply_lockout(team_id, 300, f"Hard strike {strike_count}: {detector} (5 min lockout: Dharma violated repeatedly)", current_time=now)

        log_audit(None, team_id, "HARD_STRIKE", {"strike_count": strike_count, "detector": detector, "evidence": evidence})
        return strike_count

    @staticmethod
    def record_soft_violation(team_id: str, violation_type: str, evidence: Any = None, current_time: Optional[float] = None) -> bool:
        """Records a soft violation. If >= 5 in 10 minutes, triggers a hard strike."""
        now = current_time or time.time()
        window_start = now - SOFT_VIOLATION_WINDOW

        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO soft_violations (team_id, violation_type, timestamp) VALUES (?, ?, ?)",
                (team_id, violation_type, now)
            )
            count_row = conn.execute(
                "SELECT COUNT(*) as count FROM soft_violations WHERE team_id = ? AND timestamp >= ?",
                (team_id, window_start)
            )
            count = count_row.fetchone()["count"]
            conn.commit()

        log_audit(None, team_id, "SOFT_VIOLATION", {"violation_type": violation_type, "evidence": evidence, "recent_count": count})

        if count >= SOFT_VIOLATIONS_FOR_STRIKE:
            RulesEngine.apply_hard_strike(
                team_id,
                detector="soft_violations_accumulated",
                evidence={"soft_violation_count": count, "last_type": violation_type},
                current_time=now
            )
            return True
        return False

    @staticmethod
    def is_chain_mode_off(gates_cfg: Optional[Dict[str, Any]] = None) -> bool:
        if gates_cfg is None:
            gates_cfg = load_gates_config()
        mode = gates_cfg.get("chain_mode", "strict")
        return mode is False or str(mode).lower() in ("off", "false", "disabled", "none")

    @staticmethod
    def get_team_unlocked_gates(team_id: str) -> List[str]:
        """Returns list of unlocked gate IDs for a team."""
        gates_cfg = load_gates_config()
        if RulesEngine.is_chain_mode_off(gates_cfg):
            return [g["id"] for g in gates_cfg.get("gates", [])]

        with get_db_connection() as conn:
            rows = conn.execute(
                "SELECT gate_id FROM team_gates WHERE team_id = ? AND unlocked_at IS NOT NULL",
                (team_id,)
            ).fetchall()
            return [r["gate_id"] for r in rows]

    @staticmethod
    def is_gate_unlocked(team_id: str, gate_id: str) -> bool:
        gates_cfg = load_gates_config()
        if RulesEngine.is_chain_mode_off(gates_cfg):
            return True
        norm_id = normalize_gate_id(gate_id)
        unlocked = RulesEngine.get_team_unlocked_gates(team_id)
        return norm_id in unlocked

    @staticmethod
    def check_gate_lockout(team_id: str, gate_id: str, current_time: Optional[float] = None) -> Tuple[bool, int]:
        now = current_time or time.time()
        norm_gate_id = normalize_gate_id(gate_id)
        # Check team-wide lockout
        is_locked, rem_lock, _ = RulesEngine.check_lockout(team_id, now)
        # Check gate-specific lockout
        with get_db_connection() as conn:
            row = conn.execute(
                "SELECT locked_until FROM team_gates WHERE team_id = ? AND gate_id = ?",
                (team_id, norm_gate_id)
            ).fetchone()
            if row and row["locked_until"] and row["locked_until"] > now:
                gate_rem = int(row["locked_until"] - now)
                return True, max(rem_lock, gate_rem)
        return is_locked, rem_lock

    @staticmethod
    def unlock_gate(team_id: str, gate_id: str, seal_offered: str, current_time: Optional[float] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Attempts to unlock a gate.
        Validates seal against known canonical flags, salted SHA-256 hashes, and env overrides.
        Enforces a 3-minute penalty (180s) for Gate 1 and 5-minute penalty (300s) for Gate 2 wrong answers.
        During penalty lockout, no response flags or gate offerings are accepted.
        """
        now = current_time or time.time()
        gates_cfg = load_gates_config()
        gate_defs = {g["id"]: g for g in gates_cfg.get("gates", [])}
        norm_gate_id = normalize_gate_id(gate_id)

        if norm_gate_id not in gate_defs:
            return False, f"Unknown celestial gate '{gate_id}'.", {}

        gate_cfg = gate_defs[norm_gate_id]

        # Check if already locked out
        is_locked, rem_lock, lock_reason = RulesEngine.check_lockout(team_id, now)
        gate_locked, gate_rem = RulesEngine.check_gate_lockout(team_id, norm_gate_id, now)
        if is_locked or gate_locked:
            effective_rem = max(rem_lock, gate_rem)
            return False, f"Celestial penalty active. Offering seals forbidden for {effective_rem}s.", {
                "is_locked": True,
                "lock_remaining": effective_rem
            }

        # Check if already unlocked
        unlocked_gates = RulesEngine.get_team_unlocked_gates(team_id)
        if norm_gate_id in unlocked_gates:
            return True, f"Gate {norm_gate_id} is already unlocked.", {"reveals": gate_cfg.get("reveals", []), "unlocks": gate_cfg.get("unlocks")}

        seal_raw = seal_offered.strip()
        seal_upper = seal_raw.upper()

        # 1. Check direct match against known canonical seals
        known_seals = KNOWN_GATE_SEALS.get(norm_gate_id, set())
        is_valid = (seal_upper in known_seals) or (seal_raw in known_seals)

        # 2. Check salted hash if not matched yet
        if not is_valid:
            seal_sha256 = (
                os.environ.get(f"GATE{norm_gate_id}_SEAL_SHA256") or
                os.environ.get(f"GATE{1 if norm_gate_id == 'I' else 2}_SEAL_SHA256") or
                gate_cfg.get("seal_sha256", "")
            )
            candidates = [
                seal_raw,
                seal_upper,
                f"KCTF{{{seal_upper}}}",
                f"KCTF{{{seal_raw}}}"
            ]
            if seal_upper.startswith("KCTF{") and seal_upper.endswith("}"):
                candidates.append(seal_upper[5:-1])
                candidates.append(seal_raw[5:-1])

            for cand in candidates:
                if verify_flag(cand, seal_sha256):
                    is_valid = True
                    break

        if not is_valid:
            # Penalty duration: Gate 1 (I) = 3 minutes (180s), Gate 2 (II) = 5 minutes (300s)
            if norm_gate_id in ("I", "1"):
                penalty_sec = float(gate_cfg.get("wrong_penalty_seconds", 180))  # 3 minutes
                penalty_reason = "Gate I seal rejected (Penalty: 3 minutes)"
            elif norm_gate_id in ("II", "2"):
                penalty_sec = float(gate_cfg.get("wrong_penalty_seconds", 300))  # 5 minutes
                penalty_reason = "Gate II seal rejected (Penalty: 5 minutes)"
            else:
                penalty_sec = float(gate_cfg.get("wrong_penalty_seconds", 180))
                penalty_reason = f"Gate {norm_gate_id} seal rejected"

            # Apply team-wide lockout so flags & actions are denied
            RulesEngine.apply_lockout(team_id, penalty_sec, penalty_reason, current_time=now)

            # Record in team_gates table
            with get_db_connection() as conn:
                conn.execute(
                    "INSERT INTO team_gates (team_id, gate_id, wrong_attempts, locked_until) "
                    "VALUES (?, ?, 1, ?) "
                    "ON CONFLICT(team_id, gate_id) DO UPDATE SET wrong_attempts = wrong_attempts + 1, locked_until = max(locked_until, excluded.locked_until)",
                    (team_id, norm_gate_id, now + penalty_sec)
                )
                conn.commit()

            minutes_label = int(penalty_sec // 60)
            return False, f"The offered seal is rejected by Gate {norm_gate_id}. Celestial penalty of {minutes_label} minutes engaged.", {
                "is_locked": True,
                "lock_remaining": int(penalty_sec)
            }

        # Correct seal -> Unlock gate
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO team_gates (team_id, gate_id, unlocked_at, wrong_attempts, locked_until) "
                "VALUES (?, ?, ?, 0, 0.0) "
                "ON CONFLICT(team_id, gate_id) DO UPDATE SET unlocked_at = excluded.unlocked_at, locked_until = 0.0",
                (team_id, norm_gate_id, now)
            )
            conn.commit()

        log_audit(None, team_id, "GATE_UNLOCKED", {"gate": norm_gate_id, "reveals": gate_cfg.get("reveals", [])})
        return True, f"Gate {norm_gate_id} ('{gate_cfg.get('name')}') UNLOCKED! Sacred intelligence revealed.", {
            "reveals": gate_cfg.get("reveals", []),
            "unlocks": gate_cfg.get("unlocks")
        }


