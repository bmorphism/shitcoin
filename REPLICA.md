# Noble Chain Replica via boxxy

One-to-one replica of `noble-1` as a boxxy tile.

## Noble Chain State (Live)

| Parameter | Value |
|-----------|-------|
| Chain ID | `noble-1` |
| Binary | `nobled` v11.2.0 |
| Consensus | CometBFT v0.38.19 |
| SDK | Cosmos SDK v0.45.16 (noble-assets fork) |
| Block height | ~46,466,703 (2026-03-09) |
| Block time | ~6s |
| IBC | go v4.6.0, ics20-1 |
| CosmWasm | **disabled** (was never enabled on noble-1) |
| Pruned snapshot | ~1 GB (Polkachu) |
| Archive snapshot | Weekly, larger (Polkachu) |
| Validators | Permissioned set (not standard PoS) |
| Fee tokens | `uusdc`, IBC-wrapped ATOM |

Noble is migrating to an EVM L1. The replica captures the CosmWasm-free
Cosmos SDK chain *before* that transition.

## Hardware Requirements

Noble is a lightweight Cosmos chain (no CosmWasm, no heavy DeFi state).

| Resource | Minimum | Recommended | Archive |
|----------|---------|-------------|---------|
| CPU | 4 cores | 8 cores (2.5+ GHz) | 8 cores |
| RAM | 16 GB | 32 GB | 32 GB |
| Storage | 100 GB NVMe | 500 GB NVMe | 1+ TB NVMe |
| Network | 100 Mbps | 1 Gbps | 1 Gbps |
| OS | Linux amd64 / arm64 | Linux amd64 | Linux amd64 |

Storage breakdown:
- Pruned state: ~1 GB (grows ~50 MB/month)
- Full node (recent blocks): ~50-100 GB
- Archive node (all blocks): ~200-500 GB (extrapolated from block height)
- WAL + temp: 10-20 GB headroom

## The boxxy Tile

```
        Noble chain state (genesis + snapshot)
            | | |
       +----+-+-+----+
       |              |
       |   nobled     |
       |   (Linux)    |
       |              |
       |  sync  --> * |
       |  run   --> * |
       |  query --> * |
       |              |
       +----+-+-+----+
            | | |
        Noble chain state' (synced + serving)
```

### Tile Morphism

```
tile_noble : GenesisState ⊗ NobleConfig → ChainState' ⊗ RPCEndpoint
```

Input wires:
- `genesis.json` (from strangelove-ventures/noble-networks)
- `nobled` binary v11.2.0
- Snapshot (Polkachu 1 GB pruned or archive)
- Seed peers (`seeds.lavenderfive.com:21590`, `seeds.bluestake.net:25556`)
- Config (`app.toml`, `config.toml`, chain-specific pruning)

Output wires:
- Synced chain state
- RPC endpoint (port 26657)
- REST API (port 1317)
- gRPC (port 9090)
- P2P (port 26656)

### boxxy Script

```clojure
;; Noble chain as a single boxxy tile
(def noble-disk (vz/create-disk-image "noble-chain.img" 500))

(def noble-vm
  (-> (vz/new-vm-config
        8                           ; 8 vCPU
        32                          ; 32 GB RAM
        (vz/new-linux-boot-loader
          "vmlinuz"                 ; Linux kernel
          "initrd.img"              ; initramfs with nobled
          "root=/dev/vda1 console=ttyS0")
        (vz/new-generic-platform))
      (vz/add-storage-devices
        [(vz/new-virtio-block-device
           (vz/new-disk-attachment "noble-chain.img" false))])
      (vz/add-network-devices
        [(vz/new-nat-network)])
      (vz/add-directory-shares
        [(vz/new-virtio-fs-device "genesis" "./noble-genesis")])
      (vz/new-vm)))

;; Sequential: boot ; sync ; serve
(vz/start-vm! noble-vm)
;; Inside guest: nobled start --p2p.seeds=... --home=/noble
```

### Parallel Composition: Noble + Monitor

