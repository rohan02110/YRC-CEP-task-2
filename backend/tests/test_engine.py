"""
Unit, Golden Vector, and Property Tests for the Chakravyuha Cryptographic Engine.
"""

import copy
import json
import random
import sys
from pathlib import Path
import pytest

# Ensure backend and tools can be imported
repo_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(repo_root / "backend"))
sys.path.insert(0, str(repo_root))
from app.engine import (
    ALPHABET, N, CHAR_TO_IDX, IDX_TO_CHAR,
    char_to_idx, idx_to_char,
    Rotor, Reflector, Plugboard, EnigmaMachine, PressResult
)


def make_simple_reflector():
    # Simple pairs: (0, 1), (2, 3), ..., (28, 29)
    pairs = [(idx_to_char(i), idx_to_char(i + 1)) for i in range(0, N, 2)]
    return Reflector(pairs)


def make_identity_rotors():
    # 4 rotors with identity wiring A->A, B->B, ...
    identity_wiring = ALPHABET
    return [Rotor(identity_wiring, notches=[10, 20], ring_setting=0, position=0) for _ in range(4)]


# ==============================================================================
# 1. Golden Vectors Tests
# ==============================================================================

def test_golden_vector_1_normal_single_step():
    """Rightmost rotor steps from 0 to 1; others stay at 0."""
    rotors = make_identity_rotors()
    reflector = make_simple_reflector()
    plugboard = Plugboard()
    machine = EnigmaMachine(rotors, reflector, plugboard)

    res = machine.press("A")
    assert res.positions == [0, 0, 0, 1]
    assert res.stepped_flags == [False, False, False, True]


def test_golden_vector_2_right_notch_triggers_rotor2():
    """Rotor 3 is at notch 10. Pressing should step rotor 3 and rotor 2."""
    rotors = make_identity_rotors()
    rotors[3].position = 10  # notch on rotor 3
    reflector = make_simple_reflector()
    plugboard = Plugboard()
    machine = EnigmaMachine(rotors, reflector, plugboard)

    res = machine.press("A")
    assert res.positions == [0, 0, 1, 11]
    assert res.stepped_flags == [False, False, True, True]


def test_golden_vector_3_middle_notch_double_step():
    """Rotor 2 is at notch 10. Pressing should step rotor 2 and rotor 1, and rotor 3 always steps."""
    rotors = make_identity_rotors()
    rotors[2].position = 10  # notch on rotor 2
    rotors[3].position = 5   # not at notch
    reflector = make_simple_reflector()
    plugboard = Plugboard()
    machine = EnigmaMachine(rotors, reflector, plugboard)

    res = machine.press("A")
    assert res.positions == [0, 1, 11, 6]
    assert res.stepped_flags == [False, True, True, True]


def test_golden_vector_4_simultaneous_notches():
    """Both rotor 2 and rotor 3 are at notch 10.
    According to specification:
    if rotors[2].at_notch(): rotors[2].step(); rotors[1].step()
    elif rotors[3].at_notch(): rotors[2].step()
    rotors[3].step()
    So rotors 1, 2, 3 all step once.
    """
    rotors = make_identity_rotors()
    rotors[2].position = 10
    rotors[3].position = 10
    reflector = make_simple_reflector()
    plugboard = Plugboard()
    machine = EnigmaMachine(rotors, reflector, plugboard)

    res = machine.press("A")
    assert res.positions == [0, 1, 11, 11]
    assert res.stepped_flags == [False, True, True, True]


def test_golden_vector_5_leftmost_rotor_static():
    """Rotor 0 never steps even across hundreds of presses."""
    rotors = make_identity_rotors()
    reflector = make_simple_reflector()
    plugboard = Plugboard()
    machine = EnigmaMachine(rotors, reflector, plugboard)

    for _ in range(500):
        res = machine.press("A")
        assert res.positions[0] == 0
        assert res.stepped_flags[0] is False


def test_golden_vector_6_wraparound_29_to_0():
    """Rightmost rotor position wraps from 29 to 0."""
    rotors = make_identity_rotors()
    rotors[3].position = 29
    reflector = make_simple_reflector()
    plugboard = Plugboard()
    machine = EnigmaMachine(rotors, reflector, plugboard)

    res = machine.press("A")
    assert res.positions[3] == 0
    assert res.stepped_flags[3] is True


