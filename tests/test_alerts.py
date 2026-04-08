import unittest

from shitcoin.alerts import generate_alert_report, format_status_report


class TestAlerts(unittest.TestCase):
    def test_format_status_report(self):
        scan = {
            "total_transfer": 157,
            "transfer_open": 152,
            "collision_groups": 24,
            "max_collision_size": 18,
            "unique_peer_channels": 69,
            "collisions": {
                "channel-0": {"count": 18, "chains": ["dydx-mainnet-1"]},
            },
        }
        validators = {"count": 15, "collude_to_control": 5, "bft_threshold": 11, "equal_weight": True}
        report = format_status_report(scan, validators)
        self.assertIn("Risk Score:", report)
        self.assertIn("15", report)
        self.assertIn("Collude to control: 5", report)
