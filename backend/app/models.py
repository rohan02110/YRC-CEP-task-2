"""
Pydantic Models for Chakravyuha Backend API
"""

from typing import List, Optional, Tuple, Dict, Any
from pydantic import BaseModel, Field


class SessionInitRequest(BaseModel):
    team_token: Optional[str] = None


class SessionInitResponse(BaseModel):
    session_id: str
    session_key: str
    team_id: str
    next_nonce: str
    seq: int
    is_sealed: bool
    walzenlage: List[str]
    ringstellung: List[int]
    grundstellung: List[int]
    plugboard: List[Tuple[str, str]]
    current_positions: List[int]
    window_symbols: List[str]
    baan_remaining: int
    lifetime_cap_remaining: int
    is_locked: bool
    lock_remaining_seconds: int
    lock_reason: Optional[str] = None


class HeartbeatRequest(BaseModel):
    session_id: str
    seq: int
    nonce: str


class HeartbeatResponse(BaseModel):
    next_nonce: str
    seq: int
    is_locked: bool
    lock_remaining_seconds: int
    lock_reason: Optional[str] = None
    baan_remaining: int
    lifetime_cap_remaining: int
    is_sealed: bool
    is_banned: bool


class ConfigureRequest(BaseModel):
    session_id: str
    seq: int
    nonce: str
    walzenlage: List[str] = Field(..., description="4 rotor names, e.g. ['I', 'II', 'III', 'IV']")
    ringstellung: List[int] = Field(..., description="4 ring settings 0-29")
    grundstellung: List[int] = Field(..., description="4 start positions 0-29")
    plugboard: List[Tuple[str, str]] = Field(default_factory=list, description="Up to 13 pairs")


class ConfigureResponse(BaseModel):
    success: bool
    next_nonce: str
    seq: int
    is_sealed: bool
    walzenlage: List[str]
    ringstellung: List[int]
    grundstellung: List[int]
    plugboard: List[Tuple[str, str]]
    current_positions: List[int]
    window_symbols: List[str]
    baan_remaining: int


class PressRequest(BaseModel):
    session_id: str
    seq: int
    nonce: str
    char: str
    is_trusted: bool = True


class PressResponse(BaseModel):
    out_symbol: str
    positions: List[int]
    window_symbols: List[str]
    stepped_flags: List[bool]
    next_nonce: str
    seq: int
    baan_remaining: int
    is_sealed: bool


class ResetRequest(BaseModel):
    session_id: str
    seq: int
    nonce: str


class ResetResponse(BaseModel):
    success: bool
    next_nonce: str
    seq: int
    is_sealed: bool
    current_positions: List[int]
    window_symbols: List[str]
    baan_remaining: int


class SubmitFlagRequest(BaseModel):
    session_id: str
    seq: int
    nonce: str
    flag: str


class SubmitFlagResponse(BaseModel):
    correct: bool
    message: str
    next_nonce: str
    seq: int
    is_locked: bool
    lock_remaining_seconds: int
    baan_remaining: int


class TamperBeaconRequest(BaseModel):
    session_id: str
    detector: str
    evidence: Optional[Dict[str, Any]] = None


class SoftViolationRequest(BaseModel):
    session_id: str
    seq: int
    nonce: str
    violation_type: str
    evidence: Optional[Dict[str, Any]] = None


class GateInfo(BaseModel):
    id: str
    name: str
    description: str
    is_unlocked: bool
    is_locked: bool
    lock_remaining_seconds: int
    reveals: List[str]


class UnlockGateRequest(BaseModel):
    session_id: str
    seq: int
    nonce: str
    gate_id: str
    seal: str


class UnlockGateResponse(BaseModel):
    success: bool
    message: str
    next_nonce: str
    seq: int
    gate_id: str
    is_unlocked: bool
    is_locked: bool
    lock_remaining_seconds: int
    reveals: List[str]
    unlocks: Optional[str] = None


class ModeSwitchRequest(BaseModel):
    session_id: str
    seq: int
    nonce: str
    target_mode: str  # "original"


class HintModel(BaseModel):
    id: int
    title: str
    text: str
    released: bool
    released_at: Optional[float] = None


class GatesStatusResponse(BaseModel):
    chain_mode: str
    current_mode: str
    gates: List[GateInfo]


class ModeSwitchResponse(BaseModel):
    success: bool
    mode: str
    message: str
    next_nonce: str
    seq: int


