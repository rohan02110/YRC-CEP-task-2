import json
import os
import sqlite3
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

# Ensure backend and root directory are in sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BACKEND_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI, Request, Response, HTTPException, Header, Query
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from app.db import init_db, get_db_connection, log_audit
from app.engine import (
    ALPHABET, N, char_to_idx, idx_to_char,
    Rotor, Reflector, Plugboard, EnigmaMachine
)
from app.models import (
    SessionInitRequest, SessionInitResponse,
    HeartbeatRequest, HeartbeatResponse,
    ConfigureRequest, ConfigureResponse,
    PressRequest, PressResponse,
    ResetRequest, ResetResponse,
    SubmitFlagRequest, SubmitFlagResponse,
    TamperBeaconRequest, SoftViolationRequest,
    UnlockGateRequest, UnlockGateResponse,
    ModeSwitchRequest, ModeSwitchResponse,
    GateInfo, GatesStatusResponse, HintModel
)
from app.rules import (
    RulesEngine, TOKEN_CAPACITY, LIFETIME_CAP, RESET_CHAKRA_COST,
    MIN_INTERVAL_SEC, MAX_SUSTAINED_RATE, IDLE_TIMEOUT_SEC, WATCHDOG_TIMEOUT_SEC,
    WRONG_FLAG_LOCKOUTS, WRONG_FLAG_COST, DECOY_LOCKOUT_SEC, DECOY_TOKEN_COST,
    load_gates_config
)
from app.security import (
    generate_secure_token, generate_nonce, compute_hmac, verify_hmac,
    verify_flag, hash_user_agent
)
from app.honeypots import router as honeypots_router
from app.admin import admin_router

from tools.generate_instance import (
    derive_team_instance, generate_replica_config,
    DEFAULT_MASTER_SEED, DEFAULT_DECOYS, FLAG_PHRASE_LIST, generate_flag_tag,
    UNIVERSAL_FLAG
)

app = FastAPI(title="Chakravyuha Cipher", docs_url=None, redoc_url=None, openapi_url=None)

# Initialize database
init_db()

# Configuration Paths
MASTER_SEED = os.environ.get("MASTER_SEED", DEFAULT_MASTER_SEED)
PUBLIC_ARTIFACTS_PATH = Path(os.environ.get("PUBLIC_ARTIFACTS_PATH", ROOT_DIR / "public_artifacts"))
FRONTEND_DIST_PATH = Path(os.environ.get("FRONTEND_DIST_PATH", ROOT_DIR / "frontend" / "dist"))
PHRASES_FILE = Path(os.environ.get("PHRASES_FILE", ROOT_DIR / "tools" / "phrases_sanskrit.txt"))
HINTS_FILE = Path(os.environ.get("HINTS_CONFIG_PATH", ROOT_DIR / "config" / "hints.yaml"))

# Training Replica static configuration (public)
REPLICA_CONFIG = generate_replica_config()

# In-memory cache for derived team instances
TEAM_INSTANCES_CACHE: Dict[str, Dict[str, Any]] = {}


def get_team_instance(team_id: str) -> Dict[str, Any]:
    if team_id not in TEAM_INSTANCES_CACHE:
        TEAM_INSTANCES_CACHE[team_id] = derive_team_instance(MASTER_SEED, team_id, PHRASES_FILE)
    return TEAM_INSTANCES_CACHE[team_id]


# Include Honeypots and Admin routers
app.include_router(honeypots_router)
app.include_router(admin_router)


# ==============================================================================
# Security Headers Middleware
# ==============================================================================

@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    if request.headers.get("content-length"):
        length = int(request.headers.get("content-length", "0"))
        if length > 65536:
            return PlainTextResponse("Payload Too Large", status_code=413)

    response: Response = await call_next(request)

    response.headers["Content-Security-Policy"] = (
        "default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; font-src 'self'; connect-src 'self'; "
        "worker-src 'self' blob:; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
    )
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()"
    if "server" in response.headers:
        del response.headers["server"]

    return response


# ==============================================================================
# Session & Verification Helpers
# ==============================================================================