```clojure
;; Two tiles side by side
;; noble-vm ⊗ monitor-vm
(def monitor-vm
  (-> (vz/new-vm-config 2 4
        (vz/new-linux-boot-loader
          "vmlinuz" "initrd-monitor.img"
          "root=/dev/vda1")
        (vz/new-generic-platform))
      (vz/add-network-devices [(vz/new-nat-network)])
      (vz/new-vm)))

;; Parallel: both tiles run simultaneously
(vz/start-vm! noble-vm)
(vz/start-vm! monitor-vm)
;; monitor watches noble RPC for IBC anomalies (CHANNELS.md causal chains)
```

## Cost Comparison

### MorphCloud (cloud.morph.so)

**Pricing model**: MCU (Morph Compute Unit) = 1 vCPU-hour + 4 GB RAM-hour + 16 GB disk-hour, bundled.

| Plan | Monthly | Starting MCU | Max vCPU | Max RAM | Max Disk |
|------|---------|-------------|----------|---------|----------|
| Developer | $0 | 300 MCU | 64 | 256 GB | 1 TB |
| Team | $40 | 1,000 MCU | 256 | 1 TB | 4 TB |
| Scale | $250 | 7,500 MCU | 1 TB | 4 TB | 16 TB |

Rate: **$0.05/MCU** after included credits.

**Noble replica cost on MorphCloud:**

```
Noble tile: 8 vCPU + 32 GB RAM + 500 GB disk
MCU consumption = max(8, 32/4, 500/16) = max(8, 8, 31.25) = 31.25 MCU/hr
(disk-limited: 500 GB / 16 GB per MCU)

Hourly:  31.25 MCU × $0.05 = $1.5625/hr
Daily:   $37.50
Monthly: $1,125.00

Developer plan (300 free MCU): ~9.6 hours free, then $0.05/MCU
Team plan (1,000 free MCU):    ~32 hours free, then $0.05/MCU
Scale plan (7,500 free MCU):   ~10 days free, then $0.05/MCU
```

For pruned node (100 GB disk):
```
MCU/hr = max(8, 8, 6.25) = 8 MCU/hr
Hourly:  $0.40
Monthly: $288.00
```

**MorphCloud advantage**: Snapshot/branch VMs programmatically, API-driven, massive scale ceiling.

### Vers.sh (vers.sh)

**Pricing model**: Fixed tiers, VM branching included.

| Plan | Monthly | vCPU | RAM | Storage |
|------|---------|------|-----|---------|
| Basic | $10 | 2 | 4 GB | 50 GB |
| Pro | $30 | 4 | 8 GB | 100 GB |
| Enterprise | $100 | 8 | 16 GB | 200 GB |
| Enterprise+ | Custom | 16+ | 16+ GB | Custom |

Max documented: 16 vCPU, 16 GB RAM per VM.

**Noble replica cost on Vers.sh:**

```
Enterprise ($100/mo): 8 vCPU, 16 GB RAM, 200 GB disk
  -- INSUFFICIENT: need 32 GB RAM, 500 GB disk for recommended spec
  -- MARGINAL: could run pruned node with 16 GB RAM, 200 GB disk

Enterprise+ (custom pricing, contact sales@vers.sh):
  -- Required for full Noble replica
  -- Estimate: $200-500/mo based on resource scaling pattern
```

**Vers.sh advantage**: Git-like VM branching (branch, checkout, commit). Perfect for boxxy's tile isotopy -- fork Noble state at any block height, explore alternative migration paths.

### boxxy Local (Apple Silicon)

```
Hardware: Apple M1 Pro+ (already owned)
  M1 Pro:  8P+2E CPU, 16-32 GB unified memory
  M2 Ultra: 24-core, 64-192 GB unified memory

Noble tile: 8 vCPU + 32 GB RAM + 500 GB disk
  -- M1 Pro 32 GB: sufficient (leave 8 GB for host)
  -- M2 Ultra: oversufficient, can run Noble ⊗ Monitor ⊗ Fuzzer

Cost: $0/month (hardware already amortized)
Limitation: macOS host only, arm64 guest via Virtualization.framework
  -- nobled builds for linux/arm64 (Go cross-compile)
  -- Or run linux/amd64 via Rosetta 2 in VM
```

