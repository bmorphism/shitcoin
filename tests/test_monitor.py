import unittest

from shitcoin.monitor import ibc_denom, scan_collisions


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
