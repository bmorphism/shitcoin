import unittest

from shitcoin.monitor import ibc_denom, diff_collisions, fetch_validators, risk_score


class TestMonitor(unittest.TestCase):
    def test_ibc_denom_matches_noble(self):
        """Monitor's ibc_denom must match noble.py's implementation."""
        from shitcoin.noble import ibc_denom as noble_ibc_denom
        # dYdX channel-0
        self.assertEqual(
            ibc_denom("transfer", "channel-0", "uusdc"),
            noble_ibc_denom("transfer", "channel-0", "uusdc"),
        )
        # Osmosis channel-750
        self.assertEqual(
            ibc_denom("transfer", "channel-750", "uusdc"),
            noble_ibc_denom("transfer", "channel-750", "uusdc"),
        )

    def test_dydx_denom(self):
        self.assertEqual(
            ibc_denom("transfer", "channel-0", "uusdc"),
            "ibc/8E27BA2D5493AF5636760E354E46004562C46AB7EC0CC4C1CA14E9E20E2545B5",
        )

    def test_diff_no_change(self):
        baseline = {"total_transfer": 157, "collisions": {
            "channel-0": {"count": 18, "noble_channels": ["ch-33"]},
        }}
        current = {"total_transfer": 157, "collisions": {
            "channel-0": {"count": 18, "noble_channels": ["ch-33"]},
        }}
        diff = diff_collisions(baseline, current)
        self.assertEqual(diff["new_channels"], 0)
        self.assertEqual(len(diff["new_collisions"]), 0)
        self.assertEqual(len(diff["grown"]), 0)

    def test_diff_new_collision(self):
        baseline = {"total_transfer": 157, "collisions": {}}
        current = {"total_transfer": 160, "collisions": {
            "channel-99": {"count": 2, "noble_channels": ["ch-500", "ch-501"],
                           "usdc_denom": "ibc/DEAD..."},
        }}
        diff = diff_collisions(baseline, current)
        self.assertEqual(diff["new_channels"], 3)
        self.assertIn("channel-99", diff["new_collisions"])
        self.assertTrue(any("NEW COLLISION" in a for a in diff["alerts"]))

    def test_bft_math(self):
        """BFT threshold: 2/3+1 of N validators needed to sign."""
        # For N=16: threshold=11, collude=6
        n = 16
        threshold = (n * 2 // 3) + 1
        collude = (n - 1) // 3 + 1
        self.assertEqual(threshold, 11)
        self.assertEqual(collude, 6)

    def test_diff_growing(self):
        baseline = {"total_transfer": 157, "collisions": {
            "channel-0": {"count": 18, "noble_channels": []},
        }}
        current = {"total_transfer": 159, "collisions": {
            "channel-0": {"count": 20, "noble_channels": []},
        }}
        diff = diff_collisions(baseline, current)
        self.assertIn("channel-0", diff["grown"])
        self.assertTrue(any("GROWING" in a for a in diff["alerts"]))

    def test_risk_score_critical(self):
        """The real Noble numbers should produce CRITICAL rating."""
        scan = {
            "unique_peer_channels": 69,
            "max_collision_size": 18,
            "collisions": {
                "channel-0": {"count": 18, "chains": ["dydx-mainnet-1", "hyve_7847-1", "viexchain-1"]},
                "channel-1": {"count": 16, "chains": ["bbn-1", "hyve_7847-1", "viexchain-1"]},
                "channel-2": {"count": 13, "chains": ["hyve_7847-1", "viexchain-1"]},
            },
        }
        validators = {"count": 15, "collude_to_control": 5, "equal_weight": True}
        r = risk_score(scan, validators)
        self.assertEqual(r["rating"], "CRITICAL")
        self.assertIn("hyve_7847-1", r["repeat_offender_chains"])
        self.assertIn("viexchain-1", r["repeat_offender_chains"])