### Comparison Matrix

| Dimension | MorphCloud | Vers.sh | boxxy Local |
|-----------|-----------|---------|-------------|
| Monthly cost (pruned) | ~$288 | $100 | $0 |
| Monthly cost (full) | ~$1,125 | ~$300+ (custom) | $0 |
| Monthly cost (archive) | ~$2,000+ | Custom | $0 (if disk fits) |
| VM branching | Yes (API) | Yes (git-like) | Manual (snapshot) |
| Max vCPU | 1,024 | 16 | Host-limited |
| Max RAM | 4 TB | 16 GB | Host-limited |
| Tile isotopy | API-composable | Branch/checkout | boxxy REPL native |
| IBC channel monitor | Yes | Yes | Yes |
| Parallel tiles | 128+ concurrent | Multiple VMs | Host-limited |
| Network (P2P peering) | Public IP | SSH tunnel | NAT (port forward) |
| Persistence | Cloud (survives reboot) | Cloud | Local disk |
| Architecture | x86_64 | x86_64 | arm64 native |

## Recommended Configuration

### For disclosure validation (10 days):
**MorphCloud Developer** (free tier, 300 MCU)
- Pruned node: 8 MCU/hr = 37.5 hours free
- Enough to sync, validate IBC channels, run DISCLOSURE tests
- Cost: **$0** if done within free credits

### For persistent monitoring:
**Vers.sh Enterprise** ($100/mo)
- 8 vCPU, 16 GB, 200 GB -- runs pruned Noble node
- Branch at migration block height to capture before/after states
- Perfect for CHANNELS.md causal chain monitoring

### For full replica + attack surface exploration:
**boxxy local** (Apple Silicon 32+ GB)
- Full Noble node + IBC monitor tile + demon fuzzer tile
- $0/month, full control, InvisiCap capability tracking
- Parallel composition: `noble ⊗ monitor ⊗ fuzzer`

### For production-grade archive node:
**MorphCloud Scale** ($250/mo + ~$1,750 MCU overage)
- Archive node needs ~1 TB storage
- Total: ~$2,000/month
- Can scale to multiple replicas for consensus testing

## Migration Timeline

Noble EVM migration is active. The replica captures:

1. **Pre-migration snapshot** (today): Full CosmWasm-free Cosmos SDK state
2. **Migration block** (TBD): Fork point where IBC channels reconnect to EVM
3. **Post-migration state**: New EVM L1 with bridged USDC

The boxxy tile captures all three as sequential composition:
```
pre_migration ; migration_block ; post_migration
```

Each step can be branched (via vers.sh or MorphCloud) to explore
counterfactual migration paths -- the "possible worlds" from DISCLOSURE.md.

## Setup Commands

```bash
# 1. Get Noble binary
git clone https://github.com/strangelove-ventures/noble
cd noble && git checkout v11.2.0
make install  # produces nobled

# 2. Initialize
nobled init noble-replica --chain-id noble-1
curl -s https://raw.githubusercontent.com/strangelove-ventures/noble-networks/main/mainnet/noble-1/genesis.json > ~/.noble/config/genesis.json

# 3. Set seeds
sed -i 's/seeds = ""/seeds = "20e1000e88125698264454a884812746c2eb4807@seeds.lavenderfive.com:21590,b85358e035343a3b15e77e1102857dcdaf70053b@seeds.bluestake.net:25556"/' ~/.noble/config/config.toml

# 4. Apply snapshot (fast sync)
wget -O noble_snapshot.tar.lz4 https://snapshots.polkachu.com/snapshots/noble/noble_46419300.tar.lz4
lz4 -d noble_snapshot.tar.lz4 | tar xf - -C ~/.noble

# 5. Start
nobled start
```

For boxxy, wrap steps 1-5 in the VM guest initramfs or shared directory.
