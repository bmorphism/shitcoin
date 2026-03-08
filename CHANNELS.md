# Noble IBC Channel Census: 437 Open Connections, 10 Days to Migration

**Date**: March 8, 2026
**Noble EVM launch**: March 18, 2026
**Source**: Noble chain on-chain state via REST API + cosmos/chain-registry

## The Numbers

| Category | Count | Notes |
|----------|-------|-------|
| Total on-chain channels | 437 | Noble mainnet (noble-1) |
| Token transfer channels | 155 | port_id = "transfer" |
| Interchain account channels | 280 | port_id = "icahost" — remote execution |
| Non-standard port channels | 2 | Wormhole bridge, Oraichain wasm |
| Registered in chain-registry | 59 | Public, claimed, documented |
| Unregistered transfer channels | 96 | Open, accepting packets, unclaimed |
| Numbered ICA controllers (unknown origin) | 205 | Sequential: icacontroller-2 through -206 |
| Stuck TRYOPEN channels | 37 | Half-open, never completed |
| Channel in INIT state | 1 | channel-121: created, no counterparty |

## Causal Chain 1: The Denom Collision Problem

IBC denoms are `SHA256(port/channel/base_denom)`. The port is almost always
`transfer`. The base denom for USDC is `uusdc`. The only variable is the
peer's channel-id — which is a sequential counter starting at 0.

This means every chain that opened its Nth channel to Noble produces the
same USDC denom as every other chain that opened its Nth channel to Noble.

**Observed collisions on Noble USDC**:

| Peer channel | USDC denom (truncated) | Chains sharing this denom |
|-------------|----------------------|--------------------------|
| channel-0 | `ibc/8E27BA2D...` | dYdX, titan, sunrise + **12 unregistered** |
| channel-1 | `ibc/65D0BEC6...` | joltify, mantrachain, sidechain, babylon + **8 unregistered** |
| channel-2 | `ibc/F082B65C...` | nibiru, xion, elys, bitbadges, int3face, paxi + **6 unregistered** |
| channel-4 | `ibc/BFF0D380...` | haqq, furya, xrplevm + **3 unregistered** |
| channel-5 | `ibc/BFAAB787...` | onex, pryzm, shido, namada + **1 unregistered** |
| channel-9 | `ibc/295548A7...` | aura, lava, kopi + **1 unregistered** |
| channel-62 | `ibc/FE98AAD6...` | kujira, agoric, teritori |
| channel-3 | `ibc/6490A7EA...` | beezee, zigchain + **3 unregistered** |

These are not theoretical collisions. These are on-chain, OPEN channels
producing identical USDC denomination strings on different chains. A wallet
on nibiru holding `ibc/F082B65C...` and a wallet on xion holding the same
string are holding tokens that arrived via different channels from different
security contexts, but are named identically.

**Why this matters during migration**: if the accessibility relation changes
(new validator set, new execution layer), the collision means tokens from
the old Noble and the new Noble are indistinguishable by denom.

## Causal Chain 2: The 205 Numbered ICA Controllers

Noble channels 125 through 436 contain 205 interchain account (ICA) channels
with sequential numeric controllers: `icacontroller-2`, `icacontroller-3`,
... `icacontroller-206`.

ICA channels allow a remote chain to execute transactions on Noble as if
it were a local account. This is remote code execution over IBC.

These 205 channels:
- Are not attributable to any named chain in the cosmos/chain-registry
- Use sequential numeric identifiers (not chain addresses)
- Are all in STATE_OPEN
- Have corresponding counterparty channels numbered sequentially (channel-158 through channel-371)

The first numbered controller (`icacontroller-2`) connects via Noble
channel-125. The last (`icacontroller-206`) connects via Noble channel-436.

**Who opened 205 sequential ICA channels to Noble?** The chain-registry
does not say. The on-chain state does not name the controlling chain.
The controller numbers are opaque integers, not addresses.

