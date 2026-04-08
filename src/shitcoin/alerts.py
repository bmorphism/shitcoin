"""
Noble IBC collision alert system.

Generates human-readable alert reports from collision diffs.
Designed to be called from Claude Code scheduled tasks or cron,
with output suitable for Beeper/Slack/email notifications.
"""

from .monitor import (
    scan_collisions,
    diff_collisions,
    risk_score,
    fetch_validators,
    load_baseline,
    save_baseline,
    collision_profile,
    SUPPLY_AT_RISK,
)


HIGH_VALUE_CHANNELS = {"channel-0", "channel-1", "channel-62"}
FARMING_THRESHOLD = 3


def generate_alert_report(baseline_path="noble_baseline.json", save_new_baseline=True):
    """Run a quick scan, diff against baseline, and generate an alert report.

    Returns:
        {
            "has_alerts": bool,
            "report": str,          # human-readable markdown
            "diff": dict,           # raw diff data
            "current": dict,        # current scan result
        }
    """
    try:
        baseline = load_baseline(baseline_path)
    except FileNotFoundError:
        # No baseline — do a full scan and save it
        current = scan_collisions(resolve_chains=False)
        save_baseline(current, baseline_path)
        return {
            "has_alerts": True,
            "report": f"Initial baseline created: {current['total_transfer']} channels, {current['collision_groups']} collisions",
            "diff": None,
            "current": current,
        }

    current = scan_collisions(resolve_chains=False)
    diff = diff_collisions(baseline, current)

    lines = []
    has_critical = False

    # Check for new channels
    if diff["new_channels"] > 0:
        lines.append(f"**{diff['new_channels']} new transfer channels** opened on Noble")

    # Check for new collision groups
    for peer_ch in diff["new_collisions"]:
        data = current["collisions"].get(peer_ch, {})
        severity = "CRITICAL" if peer_ch in HIGH_VALUE_CHANNELS else "WARNING"
        if severity == "CRITICAL":
            has_critical = True
        lines.append(f"{severity}: New collision on {peer_ch} ({data.get('count', '?')} chains)")

    # Check for growing collisions
    for peer_ch in diff["grown"]:
        if peer_ch in HIGH_VALUE_CHANNELS:
            has_critical = True
            old_count = baseline["collisions"].get(peer_ch, {}).get("count", 0)
            new_count = current["collisions"].get(peer_ch, {}).get("count", 0)
            lines.append(f"CRITICAL: {peer_ch} grew from {old_count} to {new_count} chains")

    # Check supply context
    for peer_ch in diff["new_collisions"] + diff["grown"]:
        if peer_ch in SUPPLY_AT_RISK:
            supply_data = SUPPLY_AT_RISK[peer_ch]
            for k, v in supply_data.items():
                if k.startswith("uusdc_on_"):
                    chain = k.replace("uusdc_on_", "")
                    usd = v / 1_000_000
                    if usd > 1_000_000:
                        lines.append(f"  └─ ${usd:,.0f} USDC at risk on {chain}")

    if not lines:
        report = "No changes since last scan."
    else:
        report = "# Noble IBC Collision Alert\n\n" + "\n".join(lines)

    if save_new_baseline:
        save_baseline(current, baseline_path)

    return {
        "has_alerts": len(lines) > 0,
        "has_critical": has_critical,
        "report": report,
        "diff": diff,
        "current": current,
    }


def format_status_report(scan_result, validator_result=None):
    """Generate a full status report (not just diff alerts)."""
    r = risk_score(scan_result, validator_result)

    lines = [
        "# Noble IBC Status Report",
        "",
        f"**Risk Score: {r['composite']}/100 — {r['rating']}**",
        "",
        f"- Transfer channels: {scan_result['total_transfer']} ({scan_result['transfer_open']} open)",
        f"- Collision groups: {scan_result['collision_groups']}",
        f"- Max collision: {scan_result['max_collision_size']} chains",
        "",
    ]

    if validator_result:
        lines.extend([
            f"- Validators: {validator_result['count']} (equal weight: {validator_result['equal_weight']})",
            f"- BFT threshold: {validator_result['bft_threshold']}/{validator_result['count']}",
            f"- Collude to control: {validator_result['collude_to_control']}",
            "",
        ])

    if r["repeat_offender_chains"]:
        lines.append("**Repeat offenders:**")
        for chain, count in sorted(r["repeat_offender_chains"].items(), key=lambda x: -x[1])[:5]:
            lines.append(f"- {chain}: {count} collision groups")

    return "\n".join(lines)
