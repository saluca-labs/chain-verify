# Check the chain yourself

Saluca says its agents keep a hash-chained record, so corruption is detectable rather than silent.
That is a claim about a data structure, and a claim about a data structure is one a stranger can
check. This repository is the stranger's copy: a sample chain, the public key it was signed with,
the format written out in full, and a verifier that imports none of our code.

```
python verify_chain.py sample-chain.jsonl --pubkey operating-key.pub
```

```
blocks     : 5
head       : 860a6a062930ceaedb51db1fbfc20429...
signatures : checked
RESULT     : chain intact
```

Now break it. Change one number in one payload, say `"bytes": 412` to `"bytes": 999999`, and run it
again:

```
  FAIL: block 2: content altered, hash 2d6b4a18c4a1deaa... does not match its body (ebba0d90785be201...)
RESULT     : CHAIN FAILS VERIFICATION
```

Exit code 2. That is the whole point of the structure, and it took one edit to demonstrate.

## Prove the verifier can fail before you trust it

```
python verify_chain.py --self-test
```

It builds a valid chain, then breaks it four ways: an edited payload, a broken link, a deleted
block, and two blocks swapped. If any of them verified, the self-test fails and says so. A checker
that has never been seen to fail is not evidence of anything.

`cryptography` is needed for the signature check (`pip install cryptography`). Without it the
hashes are still checked and the output says, in those words, that signatures were not.

## What a pass proves, and what it does not

**It proves** this file is internally consistent: every block hashes to its stated hash, every link
points at its predecessor, and each signature was made by the holder of the key in block 0.

**It does not prove** that the events described ever happened, or that any particular system
produced them. A hash chain shows a record has not been altered since it was written. It cannot
show the record was true when written. We would rather say that here than have you discover it.

**The sample is a demonstration, not an export.** The events in it are invented, and the key was
generated for this file and then discarded. What is real is the code path: the chain was produced
by the same implementation that runs in the product, not by a script written to make this sample
verify. That implementation is not open source; the format is, which is why `verify_chain.py` is
written from [CHAIN-FORMAT.md](CHAIN-FORMAT.md) and shares nothing with it.

If you want the stronger version of this artifact, a signed export from a live system with a
published key, say so. It is a reasonable thing to ask for and we do not have it published yet.

## Files

| File | What it is |
|---|---|
| `verify_chain.py` | the verifier, standard library plus optional `cryptography`, about 150 lines |
| `CHAIN-FORMAT.md` | the format, in enough detail to write your own verifier and disagree with ours |
| `sample-chain.jsonl` | five blocks, produced by the production implementation |
| `operating-key.pub` | the Ed25519 public key, PEM |

## Why this exists

Asked on 2026-09-16 what would make the claim "our agents keep a tamper-evident record" checkable
by someone who does not trust us, the honest answer was: publish the format, publish a signed
sample, and publish a verifier that does not share our code. So here it is.