These channels have remote execution capability on a chain that holds
~$250M in Circle-issued USDC. After the EVM migration, the ICA host
module behavior may change. The channels remain open.

## Causal Chain 3: The Wormhole Port Problem

Noble channel-128 uses port `wormhole` (not `transfer`). Its counterparty
on Gateway (Wormchain) uses port
`wasm.wormhole1wkwy0xh89ksdgj9hr347dyd2dw7zesmtrue6kfzyml4vdtz6e5ws2y050r`.

This is a CosmWasm smart contract acting as an IBC port. The protocol
version is `ibc-wormhole-v1`, not `ics20-1`.

Noble is migrating from CosmWasm to EVM. The Wormhole bridge channel
depends on a CosmWasm contract on the Noble side (implied by the `wormhole`
port name). After migration:

- Does the `wormhole` port survive the execution layer change?
- If Noble EVM doesn't support CosmWasm, is channel-128 orphaned?
- If orphaned, are tokens in flight on this channel recoverable?
- The Wormhole bridge connects Noble to non-Cosmos chains (Ethereum,
  Solana, etc.) — an orphaned channel affects cross-ecosystem liquidity

## Causal Chain 4: Oraichain's Two Wasm Ports

Noble has two channels to Oraichain:
- channel-34 (registered): peer port `wasm.orai195269awwnt5m6c843q6w7hp8rt0k7syfu9de4h0wz384slshuzps8y7ccm`
- channel-35 (unregistered): peer port `wasm.orai1jtt8c2lz8emh8s708y0aeduh32xef2rxyg8y78lyvxn806cu7q0sjtxsnv`

Two different CosmWasm contracts on Oraichain, both with open IBC channels
to Noble. Only one is in the chain-registry. The unregistered channel
(channel-35) produces different denoms because the port string is part
of the hash on the Oraichain side.

The registered channel's USDC denom on Oraichain:
`ibc/72CA60FB544938D70FDB0F66367F974E42BA0B8589350E340B77870EE80381BC`

The unregistered channel (if using transfer port on Noble side) produces:
same denom as channel-148 on injective — **another collision**, this time
between a wasm-ported channel and a standard transfer channel.

## Causal Chain 5: The Half-Open Osmosis Flood

37 channels are stuck in STATE_TRYOPEN. 30 of them are from a single
Osmosis address: `osmo1ry803gczgr5vta3f42eus...`

This address attempted to open ~30 ICA channels to Noble in rapid
succession, hitting channels 87256-98015 on Osmosis's side. All failed
to complete the handshake. The channels remain in TRYOPEN state on Noble.

A TRYOPEN channel is a half-open connection: Noble has allocated the
channel-id and is waiting for the counterparty to complete. The channel
exists. The id is consumed. If the counterparty later sends the
completing handshake (ChanOpenConfirm), the channel becomes OPEN.