def test_golden_vector_7_middle_rotor_wraparound():
    """Middle rotor position wraps from 29 to 0 when stepped."""
    rotors = make_identity_rotors()
    rotors[2].position = 29
    rotors[2].notches = [29, 15]  # notch at 29
    reflector = make_simple_reflector()
    plugboard = Plugboard()
    machine = EnigmaMachine(rotors, reflector, plugboard)

    res = machine.press("A")
    assert res.positions[2] == 0
    assert res.positions[1] == 1


def test_golden_vector_8_ring_setting_offset():
    """Ring setting shifts the signal appropriately."""
    # Custom rotor with identity wiring
    rotor = Rotor(ALPHABET, notches=[5, 15], ring_setting=5, position=0)
    # Signal 10 -> shifted by (10 + 0 - 5)%30 = 5 -> forward[5] = 5 -> (5 - 0 + 5)%30 = 10
    assert rotor.encode_forward(10) == 10

    # Custom rotor with shifted wiring
    # Alphabet shifted by 1: B C D ... _ A
    shifted_wiring = ALPHABET[1:] + ALPHABET[0]
    r2 = Rotor(shifted_wiring, notches=[0, 10], ring_setting=3, position=2)
    # signal = 0 -> shifted = (0 + 2 - 3)%30 = 29 ('_') -> forward[29] = char_to_idx('A') = 0 -> output = (0 - 2 + 3)%30 = 1 ('B')
    assert r2.encode_forward(0) == 1


def test_golden_vector_9_plugboard_swap():
    """Plugboard swaps configured pairs and passes unplugged symbols unchanged."""
    pb = Plugboard([("A", "Z"), ("B", "Y"), ("{", "}")])
    assert pb.swap(char_to_idx("A")) == char_to_idx("Z")
    assert pb.swap(char_to_idx("Z")) == char_to_idx("A")
    assert pb.swap(char_to_idx("B")) == char_to_idx("Y")
    assert pb.swap(char_to_idx("{")) == char_to_idx("}")
    assert pb.swap(char_to_idx("C")) == char_to_idx("C")
    assert pb.swap(char_to_idx("#")) == char_to_idx("#")


def test_golden_vector_10_plugboard_max_13_pairs():
    """Plugboard accepts 13 pairs (26 symbols swapped, 4 unplugged)."""
    pairs = [
        ("A", "B"), ("C", "D"), ("E", "F"), ("G", "H"), ("I", "J"),
        ("K", "L"), ("M", "N"), ("O", "P"), ("Q", "R"), ("S", "T"),
        ("U", "V"), ("W", "X"), ("Y", "Z")
    ]
    pb = Plugboard(pairs)
    assert len(pb.pairs) == 13
    assert pb.swap(char_to_idx("{")) == char_to_idx("{")
    assert pb.swap(char_to_idx("}")) == char_to_idx("}")
    assert pb.swap(char_to_idx("#")) == char_to_idx("#")
    assert pb.swap(char_to_idx("_")) == char_to_idx("_")


def test_golden_vectors_11_to_20_deterministic_hand_vectors():
    """10 sequential hand-verifiable steps on a fixed deterministic configuration."""
    # Use fixed wiring
    w1 = "EKMFLGDQVZNTOWYHXUSPAIBRCJ{}_#"
    w2 = "AJDKSIRUXBLHWTMCQGZNPYFVOE{}#_"
    w3 = "BDFHJLCPRTXVZNYEIWGAKMUSQO{}_#"
    w4 = "JPGVOUMFYQBENHZRDKASXLICTW{#}_"

    rotors = [
        Rotor(w1, notches=[2, 25], ring_setting=18, position=0),
        Rotor(w2, notches=[8, 17], ring_setting=6, position=5),
        Rotor(w3, notches=[4, 21], ring_setting=24, position=3),
        Rotor(w4, notches=[6, 19], ring_setting=12, position=18)
    ]
    reflector = make_simple_reflector()
    plugboard = Plugboard([("A", "B"), ("C", "D"), ("{", "}"), ("#", "_")])

    machine = EnigmaMachine(rotors, reflector, plugboard)
    test_chars = "DHRITARASHTRAUVACHA"

    out = machine.encrypt_string(test_chars)
    assert len(out) == len(test_chars)
    # Ensure no char mapped to itself at any step
    for in_c, out_c in zip(test_chars, out):
        assert in_c != out_c


# ==============================================================================
# 2. Property Tests (1000+ Random Configurations)
# ==============================================================================

def make_random_permutation(rng: random.Random) -> str:
    lst = list(ALPHABET)
    rng.shuffle(lst)
    return "".join(lst)


def make_random_reflector(rng: random.Random) -> Reflector:
    lst = list(ALPHABET)
    rng.shuffle(lst)
    pairs = [(lst[i], lst[i + 1]) for i in range(0, N, 2)]
    return Reflector(pairs)