def verify_session_and_request(
    session_id: str,
    req_seq: int,
    req_nonce: str,
    request: Request,
    body_data: Dict,
    sig_header: Optional[str] = None
) -> Tuple[sqlite3.Row, sqlite3.Row]:
    now = time.time()
    with get_db_connection() as conn:
        session = conn.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,)).fetchone()
        if not session or not session["is_active"]:
            raise HTTPException(status_code=401, detail="Session invalid or terminated.")

        team_id = session["team_id"]
        team = conn.execute("SELECT * FROM teams WHERE team_id = ?", (team_id,)).fetchone()
        if not team or team["banned"]:
            raise HTTPException(status_code=403, detail="Dharma violated: Access forbidden.")

        # Check Lockout
        is_locked, rem_lock, reason = RulesEngine.check_lockout(team_id, now)
        if is_locked:
            raise HTTPException(status_code=423, detail=f"Locked: {reason} ({rem_lock}s remaining)")

        # Check Lifetime Cap
        if team["lifetime_cap_remaining"] <= 0:
            raise HTTPException(status_code=429, detail="Your arrows are spent. Formation sealed.")

        # Check Idle Timeout (8 min)
        if now - session["last_active_at"] > IDLE_TIMEOUT_SEC:
            conn.execute("UPDATE sessions SET is_active = 0 WHERE session_id = ?", (session_id,))
            conn.execute("UPDATE machine_state SET is_sealed = 0 WHERE session_id = ?", (session_id,))
            conn.commit()
            raise HTTPException(status_code=408, detail="Session timed out due to inactivity.")

        # Monotonic sequence check
        if req_seq != session["seq"] + 1:
            RulesEngine.apply_hard_strike(team_id, "out_of_order_seq", {"expected": session["seq"] + 1, "received": req_seq})
            raise HTTPException(status_code=400, detail="Invalid sequence order.")

        # Nonce check
        if req_nonce != session["next_nonce"]:
            RulesEngine.apply_hard_strike(team_id, "invalid_nonce", {"expected": session["next_nonce"], "received": req_nonce})
            raise HTTPException(status_code=400, detail="Invalid request nonce.")

        # Optional signature verification
        if sig_header:
            sig_msg = f"{req_seq}|{req_nonce}|{json.dumps(body_data, sort_keys=True, separators=(',', ':'))}"
            if not verify_hmac(session["session_key"], sig_msg, sig_header):
                RulesEngine.apply_hard_strike(team_id, "signature_mismatch", {})
                raise HTTPException(status_code=403, detail="Integrity check failed.")

        return session, team


# ==============================================================================
# Public API Endpoints
# ==============================================================================

@app.post("/api/v1/session", response_model=SessionInitResponse)
def init_session(req: SessionInitRequest, request: Request):
    now = time.time()
    team_id, team_token, banned, lifetime_cap = RulesEngine.get_or_create_team(req.team_token)
    if banned:
        raise HTTPException(status_code=403, detail="Team is banned.")

    # Deactivate existing sessions for single-session lock
    with get_db_connection() as conn:
        conn.execute("UPDATE sessions SET is_active = 0 WHERE team_id = ?", (team_id,))

        session_id = f"sess_{generate_secure_token(16)}"
        session_key = generate_secure_token(32)
        initial_nonce = generate_nonce()
        next_nonce = generate_nonce()

        conn.execute(
            "INSERT INTO sessions (session_id, team_id, session_key, seq, current_nonce, next_nonce, created_at, last_active_at, last_heartbeat_at, is_active) VALUES (?, ?, ?, 0, ?, ?, ?, ?, ?, 1)",
            (session_id, team_id, session_key, initial_nonce, next_nonce, now, now, now)
        )

        # Default Replica Settings
        default_rotors = REPLICA_CONFIG["seated_rotors"]
        default_rings = REPLICA_CONFIG["default_ringstellung"]
        default_grund = REPLICA_CONFIG["default_grundstellung"]
        default_pb = REPLICA_CONFIG["default_plugboard"]

        conn.execute(
            "INSERT INTO machine_state (session_id, team_id, mode, is_sealed, walzenlage, ringstellung, grundstellung, plugboard, current_positions, updated_at) VALUES (?, ?, 'replica', 0, ?, ?, ?, ?, ?, ?)",
            (session_id, team_id, json.dumps(default_rotors), json.dumps(default_rings), json.dumps(default_grund), json.dumps(default_pb), json.dumps(default_grund), now)
        )
        conn.commit()

    tokens = RulesEngine.get_bucket_tokens(team_id, now)
    is_locked, lock_rem, reason = RulesEngine.check_lockout(team_id, now)

    log_audit(session_id, team_id, "SESSION_INIT", {"ip": request.client.host if request.client else "unknown"})

    return SessionInitResponse(
        session_id=session_id,
        session_key=session_key,
        team_id=team_id,
        next_nonce=next_nonce,
        seq=0,
        is_sealed=False,
        walzenlage=default_rotors,
        ringstellung=default_rings,
        grundstellung=default_grund,
        plugboard=default_pb,
        current_positions=default_grund,
        window_symbols=[idx_to_char(p) for p in default_grund],
        baan_remaining=int(tokens),
        lifetime_cap_remaining=lifetime_cap,
        is_locked=is_locked,
        lock_remaining_seconds=lock_rem,
        lock_reason=reason
    )


