"""
Admin API for Kurukshetra CTF Challenge 3
Bound to administrative port/routes, secured via X-Admin-Token with constant-time comparison.
"""

import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel

from app.db import get_db_connection, log_audit
from app.rules import RulesEngine, TOKEN_CAPACITY, LIFETIME_CAP
from app.security import constant_time_compare

ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "KURUKSHETRA_SACRED_ADMIN_TOKEN_2026")

admin_router = APIRouter(prefix="/admin", tags=["Admin"])


def verify_admin_auth(x_admin_token: Optional[str] = Header(None)):
    if not x_admin_token or not constant_time_compare(x_admin_token, ADMIN_TOKEN):
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid Admin Token")
    return True


class TeamActionRequest(BaseModel):
    team_id: str


@admin_router.get("/health")
def admin_health(x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token")):
    verify_admin_auth(x_admin_token)
    return {"status": "ok", "service": "chakravyuha_admin", "timestamp": time.time()}


@admin_router.get("/teams")
def list_teams(x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token")):
    verify_admin_auth(x_admin_token)
    with get_db_connection() as conn:
        teams_rows = conn.execute("SELECT * FROM teams").fetchall()
        teams = []
        now = time.time()
        for t in teams_rows:
            team_id = t["team_id"]
            tokens = RulesEngine.get_bucket_tokens(team_id, now)
            is_locked, lock_rem, reason = RulesEngine.check_lockout(team_id, now)
            strikes = conn.execute("SELECT COUNT(*) as count FROM strikes WHERE team_id = ?", (team_id,)).fetchone()["count"]
            teams.append({
                "team_id": team_id,
                "team_token": t["team_token"],
                "banned": bool(t["banned"]),
                "lifetime_cap_remaining": t["lifetime_cap_remaining"],
                "tokens": tokens,
                "is_locked": is_locked,
                "lock_remaining_seconds": lock_rem,
                "lock_reason": reason,
                "strikes_count": strikes
            })
    return {"teams": teams}


@admin_router.post("/pardon")
def pardon_team(req: TeamActionRequest, x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token")):
    verify_admin_auth(x_admin_token)
    with get_db_connection() as conn:
        conn.execute("DELETE FROM strikes WHERE team_id = ?", (req.team_id,))
        conn.execute("DELETE FROM soft_violations WHERE team_id = ?", (req.team_id,))
        conn.execute("DELETE FROM lockouts WHERE team_id = ?", (req.team_id,))
        conn.execute("UPDATE teams SET banned = 0 WHERE team_id = ?", (req.team_id,))
        conn.commit()
    log_audit(None, req.team_id, "ADMIN_PARDON", {"action": "pardon"})
    return {"success": True, "message": f"Team {req.team_id} pardoned."}


@admin_router.post("/reset-budget")
def reset_team_budget(req: TeamActionRequest, x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token")):
    verify_admin_auth(x_admin_token)
    now = time.time()
    with get_db_connection() as conn:
        conn.execute(
            "UPDATE token_buckets SET tokens = ?, last_refill_at = ? WHERE team_id = ?",
            (TOKEN_CAPACITY, now, req.team_id)
        )
        conn.execute(
            "UPDATE teams SET lifetime_cap_remaining = ? WHERE team_id = ?",
            (LIFETIME_CAP, req.team_id)
        )
        conn.commit()
    log_audit(None, req.team_id, "ADMIN_RESET_BUDGET", {"action": "reset_budget"})
    return {"success": True, "message": f"Budget reset for team {req.team_id}."}


@admin_router.post("/kill-session")
def kill_team_session(req: TeamActionRequest, x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token")):
    verify_admin_auth(x_admin_token)
    with get_db_connection() as conn:
        conn.execute("UPDATE sessions SET is_active = 0 WHERE team_id = ?", (req.team_id,))
        conn.commit()
    log_audit(None, req.team_id, "ADMIN_KILL_SESSION", {"action": "kill_session"})
    return {"success": True, "message": f"Sessions killed for team {req.team_id}."}


@admin_router.post("/ban")
def ban_team(req: TeamActionRequest, x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token")):
    verify_admin_auth(x_admin_token)
    with get_db_connection() as conn:
        conn.execute("UPDATE teams SET banned = 1 WHERE team_id = ?", (req.team_id,))
        conn.commit()
    RulesEngine.apply_lockout(req.team_id, 86400 * 365, "Banned by administrator")
    log_audit(None, req.team_id, "ADMIN_BAN", {"action": "ban"})
    return {"success": True, "message": f"Team {req.team_id} banned."}


@admin_router.post("/unban")
def unban_team(req: TeamActionRequest, x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token")):
    verify_admin_auth(x_admin_token)
    with get_db_connection() as conn:
        conn.execute("UPDATE teams SET banned = 0 WHERE team_id = ?", (req.team_id,))
        conn.execute("DELETE FROM lockouts WHERE team_id = ?", (req.team_id,))
        conn.commit()
    log_audit(None, req.team_id, "ADMIN_UNBAN", {"action": "unban"})
    return {"success": True, "message": f"Team {req.team_id} unbanned."}


@admin_router.get("/audit")
def tail_audit(limit: int = Query(50, ge=1, le=500), x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token")):
    verify_admin_auth(x_admin_token)
    with get_db_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?",
            (limit,)
        ).fetchall()
        logs = [dict(r) for r in rows]
    return {"audit_logs": logs}


HINTS_FILE = Path(os.environ.get("HINTS_CONFIG_PATH", Path(__file__).resolve().parent.parent.parent / "config" / "hints.yaml"))


def _load_hints_data() -> List[Dict[str, Any]]:
    import yaml
    if HINTS_FILE.exists():
        with open(HINTS_FILE, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            return data.get("hints", [])
    return []


def _save_hints_data(hints: List[Dict[str, Any]]):
    import yaml
    with open(HINTS_FILE, "w", encoding="utf-8") as f:
        yaml.safe_dump({"hints": hints}, f, sort_keys=False)


@admin_router.get("/hints")
def admin_list_hints(x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token")):
    verify_admin_auth(x_admin_token)
    return {"hints": _load_hints_data()}


@admin_router.post("/hints/{hint_id}/release")
def admin_release_hint(hint_id: int, x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token")):
    verify_admin_auth(x_admin_token)
    hints = _load_hints_data()
    found = False
    for h in hints:
        if h["id"] == hint_id:
            h["released"] = True
            h["released_at"] = time.time()
            found = True
            break
    if not found:
        raise HTTPException(status_code=404, detail=f"Hint #{hint_id} not found")
    _save_hints_data(hints)
    log_audit(None, None, "ADMIN_HINT_RELEASED", {"hint_id": hint_id})
    return {"success": True, "message": f"Hint #{hint_id} released to all warriors.", "hint_id": hint_id}


@admin_router.post("/hints/{hint_id}/withdraw")
def admin_withdraw_hint(hint_id: int, x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token")):
    verify_admin_auth(x_admin_token)
    hints = _load_hints_data()
    found = False
    for h in hints:
        if h["id"] == hint_id:
            h["released"] = False
            found = True
            break
    if not found:
        raise HTTPException(status_code=404, detail=f"Hint #{hint_id} not found")
    _save_hints_data(hints)
    log_audit(None, None, "ADMIN_HINT_WITHDRAWN", {"hint_id": hint_id})
    return {"success": True, "message": f"Hint #{hint_id} withdrawn.", "hint_id": hint_id}

