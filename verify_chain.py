#!/usr/bin/env python3
"""Verify a Saluca tamper-evident hash chain. Independent, offline, no Saluca code.

    python verify_chain.py sample-chain.jsonl --pubkey operating-key.pub
    python verify_chain.py --self-test

WHAT THIS IS FOR. Saluca says its agents keep a hash-chained record, so that corruption is
detectable rather than silent. That is a claim about a data structure, and a claim about a data
structure can be checked by a stranger. This script is the stranger's copy.

IT DELIBERATELY IMPORTS NOTHING FROM SALUCA. It re-derives every hash from the format described in
CHAIN-FORMAT.md, using the Python standard library. If it agreed with the producer because it
shared the producer's code, it would prove nothing at all. `--self-test` is the other half of that:
it builds a valid chain, breaks it four different ways, and fails if any break goes undetected.

WHAT A PASS MEANS: this file is internally consistent, every block hashes to its stated hash, every
link points at its predecessor, and (with --pubkey) the signatures are real signatures by the
holder of that key.

WHAT A PASS DOES NOT MEAN: that the events described ever happened, or that any particular system
produced them. A hash chain proves a record has not been altered since it was written. It cannot
prove the record was true when written. Anyone claiming otherwise, including Saluca, is overselling
it.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys

GENESIS_ROOT = "hctp-genesis-v1"
SEP = b"\x1e"          # the record separator between hashed parts
BODY_FIELDS = ("seq", "ts", "kind", "payload", "prev_hash")


def body_hash(block: dict) -> str:
    """SHA-512 over the canonical JSON body. See CHAIN-FORMAT.md.

    `hash` and `sig` are excluded by construction: a block cannot commit to its own hash, and the
    signature is attached after sealing, so including it would break every chain on signing.
    """
    body = json.dumps({k: block[k] for k in BODY_FIELDS},
                      sort_keys=True, separators=(",", ":"))
    m = hashlib.sha512()
    m.update(body.encode("utf-8"))
    m.update(SEP)
    return m.hexdigest()


def load_pubkey(path: str):
    """Ed25519 public key, PEM. Returns None if `cryptography` is missing."""
    try:
        from cryptography.hazmat.primitives.serialization import load_pem_public_key
    except ImportError:
        return None
    with open(path, "rb") as fh:
        return load_pem_public_key(fh.read())


def verify(blocks: list[dict], pubkey=None) -> tuple[bool, list[str]]:
    """Return (ok, findings). Findings are recorded for every block, not just the first failure."""
    findings: list[str] = []
    prev = GENESIS_ROOT
    for i, b in enumerate(blocks):
        missing = [f for f in (*BODY_FIELDS, "hash") if f not in b]
        if missing:
            findings.append(f"block {i}: missing field(s) {missing}")
            return False, findings
        if b["seq"] != i:
            findings.append(f"block {i}: seq is {b['seq']}, expected {i}")
        if b["prev_hash"] != prev:
            findings.append(f"block {i}: broken link, prev_hash does not match block {i - 1}")
        want = body_hash(b)
        if b["hash"] != want:
            findings.append(f"block {i}: content altered, hash {b['hash'][:16]}... "
                            f"does not match its body ({want[:16]}...)")
        prev = b["hash"]

        sig = b.get("sig") or ""
        if pubkey is not None:
            if not sig:
                findings.append(f"block {i}: unsigned")
            else:
                try:
                    pubkey.verify(bytes.fromhex(sig), b["hash"].encode("ascii"))
                except Exception:
                    findings.append(f"block {i}: signature does not verify under this key")
    return not findings, findings


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("chain", nargs="?", help="chain file, one JSON block per line")
    ap.add_argument("--pubkey", help="Ed25519 public key PEM; without it signatures are NOT checked")
    ap.add_argument("--self-test", action="store_true", help="prove this verifier can fail")
    a = ap.parse_args(argv)

    if a.self_test:
        return self_test()
    if not a.chain:
        ap.error("give a chain file, or --self-test")

    with open(a.chain, encoding="utf-8") as fh:
        blocks = [json.loads(line) for line in fh if line.strip()]

    pubkey = None
    if a.pubkey:
        pubkey = load_pubkey(a.pubkey)
        if pubkey is None:
            print("! the `cryptography` package is not installed, so SIGNATURES WERE NOT CHECKED.")
            print("  pip install cryptography, then run this again. Hashes are still checked.")

    ok, findings = verify(blocks, pubkey)
    print(f"blocks     : {len(blocks)}")
    print(f"head       : {blocks[-1]['hash'][:32] + '...' if blocks else '(empty)'}")
    print(f"signatures : {'checked' if pubkey else 'NOT CHECKED (no --pubkey)'}")
    for f in findings:
        print("  FAIL:", f)
    print("RESULT     :", "chain intact" if ok else "CHAIN FAILS VERIFICATION")
    return 0 if ok else 2


def self_test() -> int:
    """Build a chain, break it four ways, and require every break to be caught."""
    import copy

    good = []
    prev = GENESIS_ROOT
    for i, kind in enumerate(("genesis", "policy_decision", "memory_write")):
        b = {"seq": i, "ts": 1757000000.0 + i, "kind": kind,
             "payload": {"n": i, "note": "self-test"}, "prev_hash": prev}
        b["hash"] = body_hash(b)
        good.append(b)
        prev = b["hash"]

    ok, findings = verify(good)
    if not ok:
        print("SELF-TEST FAILED: a valid chain did not verify:", findings)
        return 1

    cases = {}
    c = copy.deepcopy(good); c[1]["payload"]["note"] = "edited after the fact"
    cases["edited payload"] = c
    c = copy.deepcopy(good); c[2]["prev_hash"] = "0" * 128
    cases["broken link"] = c
    c = copy.deepcopy(good); del c[1]
    cases["deleted block"] = c
    c = copy.deepcopy(good); c[1], c[2] = c[2], c[1]
    cases["reordered blocks"] = c

    bad = [name for name, chain in cases.items() if verify(chain)[0]]
    for name, chain in cases.items():
        print(f"  {name:18} -> {'NOT DETECTED' if verify(chain)[0] else 'detected'}")
    if bad:
        print("SELF-TEST FAILED: these tampering cases passed verification:", bad)
        return 1
    print("SELF-TEST PASSED: valid chain verifies, and all four tampering cases are caught.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