@app.post("/api/v1/heartbeat", response_model=HeartbeatResponse)
def heartbeat(req: HeartbeatRequest, request: Request):
    now = time.time()
    with get_db_connection() as conn:
        session = conn.execute("SELECT * FROM sessions WHERE session_id = ?", (req.session_id,)).fetchone()
        if not session or not session["is_active"]:
            raise HTTPException(status_code=401, detail="Session expired.")

        team_id = session["team_id"]
        team = conn.execute("SELECT * FROM teams WHERE team_id = ?", (team_id,)).fetchone()
        is_banned = bool(team["banned"]) if team else True

        # Update last_heartbeat_at
        conn.execute("UPDATE sessions SET last_heartbeat_at = ? WHERE session_id = ?", (now, req.session_id))
        conn.commit()

        # Check machine state
        m_state = conn.execute("SELECT is_sealed FROM machine_state WHERE session_id = ?", (req.session_id,)).fetchone()
        is_sealed = bool(m_state["is_sealed"]) if m_state else False

    tokens = RulesEngine.get_bucket_tokens(team_id, now)
    is_locked, lock_rem, reason = RulesEngine.check_lockout(team_id, now)

    return HeartbeatResponse(
        next_nonce=session["next_nonce"],
        seq=session["seq"],
        is_locked=is_locked,
        lock_remaining_seconds=lock_rem,
        lock_reason=reason,
        baan_remaining=int(tokens),
        lifetime_cap_remaining=team["lifetime_cap_remaining"] if team else 0,
        is_sealed=is_sealed,
        is_banned=is_banned
    )


