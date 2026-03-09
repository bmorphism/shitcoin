# world://noble-1 — Colored Identity for IBC Channel Authentication

## The Bridge

The `shitcoin` disclosure identifies a specific failure: IBC channel identity
is `SHA256(string)` with no authentication predicate. The `did:gay` protocol
and `world://` URI scheme provide the missing predicate.

## Color Assignment

Each concept in the disclosure has a deterministic color via Share3 hash:

| Concept | Color | Trit | URI |
|---------|-------|------|-----|
| shitcoin | `#C5F120` | +1 (Generator) | `skill://shitcoin#C5F120` |
| noble-ibc | `#38B861` | 0 (Ergodic) | `skill://noble-ibc#38B861` |
| delayed-action-capacity | `#2CA64A` | +1 (Generator) | `skill://delayed-action-capacity#2CA64A` |
| necessary-neighbors | `#801ED0` | -1 (Validator) | `skill://necessary-neighbors#801ED0` |
| multiscale-unfolding | `#9AE013` | 0 (Ergodic) | `skill://multiscale-unfolding#9AE013` |
| alien-in-the-fstring | `#EB7CDE` | -1 (Validator) | `skill://alien-in-the-fstring#EB7CDE` |
| context-defragmentation | `#61DDC2` | 0 (Ergodic) | `skill://context-defragmentation#61DDC2` |

The triad `{shitcoin(+1), necessary-neighbors(-1), alien-in-the-fstring(-1)}`
sums to -1. Needs a +1 skill to balance. The GF(3) structure says: two
validators and a generator need another generator to close the quad.

## What world:// Adds to IBC

### Current IBC Channel Identity

```
channel_identity = SHA256("transfer/channel-N/uusdc")
type: (str, str, str) -> str
```

No color. No trit. No proof. The alien hides in the f-string.

### world:// Channel Identity

```
world://noble-1/channel/750
  ├── did:gay:<noble-validator-set-hash>
  │   ├── color: deterministic from validator set
  │   ├── trit: GF(3) role classification
  │   └── agentType: "autonomous" (chain is an agent)
  ├── state_proof: ZK validity proof of current Noble state
  ├── execution_layer: "evm" | "cosmwasm"
  └── denom: ibc/498A0751... (same hash, but now BOUND to proof)
```

The denom is still `SHA256(transfer/channel-750/uusdc)`. The hash doesn't
change. What changes: the world:// URI binds the channel to a `did:gay`
identity derived from the validator set, which carries a deterministic
color and GF(3) trit. The color is the authentication predicate the
f-string lacks.

### Migration Detection

```
Before March 18:
  world://noble-1/channel/750
    did:gay:abc123... → color: #38B861 (cosmwasm validator set)
    execution_layer: "cosmwasm"

After March 18:
  world://noble-1/channel/750  
    did:gay:xyz789... → color: #E04532 (evm validator set)
    execution_layer: "evm"

Color changed. Identity changed. Channel name didn't.
The world:// protocol makes this visible.
The IBC denom alone makes it invisible.
```

### The 7 Causal Chains, Colored

Using the golden thread (φ-spiral, 137.508° per step):

| Chain | Hue | Color | Finding |
|-------|-----|-------|---------|
| 1. Denom collisions | 0° | `#DD3C3C` | 15 chains share channel-0 USDC denom |
| 2. 205 numbered ICA | 137.5° | `#3CDD6B` | Remote execution from unknown origin |
| 3. Wormhole port | 275.0° | `#9A3CDD` | CosmWasm dependency on chain removing CosmWasm |
| 4. Oraichain dual wasm | 52.5° | `#DDC93C` | Shadow channel collides with injective |
| 5. Osmosis TRYOPEN flood | 190.0° | `#3CC2DD` | 30 half-open channels, one address |
| 6. channel-121 INIT | 327.5° | `#DD3C93` | No counterparty, open to claim |
| 7. 96 shadow channels | 105.0° | `#64DD3C` | 62% of transfer surface undocumented |

Golden angle ensures maximum perceptual dispersion. No two adjacent
causal chains share similar colors. The spiral never repeats.

## did:gay for IBC Channels

Each IBC channel can be assigned a `did:gay` identity:

```
did:gay:<base32(sha256(dag-cbor({
  chain_id: "noble-1",
  channel_id: "channel-750",
  counterparty_chain_id: "osmosis-1",
  counterparty_channel_id: "channel-1",
  validator_set_hash: <current_validator_set_hash>,
  execution_layer: "cosmwasm" | "evm",
  timestamp: <block_height>
})))>
```

The `did:gay` color for a channel changes when the validator set changes.
This is the authentication predicate. If the color changes, the neighbor
changed. The denom stays the same but the identity doesn't.

### Counterfactual Perception (world:// protocol)

From the World Protocol Agent Perception spec:

```
world://noble-1/channel/750/healthy
  └── Noble EVM is running, validator set matches did:gay color
  └── USDC transfers resolve correctly

world://noble-1/channel/750/migrating
  └── Execution layer transition in progress
  └── Validator set rotating
  └── did:gay color is changing — neighbor identity in flux

world://noble-1/channel/750/alien
  └── Possible world where channel-750 is claimed by unknown entity
  └── Same denom. Different did:gay. Different color.
  └── The hash can't tell. The color can.
```

## The Quad

To balance the disclosure triad `{shitcoin(+1), necessary-neighbors(-1),
alien-in-the-fstring(-1)}` (sum = -1), the balancing skill must have
trit = +1.

`delayed-action-capacity` has trit = +1.

```
shitcoin(+1) + necessary-neighbors(-1) + alien-in-the-fstring(-1) + delayed-action-capacity(+1)
= +1 + (-1) + (-1) + (+1)
= 0 (mod 3)

Balanced quad. GF(3) conservation holds.
```

The generator skills (shitcoin, delayed-action-capacity) create the
attack surface and the temporal structure. The validator skills
(necessary-neighbors, alien-in-the-fstring) identify what's broken.
The sum is zero: the disclosure is complete.
