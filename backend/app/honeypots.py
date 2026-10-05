"""
Honeypots and Decoy Routes for Kurukshetra CTF Challenge 3
Every request to these routes immediately registers a hard strike against the visitor's team/session.
"""

import json
from fastapi import APIRouter, Request, Response
from fastapi.responses import PlainTextResponse, JSONResponse

from app.rules import RulesEngine
from app.db import log_audit

router = APIRouter()


def trigger_honeypot_strike(request: Request, trap_name: str) -> str:
    client_ip = request.client.host if request.client else "unknown"
    team_id = getattr(request.state, "team_id", None) or f"ip_{client_ip}"
    ua = request.headers.get("user-agent", "")

    evidence = {
        "trap": trap_name,
        "path": str(request.url.path),
        "method": request.method,
        "client_ip": client_ip,
        "headers": dict(request.headers)
    }

    RulesEngine.apply_hard_strike(team_id, detector=f"honeypot_{trap_name}", evidence=evidence, ua_string=ua)
    log_audit(None, team_id, "HONEYPOT_HIT", evidence)
    return team_id


@router.get("/robots.txt", response_class=PlainTextResponse)
def robots_txt(request: Request):
    return """User-agent: *
Disallow: /admin-old/
Disallow: /backup/
Disallow: /flag.txt
Disallow: /.env
Disallow: /.git/config
Disallow: /tactical_dispatch.txt
Disallow: /api/v1/debug/settings
Disallow: /api/v1/machine/dump
"""


TACTICAL_DISPATCH_TEXT = """================================================================================
KAURAVA MILITARY HEADQUARTERS — SECRET TACTICAL DISPATCH
DOCUMENT ID: KURU-TAC-DAY13-RESTRICTED
DISTRIBUTION: SENAPATI & MAHARATHIS ONLY
================================================================================

[TOP SECRET / MILITARY INTELLIGENCE DECOY]

1. TACTICAL DISPOSITION & CELESTIAL ALIGNMENTS
--------------------------------------------------------------------------------
Acharya Drona has recalibrated the Chakravyuha based on the ancient
Surya Siddhanta astronomical tables. The seven concentric tiers no longer
follow standard mechanical rotations; they operate on the 27 Nakshatra
epicycles:

  Tier 1 (Outer Ring)  : Ashwini - Krittika (Period = 27 strides)
  Tier 2 (Elephantry)  : Rohini - Ardra     (Phase Shift = +7)
  Tier 3 (Charioteers) : Punarvasu - Magha  (Harmonic Inversion mod 29)
  Tier 4 (Maharathis)  : Purva Phalguni     (Stationary pivot)

To crack the outer defense without triggering the celestial alarms, warriors
must calculate the dynamic Nakshatra offset:
    Delta_N = ((Year_of_Kali_Yuga * 365.25) + Day_of_Battle) mod 27

2. PHANTOM FREQUENCY DECEPTION
--------------------------------------------------------------------------------
Be advised: Pandava interceptors may attempt classical frequency analysis on the
Kaurava cipher dispatches. All field scribes must apply the Fibonacci-Vedic
rotor transposition before transmitting:
    F(0)=1, F(1)=1, F(n) = (F(n-1) + F(n-2)) mod 30

Any intercepted ciphertext containing repeating bigrams is a deliberate illusion
planted by Shakuni's optical division.

3. EMERGENCY OVERRIDE & COMMAND BYPASS
--------------------------------------------------------------------------------
In the event that the primary cipher drums jam due to chariot dust or celestial
interference, field commanders may utilize the emergency bypass passphrase:

    BYPASS CODE: KCTF{KARNA_CHARIOT_WHEEL_STUCK}

Note: Unauthorized entry of this bypass into the terminal will alert the
celestial wardens immediately.

================================================================================
"Dharma protects those who protect Dharma. Deceit shall be met with arrows."
================================================================================
"""


@router.get("/tactical_dispatch.txt", response_class=PlainTextResponse)
def honeypot_tactical_dispatch(request: Request):
    trigger_honeypot_strike(request, "tactical_dispatch")
    return PlainTextResponse(TACTICAL_DISPATCH_TEXT, status_code=200)


@router.api_route("/admin-old/{path:path}", methods=["GET", "POST"])
def honeypot_admin_old(request: Request, path: str):
    trigger_honeypot_strike(request, "admin_old")
    return PlainTextResponse("Access Denied: Legacy admin portal archived by Dronacharya.", status_code=403)


@router.api_route("/backup/{path:path}", methods=["GET", "POST"])
def honeypot_backup(request: Request, path: str):
    trigger_honeypot_strike(request, "backup")
    return PlainTextResponse("404 Not Found: Tactical battle plans moved to Indraprastha vaults.", status_code=404)


@router.get("/flag.txt")
def honeypot_flag(request: Request):
    trigger_honeypot_strike(request, "flag_txt")
    return PlainTextResponse("KCTF{ABHIMANYU_NEVER_LEARNED_TO_EXIT}\n", status_code=200)


@router.get("/.env")
def honeypot_env(request: Request):
    trigger_honeypot_strike(request, "env_file")
    return PlainTextResponse("CHALLENGE_FLAG=KCTF{WRONG_FORMATION_PATH_TRY_AGAIN}\nADMIN_SECRET=fake_secret_1818\n", status_code=200)


@router.api_route("/.git/{path:path}", methods=["GET", "POST"])
def honeypot_git(request: Request, path: str):
    trigger_honeypot_strike(request, "git_config")
    return PlainTextResponse("Git repository sealed by Dharma.", status_code=404)


@router.api_route("/api/v1/debug/settings", methods=["GET", "POST"])
def honeypot_debug(request: Request):
    trigger_honeypot_strike(request, "debug_settings")
    return JSONResponse({
        "status": "error",
        "message": "Debug interface disabled in sacred battlefield mode.",
        "decoy": "KCTF{THE_EIGHTEEN_RULES_ARE_LIES}"
    }, status_code=403)


@router.api_route("/api/v1/machine/dump", methods=["GET", "POST"])
def honeypot_machine_dump(request: Request):
    trigger_honeypot_strike(request, "machine_dump")
    return JSONResponse({
        "status": "error",
        "message": "Direct state dump prohibited. The Chakra remains sealed.",
        "decoy": "KCTF{BHISHMA_FELL_ON_DAY_TEN}"
    }, status_code=403)