@app.post("/api/v1/configure", response_model=ConfigureResponse)
def configure_machine(req: ConfigureRequest, request: Request, x_sig: Optional[str] = Header(None, alias="X-Sig")):
    now = time.time()
    session, team = verify_session_and_request(
        req.session_id, req.seq, req.nonce, request, req.model_dump(), x_sig
    )
    team_id = session["team_id"]

    # Validate configuration parameters
    valid_rotors = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"]
    if len(req.walzenlage) != 4 or len(set(req.walzenlage)) != 4:
        raise HTTPException(status_code=400, detail="Walzenlage must contain exactly 4 distinct rotors")
    for r in req.walzenlage:
        if r not in valid_rotors:
            raise HTTPException(status_code=400, detail=f"Unknown rotor: {r}")

    if len(req.ringstellung) != 4 or not all(0 <= val < N for val in req.ringstellung):
        raise HTTPException(status_code=400, detail="Ringstellung values must be between 0 and 29")

    if len(req.grundstellung) != 4 or not all(0 <= val < N for val in req.grundstellung):
        raise HTTPException(status_code=400, detail="Grundstellung values must be between 0 and 29")

    if len(req.plugboard) > 13:
        raise HTTPException(status_code=400, detail="Plugboard cannot exceed 13 pairs")

    # Check if reconfiguring an already-sealed machine (costs RESET_CHAKRA_COST)
    with get_db_connection() as conn:
        state = conn.execute("SELECT is_sealed FROM machine_state WHERE session_id = ?", (req.session_id,)).fetchone()
        if state and state["is_sealed"]:
            ok, rem_tokens = RulesEngine.deduct_tokens(team_id, RESET_CHAKRA_COST, now)
            if not ok:
                raise HTTPException(status_code=429, detail="Insufficient arrows to reconfigure the formation.")

        new_nonce = generate_nonce()
        conn.execute(
            "UPDATE sessions SET seq = ?, current_nonce = ?, next_nonce = ?, last_active_at = ? WHERE session_id = ?",
            (req.seq, req.nonce, new_nonce, now, req.session_id)
        )
        conn.execute(
            "UPDATE machine_state SET is_sealed = 0, walzenlage = ?, ringstellung = ?, grundstellung = ?, plugboard = ?, current_positions = ?, updated_at = ? WHERE session_id = ?",
            (
                json.dumps(req.walzenlage),
                json.dumps(req.ringstellung),
                json.dumps(req.grundstellung),
                json.dumps(req.plugboard),
                json.dumps(req.grundstellung),
                now,
                req.session_id
            )
        )
        conn.commit()

    tokens = RulesEngine.get_bucket_tokens(team_id, now)

    return ConfigureResponse(
        success=True,
        next_nonce=new_nonce,
        seq=req.seq,
        is_sealed=False,
        walzenlage=req.walzenlage,
        ringstellung=req.ringstellung,
        grundstellung=req.grundstellung,
        plugboard=req.plugboard,
        current_positions=req.grundstellung,
        window_symbols=[idx_to_char(p) for p in req.grundstellung],
        baan_remaining=int(tokens)
    )


@app.post("/api/v1/press", response_model=PressResponse)
def press_key(req: PressRequest, request: Request, x_sig: Optional[str] = Header(None, alias="X-Sig")):
    now = time.time()
    session, team = verify_session_and_request(
        req.session_id, req.seq, req.nonce, request, req.model_dump(), x_sig
    )
    team_id = session["team_id"]

    if req.char not in ALPHABET:
        raise HTTPException(status_code=400, detail=f"Invalid character '{req.char}'")

    # Enforce min keypress interval (70ms)
    elapsed_since_active = now - session["last_active_at"]
    if elapsed_since_active < MIN_INTERVAL_SEC:
        RulesEngine.record_soft_violation(team_id, "key_interval_too_fast", {"elapsed": elapsed_since_active})
        raise HTTPException(status_code=429, detail="The formation does not yield to the impatient.")

    # Deduct 1 token for keypress
    ok, rem_tokens = RulesEngine.deduct_tokens(team_id, 1.0, now)
    if not ok:
        raise HTTPException(status_code=429, detail="Your arrows are spent.")

    # Decrement lifetime cap
    with get_db_connection() as conn:
        conn.execute("UPDATE teams SET lifetime_cap_remaining = lifetime_cap_remaining - 1 WHERE team_id = ?", (team_id,))

        m_state = conn.execute("SELECT * FROM machine_state WHERE session_id = ?", (req.session_id,)).fetchone()
        if not m_state:
            raise HTTPException(status_code=500, detail="Machine state uninitialized")

        mode = m_state["mode"] if "mode" in m_state.keys() else "replica"
        walzenlage = json.loads(m_state["walzenlage"])
        ringstellung = json.loads(m_state["ringstellung"])
        current_positions = json.loads(m_state["current_positions"])
        plugboard_pairs = json.loads(m_state["plugboard"])

        if mode == "original":
            if not RulesEngine.is_gate_unlocked(team_id, "II"):
                raise HTTPException(status_code=403, detail="Original celestial machine locked until Gate II seal is offered.")
            team_inst = get_team_instance(team_id)
            rotors_pool = team_inst["all_rotors"]
            reflector_pairs = team_inst["reflector_pairs"]
        else:
            rotors_pool = REPLICA_CONFIG["rotors"]
            reflector_pairs = REPLICA_CONFIG["reflector_pairs"]

        rotors = [
            Rotor(
                wiring=rotors_pool[walzenlage[i]]["wiring"],
                notches=rotors_pool[walzenlage[i]]["notches"],
                ring_setting=ringstellung[i],
                position=current_positions[i]
            )
            for i in range(4)
        ]
        reflector = Reflector(reflector_pairs)
        plugboard = Plugboard(plugboard_pairs)

        machine = EnigmaMachine(rotors, reflector, plugboard)
        press_result = machine.press(req.char)

        # Update machine state and seal it
        new_nonce = generate_nonce()
        conn.execute(
            "UPDATE machine_state SET is_sealed = 1, current_positions = ?, updated_at = ? WHERE session_id = ?",
            (json.dumps(press_result.positions), now, req.session_id)
        )
        conn.execute(
            "UPDATE sessions SET seq = ?, current_nonce = ?, next_nonce = ?, last_active_at = ? WHERE session_id = ?",
            (req.seq, req.nonce, new_nonce, now, req.session_id)
        )
        conn.commit()

    return PressResponse(
        out_symbol=press_result.out_symbol,
        positions=press_result.positions,
        window_symbols=press_result.window_symbols,
        stepped_flags=press_result.stepped_flags,
        next_nonce=new_nonce,
        seq=req.seq,
        baan_remaining=int(rem_tokens),
        is_sealed=True
    )


