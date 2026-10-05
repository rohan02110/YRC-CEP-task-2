export const ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ{}#_";
export const N = ALPHABET.length;

export function idx_to_char(idx: number): string {
  return ALPHABET[((idx % N) + N) % N];
}

export interface SessionState {
  sessionId: string;
  sessionKey: string;
  teamId: string;
  nextNonce: string;
  seq: number;
  isSealed: boolean;
  walzenlage: string[];
  ringstellung: number[];
  grundstellung: number[];
  plugboard: [string, string][];
  currentPositions: number[];
  windowSymbols: string[];
  baanRemaining: number;
  lifetimeCapRemaining: number;
  isLocked: boolean;
  lockRemainingSeconds: number;
  lockReason: string | null;
  isBanned?: boolean;
  mode?: string;
}

export interface PressResult {
  outSymbol: string;
  positions: number[];
  windowSymbols: string[];
  steppedFlags: boolean[];
  nextNonce: string;
  seq: number;
  baanRemaining: number;
  isSealed: boolean;
}

export interface GateItem {
  id: string;
  name: string;
  description: string;
  is_unlocked: boolean;
  is_locked: boolean;
  lock_remaining_seconds: number;
  reveals: string[];
}

export interface GatesStatus {
  chain_mode: string;
  current_mode: string;
  gates: GateItem[];
}

export interface HintItem {
  id: number;
  title: string;
  text: string;
  released: boolean;
  released_at?: number;
}
