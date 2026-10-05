/**
 * Network API Client for Chakravyuha
 * Handles HMAC-SHA256 request signing, rolling nonce state, heartbeats, and tamper beacons.
 */

import { SessionState, PressResult } from '../machine/types';
import { hmacSha256 } from './cryptoFallback';

export class ApiClient {
  private state: SessionState | null = null;
  private heartbeatTimer: number | null = null;
  private onStateChangeCallback: ((state: SessionState) => void) | null = null;
  private onTamperCallback: (() => void) | null = null;

  public setOnStateChange(cb: (state: SessionState) => void) {
    this.onStateChangeCallback = cb;
  }

  public setOnTamper(cb: () => void) {
    this.onTamperCallback = cb;
  }

  public getState(): SessionState | null {
    return this.state;
  }

  public async initSession(teamToken?: string): Promise<SessionState> {
    const res = await fetch('/api/v1/session', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ team_token: teamToken || null })
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to initialize session' }));
      throw new Error(err.detail || 'Initialization failed');
    }

    const data = await res.json();
    this.state = {
      sessionId: data.session_id,
      sessionKey: data.session_key,
      teamId: data.team_id,
      nextNonce: data.next_nonce,
      seq: data.seq,
      isSealed: data.is_sealed,
      walzenlage: data.walzenlage,
      ringstellung: data.ringstellung,
      grundstellung: data.grundstellung,
      plugboard: data.plugboard,
      currentPositions: data.current_positions,
      windowSymbols: data.window_symbols,
      baanRemaining: data.baan_remaining,
      lifetimeCapRemaining: data.lifetime_cap_remaining,
      isLocked: data.is_locked,
      lockRemainingSeconds: data.lock_remaining_seconds,
      lockReason: data.lock_reason
    };

    this.startHeartbeat();
    if (this.onStateChangeCallback) this.onStateChangeCallback(this.state);
    return this.state;
  }

  private startHeartbeat() {
    if (this.heartbeatTimer) clearInterval(this.heartbeatTimer);
    this.heartbeatTimer = window.setInterval(async () => {
      if (!this.state) return;
      try {
        const res = await fetch('/api/v1/heartbeat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session_id: this.state.sessionId,
            seq: this.state.seq,
            nonce: this.state.nextNonce
          })
        });

        if (res.ok) {
          const data = await res.json();
          if (this.state) {
            this.state.isLocked = data.is_locked;
            this.state.lockRemainingSeconds = data.lock_remaining_seconds;
            this.state.lockReason = data.lock_reason;
            this.state.baanRemaining = data.baan_remaining;
            this.state.lifetimeCapRemaining = data.lifetime_cap_remaining;
            this.state.isSealed = data.is_sealed;
            this.state.isBanned = data.is_banned;
            if (this.onStateChangeCallback) this.onStateChangeCallback(this.state);
          }
        } else if (res.status === 401 || res.status === 403) {
          if (this.onTamperCallback) this.onTamperCallback();
        }
      } catch {
        // Network heartbeat error handled gracefully
      }
    }, 3000);
  }

  public async pressKey(char: string): Promise<PressResult> {
    if (!this.state) throw new Error('Session not initialized');

    const nextSeq = this.state.seq + 1;
    const bodyObj = {
      session_id: this.state.sessionId,
      seq: nextSeq,
      nonce: this.state.nextNonce,
      char: char,
      is_trusted: true
    };

    const sigMsg = `${nextSeq}|${this.state.nextNonce}|${JSON.stringify(bodyObj, Object.keys(bodyObj).sort())}`;
    const signature = hmacSha256(this.state.sessionKey, sigMsg);

    const res = await fetch('/api/v1/press', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Sig': signature
      },
      body: JSON.stringify(bodyObj)
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Press request failed' }));
      throw new Error(err.detail || 'Key press rejected');
    }

    const data = await res.json();
    this.state.seq = data.seq;
    this.state.nextNonce = data.next_nonce;
    this.state.currentPositions = data.positions;
    this.state.windowSymbols = data.window_symbols;
    this.state.baanRemaining = data.baan_remaining;
    this.state.isSealed = data.is_sealed;

    if (this.onStateChangeCallback) this.onStateChangeCallback(this.state);

    return {
      outSymbol: data.out_symbol,
      positions: data.positions,
      windowSymbols: data.window_symbols,
      steppedFlags: data.stepped_flags,
      nextNonce: data.next_nonce,
      seq: data.seq,
      baanRemaining: data.baan_remaining,
      isSealed: data.is_sealed
    };
  }

  public async configureMachine(walzenlage: string[], rings: number[], grund: number[], plugboard: [string, string][]): Promise<void> {
    if (!this.state) throw new Error('Session not initialized');

    const nextSeq = this.state.seq + 1;
    const bodyObj = {
      session_id: this.state.sessionId,
      seq: nextSeq,
      nonce: this.state.nextNonce,
      walzenlage: walzenlage,
      ringstellung: rings,
      grundstellung: grund,
      plugboard: plugboard
    };

    const sigMsg = `${nextSeq}|${this.state.nextNonce}|${JSON.stringify(bodyObj, Object.keys(bodyObj).sort())}`;
    const signature = hmacSha256(this.state.sessionKey, sigMsg);

    const res = await fetch('/api/v1/configure', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Sig': signature
      },
      body: JSON.stringify(bodyObj)
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Configuration rejected' }));
      throw new Error(err.detail || 'Configuration rejected');
    }

    const data = await res.json();
    this.state.seq = data.seq;
    this.state.nextNonce = data.next_nonce;
    this.state.walzenlage = data.walzenlage;
    this.state.ringstellung = data.ringstellung;
    this.state.grundstellung = data.grundstellung;
    this.state.plugboard = data.plugboard;
    this.state.currentPositions = data.current_positions;
    this.state.windowSymbols = data.window_symbols;
    this.state.baanRemaining = data.baan_remaining;
    this.state.isSealed = data.is_sealed;

    if (this.onStateChangeCallback) this.onStateChangeCallback(this.state);
  }

  public async resetChakra(): Promise<void> {
    if (!this.state) throw new Error('Session not initialized');

    const nextSeq = this.state.seq + 1;
    const bodyObj = {
      session_id: this.state.sessionId,
      seq: nextSeq,
      nonce: this.state.nextNonce
    };

    const sigMsg = `${nextSeq}|${this.state.nextNonce}|${JSON.stringify(bodyObj, Object.keys(bodyObj).sort())}`;
    const signature = hmacSha256(this.state.sessionKey, sigMsg);

    const res = await fetch('/api/v1/reset', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Sig': signature
      },
      body: JSON.stringify(bodyObj)
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Reset failed' }));
      throw new Error(err.detail || 'Reset failed');
    }

    const data = await res.json();
    this.state.seq = data.seq;
    this.state.nextNonce = data.next_nonce;
    this.state.currentPositions = data.current_positions;
    this.state.windowSymbols = data.window_symbols;
    this.state.baanRemaining = data.baan_remaining;
    this.state.isSealed = data.is_sealed;

    if (this.onStateChangeCallback) this.onStateChangeCallback(this.state);
  }

  public async submitFlag(flag: string): Promise<{ correct: boolean; message: string; isLocked: boolean; lockRemaining: number }> {
    if (!this.state) throw new Error('Session not initialized');

    const nextSeq = this.state.seq + 1;
    const bodyObj = {
      session_id: this.state.sessionId,
      seq: nextSeq,
      nonce: this.state.nextNonce,
      flag: flag
    };

    const sigMsg = `${nextSeq}|${this.state.nextNonce}|${JSON.stringify(bodyObj, Object.keys(bodyObj).sort())}`;
    const signature = hmacSha256(this.state.sessionKey, sigMsg);

    const res = await fetch('/api/v1/submit', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Sig': signature
      },
      body: JSON.stringify(bodyObj)
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Submission failed' }));
      throw new Error(err.detail || 'Submission failed');
    }

    const data = await res.json();
    this.state.seq = data.seq;
    this.state.nextNonce = data.next_nonce;
    this.state.isLocked = data.is_locked;
    this.state.lockRemainingSeconds = data.lock_remaining_seconds;
    this.state.baanRemaining = data.baan_remaining;

    if (this.onStateChangeCallback) this.onStateChangeCallback(this.state);

    return {
      correct: data.correct,
      message: data.message,
      isLocked: data.is_locked,
      lockRemaining: data.lock_remaining_seconds
    };
  }

  public sendTamperBeacon(detector: string, evidence?: unknown) {
    if (!this.state) return;
    const payload = JSON.stringify({
      session_id: this.state.sessionId,
      detector: detector,
      evidence: evidence || {}
    });

    if (typeof navigator !== 'undefined' && navigator.sendBeacon) {
      navigator.sendBeacon('/api/v1/tamper', new Blob([payload], { type: 'application/json' }));
    } else {
      fetch('/api/v1/tamper', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: payload,
        keepalive: true
      }).catch(() => {});
    }
  }

  public reportSoftViolation(violationType: string, evidence?: unknown) {
    if (!this.state) return;
    const nextSeq = this.state.seq + 1;
    const bodyObj = {
      session_id: this.state.sessionId,
      seq: nextSeq,
      nonce: this.state.nextNonce,
      violation_type: violationType,
      evidence: evidence || {}
    };

    fetch('/api/v1/violation', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(bodyObj)
    }).catch(() => {});
  }

  public async getGates(): Promise<import('../machine/types').GatesStatus> {
    if (!this.state) throw new Error('Session not initialized');
    const res = await fetch(`/api/v1/gates?session_id=${encodeURIComponent(this.state.sessionId)}`);
    if (!res.ok) {
      throw new Error('Failed to fetch gates status');
    }
    return res.json();
  }

  public async unlockGate(gateId: string, seal: string): Promise<{ success: boolean; message: string; isUnlocked: boolean; reveals: string[]; unlocks?: string }> {
    if (!this.state) throw new Error('Session not initialized');

    const nextSeq = this.state.seq + 1;
    const bodyObj = {
      session_id: this.state.sessionId,
      seq: nextSeq,
      nonce: this.state.nextNonce,
      gate_id: gateId,
      seal: seal
    };

    const sigMsg = `${nextSeq}|${this.state.nextNonce}|${JSON.stringify(bodyObj, Object.keys(bodyObj).sort())}`;
    const signature = hmacSha256(this.state.sessionKey, sigMsg);

    const res = await fetch('/api/v1/gates/unlock', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Sig': signature
      },
      body: JSON.stringify(bodyObj)
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Unlock attempt failed' }));
      throw new Error(err.detail || 'Unlock attempt failed');
    }

    const data = await res.json();
    this.state.seq = data.seq;
    this.state.nextNonce = data.next_nonce;

    if (this.onStateChangeCallback) this.onStateChangeCallback(this.state);

    return {
      success: data.success,
      message: data.message,
      isUnlocked: data.is_unlocked,
      reveals: data.reveals,
      unlocks: data.unlocks
    };
  }

  public async switchMode(targetMode: string = 'original'): Promise<{ success: boolean; mode: string; message: string }> {
    if (!this.state) throw new Error('Session not initialized');

    const nextSeq = this.state.seq + 1;
    const bodyObj = {
      session_id: this.state.sessionId,
      seq: nextSeq,
      nonce: this.state.nextNonce,
      target_mode: targetMode
    };

    const sigMsg = `${nextSeq}|${this.state.nextNonce}|${JSON.stringify(bodyObj, Object.keys(bodyObj).sort())}`;
    const signature = hmacSha256(this.state.sessionKey, sigMsg);

    const res = await fetch('/api/v1/mode/switch', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Sig': signature
      },
      body: JSON.stringify(bodyObj)
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Mode switch failed' }));
      throw new Error(err.detail || 'Mode switch failed');
    }

    const data = await res.json();
    this.state.seq = data.seq;
    this.state.nextNonce = data.next_nonce;
    this.state.mode = data.mode;

    if (this.onStateChangeCallback) this.onStateChangeCallback(this.state);

    return {
      success: data.success,
      mode: data.mode,
      message: data.message
    };
  }

  public async getHints(): Promise<import('../machine/types').HintItem[]> {
    const res = await fetch('/api/v1/hints');
    if (!res.ok) return [];
    const data = await res.json();
    return data.hints || [];
  }
}

export const api = new ApiClient();

