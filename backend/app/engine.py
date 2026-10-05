"""
Chakravyuha Enigma Engine (Server-Side Cryptographic Core)
30-Symbol Custom Enigma Machine with Double-Notch Stepping, Involutory Reflector, and 13-Pair Plugboard.
"""

import hashlib
import hmac
import struct
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional, Any

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ{}#_"
N = len(ALPHABET)  # 30 symbols

CHAR_TO_IDX: Dict[str, int] = {c: i for i, c in enumerate(ALPHABET)}
IDX_TO_CHAR: Dict[int, str] = {i: c for i, c in enumerate(ALPHABET)}


def char_to_idx(c: str) -> int:
    if c not in CHAR_TO_IDX:
        raise ValueError(f"Invalid character '{c}' for Chakravyuha alphabet")
    return CHAR_TO_IDX[c]


def idx_to_char(i: int) -> str:
    return IDX_TO_CHAR[i % N]


class HMAC_DRBG:
    """
    Deterministic CSPRNG based on HMAC-SHA256 (RFC 6979 / NIST SP 800-90A).
    Guarantees deterministic, platform-independent cryptographic derivation.
    """
    def __init__(self, seed: bytes | str):
        if isinstance(seed, str):
            seed = seed.encode("utf-8")
        self.k = b"\x00" * 32
        self.v = b"\x01" * 32
        self._update(seed)

    def _update(self, data: Optional[bytes] = None):
        self.k = hmac.new(self.k, self.v + b"\x00" + (data or b""), hashlib.sha256).digest()
        self.v = hmac.new(self.k, self.v, hashlib.sha256).digest()
        if data:
            self.k = hmac.new(self.k, self.v + b"\x01" + data, hashlib.sha256).digest()
            self.v = hmac.new(self.k, self.v, hashlib.sha256).digest()

    def next_bytes(self, n: int) -> bytes:
        out = b""
        while len(out) < n:
            self.v = hmac.new(self.k, self.v, hashlib.sha256).digest()
            out += self.v
        self._update(None)
        return out[:n]

    def next_int(self, min_val: int, max_val: int) -> int:
        if min_val > max_val:
            raise ValueError("min_val must be <= max_val")
        range_size = max_val - min_val + 1
        if range_size == 1:
            return min_val
        mask = 0xFFFFFFFF
        limit = (mask // range_size) * range_size
        while True:
            raw = struct.unpack(">I", self.next_bytes(4))[0]
            if raw < limit:
                return min_val + (raw % range_size)

    def choice(self, seq: list) -> Any:
        if not seq:
            raise IndexError("Cannot choose from empty sequence")
        idx = self.next_int(0, len(seq) - 1)
        return seq[idx]

    def shuffle(self, seq: list) -> list:
        for i in range(len(seq) - 1, 0, -1):
            j = self.next_int(0, i)
            seq[i], seq[j] = seq[j], seq[i]
        return seq

    def sample(self, seq: list, k: int) -> list:
        if k > len(seq):
            raise ValueError("Sample larger than population")
        pool = list(seq)
        self.shuffle(pool)
        return pool[:k]

    def permutation(self, alphabet: str = ALPHABET) -> str:
        chars = list(alphabet)
        self.shuffle(chars)
        return "".join(chars)


class KeywordSubstitution:
    """
    Monoalphabetic keyword-mixed substitution cipher (Layer S) over ALPHABET (N=30).
    Default keyword: SANJAYAUVACHA (Challenge 2 passphrase).
    """
    def __init__(self, keyword: str = "SANJAYAUVACHA"):
        self.keyword = keyword.upper()
        unique_key_chars = []
        for c in self.keyword:
            if c in ALPHABET and c not in unique_key_chars:
                unique_key_chars.append(c)
        remaining_chars = [c for c in ALPHABET if c not in unique_key_chars]
        self.sub_alphabet = "".join(unique_key_chars + remaining_chars)
        if len(self.sub_alphabet) != N or set(self.sub_alphabet) != set(ALPHABET):
            raise ValueError(f"Invalid substitution alphabet of length {len(self.sub_alphabet)}")

        self.forward_map = {orig: sub for orig, sub in zip(ALPHABET, self.sub_alphabet)}
        self.backward_map = {sub: orig for orig, sub in zip(ALPHABET, self.sub_alphabet)}

    def encrypt(self, text: str) -> str:
        return "".join(self.forward_map.get(c, c) for c in text if c in ALPHABET)

    def decrypt(self, text: str) -> str:
        return "".join(self.backward_map.get(c, c) for c in text if c in ALPHABET)


@dataclass
class RotorDef:
    name: str
    wiring: str
    notches: List[int]

    def validate(self):
        if len(self.wiring) != N:
            raise ValueError(f"Rotor {self.name} wiring must be of length {N}")
        if set(self.wiring) != set(ALPHABET):
            raise ValueError(f"Rotor {self.name} wiring must be an exact permutation of alphabet")
        if len(self.notches) != 2:
            raise ValueError(f"Rotor {self.name} must have exactly 2 notches")
        for notch in self.notches:
            if not (0 <= notch < N):
                raise ValueError(f"Notch {notch} out of range [0, {N-1}]")


class Rotor:
    def __init__(self, wiring: str, notches: List[int], ring_setting: int = 0, position: int = 0):
        if len(wiring) != N or set(wiring) != set(ALPHABET):
            raise ValueError("Wiring must be a 30-symbol permutation of the alphabet")
        self.forward = [char_to_idx(c) for c in wiring]
        self.backward = [0] * N
        for i, j in enumerate(self.forward):
            self.backward[j] = i
        self.notches = list(notches)
        self.ring = ring_setting % N
        self.position = position % N

    def at_notch(self) -> bool:
        """Evaluated before stepping."""
        return self.position in self.notches

    def step(self):
        self.position = (self.position + 1) % N

    def encode_forward(self, signal: int) -> int:
        shifted = (signal + self.position - self.ring) % N
        encoded = self.forward[shifted]
        return (encoded - self.position + self.ring) % N

    def encode_backward(self, signal: int) -> int:
        shifted = (signal + self.position - self.ring) % N
        encoded = self.backward[shifted]
        return (encoded - self.position + self.ring) % N


class Reflector:
    def __init__(self, pairs: List[Tuple[str, str]] | List[int] | str):
        """
        Pairs can be:
        - List of 15 tuple pairs of characters [('A', 'B'), ...]
        - List of 30 integers mapping each index to its reflected index
        - 30-character wiring string where wiring[i] = reflected char
        """
        self.mapping = [0] * N
        if isinstance(pairs, str):
            if len(pairs) != N:
                raise ValueError("Reflector string must have length 30")
            for i, c in enumerate(pairs):
                self.mapping[i] = char_to_idx(c)
        elif isinstance(pairs, list) and len(pairs) == N and isinstance(pairs[0], int):
            self.mapping = list(pairs)
        elif isinstance(pairs, list):
            if len(pairs) != 15:
                raise ValueError("Reflector must have exactly 15 disjoint pairs")
            seen = set()
            for a, b in pairs:
                ia, ib = char_to_idx(a) if isinstance(a, str) else a, char_to_idx(b) if isinstance(b, str) else b
                if ia == ib:
                    raise ValueError(f"Reflector cannot map symbol {ia} to itself (fixed point)")
                if ia in seen or ib in seen:
                    raise ValueError(f"Duplicate symbol in reflector pairs: {ia}, {ib}")
                seen.add(ia)
                seen.add(ib)
                self.mapping[ia] = ib
                self.mapping[ib] = ia
            if len(seen) != N:
                raise ValueError("Reflector must cover all 30 symbols")
        else:
            raise ValueError("Invalid reflector definition")

        self.validate()

    def validate(self):
        for i in range(N):
            target = self.mapping[i]
            if target == i:
                raise ValueError(f"Reflector has fixed point at {i} ({idx_to_char(i)})")
            if self.mapping[target] != i:
                raise ValueError(f"Reflector is not an involution: {i} -> {target} -> {self.mapping[target]}")

    def reflect(self, signal: int) -> int:
        return self.mapping[signal]


class Plugboard:
    def __init__(self, pairs: Optional[List[Tuple[str, str]]] = None):
        """
        Pairs of characters to swap. Up to 13 pairs (26 symbols swapped, 4 unplugged).
        """
        self.mapping = list(range(N))
        self.pairs: List[Tuple[str, str]] = []
        if pairs:
            if len(pairs) > 13:
                raise ValueError("Plugboard cannot have more than 13 pairs")
            seen = set()
            for a, b in pairs:
                ia, ib = char_to_idx(a) if isinstance(a, str) else a, char_to_idx(b) if isinstance(b, str) else b
                if ia == ib:
                    continue  # identity / unplugged
                if ia in seen or ib in seen:
                    raise ValueError(f"Symbol reused in plugboard: {a}, {b}")
                seen.add(ia)
                seen.add(ib)
                self.mapping[ia] = ib
                self.mapping[ib] = ia
                self.pairs.append((idx_to_char(min(ia, ib)), idx_to_char(max(ia, ib))))
        self.validate()

    def validate(self):
        for i in range(N):
            target = self.mapping[i]
            if self.mapping[target] != i:
                raise ValueError(f"Plugboard is not an involution at {i}")

    def swap(self, signal: int) -> int:
        return self.mapping[signal]


@dataclass
class PressResult:
    out_symbol: str
    positions: List[int]
    window_symbols: List[str]
    stepped_flags: List[bool]


class EnigmaMachine:
    def __init__(self, rotors: List[Rotor], reflector: Reflector, plugboard: Plugboard):
        if len(rotors) != 4:
            raise ValueError("EnigmaMachine requires exactly 4 rotors (slots 0 to 3, left to right)")
        self.rotors = rotors
        self.reflector = reflector
        self.plugboard = plugboard

    def step_rotors(self) -> List[bool]:
        """
        Evaluates notch positions before advancing:
        - If rotors[2] at notch: rotors[2] and rotors[1] step (double-stepping anomaly)
        - Elif rotors[3] at notch: rotors[2] steps
        - rotors[3] steps on every press
        - rotors[0] (leftmost) is static
        Returns list of 4 booleans indicating which rotors stepped.
        """
        notch2 = self.rotors[2].at_notch()
        notch3 = self.rotors[3].at_notch()

        stepped = [False, False, False, False]

        if notch2:
            self.rotors[2].step()
            self.rotors[1].step()
            stepped[2] = True
            stepped[1] = True
        elif notch3:
            self.rotors[2].step()
            stepped[2] = True

        self.rotors[3].step()
        stepped[3] = True

        return stepped

    def press(self, symbol: str) -> PressResult:
        if symbol not in CHAR_TO_IDX:
            raise ValueError(f"Invalid input symbol: {symbol}")

        # 1. Step rotors
        stepped_flags = self.step_rotors()

        # 2. Signal path
        signal = char_to_idx(symbol)

        # Plugboard entry
        signal = self.plugboard.swap(signal)

        # Forward pass: rotors 3 -> 2 -> 1 -> 0
        for rotor in reversed(self.rotors):
            signal = rotor.encode_forward(signal)

        # Reflector
        signal = self.reflector.reflect(signal)

        # Backward pass: rotors 0 -> 1 -> 2 -> 3
        for rotor in self.rotors:
            signal = rotor.encode_backward(signal)

        # Plugboard exit
        signal = self.plugboard.swap(signal)

        out_symbol = idx_to_char(signal)
        positions = [r.position for r in self.rotors]
        window_symbols = [idx_to_char(p) for p in positions]

        return PressResult(
            out_symbol=out_symbol,
            positions=positions,
            window_symbols=window_symbols,
            stepped_flags=stepped_flags
        )

    def encrypt_string(self, text: str) -> str:
        out = []
        for ch in text:
            if ch in CHAR_TO_IDX:
                res = self.press(ch)
                out.append(res.out_symbol)
        return "".join(out)
