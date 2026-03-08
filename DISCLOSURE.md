# Early Disclosure: IBC Denom Derivation and Delayed Action Capacity

## The 4-Line Attack Surface

```python
denom = f"{port_id}/{channel_id}/{address}"
return f"ibc/{hashlib.sha256(denom.encode('utf-8')).hexdigest().upper()}"
```

IBC denomination derivation is `SHA256(port/channel/address)`. This is:
- **Deterministic**: same inputs always produce the same denom
- **Pre-computable**: channel-ids are sequential counters (`channel-0`, `channel-1`, ...)
- **No authentication**: the hash doesn't bind to a validator set or chain state

You can compute every `ibc/...` denom for every future channel before it exists.

This package (`shitcoin`) was published in 2022 as an educational tool to make
this derivation transparent. The tests verify known denoms for MARBLE, RAC, DOG,
and HABERMAS tokens on `channel-169` (Juno -> Osmosis).

## From Possible Worlds to Necessary Neighbors

In normal operation, IBC channels are like possible worlds in modal logic:
any chain *could* be on the other end, but social consensus and validator
economics constrain the space to well-known counterparties. The channel is
a name for a relationship, and the relationship is authenticated socially.

During a migration, possible worlds collapse to necessary neighbors. Noble
has issued ~$250M USDC via Cosmos IBC. When Noble EVM goes live (March 18,
2026), every chain with an IBC channel to Noble becomes a *necessary*
neighbor -- not by choice, but by the fact that their `ibc/SHA256(...)` denoms
resolve to the same strings regardless of which execution layer or validator
set is on the Noble end.

The denom doesn't know who its neighbor is. It only knows the string
`transfer/channel-N/uusdc`. In modal terms: the accessibility relation
between worlds (channels) has no authentication predicate. Every world
that can produce the right port/channel/denom string is an equally valid
neighbor. IBC is permissionless by design, but permissionless accessibility
means you cannot distinguish the actual world from any possible world that
shares the same channel coordinates.

This matters concretely:

1. The chain identity is defined by its channel-id and port-id
2. A new validator set is being bootstrapped on EVM
3. The old IBC channels must be preserved for continuity of the ~$250M
4. The denom derivation produces identical hashes regardless of which
   validator set is on the other end

The Kripkean framing is not decorative. It identifies the exact failure mode:
IBC's accessibility relation is symmetric and transitive but not authenticated.
Any world accessible via `channel-N` is treated as the same neighbor. The
migration makes this concrete by changing who is actually on the other end
while preserving the channel name.

## The Actual Vulnerability

The vulnerability was always there. `shitcoin` published the derivation
function in 2022 so anyone could see it. The IBC denom is a hash of a
predictable string. The security assumption was never "this hash is hard
to compute" -- it was "nobody will bother to set up a fake chain on the
other end of a channel."

That assumption holds when:
- Running a validator set is expensive
- There is social consensus about which chain owns which channel
- Migrations don't happen

That assumption breaks when:
- Validator sets can be spun up cheaply (cloud, ephemeral)
- Chains migrate execution layers (identity becomes ambiguous)
- The social layer fragments (which is happening)

This is a protocol-level issue, not a cryptographic one. SHA256 is not
the weak link. The weak link is that channel identity is a string, not
a proof.

## Delayed Action Capacity

The protocol-level weakness has a specific temporal structure: you can
pre-compute every future IBC denom today and act on that knowledge later.
This is delayed action capacity -- the ability to prepare an attack
surface now and exploit it when conditions change.

Concretely:
- Enumerate `channel-0` through `channel-N` for any plausible N
- Compute `SHA256(transfer/channel-K/uusdc)` for each
- Wait for a migration window (CosmWasm -> EVM, validator set rotation,
  social consensus fragmentation)
- Stand up infrastructure on the other end of a channel whose denom
  you already know

The cost of pre-computation is negligible. The cost of exploitation
scales with the cost of running a validator set -- which is falling.
The window of opportunity is the migration itself.

This is distinct from a cryptographic attack. No hash needs to be broken.
The denom derivation is working exactly as specified. The issue is that
"working as specified" means channel identity is a predictable string,
not a bound proof of who is on the other end.

### Multiscale Unfolding

The exploitability of this surface is not a single threshold event. It
unfolds across timescales that are coupled but not causally chained:

| Scale | Parameter | Rate |
|-------|-----------|------|
| Seconds | Denom pre-computation | Instant, O(N) for N channels |
| Days | Validator set bootstrap | Cloud spin-up, declining cost |
| Weeks | Migration window | Governance-gated, publicly announced |
| Months | Social consensus on channel ownership | Fragmentation is monotonic |
| Years | Cryptographic margin erosion | Independent research fronts |

The curve of exploitability is the envelope over these scales, not the
product of their probabilities. An attacker only needs one scale to be
favorable -- the fastest-unfolding parameter at any given moment sets the
actual risk.

Previous versions of this document presented these scales as a causal
chain (each feeding the next). That framing is wrong. They are independent
parameters of a multiscale unfolding. The vulnerability surface is the
supremum over the individual curves, not their composition.

The practical consequence: defending only at the cryptographic scale
(post-quantum hashes) leaves the faster-unfolding scales (cheap validators,
migration windows, social fragmentation) completely unaddressed. The fix
must operate at the fastest scale -- which is the protocol level.

## On the Quantum Timeline (Epistemic Status: Speculative)

Several recent results are individually noteworthy:

- **AlphaEvolve** (DeepMind, 2025): 4x4 matrix multiplication in 48
  multiplications, breaking Strassen's 56-year record by ~2%
- **Keccak preimage** (December 2025): quantum attack reduces complexity
  from 2^57.8 to 2^28.9, requiring ~3,200 logical qubits (~3.2M physical)
- **JVG algorithm**: reduces qubit requirements for RSA by ~1000x vs
  prior estimates

These are independent results. They do not compose into a causal chain.
A 2% improvement in matrix multiplication does not "compound exponentially
through all of cryptography" -- that framing treats each conditional
improvement as a confirmed premise for the next step, making the joint
probability appear far higher than the product of the individual
conditionals warrants.

What can be said without overclaiming:
- SHA256 preimage resistance is large today (2^256)
- Multiple independent lines of research are reducing security margins
  on related primitives
- The rate of reduction is not predictable from any single result
- The protocol-level issue (unauthenticated channel identity) does not
  require any cryptographic break to exploit -- it is the immediate concern

## What Zero-Copy Verification Changes

ZK IBC (zero-knowledge IBC) eliminates the attack surface:
- Channel identity is bound to a validity proof, not a hash of a string
- The proof covers the state transition, not just the denomination
- Pre-computation doesn't help because the proof includes the current state
- Ghost chains can't produce valid proofs of state they don't have

This is the same insight as flicks vs floating-point:
- **Message passing** (IBC channels): trust the channel identifier (drifts)
- **Algebraic identity** (ZK proofs): verify the math (can't drift)

The integer path (flicks, ZK proofs) is correct by construction.
The string path (f64 accumulation, SHA256 of predictable inputs) drifts.

## Responsible Disclosure Note

This document describes publicly known protocol mechanics. The IBC denom
derivation is specified in [ICS-020](https://github.com/cosmos/ibc/tree/main/spec/app/ics-020-fungible-token-transfer)
and implemented in every IBC-compatible chain. The `shitcoin` package has
been on PyPI since 2022. No novel exploit code is included here.

The purpose of this disclosure is to:
1. Make the unauthenticated channel identity explicit during migration windows
2. Motivate adoption of ZK IBC and authenticated channel identity
3. Separate the protocol-level concern (exploitable today) from the
   cryptographic concern (speculative timeline)

## References

- [ICS-020: Fungible Token Transfer](https://github.com/cosmos/ibc/tree/main/spec/app/ics-020-fungible-token-transfer)
- [AlphaEvolve: 48-mult 4x4 matrix multiplication](https://deepmind.google/blog/alphaevolve-a-gemini-powered-coding-agent-for-de...)
- [Quantum Attack on Keccak/SHA-3: 2^28.9 preimage](https://quantumzeitgeist.com/quantum-security-attack-reduces-keccak-sha-preimage-complexity/)
- [JVG Algorithm: 1000x fewer qubits for RSA](https://www.abhs.in/blog/quantum-computing-rsa-encryption-threat-march-2026)
- [Noble Chain](https://www.noble.xyz/)
- [Noble EVM migration announcement](https://www.kucoin.com/news/flash/cosmos-stablecoin-project-noble-migrates-to-evm-l1-sparks-exit-trend) (January 20, 2026)
- [ZK IBC](https://github.com/cosmos/ibc/discussions) (various proposals)
- Kripke, S. (1963). Semantical Considerations on Modal Logic. *Acta Philosophica Fennica* 16: 83-94
