"""
Noble USDC IBC denom pre-computation.

Demonstrates delayed action capacity: every denom on every chain that
has an IBC channel to Noble can be computed before March 18, 2026.

The hash doesn't know who is on the other end. It only knows the string.
"""

import hashlib

NOBLE_CHANNELS = {
    "osmosis":   {"noble_channel": "channel-1",  "peer_channel": "channel-750", "chain_id": "osmosis-1"},
    "cosmoshub": {"noble_channel": "channel-4",  "peer_channel": "channel-536", "chain_id": "cosmoshub-4"},
    "neutron":   {"noble_channel": "channel-18", "peer_channel": "channel-30",  "chain_id": "neutron-1"},
    "stargaze":  {"noble_channel": "channel-11", "peer_channel": "channel-204", "chain_id": "stargaze-1"},
    "sei":       {"noble_channel": "channel-39", "peer_channel": "channel-45",  "chain_id": "sei-pacific-1"},
    "dydx":      {"noble_channel": "channel-33", "peer_channel": "channel-0",   "chain_id": "dydx-mainnet-1"},
    "injective": {"noble_channel": "channel-31", "peer_channel": "channel-148", "chain_id": "injective-1"},
    "terra2":    {"noble_channel": "channel-30", "peer_channel": "channel-253", "chain_id": "phoenix-1"},
}

NOBLE_USDC_DENOM = "uusdc"


def ibc_denom(port_id, channel_id, base_denom):
    path = f"{port_id}/{channel_id}/{base_denom}"
    return f"ibc/{hashlib.sha256(path.encode('utf-8')).hexdigest().upper()}"


def noble_usdc_on(chain_name):
    """What does Noble USDC look like on the peer chain?

    The peer receives tokens via their channel to Noble.
    denom = SHA256(transfer/{peer_channel}/{base_denom})

    This is the same before and after the EVM migration.
    The hash doesn't know who is running Noble.
    """
    info = NOBLE_CHANNELS.get(chain_name)
    if not info:
        raise ValueError(f"Unknown chain: {chain_name}. Known: {list(NOBLE_CHANNELS.keys())}")
    return ibc_denom("transfer", info["peer_channel"], NOBLE_USDC_DENOM)


def precompute_all():
    """Pre-compute every Noble USDC denom on every known peer chain.

    Cost: O(N) string hashes. Time: instant.
    These denoms are valid before, during, and after the migration.
    The validator set changes. The execution layer changes.
    The denom does not change. That is the vulnerability.
    """
    results = {}
    for chain_name, info in NOBLE_CHANNELS.items():
        results[chain_name] = {
            "chain_id": info["chain_id"],
            "noble_channel": info["noble_channel"],
            "peer_channel": info["peer_channel"],
            "usdc_denom": noble_usdc_on(chain_name),
            "raw_path": f"transfer/{info['peer_channel']}/{NOBLE_USDC_DENOM}",
        }
    return results


def precompute_future(n=100):
    """Pre-compute USDC denoms for channels that don't exist yet.

    channel-ids are sequential counters. This function computes
    the denom for channel-0 through channel-{n} on a hypothetical
    chain that opens a new IBC channel to Noble.

    Cost: negligible. Every future channel's denom is known now.
    """
    return {
        f"channel-{i}": ibc_denom("transfer", f"channel-{i}", NOBLE_USDC_DENOM)
        for i in range(n)
    }


if __name__ == "__main__":
    print("Noble USDC denoms on peer chains (pre-computed)")
    print("=" * 72)
    print(f"Migration date: March 18, 2026 (CosmWasm -> EVM)")
    print(f"These denoms are identical before and after migration.")
    print()

    for chain_name, data in precompute_all().items():
        print(f"  {chain_name:12s} ({data['chain_id']})")
        print(f"    channel:  {data['peer_channel']} <-> Noble {data['noble_channel']}")
        print(f"    path:     {data['raw_path']}")
        print(f"    denom:    {data['usdc_denom']}")
        print()

    print("=" * 72)
    print("Future channels (pre-computed, channels 0-9):")
    print()
    future = precompute_future(10)
    for ch, denom in future.items():
        print(f"  {ch:12s} -> {denom}")

    print()
    print("The hash does not know who is on the other end.")
    print("The hash does not know the execution layer changed.")
    print("The hash does not know the validator set rotated.")
    print("The hash knows: transfer/channel-N/uusdc. That is all.")
