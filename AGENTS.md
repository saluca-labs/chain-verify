# AGENTS.md

Instructions for AI coding agents working in this repository.

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
- No em-dashes in docs. If README.md or CHAIN-FORMAT.md changes, regenerate `llms-full.txt`.

## Do not

- Edit `sample-chain.jsonl` or `operating-key.pub`. They are the signed published sample; any edit
  breaks verification, which is the point.
- Commit secrets, hostnames, internal paths or personal emails.

## Done means

The self-test passes, the sample verifies with `--pubkey operating-key.pub`, and a tampered copy
exits non-zero.
