# Noble Validator Set: OSI Recon + Heterogeneous Design

Reconnaissance of the `noble-1` validator set across all OSI layers,
followed by a heterogeneous validator set specification that breaks
every monoculture surface found.

## Census (2026-03-09, block ~46,466,703)

| Category | Count |
|----------|-------|
| Bonded validators | 18 |
| Unbonded validators | 5 (strangelove, Notional, Everstake, a41, B-Harvest) |
| Unbonding | 0 |
| Observable P2P peers | 75 |
| Unique public IPs | 74 |

All 18 bonded validators hold exactly **1,000,000 tokens each**.
This is a permissioned set with uniform stake -- no market-driven
validator selection. Noble chooses who validates.

## Layer 7: Application

### Software Monoculture

| Component | Version | Penetration |
|-----------|---------|-------------|
| nobled | v11.2.0 | 100% of validators |
| CometBFT | v0.38.19 | 97% of peers (74/76) |
| CometBFT | v0.38.17 | 1 peer (SG-1) |
| CometBFT | v0.0.1 | 1 peer (unknown) |
| Go runtime | go1.24.12 | 100% (from build info) |
| Cosmos SDK | v0.45.16-send-restrictions | 100% |
| IBC-Go | v4.6.0 | 100% |
| Key algorithm | ed25519 | 100% (consensus_pubkey) |
| CosmWasm | disabled | 100% |