@app.post("/api/v1/reset", response_model=ResetResponse)
def reset_chakra(req: ResetRequest, request: Request, x_sig: Optional[str] = Header(None, alias="X-Sig")):
    now = time.time()
    session, team = verify_session_and_request(
        req.session_id, req.seq, req.nonce, request, req.model_dump(), x_sig
    )
    team_id = session["team_id"]

    # Resetting the chakra costs 30 tokens
    ok, rem_tokens = RulesEngine.deduct_tokens(team_id, RESET_CHAKRA_COST, now)
    if not ok:
        raise HTTPException(status_code=429, detail="Insufficient arrows to reset the Chakra.")

    with get_db_connection() as conn:
        m_state = conn.execute("SELECT grundstellung FROM machine_state WHERE session_id = ?", (req.session_id,)).fetchone()
        grundstellung = json.loads(m_state["grundstellung"]) if m_state else [0, 0, 0, 0]

        new_nonce = generate_nonce()
        conn.execute(
            "UPDATE machine_state SET is_sealed = 0, current_positions = grundstellung, updated_at = ? WHERE session_id = ?",
            (now, req.session_id)
        )
        conn.execute(
            "UPDATE sessions SET seq = ?, current_nonce = ?, next_nonce = ?, last_active_at = ? WHERE session_id = ?",
            (req.seq, req.nonce, new_nonce, now, req.session_id)
        )
        conn.commit()

    log_audit(req.session_id, team_id, "RESET_CHAKRA", {"cost": RESET_CHAKRA_COST})

    return ResetResponse(
        success=True,
        next_nonce=new_nonce,
        seq=req.seq,
        is_sealed=False,
        current_positions=grundstellung,
        window_symbols=[idx_to_char(p) for p in grundstellung],
        baan_remaining=int(rem_tokens)
    )


