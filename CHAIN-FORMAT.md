# The chain format, in enough detail to write your own verifier

Everything here is what you need to check a chain yourself. Nothing in it depends on Saluca code,
and `verify_chain.py` in this directory was written from this page rather than the other way round.

## A block

One JSON object per line. Order in the file is the order in the chain.

```json
{"seq": 1, "ts": 1789600012.0, "kind": "policy_decision",
 "payload": {"decision": "deny", "actor": "agent:demo-01"},
 "prev_hash": "<hash of block 0>", "hash": "<this block's hash>", "sig": "<hex Ed25519>"}
```

| Field | Meaning |
|---|---|
| `seq` | position, starting at 0. Block 0 is the genesis block |
| `ts` | Unix seconds, float |
| `kind` | event type, free text (`genesis`, `policy_decision`, `memory_write`, ...) |
| `payload` | the event. Any JSON object |
| `prev_hash` | the `hash` of the previous block. For block 0, the literal `hctp-genesis-v1` |
| `hash` | SHA-512 over the body, below |
| `sig` | optional. Ed25519 over the ASCII bytes of `hash`, hex encoded |

## The hash

    body   = json({seq, ts, kind, payload, prev_hash}, sorted keys, separators "," and ":")
    hash   = SHA-512( utf8(body) || 0x1E )

Three details a re-implementation gets wrong if nobody writes them down:

1. **`hash` and `sig` are not in the body.** A block cannot commit to its own hash, and the
   signature is attached after the block is sealed, so including either would mean every signature
   broke the chain it was signing.
2. **Keys are sorted and the separators are tight** (`,` and `:`, no spaces). Canonical JSON, so
   two implementations hash the same bytes.
3. **One 0x1E byte is appended** after the body before hashing. It is the ASCII record separator.
   Miss it and every hash you compute is wrong in a way that looks like tampering.

## Genesis

Block 0 has `kind: "genesis"` and `prev_hash: "hctp-genesis-v1"`, and its payload carries:

- `constitution_hash`: what the entity was sealed against
- `operating_pubkey`: the raw hex Ed25519 public key that signs blocks
- `root_before`: `hctp-genesis-v1`

Anchoring the key in block 0 means a chain that switches signing keys mid-way cannot do so
silently: the key is part of the hashed record.

## Verifying

For each block, in order:

1. `seq` equals its index.
2. `prev_hash` equals the previous block's `hash` (or `hctp-genesis-v1` at index 0).
3. Recomputing the body hash gives `hash`.
4. If a public key is supplied, `sig` verifies over `hash`.

Any single failure fails the chain. A deleted block breaks rule 1 and rule 2, a reordering breaks
both, an edit breaks rule 3, and a forged block without the key breaks rule 4.

## What this format does and does not give you

It gives you **tamper evidence**: nothing in a chain you already hold can be changed without the
change showing.

It does not give you **tamper resistance**, and it never claimed to. Whoever holds the signing key
can write whatever they like into new blocks, and whoever holds the file can throw the file away.
What the structure guarantees is that quiet editing is not one of their options.

It also says nothing about whether the recorded events are TRUE. A chain records that something was
written and when, relative to everything else in the chain. Truth of content is a separate problem,
and anyone selling a hash chain as a solution to it is selling something else.