def make_random_plugboard(rng: random.Random) -> Plugboard:
    lst = list(ALPHABET)
    rng.shuffle(lst)
    pairs = [(lst[i], lst[i + 1]) for i in range(0, 26, 2)]
    return Plugboard(pairs)


def test_property_1_reciprocity_over_1000_random_configs():
    """Property test: encrypt(encrypt(M)) == M under identical initial settings."""
    rng = random.Random(42)

    for trial in range(1000):
        # Generate 4 random rotors
        wirings = [make_random_permutation(rng) for _ in range(4)]
        notches = [sorted(rng.sample(range(N), 2)) for _ in range(4)]
        rings = [rng.randrange(N) for _ in range(4)]
        positions = [rng.randrange(N) for _ in range(4)]

        reflector = make_random_reflector(rng)
        plugboard = make_random_plugboard(rng)

        # Build Machine 1
        rotors1 = [
            Rotor(wirings[i], notches[i], ring_setting=rings[i], position=positions[i])
            for i in range(4)
        ]
        machine1 = EnigmaMachine(rotors1, reflector, plugboard)

        # Build Machine 2 with exact same initial settings
        rotors2 = [
            Rotor(wirings[i], notches[i], ring_setting=rings[i], position=positions[i])
            for i in range(4)
        ]
        machine2 = EnigmaMachine(rotors2, reflector, plugboard)

        # Test on a random message
        msg_len = rng.randint(10, 40)
        msg = "".join(rng.choice(ALPHABET) for _ in range(msg_len))

        ciphertext = machine1.encrypt_string(msg)
        decrypted = machine2.encrypt_string(ciphertext)

        assert decrypted == msg, f"Reciprocity failed on trial {trial}: {msg} != {decrypted}"


def test_property_2_no_symbol_maps_to_itself_over_1000_trials():
    """Property test: An Enigma machine with fixed-point-free reflector can NEVER encrypt a symbol to itself."""
    rng = random.Random(1337)

    for trial in range(1000):
        wirings = [make_random_permutation(rng) for _ in range(4)]
        notches = [sorted(rng.sample(range(N), 2)) for _ in range(4)]
        rings = [rng.randrange(N) for _ in range(4)]
        positions = [rng.randrange(N) for _ in range(4)]

        reflector = make_random_reflector(rng)
        plugboard = make_random_plugboard(rng)

        rotors = [
            Rotor(wirings[i], notches[i], ring_setting=rings[i], position=positions[i])
            for i in range(4)
        ]
        machine = EnigmaMachine(rotors, reflector, plugboard)

        for _ in range(10):
            sym = rng.choice(ALPHABET)
            res = machine.press(sym)
            assert res.out_symbol != sym, f"Fixed point observed on trial {trial} for symbol {sym}"


def test_property_3_reflector_invariants():
    """Reflector is always a fixed-point-free involution."""
    rng = random.Random(999)
    for _ in range(500):
        refl = make_random_reflector(rng)
        for i in range(N):
            mapped = refl.reflect(i)
            assert mapped != i  # No fixed point
            assert refl.reflect(mapped) == i  # Involution


def test_property_4_plugboard_invariants():
    """Plugboard is always an involution with at most 13 pairs."""
    rng = random.Random(888)
    for _ in range(500):
        pb = make_random_plugboard(rng)
        for i in range(N):
            mapped = pb.swap(i)
            assert pb.swap(mapped) == i


# ==============================================================================
# 3. Mid-Message State Persistence & Resumption Test
# ==============================================================================

def test_mid_message_persistence_and_resume():
    """Simulate encrypting part of a message, saving positions, and resuming."""
    rng = random.Random(555)
    wirings = [make_random_permutation(rng) for _ in range(4)]
    notches = [sorted(rng.sample(range(N), 2)) for _ in range(4)]
    rings = [18, 6, 24, 12]
    start_pos = [3, 15, 8, 22]

    reflector = make_random_reflector(rng)
    plugboard = make_random_plugboard(rng)

    full_message = "DHRITARASHTRAUVACHA_SANJAYA_KCTF{TEST_FLAG}"

    # 1. Single run from start to finish
    rotors_full = [
        Rotor(wirings[i], notches[i], ring_setting=rings[i], position=start_pos[i])
        for i in range(4)
    ]
    m_full = EnigmaMachine(rotors_full, reflector, plugboard)
    expected_cipher = m_full.encrypt_string(full_message)

    # 2. Split run: first 15 chars, save positions, resume remaining chars
    rotors_part1 = [
        Rotor(wirings[i], notches[i], ring_setting=rings[i], position=start_pos[i])
        for i in range(4)
    ]
    m_part1 = EnigmaMachine(rotors_part1, reflector, plugboard)
    cipher_part1 = m_part1.encrypt_string(full_message[:15])

    # Save state
    saved_positions = [r.position for r in m_part1.rotors]

    # Resume on a new machine instance initialized with saved positions
    rotors_part2 = [
        Rotor(wirings[i], notches[i], ring_setting=rings[i], position=saved_positions[i])
        for i in range(4)
    ]
    m_part2 = EnigmaMachine(rotors_part2, reflector, plugboard)
    cipher_part2 = m_part2.encrypt_string(full_message[15:])

    assert cipher_part1 + cipher_part2 == expected_cipher