@app.post("/api/v1/submit", response_model=SubmitFlagResponse)
def submit_flag(req: SubmitFlagRequest, request: Request, x_sig: Optional[str] = Header(None, alias="X-Sig")):
    now = time.time()
    session, team = verify_session_and_request(
        req.session_id, req.seq, req.nonce, request, req.model_dump(), x_sig
    )
    team_id = session["team_id"]
    submitted = req.flag.strip()

    team_inst = get_team_instance(team_id)
    decoy_flags = team_inst.get("decoy_flags", DEFAULT_DECOYS)
    stored_salted_hash = team_inst["flag_sha256"]

    new_nonce = generate_nonce()
    with get_db_connection() as conn:
        conn.execute(
            "UPDATE sessions SET seq = ?, current_nonce = ?, next_nonce = ?, last_active_at = ? WHERE session_id = ?",
            (req.seq, req.nonce, new_nonce, now, req.session_id)
        )
        conn.commit()

    # 1. Check Decoy Flag
    if submitted in decoy_flags:
        RulesEngine.deduct_tokens(team_id, DECOY_TOKEN_COST, now)
        RulesEngine.apply_hard_strike(
            team_id,
            detector="decoy_flag_submitted",
            evidence={"submitted": submitted},
            current_time=now
        )
        RulesEngine.apply_lockout(team_id, DECOY_LOCKOUT_SEC, "Deceit detected: Decoy flag offered to Dharma.", current_time=now)
        tokens = RulesEngine.get_bucket_tokens(team_id, now)
        return SubmitFlagResponse(
            correct=False,
            message="Dharma rejects illusions. Decoy banner burned.",
            next_nonce=new_nonce,
            seq=req.seq,
            is_locked=True,
            lock_remaining_seconds=int(DECOY_LOCKOUT_SEC),
            baan_remaining=int(tokens)
        )

    # 2. Verify True Flag (Universal for all teams)
    if submitted == team_inst["flag"] or submitted == UNIVERSAL_FLAG or verify_flag(submitted, stored_salted_hash):
        tokens = RulesEngine.get_bucket_tokens(team_id, now)
        log_audit(req.session_id, team_id, "FLAG_SOLVED", {"flag": submitted})
        return SubmitFlagResponse(
            correct=True,
            message="Abhimanyu has broken through the 7th circle! Victory is yours.",
            next_nonce=new_nonce,
            seq=req.seq,
            is_locked=False,
            lock_remaining_seconds=0,
            baan_remaining=int(tokens)
        )

    # 4. Wrong Flag
    RulesEngine.deduct_tokens(team_id, WRONG_FLAG_COST, now)
    with get_db_connection() as conn:
        row = conn.execute("SELECT wrong_flag_count FROM lockouts WHERE team_id = ?", (team_id,)).fetchone()
        wrong_count = row["wrong_flag_count"] if row else 0

    ladder_idx = min(wrong_count, len(WRONG_FLAG_LOCKOUTS) - 1)
    lock_duration = WRONG_FLAG_LOCKOUTS[ladder_idx]
    RulesEngine.apply_lockout(team_id, lock_duration, f"Wrong flag submission #{wrong_count + 1}", is_wrong_flag=True, current_time=now)

    tokens = RulesEngine.get_bucket_tokens(team_id, now)
    return SubmitFlagResponse(
        correct=False,
        message="The sacred seal remains unyielding. Offer the true word of Dharma.",
        next_nonce=new_nonce,
        seq=req.seq,
        is_locked=True,
        lock_remaining_seconds=int(lock_duration),
        baan_remaining=int(tokens)
    )


@app.get("/api/v1/gates", response_model=GatesStatusResponse)
def get_gates_status(session_id: str):
    now = time.time()
    with get_db_connection() as conn:
        session = conn.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,)).fetchone()
        if not session or not session["is_active"]:
            raise HTTPException(status_code=401, detail="Invalid session")
        team_id = session["team_id"]
        m_state = conn.execute("SELECT mode FROM machine_state WHERE session_id = ?", (session_id,)).fetchone()
        current_mode = m_state["mode"] if (m_state and "mode" in m_state.keys()) else "replica"

    gates_cfg = load_gates_config()
    unlocked_gates = RulesEngine.get_team_unlocked_gates(team_id)

    gate_infos: List[GateInfo] = []
    for g in gates_cfg.get("gates", []):
        gid = g["id"]
        is_unlocked = gid in unlocked_gates
        is_locked, rem_lock = RulesEngine.check_gate_lockout(team_id, gid, now)
        if is_unlocked:
            is_locked = False
            rem_lock = 0
        gate_infos.append(GateInfo(
            id=gid,
            name=g.get("name", f"Gate {gid}"),
            description=f"Reward for the trial of Gate {gid}.",
            is_unlocked=is_unlocked,
            is_locked=is_locked,
            lock_remaining_seconds=rem_lock,
            reveals=g.get("reveals", [])
        ))

    return GatesStatusResponse(
        chain_mode=gates_cfg.get("chain_mode", "off"),
        current_mode=current_mode,
        gates=gate_infos
    )


