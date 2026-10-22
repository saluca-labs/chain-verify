# AGENTS.md

Instructions for AI coding agents working in this repository.

## What this is

A kit for checking a Saluca hash chain without trusting Saluca: the format, a five-block signed sample, its public key, and one Python verifier that shares no code with the producer. It is a verification artifact, not a library and not the producer.

## Read in this order

1. [README.md](README.md): the correction note at the top, then "How it works" and "What a pass proves, and what it does not".
2. [CHAIN-FORMAT.md](CHAIN-FORMAT.md): the block, the hash, genesis and the four verification rules.
3. [verify_chain.py](verify_chain.py): `body_hash()`, `verify()`, `main()` and `self_test()`, about 160 lines.
4. [.github/workflows/verify.yml](.github/workflows/verify.yml): what CI requires.

## What you can and cannot see

- You can see the whole verifier, the format, the sample and its public key.
- You cannot see the producer that wrote the sample. It is closed source and deliberately not here: the verifier's value is that it shares no code with what it checks.
- The private key that signed the sample was discarded. Nobody can add a validly signed block to it.
- The events in the sample are invented; the code path that wrote them is real.

## Using it as an agent

```bash
python verify_chain.py <chain.jsonl> --pubkey <key.pub>   # exit 0 intact, 2 fails (or usage error)
python verify_chain.py --self-test                         # exit 0 passed, 1 failed
```

Read the `signatures :` line, not only `RESULT`: without `--pubkey`, or without `cryptography`, a chain can print `chain intact` with signatures unchecked.

## The only numbers to trust

| Number | Value | Source |
|---|---|---|
| Blocks in the sample | 5 | `sample-chain.jsonl`, one block per line |
| Hash | SHA-512, 128 hex characters | `body_hash()` in `verify_chain.py`, "The hash" in `CHAIN-FORMAT.md` |
| Tampering cases in the self-test | 4 | `cases` in `self_test()` |
| Exit codes | 0, 1, 2 | `main()` and `self_test()` in `verify_chain.py`; argparse usage errors also exit 2 |
| Tested runtime | Python 3.12.10, `cryptography` 50.0.2 | README "Install" (CI uses Python 3.12, `cryptography>=49.0.0`) |

## Setup

```bash
pip install cryptography      # only for the signature check
```

## Test

```bash
python verify_chain.py --self-test
python verify_chain.py sample-chain.jsonl --pubkey operating-key.pub
```

Passing looks like: the self-test prints `detected` for all four cases and `SELF-TEST PASSED`, and
the sample prints `signatures : checked` and `RESULT     : chain intact`, exit 0. CI
(`.github/workflows/verify.yml`) also requires a copy with `"bytes": 412` changed to be rejected.

## Conventions

- The default branch is `verify-artifact`. Target pull requests at it.
- `verify_chain.py` is written from `CHAIN-FORMAT.md` and must import nothing but the standard
  library and, optionally, `cryptography`. Never import, vendor or copy producer code: the
  verifier's value is that it shares no code with what it checks.
- A new check needs a matching tampering case in `--self-test` that fails without it.
- The README diagram is Mermaid source drawn from `verify()`. Change it when the walk changes.
- No em-dashes in docs. If README.md or CHAIN-FORMAT.md changes, regenerate `llms-full.txt`.

## Do not

- Edit `sample-chain.jsonl` or `operating-key.pub`. They are the signed published sample; any edit
  breaks verification, which is the point.
- Describe a pass as proving more than the README's "What a pass proves" section says.
- Commit secrets, hostnames, internal paths or personal emails.

## Done means

The self-test passes, the sample verifies with `--pubkey operating-key.pub`, and a tampered copy
exits non-zero.