30 half-open channels from one address is either:
- A malfunctioning relayer (benign)
- A channel exhaustion attack (consuming Noble's channel-id space)
- Probing for ICA host behavior (reconnaissance)

## Causal Chain 6: channel-121 — Created, No Counterparty

Noble channel-121 is in STATE_INIT with an empty counterparty. It was
created on Noble but no remote chain ever connected to it. It is a
channel that exists in name but has no neighbor.

In the Kripkean framing: this is a possible world with no accessibility
relation. It is a channel-id that has been allocated but not bound.
Anyone who sends the right ChanOpenTry to Noble can become the
counterparty for channel-121.

## Causal Chain 7: The 96 Shadow Channels

96 transfer channels on Noble are OPEN and functioning but are not
listed in the cosmos/chain-registry. They are shadow channels:
legitimate IBC connections that exist on-chain but have no public
documentation.

Some are likely:
- Test channels that were never cleaned up
- Duplicate channels opened by mistake (channel-19 is a TRYOPEN
  duplicate of channel-18, both pointing at the same counterparty)
- Channels opened by chains too small or new to register

But "likely" is not "proven." The chain-registry is voluntary.
Not registering a channel is not suspicious by itself. But 96
unregistered channels out of 155 total transfer channels means
**62% of Noble's IBC transfer surface is undocumented**.

After the EVM migration, all 155 channels — documented and
undocumented — continue to produce valid USDC denoms. The
hash does not check the registry.

## Pre-Computed Denom Table

Every USDC denom on every registered peer chain, valid before and after
March 18, 2026:

| Chain | Peer Channel | USDC Denom |
|-------|-------------|------------|
| osmosis | channel-750 | `ibc/498A0751C798A0D9A389AA3691123DADA57DAA4FE165D5C75894505B876BA6E4` |
| cosmoshub | channel-536 | `ibc/F663521BF1836B00F5F177680F74BFB9A8B5654A694D0D2BC249E03CF2509013` |
| neutron | channel-30 | `ibc/B559A80D62249C8AA07A380E2A2BEA6E5CA9A6F079C912C3A9E9B494105E4F81` |
| dydx | channel-0 | `ibc/8E27BA2D5493AF5636760E354E46004562C46AB7EC0CC4C1CA14E9E20E2545B5` |
| injective | channel-148 | `ibc/2CBC2EA121AE42563B08028466F37B600F2D7D4282342DE938283CC3FB2BC00E` |
| sei | channel-45 | `ibc/CA6FBFAF399474A06263E10D0CE5AEBBE15189D6D4B2DD9ADE61007E68EB9DB0` |
| stargaze | channel-204 | `ibc/4A1C18CA7F50544760CF306189B810CE4C1CB156C7FC870143D401FE7280E591` |
| terra2 | channel-253 | `ibc/2C962DAB9F57FE0921435426AE75196009FAA1981BF86991203C8411F8980FDB` |
| kujira | channel-62 | `ibc/FE98AAD68F02F03565E9FA39A5E627946699B2B07115889ED812D8BA639576A9` |
| juno | channel-224 | `ibc/4A482FA914A4B9B05801A2B0F8B9D2D088C2F1B5E57F0C4F2BA5EB4801B3E6F` |
| evmos | channel-64 | `ibc/35357FE55D81D88054E1BA94B717A3A4DDD81F2C1FE498C75ECB8A3B4E1E4E97` |
| archway | channel-29 | `ibc/43897B9739BD63E3A08A88191999C632E052724AB96BD4C74AE31375C991F48D` |
| secretnetwork | channel-88 | `ibc/9162FF8AC138FFAB8723C22EC72D8E0C43C10B0A1AEAB4A47E4E5F0B1400A9D5` |
| agoric | channel-62 | `ibc/FE98AAD68F02F03565E9FA39A5E627946699B2B07115889ED812D8BA639576A9` |
| persistence | channel-132 | `ibc/B3792E4A62DF4A934EF2BCA4D629E9FBA0F0B4ADAAE0E8AE44AD1AF7E584D2E0` |
| dymension | channel-6 | `ibc/B3504E092456BA618CC28AC671A71FB08C6CA0FD0BE7C8A5B5A3E2DD933CC9E4` |
| babylon | channel-1 | `ibc/65D0BEC6DAD96C7F5043D1E54E54B6BB5D5B3AEC3FF6CEBB75B9E059F3580EA3` |

Note: kujira and agoric share the same USDC denom (`ibc/FE98AAD6...`)
because both use channel-62 as their peer channel.

## What Would Fix This

1. **Authenticated channel identity**: bind the denom derivation to a
   validator set commitment or state proof, not just port/channel/denom
2. **ZK IBC**: channel identity via validity proof, not string hash
3. **Channel registry enforcement**: require chain-registry listing for
   IBC relayer acceptance (social layer fix, imperfect but immediate)
4. **ICA audit**: identify the origin of the 205 numbered controllers
   before the execution layer changes under them
5. **Wormhole port migration plan**: explicit documentation of what
   happens to the wormhole port on Noble after EVM launch

None of these are in place. 10 days remain.
