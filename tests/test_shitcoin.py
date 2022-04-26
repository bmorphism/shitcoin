import unittest

import shitcoin


class Test(unittest.TestCase):
    def test_MARBLE(self):
        self.assertEqual(
            shitcoin.cw20_ibc_denom(
                "transfer",
                "channel-169",
                "cw20:juno1g2g7ucurum66d42g8k5twk34yegdq8c82858gz0tq2fc75zy7khssgnhjl",
            ),
            "ibc/F6B691D5F7126579DDC87357B09D653B47FDCE0A3383FF33C8D8B544FE29A8A6",
        )

    def test_RAC(self):
        self.assertEqual(
            shitcoin.cw20_ibc_denom(
                "transfer",
                "channel-169",
                "cw20:juno1r4pzw8f9z0sypct5l9j906d47z998ulwvhvqe5xdwgy8wf84583sxwh0pa",
            ),
            "ibc/6BDB4C8CCD45033F9604E4B93ED395008A753E01EECD6992E7D1EA23D9D3B788",
        )

    def test_DOG(self):
        self.assertEqual(
            shitcoin.cw20_ibc_denom(
                "transfer",
                "channel-169",
                "cw20:juno1t3h9jrgl9ngz2rlqmcap07jcsugtw95ek5wvh38dzd4xunh3p6js0uyt75",
            ),
            "ibc/097BAB21B9871A3A9C286878562582BA62FB2EFD5D41D123BDC204A1AC2271D1",
        )

    def test_HABERMAS(self):
        self.assertEqual(
            shitcoin.cw20_ibc_denom(
                "transfer",
                "channel-169",
                "cw20:juno14cr367h7vrgkx4u6q6prk2s29rlrp8hn478q2r9zrpyhkx7mx5dsuw7syw",
            ),
            "ibc/8C8BFD62EA45671ADEBA13835AF3DEAAA0661EA7D1283BB1C54D679898DB29FB",
        )