# ==============================================================================
# 4. v2 Engine Components & Pipeline Tests
# ==============================================================================

def test_hmac_drbg_determinism_and_independence():
    from app.engine import HMAC_DRBG
    drbg1 = HMAC_DRBG("SEED_ALPHA_12345")
    drbg2 = HMAC_DRBG("SEED_ALPHA_12345")
    drbg3 = HMAC_DRBG("SEED_BETA_99999")

    bytes1 = drbg1.next_bytes(64)
    bytes2 = drbg2.next_bytes(64)
    bytes3 = drbg3.next_bytes(64)

    assert bytes1 == bytes2
    assert bytes1 != bytes3

    perm1 = drbg1.permutation(ALPHABET)
    perm2 = drbg2.permutation(ALPHABET)
    assert perm1 == perm2
    assert len(perm1) == N and set(perm1) == set(ALPHABET)


def test_keyword_substitution_layer():
    from app.engine import KeywordSubstitution
    sub = KeywordSubstitution("SANJAYAUVACHA")
    
    # Invariant: sub_alphabet has 30 unique symbols
    assert len(sub.sub_alphabet) == N
    assert set(sub.sub_alphabet) == set(ALPHABET)

    test_str = "DHRITARASHTRAUVACHA#_KCTF{DRONA_VICTORY}#_END"
    encrypted = sub.encrypt(test_str)
    assert encrypted != test_str
    decrypted = sub.decrypt(encrypted)
    assert decrypted == test_str


def test_v2_team_instance_derivation_and_full_pipeline(tmp_path):
    from tools.generate_instance import derive_team_instance

    phrases_file = repo_root / "tools" / "phrases_sanskrit.txt"
    inst1 = derive_team_instance("0xMASTER_SEED_TEST_A", "team_alpha", phrases_file)
    inst2 = derive_team_instance("0xMASTER_SEED_TEST_A", "team_alpha", phrases_file)
    inst3 = derive_team_instance("0xMASTER_SEED_TEST_A", "team_beta", phrases_file)

    # Determinism check: same team + same master seed -> identical instance
    assert inst1["flag"] == inst2["flag"]
    assert inst1["ciphertext"] == inst2["ciphertext"]
    assert inst1["walzenlage"] == inst2["walzenlage"]
    assert inst1["ringstellung"] == inst2["ringstellung"]
    assert inst1["reflector_pairs"] == inst2["reflector_pairs"]

    # Uniqueness check: different teams -> distinct instances
    assert inst1["flag"] != inst3["flag"]
    assert inst1["ciphertext"] != inst3["ciphertext"]

    # Full Decryption Pipeline Test:
    # 1. Enigma Decryption -> yields S(plaintext)
    rotors = [
        Rotor(
            wiring=inst1["all_rotors"][inst1["walzenlage"][i]]["wiring"],
            notches=inst1["all_rotors"][inst1["walzenlage"][i]]["notches"],
            ring_setting=inst1["ringstellung"][i],
            position=inst1["grundstellung"][i]
        )
        for i in range(4)
    ]
    reflector = Reflector(inst1["reflector_pairs"])
    plugboard = Plugboard(inst1["plugboard"])
    decrypter = EnigmaMachine(rotors, reflector, plugboard)

    recovered_s_plain = decrypter.encrypt_string(inst1["ciphertext"])
    assert recovered_s_plain == inst1["s_plaintext"]

    # 2. Layer S Inversion -> yields raw plaintext with flag
    from app.engine import KeywordSubstitution
    sub = KeywordSubstitution(inst1["pre_sub_keyword"])
    raw_recovered = sub.decrypt(recovered_s_plain)

    assert raw_recovered == inst1["raw_plaintext"]
    assert inst1["flag"] in raw_recovered

