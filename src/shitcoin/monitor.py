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


def diff_collisions(baseline, current):
    """Compare two scan results. Returns new/grown/shrunk collision groups.

    Args:
        baseline: previous scan_collisions() result
        current: fresh scan_collisions() result

    Returns:
        {
            "new_channels": int,       # transfer channels added since baseline
            "new_collisions": [...],   # peer channels that are newly colliding
            "grown": [...],            # existing collisions that gained members
            "shrunk": [...],           # existing collisions that lost members
            "alerts": [...],           # human-readable alert strings
        }
    """
    b_col = baseline.get("collisions", {})
    c_col = current.get("collisions", {})

    new_collisions = []
    grown = []
    shrunk = []
    alerts = []

    new_ch = current["total_transfer"] - baseline["total_transfer"]
    if new_ch > 0:
        alerts.append(f"{new_ch} new transfer channels since baseline")

    for peer_ch, data in c_col.items():
        if peer_ch not in b_col:
            new_collisions.append(peer_ch)
            chains_str = ", ".join(data.get("chains", data["noble_channels"]))
            alerts.append(
                f"NEW COLLISION: {peer_ch} ({data['count']} chains: {chains_str}) "
                f"denom={data['usdc_denom'][:24]}..."
            )
        elif data["count"] > b_col[peer_ch]["count"]:
            grown.append(peer_ch)
            delta = data["count"] - b_col[peer_ch]["count"]
            alerts.append(
                f"GROWING: {peer_ch} gained {delta} chain(s), "
                f"now {data['count']} total"
            )

    for peer_ch, data in b_col.items():
        if peer_ch in c_col and c_col[peer_ch]["count"] < data["count"]:
            shrunk.append(peer_ch)

    return {
        "new_channels": new_ch,
        "new_collisions": new_collisions,
        "grown": grown,
        "shrunk": shrunk,
        "alerts": alerts,
    }


def fetch_validators(api=DEFAULT_API):
    """Fetch Noble's bonded validator set.

    Noble uses an equal-weight authority set (not proof-of-stake).
    All validators have 1M tokens. Any 11/16 can sign a block.
    6 colluding validators = total control of ~$250M USDC.
    """
    url = f"{api}/cosmos/staking/v1beta1/validators?status=BOND_STATUS_BONDED&pagination.limit=50"
    data = _fetch_json(url)
    validators = []
    for v in data.get("validators", []):
        desc = v.get("description", {})
        validators.append({
            "moniker": desc.get("moniker", "unknown"),
            "operator": v.get("operator_address", ""),
            "website": desc.get("website", ""),
            "commission": v.get("commission", {}).get("commission_rates", {}).get("rate", "0"),
            "tokens": v.get("tokens", "0"),
        })
    n = len(validators)
    return {
        "count": n,
        "bft_threshold": (n * 2 // 3) + 1,
        "collude_to_control": (n - 1) // 3 + 1,
        "equal_weight": len(set(v["tokens"] for v in validators)) == 1,
        "validators": validators,
    }


def risk_score(scan_result, validator_result=None):
    """Compute a collision risk score for the Noble IBC ecosystem.

    Factors:
    1. Collision density: what fraction of peer channels are colliding
    2. Mega-collision severity: how large the biggest groups are
    3. Repeat offenders: chains appearing in multiple collision groups
    4. Validator concentration: how few entities needed to collude

    Returns a dict with component scores and a composite 0-100 rating.
    Higher = more dangerous.
    """
    collisions = scan_result.get("collisions", {})
    total_peers = scan_result.get("unique_peer_channels", 1)
    max_size = scan_result.get("max_collision_size", 0)

    # Factor 1: collision density (0-25)
    collision_ratio = len(collisions) / max(total_peers, 1)
    density_score = min(25, collision_ratio * 75)

    # Factor 2: mega-collision severity (0-25)
    # 18 chains sharing one denom is catastrophic
    severity_score = min(25, (max_size / 20) * 25)

    # Factor 3: repeat offenders (0-25)
    chain_appearances = {}
    for data in collisions.values():
        for chain in data.get("chains", []):
            chain_appearances[chain] = chain_appearances.get(chain, 0) + 1
    repeaters = sum(1 for c in chain_appearances.values() if c > 1)
    repeater_score = min(25, (repeaters / max(len(chain_appearances), 1)) * 50)

    # Factor 4: validator concentration (0-25)
    val_score = 0
    if validator_result:
        n = validator_result.get("count", 100)
        collude = validator_result.get("collude_to_control", 34)
        equal = validator_result.get("equal_weight", False)
        # Fewer validators to collude = higher risk
        val_score = min(25, (1 - collude / max(n, 1)) * 50)
        if equal:
            val_score = min(25, val_score + 5)  # equal weight = easier coordination

    composite = density_score + severity_score + repeater_score + val_score

    return {
        "composite": round(composite, 1),
        "density": round(density_score, 1),
        "severity": round(severity_score, 1),
        "repeaters": round(repeater_score, 1),
        "validator_risk": round(val_score, 1),
        "repeat_offender_chains": {k: v for k, v in chain_appearances.items() if v > 1},
        "rating": "CRITICAL" if composite >= 70 else "HIGH" if composite >= 50 else "MEDIUM" if composite >= 30 else "LOW",
    }


def save_baseline(result, path="noble_baseline.json"):
    """Save a scan result as JSON baseline for future diffs."""
    with open(path, "w") as f:
        json.dump(result, f, indent=2)


def load_baseline(path="noble_baseline.json"):
    """Load a previously saved baseline."""
    with open(path) as f:
        return json.load(f)


if __name__ == "__main__":
    import sys
    import os

    mode = sys.argv[1] if len(sys.argv) > 1 else "scan"
    baseline_path = os.environ.get("NOBLE_BASELINE", "noble_baseline.json")

    print("Noble IBC Collision Monitor")
    print("=" * 72)

    if mode == "scan":
        # Full scan with chain resolution
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
        save_baseline(result, baseline_path)
        print(f"Baseline saved to {baseline_path}")

    elif mode == "diff":
        # Quick scan (no chain resolution) and diff against baseline
        if not os.path.exists(baseline_path):
            print(f"No baseline at {baseline_path}. Run 'scan' first.")
            sys.exit(1)
        baseline = load_baseline(baseline_path)
        current = scan_collisions(resolve_chains=False, verbose=True)
        diff = diff_collisions(baseline, current)
        print()
        if diff["alerts"]:
            for alert in diff["alerts"]:
                print(f"  ALERT: {alert}")
        else:
            print("  No changes since baseline.")
        print()
        print(f"  New collisions: {len(diff['new_collisions'])}")
        print(f"  Growing groups: {len(diff['grown'])}")
        print(f"  New channels: {diff['new_channels']}")

    elif mode == "quick":
        # Fast scan without chain resolution
        result = scan_collisions(resolve_chains=False, verbose=False)
        print(f"\n{result['total_transfer']} channels, {result['collision_groups']} collisions, max={result['max_collision_size']}")
        for peer_ch, data in list(result["collisions"].items())[:10]:
            print(f"  {peer_ch}: {data['count']} -> {data['usdc_denom'][:28]}...")

    print()
    print("The hash does not know who is on the other end.")
