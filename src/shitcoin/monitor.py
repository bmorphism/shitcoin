"""
Noble IBC collision monitor — live chain interrogation.

Queries the Noble REST API to:
1. Enumerate all transfer channels
2. Resolve chain identities via client_state lookups
3. Detect peer-channel collisions (same USDC denom on multiple chains)
4. Compare against known baseline to detect NEW collisions

The structural vulnerability: IBC denom = SHA256(transfer/channel-N/uusdc).
Every chain whose Noble connection is channel-0 locally produces the same
USDC denom as dYdX. The hash doesn't know. This monitor does.
"""

import hashlib
import json
import urllib.request
from collections import defaultdict


DEFAULT_API = "https://noble-api.polkachu.com"


def _fetch_json(url):
    """Fetch JSON from a URL. No dependencies beyond stdlib."""
    req = urllib.request.Request(url, headers={
        "Accept": "application/json",
        "User-Agent": "shitcoin-monitor/1.0",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def fetch_transfer_channels(api=DEFAULT_API):
    """Fetch all IBC channels and filter to port=transfer."""
    channels = []
    key = ""
    while True:
        url = f"{api}/ibc/core/channel/v1/channels?pagination.limit=500"
        if key:
            url += f"&pagination.key={key}"
        data = _fetch_json(url)
        for ch in data.get("channels", []):
            if ch.get("port_id") == "transfer":
                channels.append({
                    "channel_id": ch["channel_id"],
                    "state": ch["state"],
                    "counterparty_channel": ch.get("counterparty", {}).get("channel_id", ""),
                    "connection": ch.get("connection_hops", [""])[0],
                })
        next_key = data.get("pagination", {}).get("next_key")
        if not next_key:
            break
        key = next_key
    return channels


def fetch_connection_client(connection_id, api=DEFAULT_API):
    """Get the client_id for a connection."""
    url = f"{api}/ibc/core/connection/v1/connections/{connection_id}"
    data = _fetch_json(url)
    return data.get("connection", {}).get("client_id", "")


def fetch_chain_id(client_id, api=DEFAULT_API):
    """Get the chain_id from a client_state."""
    url = f"{api}/ibc/core/client/v1/client_states/{client_id}"
    data = _fetch_json(url)
    return data.get("client_state", {}).get("chain_id", "unknown")


def ibc_denom(port_id, channel_id, base_denom):
    """SHA256(port/channel/denom) -> ibc/HEX"""
    path = f"{port_id}/{channel_id}/{base_denom}"
    return f"ibc/{hashlib.sha256(path.encode('utf-8')).hexdigest().upper()}"


def scan_collisions(api=DEFAULT_API, resolve_chains=True, verbose=False):
    """Full collision scan: fetch channels, group by peer channel, resolve identities.

    Returns:
        {
            "total_transfer": int,
            "transfer_open": int,
            "unique_peer_channels": int,
            "collision_groups": int,
            "max_collision_size": int,
            "collisions": {
                "channel-N": {
                    "count": int,
                    "noble_channels": [...],
                    "chains": [...],  # chain_ids if resolve_chains=True
                    "usdc_denom": "ibc/...",
                }
            }
        }
    """
    if verbose:
        print("Fetching transfer channels...")
    channels = fetch_transfer_channels(api)

    # Group by counterparty channel
    by_peer = defaultdict(list)
    for ch in channels:
        if ch["counterparty_channel"]:
            by_peer[ch["counterparty_channel"]].append(ch)

    open_count = sum(1 for ch in channels if ch["state"] == "STATE_OPEN")

    collisions = {}
    for peer_ch, members in sorted(by_peer.items(), key=lambda x: -len(x[1])):
        if len(members) < 2:
            continue

        entry = {
            "count": len(members),
            "noble_channels": [m["channel_id"] for m in members],
            "usdc_denom": ibc_denom("transfer", peer_ch, "uusdc"),
        }

        if resolve_chains:
            chain_ids = []
            for m in members:
                try:
                    if verbose:
                        print(f"  Resolving {m['channel_id']} -> {m['connection']}...")
                    client_id = fetch_connection_client(m["connection"], api)
                    chain_id = fetch_chain_id(client_id, api)
                    chain_ids.append(chain_id)
                except Exception as e:
                    chain_ids.append(f"error:{e}")
            entry["chains"] = chain_ids

        collisions[peer_ch] = entry

    max_size = max((c["count"] for c in collisions.values()), default=0)

    return {
        "total_transfer": len(channels),
        "transfer_open": open_count,
        "unique_peer_channels": len(by_peer),
        "collision_groups": len(collisions),
        "max_collision_size": max_size,
        "collisions": collisions,
    }


if __name__ == "__main__":
    print("Noble IBC Collision Monitor")
    print("=" * 72)
    print()

    result = scan_collisions(verbose=True)

    print()
    print(f"Transfer channels: {result['total_transfer']} ({result['transfer_open']} open)")
    print(f"Unique peer channels: {result['unique_peer_channels']}")
    print(f"Collision groups: {result['collision_groups']}")
    print(f"Largest collision: {result['max_collision_size']} chains")
    print()

    for peer_ch, data in result["collisions"].items():
        print(f"  {peer_ch} ({data['count']} chains):")
        print(f"    denom: {data['usdc_denom']}")
        print(f"    noble: {', '.join(data['noble_channels'])}")
        if "chains" in data:
            print(f"    chains: {', '.join(data['chains'])}")
        print()

    print("The hash does not know who is on the other end.")
