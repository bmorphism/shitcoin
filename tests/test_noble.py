import unittest

import shitcoin


class TestNoble(unittest.TestCase):
    def test_usdc_on_osmosis(self):
        denom = shitcoin.noble_usdc_on("osmosis")
        self.assertTrue(denom.startswith("ibc/"))
        self.assertEqual(len(denom), 4 + 64)  # ibc/ + 64 hex chars
        # This denom is the same before and after the EVM migration.
        # The hash doesn't know who is running Noble.
        self.assertEqual(
            denom,
            shitcoin.ibc_denom("transfer", "channel-750", "uusdc"),
        )

    def test_usdc_on_cosmoshub(self):
        denom = shitcoin.noble_usdc_on("cosmoshub")
        self.assertEqual(
            denom,
            shitcoin.ibc_denom("transfer", "channel-536", "uusdc"),
        )

    def test_usdc_on_dydx(self):
        # dYdX channel-0 to Noble. The most important channel.
        denom = shitcoin.noble_usdc_on("dydx")
        self.assertEqual(
            denom,
            shitcoin.ibc_denom("transfer", "channel-0", "uusdc"),
        )

    def test_precompute_all(self):
        results = shitcoin.precompute_all()
        self.assertEqual(len(results), len(shitcoin.NOBLE_CHANNELS))
        for chain_name, data in results.items():
            self.assertIn("usdc_denom", data)
            self.assertTrue(data["usdc_denom"].startswith("ibc/"))
            self.assertIn("raw_path", data)
            self.assertIn("uusdc", data["raw_path"])

    def test_precompute_future(self):
        future = shitcoin.precompute_future(100)
        self.assertEqual(len(future), 100)
        # All denoms are unique (no collisions in 100 sequential channels)
        denoms = list(future.values())
        self.assertEqual(len(set(denoms)), 100)

    def test_determinism(self):
        """Same inputs, same outputs. Always. Before and after migration."""
        d1 = shitcoin.noble_usdc_on("osmosis")
        d2 = shitcoin.noble_usdc_on("osmosis")
        self.assertEqual(d1, d2)

    def test_alien_indistinguishable(self):
        """An alien chain using the same channel-id produces the same denom.
        The hash cannot tell the difference. This is the vulnerability."""
        legitimate = shitcoin.ibc_denom("transfer", "channel-750", "uusdc")
        # A ghost chain that claims to be on channel-750
        alien = shitcoin.ibc_denom("transfer", "channel-750", "uusdc")
        self.assertEqual(legitimate, alien)
        # The function accepted (str, str, str). It did not ask for a proof.

    def test_collision_kujira_agoric(self):
        """kujira and agoric both use channel-62 as peer channel.
        They produce the SAME USDC denom. This is a real on-chain collision."""
        kujira = shitcoin.noble_usdc_on("kujira")
        agoric = shitcoin.noble_usdc_on("agoric")
        self.assertEqual(kujira, agoric)
        self.assertEqual(
            kujira,
            "ibc/FE98AAD68F02F03565E9FA39A5E627946699B2B07115889ED812D8BA639576A9",
        )

    def test_detect_collisions(self):
        """detect_collisions() finds channels shared by multiple chains."""
        collisions = shitcoin.detect_collisions()
        self.assertIn("channel-62", collisions)
        self.assertIn("kujira", collisions["channel-62"]["chains"])
        self.assertIn("agoric", collisions["channel-62"]["chains"])
        self.assertTrue(collisions["channel-62"]["denom"].startswith("ibc/"))

    def test_live_census(self):
        """Live Noble API census (2026-04-07): collision landscape."""
        census = shitcoin.live_collision_census()
        self.assertEqual(census["total_transfer"], 157)
        self.assertEqual(census["collision_groups"], 24)
        self.assertEqual(census["max_collision_size"], 18)
        # channel-0 is the worst: 18 chains all produce the same USDC denom
        self.assertEqual(census["top_collisions"]["channel-0"]["count"], 18)
        self.assertIn("dydx", census["top_collisions"]["channel-0"]["chains"])
        # channel-1: 16 chains including Babylon
        self.assertEqual(census["top_collisions"]["channel-1"]["count"], 16)
        self.assertIn("babylon", census["top_collisions"]["channel-1"]["chains"])

    def test_channel0_mega_collision(self):
        """18 chains share channel-0. All produce the same USDC denom.
        This includes dYdX — the single largest USDC destination."""
        dydx = shitcoin.ibc_denom("transfer", "channel-0", "uusdc")
        # Any chain whose first Noble connection is channel-0 gets this denom
        self.assertEqual(
            dydx,
            "ibc/8E27BA2D5493AF5636760E354E46004562C46AB7EC0CC4C1CA14E9E20E2545B5",
        )

    def test_authenticated_denom_distinguishes_collisions(self):
        """chain_fingerprint distinguishes chains that SHA256 path cannot."""
        dydx = shitcoin.authenticated_denom("dydx-mainnet-1", "genesis-dydx", "channel-0")
        titan = shitcoin.authenticated_denom("titan_18888-1", "genesis-titan", "channel-0")
        # Same denom (the vulnerability)
        self.assertEqual(dydx["denom"], titan["denom"])
        # Different fingerprint (the fix)
        self.assertNotEqual(dydx["fingerprint"], titan["fingerprint"])

    def test_chain_fingerprint_deterministic(self):
        fp1 = shitcoin.chain_fingerprint("osmosis-1", "genesis-osmosis")
        fp2 = shitcoin.chain_fingerprint("osmosis-1", "genesis-osmosis")
        self.assertEqual(fp1, fp2)
        self.assertEqual(len(fp1), 16)  # 16 hex chars

    def test_unknown_chain_raises(self):
        with self.assertRaises(ValueError):
            shitcoin.noble_usdc_on("rebecca_roberts_chain")
