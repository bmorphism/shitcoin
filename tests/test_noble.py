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

    def test_unknown_chain_raises(self):
        with self.assertRaises(ValueError):
            shitcoin.noble_usdc_on("rebecca_roberts_chain")