@app.post("/api/v1/gates/unlock", response_model=UnlockGateResponse)
def unlock_gate_endpoint(req: UnlockGateRequest, request: Request, x_sig: Optional[str] = Header(None, alias="X-Sig")):
    now = time.time()
    session, team = verify_session_and_request(
        req.session_id, req.seq, req.nonce, request, req.model_dump(), x_sig
    )
    team_id = session["team_id"]

    new_nonce = generate_nonce()
    with get_db_connection() as conn:
        conn.execute(
            "UPDATE sessions SET seq = ?, current_nonce = ?, next_nonce = ?, last_active_at = ? WHERE session_id = ?",
            (req.seq, req.nonce, new_nonce, now, req.session_id)
        )
        conn.commit()

    success, msg, details = RulesEngine.unlock_gate(team_id, req.gate_id, req.seal, now)
    is_locked, rem_lock = RulesEngine.check_gate_lockout(team_id, req.gate_id, now)

    return UnlockGateResponse(
        success=success,
        message=msg,
        next_nonce=new_nonce,
        seq=req.seq,
        gate_id=req.gate_id,
        is_unlocked=RulesEngine.is_gate_unlocked(team_id, req.gate_id),
        is_locked=is_locked,
        lock_remaining_seconds=rem_lock,
        reveals=details.get("reveals", []),
        unlocks=details.get("unlocks")
    )


@app.post("/api/v1/mode/switch", response_model=ModeSwitchResponse)
def switch_machine_mode(req: ModeSwitchRequest, request: Request, x_sig: Optional[str] = Header(None, alias="X-Sig")):
    now = time.time()
    session, team = verify_session_and_request(
        req.session_id, req.seq, req.nonce, request, req.model_dump(), x_sig
    )
    team_id = session["team_id"]

    if req.target_mode != "original":
        raise HTTPException(status_code=400, detail="Only switching to 'original' is permitted.")

    if not RulesEngine.is_gate_unlocked(team_id, "II"):
        raise HTTPException(status_code=403, detail="Seal of Sanjaya (Gate II) required to unlock original machine.")

    new_nonce = generate_nonce()
    with get_db_connection() as conn:
        conn.execute(
            "UPDATE machine_state SET mode = 'original', is_sealed = 0, updated_at = ? WHERE session_id = ?",
            (now, req.session_id)
        )
        conn.execute(
            "UPDATE sessions SET seq = ?, current_nonce = ?, next_nonce = ?, last_active_at = ? WHERE session_id = ?",
            (req.seq, req.nonce, new_nonce, now, req.session_id)
        )
        conn.commit()

    log_audit(req.session_id, team_id, "MODE_SWITCHED_ORIGINAL", {})

    return ModeSwitchResponse(
        success=True,
        mode="original",
        message="Original celestial machine engaged. Your army now controls the sacred formation.",
        next_nonce=new_nonce,
        seq=req.seq
    )