**Finding**: Complete application-layer monoculture. A single bug in
CometBFT v0.38.19 or Go 1.24.12 takes the entire chain offline.
Zero client diversity (cf. Ethereum's Geth/Lighthouse/Prysm/Teku/Nimbus).

### Consensus Parameters

```
max_block_bytes:   5,242,880 (5 MB)
max_gas:           30,000,000
evidence_max_age:  100,000 blocks (~6.9 days)
evidence_max_bytes: 1,048,576 (1 MB)
pub_key_types:     [ed25519]
```

### Slashing State

- 24 signing infos (18 bonded + 5 unbonded + 1 historical)
- 517 total missed blocks across all validators
- 9 jailed validators (currently non-bonded)
- 0 tombstoned
- Worst offender: 196 missed blocks (still bonded)

## Layer 4-5: Transport / Session

### Protocol

| Protocol | Count | Percentage |
|----------|-------|-----------|
| TCP (CometBFT P2P) | 76/76 | 100% |
| QUIC | 0 | 0% |
| WebSocket | 0 | 0% |

### Port Distribution

| Port | Count | Note |
|------|-------|------|
| 26656 (default) | 31 | CometBFT default P2P |
| 21556 (polkachu convention) | 16 | Polkachu-operated or following their guide |
| Custom ports | 29 | Various non-standard |

### Listen Address Patterns

| Pattern | Count |
|---------|-------|
| `0.0.0.0` (all interfaces) | 40 (53%) |
| Bare IP (specific) | 33 (43%) |
| `tcp://` prefix | 3 (4%) |

**Finding**: 53% of nodes bind to all interfaces. No QUIC, no
alternative transports, no onion routing, no mixnet. The entire
P2P layer is cleartext TCP with CometBFT's SecretConnection
(Diffie-Hellman + ChaCha20-Poly1305). A single TLS/transport
vulnerability is chain-wide.

## Layer 3: Network

### Geographic Distribution

| Country | Nodes | % |
|---------|-------|---|
| DE (Germany) | 27 | 36% |
| FI (Finland) | 16 | 22% |
| US | 9 | 12% |
| CA (Canada) | 5 | 7% |
| FR (France) | 5 | 7% |
| HK | 2 | 3% |
| LT | 2 | 3% |
| NL | 2 | 3% |
| SG | 2 | 3% |
| AT, MT, SE, IN | 1 each | 1% each |

**Finding**: 58% of nodes in DE+FI. A single EU regulatory action or
submarine cable cut between Helsinki and Frankfurt partitions the majority.

### ASN Concentration

| ASN | Operator | Nodes | % |
|-----|----------|-------|---|
| AS24940 | **Hetzner Online GmbH** | **32** | **43%** |
| AS16276 | OVH SAS | 6 | 8% |
| AS14061 | DigitalOcean | 5 | 7% |
| AS197540 | netcup GmbH | 4 | 5% |
| AS16509 | Amazon (AWS) | 4 | 5% |
| AS45102 | Alibaba Cloud | 2 | 3% |
| AS16125 | Cherry Servers | 2 | 3% |
| AS14618 | Amazon (AWS) | 2 | 3% |
| AS396982 | Google Cloud | 1 | 1% |
| AS8075 | Microsoft Azure | 1 | 1% |
| Others | Various | 15 | 20% |

**Finding**: Hetzner alone hosts 43% of all Noble P2P nodes.
Hetzner + OVH + DigitalOcean = 58%. A single Hetzner AUP change
(as happened with Ethereum staking in 2022) disrupts consensus.

AWS total (AS16509 + AS14618) = 6 nodes (8%).
Top-3 ASNs control 58% of the network.

## Layer 1-2: Physical / Data Link

### Architecture

| Architecture | Count | Source |
|-------------|-------|--------|
| linux/amd64 | 100% | Go build info: `go1.24.12 linux/amd64` |
| linux/arm64 | 0% | - |
| Other | 0% | - |

### Hosting Classification

| Type | Count | % |
|------|-------|---|
| Datacenter/hosting | 67 | 91% |
| Residential/other | 7 | 9% |

**Finding**: 100% x86_64. Zero ARM nodes. A microarchitectural
vulnerability (Spectre/Meltdown class) in Intel/AMD affects every
node simultaneously. No hardware diversity whatsoever.

The 7 "residential" IPs are likely misclassified VPN endpoints or
small hosting providers, not actual home hardware.

### Hetzner Specific Risk

Hetzner's 32 nodes are concentrated in two datacenters:
- **Falkenstein (DE)**: majority of DE Hetzner nodes
- **Helsinki (FI)**: all FI Hetzner nodes

Both datacenters share:
- Same BGP peering policies
- Same abuse team / AUP enforcement
- Same maintenance windows
- Same power grid region (EU)

## Monoculture Summary

```
┌──────────────────────────────────────────────────────────┐
│ OSI LAYER          MONOCULTURE SURFACE       SEVERITY    │
├──────────────────────────────────────────────────────────┤
│ L7 Application     nobled v11.2.0            CRITICAL    │
│                    CometBFT v0.38.19         CRITICAL    │
│                    Go 1.24.12                HIGH        │
│                    Cosmos SDK v0.45.16       CRITICAL    │
│                    ed25519 only              MEDIUM      │
│                                                          │
│ L4 Transport       TCP only                  HIGH        │
│                    SecretConnection only     MEDIUM      │
│                    No QUIC/onion/mixnet      HIGH        │
│                                                          │
│ L3 Network         43% Hetzner (1 ASN)       CRITICAL    │
│                    58% DE+FI (2 countries)   HIGH        │
│                    91% datacenter hosting    HIGH        │
│                                                          │
│ L1-2 Physical      100% x86_64              HIGH        │
│                    100% Linux                MEDIUM      │
│                    0% ARM / RISC-V           HIGH        │
└──────────────────────────────────────────────────────────┘
```

Every layer is a single point of failure. The chain has
**zero client diversity** at any OSI level.

---

## Heterogeneous Validator Set Specification

Break every monoculture surface. The design principle:
**no single bug, vendor, jurisdiction, ISP, architecture,
or software version can take >33% of stake offline**.

### Target: 27 Validators (3x9 Triad Structure)

GF(3) balanced: 9 validators per trit class.

| Trit | Role | Count |
|------|------|-------|
| +1 (PLUS) | Block producers (primary signers) | 9 |
| 0 (ERGODIC) | Relayers + sentries (IBC bridge nodes) | 9 |
| -1 (MINUS) | Monitors + archivers (verification) | 9 |

### Layer 7: Client Diversity

Each trit class runs 3 different consensus implementations:

| Slot | Trit +1 (Producers) | Trit 0 (Relayers) | Trit -1 (Monitors) |
|------|--------------------|--------------------|---------------------|
| A (×3) | nobled/CometBFT Go | nobled/CometBFT Go | nobled/CometBFT Go |
| B (×3) | nobled/CometBFT-RS (Rust) | nobled/CometBFT-RS | nobled/CometBFT-RS |
| C (×3) | nobled/Malachite (Informal, Rust) | nobled/Malachite | nobled/Malachite |

Go version diversity within slot A:
- 1 node: Go 1.24.x (current)
- 1 node: Go 1.23.x (previous stable)
- 1 node: Go 1.25.x (next, when available)

### Layer 4: Transport Diversity

| Transport | Nodes | Purpose |
|-----------|-------|---------|
| TCP + SecretConnection | 9 | Standard CometBFT P2P |
| TCP + Noise Protocol | 9 | Alternative handshake (libp2p-compatible) |
| QUIC | 9 | UDP-based, 0-RTT resume, multiplexed |

Each trit class uses all three transports (3 nodes each).
Sentry nodes bridge between transport types.

### Layer 3: Geographic + ASN Diversity

| Region | Nodes | Max per ASN |
|--------|-------|-------------|
| EU (DE, FI, FR, NL, CH) | 9 | 2 per ASN |
| Americas (US-E, US-W, CA, BR) | 9 | 2 per ASN |
| Asia-Pacific (SG, JP, AU, IN) | 9 | 2 per ASN |

**ASN constraint**: No ASN may host >3 nodes (11%).
Enforced ASN diversity per trit class:

| Trit +1 (Producers) | Trit 0 (Relayers) | Trit -1 (Monitors) |
|---------------------|--------------------|--------------------|
| 3× EU (Hetzner, OVH, Scaleway) | 3× EU (netcup, Equinix, IONOS) | 3× EU (Cherry, AWS-EU, Azure-EU) |
| 3× US (AWS, GCP, Vultr) | 3× US (DO, Oracle, Akamai) | 3× US (bare-metal, Cogent, Lumen) |
| 3× APAC (Alibaba, NTT, Telstra) | 3× APAC (AWS-AP, Azure-AP, Linode) | 3× APAC (Cherry, BM, residential) |

### Layer 1-2: Architecture Diversity

| Architecture | Nodes | Percentage |
|-------------|-------|-----------|
| x86_64 (Intel/AMD) | 15 | 56% |
| ARM64 (Ampere/Graviton) | 9 | 33% |
| RISC-V (SiFive/StarFive) | 3 | 11% |

Distribution:
- x86_64: all slot A (Go CometBFT compiles natively)
- ARM64: all slot B (CometBFT-RS compiles natively, AWS Graviton / Ampere Altra)
- RISC-V: slot C monitors only (Malachite, experimental but functional)

### OS Diversity

| OS | Nodes | Purpose |
|----|-------|---------|
| Linux (various distros) | 18 | Primary |
| FreeBSD | 6 | Alternative network stack |
| Guix System | 3 | Reproducible builds, bit-for-bit verification |

Linux distro diversity: Ubuntu, Debian, NixOS, Alpine (no monoculture).

### Key Algorithm Diversity

| Algorithm | Nodes | Use |
|-----------|-------|-----|
| ed25519 | 18 | Current Noble consensus key |
| secp256k1 | 6 | Alternative curve (Bitcoin-compatible) |
| BLS12-381 | 3 | Aggregate signatures (future threshold) |

Note: CometBFT currently only supports ed25519 for consensus keys.
secp256k1 and BLS are for operator/signing keys and future-proofing.
Multi-sig threshold signing via Horcrux or similar.

### boxxy Tile Composition

The heterogeneous set is a parallel composition of 27 tiles:

```
Heterogeneous Noble = ⊗_{i=1}^{27} tile_i

where tile_i : GenesisState ⊗ Config_i → ChainState' ⊗ Consensus_i

Config_i varies across:
  - binary (Go / Rust-CometBFT / Malachite)
  - transport (TCP / Noise / QUIC)
  - architecture (x86_64 / ARM64 / RISC-V)
  - ASN (no two tiles share more than 3 per ASN)
  - jurisdiction (EU / Americas / APAC)
```

The swap morphism (σ) connects tiles across transport boundaries:
```
TCP_tile ⊗ QUIC_tile
     ╲ ╱
      σ         (sentry node bridges TCP ↔ QUIC)
     ╱ ╲
QUIC_tile ⊗ TCP_tile
```

### Monitoring: The Demon Probe

From boxxy's `internal/demon/` -- the active inference fuzzer:

Each trit -1 (MINUS) monitor node runs the demon probe against
its trit +1 (PLUS) producer partner:

```
Monitor_i observes Producer_j:
  Perception  = block signatures, timing, IBC relay latency
  Prediction  = expected signature set from BFT quorum
  Surprise    = missing signature || unexpected validator || timing anomaly
  Action      = alert if surprise > threshold (free energy minimization)
```

The InvisiCap FFI blanket (from boxxy `internal/vm/invisicap.go`)
wraps each tile boundary:

```
CapTable per tile:
  "chain_state"   → CapData (+1)     -- writable by consensus
  "genesis"       → CapReadonly (0)  -- immutable reference
  "validator_key" → CapFunction (-1) -- callable for signing only

GF(3) balance: +1 + 0 + (-1) = 0 ✓
```

### Cost Estimate (27-node heterogeneous set)

| Provider Mix | Monthly | Notes |
|-------------|---------|-------|
| 9× Hetzner (EU, x86) | ~$270 | CX41: 8 vCPU, 16 GB, 160 GB = ~$30/mo |
| 9× AWS Graviton (ARM64) | ~$630 | t4g.2xlarge: 8 vCPU, 32 GB = ~$70/mo |
| 3× Vultr bare-metal (RISC-V/x86) | ~$360 | Bare metal: ~$120/mo |
| 3× DigitalOcean (misc) | ~$150 | Premium: 8 vCPU, 16 GB = ~$50/mo |
| 3× OVH (FR) | ~$90 | B2-30: 8 vCPU, 30 GB = ~$30/mo |
| **Total** | **~$1,500/mo** | 27 nodes, 13 countries, 9 ASNs |

Compare to Noble's current set: 18 validators, ~43% Hetzner,
estimated ~$500-800/mo total (all cheap EU hosting).

The heterogeneous premium is ~2-3x for genuine fault isolation
across every OSI layer.

### Migration Path

1. **Phase 0** (now): Snapshot noble-1 into boxxy tile, verify sync
2. **Phase 1** (week 1): Stand up 3 nodes (1 per trit) on 3 different ASNs
3. **Phase 2** (week 2): Add transport diversity (TCP + QUIC + Noise)
4. **Phase 3** (week 3): Add architecture diversity (ARM64 nodes via Graviton)
5. **Phase 4** (week 4): Full 27-node set with monitoring demon probes
6. **Phase 5** (ongoing): RISC-V experimental nodes, BLS threshold signing

Each phase is a sequential composition of boxxy tiles:
`phase_0 ; phase_1 ; phase_2 ; phase_3 ; phase_4 ; phase_5`

Branching (via vers.sh) at each phase boundary enables rollback.