@app.get("/api/v1/hints")
def get_hints():
    import yaml
    if HINTS_FILE.exists():
        with open(HINTS_FILE, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            all_hints = data.get("hints", [])
            released = [h for h in all_hints if h.get("released")]
            return {"hints": released}
    return {"hints": []}


@app.post("/api/v1/tamper")
def tamper_beacon(req: TamperBeaconRequest, request: Request):
    now = time.time()
    with get_db_connection() as conn:
        session = conn.execute("SELECT team_id FROM sessions WHERE session_id = ?", (req.session_id,)).fetchone()
        team_id = session["team_id"] if session else f"ip_{request.client.host if request.client else 'unknown'}"

    strike_count = RulesEngine.apply_hard_strike(
        team_id,
        detector=req.detector,
        evidence=req.evidence or {},
        ua_string=request.headers.get("user-agent", ""),
        current_time=now
    )

    return {"status": "recorded", "strike_count": strike_count}


@app.post("/api/v1/violation")
def report_soft_violation(req: SoftViolationRequest, request: Request):
    now = time.time()
    with get_db_connection() as conn:
        session = conn.execute("SELECT team_id FROM sessions WHERE session_id = ?", (req.session_id,)).fetchone()
        if not session:
            raise HTTPException(status_code=401, detail="Invalid session")
        team_id = session["team_id"]

    escalated = RulesEngine.record_soft_violation(team_id, req.violation_type, req.evidence, now)
    return {"status": "recorded", "escalated_to_strike": escalated}


@app.get("/api/v1/artifacts/{name}")
def download_artifact(name: str, session_id: Optional[str] = Query(None)):
    now = time.time()

    # Pre-gate public files
    if name == "flavor.txt":
        file_path = PUBLIC_ARTIFACTS_PATH / "flavor.txt"
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Artifact unavailable")
        return FileResponse(path=str(file_path), filename="flavor.txt", media_type="text/plain; charset=utf-8")

    if name == "replica_config.json":
        return JSONResponse(content=REPLICA_CONFIG)

    # Session authentication required for all per-team and gated files
    if not session_id:
        raise HTTPException(status_code=401, detail="Session required for team-specific artifacts.")

    with get_db_connection() as conn:
        session = conn.execute("SELECT team_id, is_active FROM sessions WHERE session_id = ?", (session_id,)).fetchone()
        if not session or not session["is_active"]:
            raise HTTPException(status_code=401, detail="Invalid or expired session.")
        team_id = session["team_id"]

    team_inst = get_team_instance(team_id)

    # Pre-gate per-team ciphertext
    if name == "ciphertext.txt":
        content = team_inst["ciphertext_grouped"]
        return PlainTextResponse(content=content, headers={"Content-Disposition": 'attachment; filename="ciphertext.txt"'})

    # Gate I Gated Artifacts
    if name in ["enigma_spec.txt", "rotor_wirings.json", "rotor_notches.json"]:
        if not RulesEngine.is_gate_unlocked(team_id, "I"):
            RulesEngine.record_soft_violation(team_id, "gated_artifact_premature_access", {"artifact": name}, now)
            raise HTTPException(status_code=403, detail="Seal of Gandiva (Gate I) required.")

        if name == "enigma_spec.txt":
            spec_content = (
                "CHAKRAVYUHA SACRED CIPHER SPECIFICATION (GATE I REVEAL)\n"
                "----------------------------------------------------\n"
                f"Alphabet ({N} symbols): {ALPHABET}\n"
                "Rotor Pool: 8 rotors (I to VIII), 4 seated simultaneously.\n"
                "Rotor Stepping: Leftmost rotor steps when immediate right neighbor is on a notch symbol.\n"
                "Reflector: Involutory, reciprocal substitution over all 30 symbols.\n"
                "Plugboard: Symmetric swapping of up to 13 pairs (26 symbols).\n"
            )
            return PlainTextResponse(content=spec_content, headers={"Content-Disposition": 'attachment; filename="enigma_spec.txt"'})

        if name == "rotor_wirings.json":
            wirings_data = {
                "alphabet": ALPHABET,
                "rotors": team_inst["all_rotors"]
            }
            return JSONResponse(content=wirings_data, headers={"Content-Disposition": 'attachment; filename="rotor_wirings.json"'})

        if name == "rotor_notches.json":
            notches_data = {
                "notches": {k: v["notches"] for k, v in team_inst["all_rotors"].items()}
            }
            return JSONResponse(content=notches_data, headers={"Content-Disposition": 'attachment; filename="rotor_notches.json"'})

    # Gate II Gated Artifacts
    if name in ["reflector.json", "ring_settings.json"]:
        if not RulesEngine.is_gate_unlocked(team_id, "II"):
            RulesEngine.record_soft_violation(team_id, "gated_artifact_premature_access", {"artifact": name}, now)
            raise HTTPException(status_code=403, detail="Seal of Sanjaya (Gate II) required.")

        if name == "reflector.json":
            reflector_data = {
                "reflector_pairs": team_inst["reflector_pairs"]
            }
            return JSONResponse(content=reflector_data, headers={"Content-Disposition": 'attachment; filename="reflector.json"'})

        if name == "ring_settings.json":
            rings_data = {
                "ringstellung": team_inst["ringstellung"],
                "note": "Ring settings for the seated celestial wheels."
            }
            return JSONResponse(content=rings_data, headers={"Content-Disposition": 'attachment; filename="ring_settings.json"'})

    raise HTTPException(status_code=404, detail="Artifact not found")


# Serve static files for frontend
if FRONTEND_DIST_PATH.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST_PATH), html=True), name="frontend")
