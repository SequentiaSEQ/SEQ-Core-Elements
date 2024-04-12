#!/usr/bin/env python3
# Copyright (c) 2017-2020 The Bitcoin Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Tests fees being paid in any asset featur"""

from test_framework.blocktools import COINBASE_MATURITY
from test_framework.test_framework import BitcoinTestFramework
from decimal import Decimal
from test_framework.util import (
    assert_equal,
    assert_raises_rpc_error,
)

class AnyAssetFeeTest(BitcoinTestFramework):
    def set_test_params(self):
        self.setup_clean_chain = True
        self.num_nodes = 2
        self.extra_args = [[
            "-blindedaddresses=1",
            "-initialfreecoins=1000000000",
            "-con_blocksubsidy=0",
            "-con_connect_genesis_outputs=1",
            "-con_any_asset_fees=1",
            "-defaultpeggedassetname=gasset",
            "-txindex=1",
        ]] * self.num_nodes
        self.extra_args[0].append("-anyonecanspendaremine=1")

    def skip_test_if_missing_module(self):
        self.skip_if_no_wallet()

    def init(self):
        self.generate(self.nodes[0], COINBASE_MATURITY + 1)
        self.sync_all()

        assert self.nodes[0].dumpassetlabels() == {'gasset': 'b2e15d0d7a0c94e4e2ce0fe6e8691b9e451377f6e46e8045a86f7c4b5d4f0f23'}

        self.issue_amount = Decimal('100')
        self.issuance = self.nodes[0].issueasset(self.issue_amount, 1)
        self.asset = self.issuance['asset']
        #token = issuance['token']
        self.issuance_txid = self.issuance['txid']
        self.issuance_vin = self.issuance['vin']

        assert len(self.nodes[0].listissuances()) == 2  # asset & reisuance token

        self.nodes[0].generatetoaddress(1, self.nodes[0].getnewaddress(), invalid_call=False)  # confirm the tx

        self.issuance_addr = self.nodes[0].gettransaction(self.issuance_txid)['details'][0]['address']
        self.nodes[1].importaddress(self.issuance_addr)

        issuance_key = self.nodes[0].dumpissuanceblindingkey(self.issuance_txid, self.issuance_vin)
        self.nodes[1].importissuanceblindingkey(self.issuance_txid, self.issuance_vin, issuance_key)
        issuances = self.nodes[1].listissuances()
        assert (issuances[0]['tokenamount'] == 1 and issuances[0]['assetamount'] == self.issue_amount) \
            or (issuances[1]['tokenamount'] == 1 and issuances[1]['assetamount'] == self.issue_amount)

        self.node0_address = self.nodes[0].getnewaddress()
        self.node0_nonct_address = self.nodes[0].getaddressinfo(self.node0_address)["unconfidential"]
        self.node1_address = self.nodes[1].getnewaddress()
        self.node1_nonct_address = self.nodes[1].getaddressinfo(self.node1_address)["unconfidential"]

        self.nodes[0].setfeeexchangerates({ "gasset": 100000000, self.asset: 100000000 })
        self.nodes[1].setfeeexchangerates({ "gasset": 100000000, self.asset: 100000000 })

    def transfer_asset_to_node1(self):
        node0_balance = self.nodes[0].getbalances()["mine"]
        assert len(node0_balance["trusted"]) == 3
        assert_equal(node0_balance["trusted"][self.asset], self.issue_amount)

        self.nodes[0].sendtoaddress(
            address=self.node1_address,
            amount=2.0,
            assetlabel=self.asset,
            fee_assetlabel=self.asset)

        self.generatetoaddress(self.nodes[0], 1, self.node0_address)
        self.sync_all()

        node0_new_balance = self.nodes[0].getbalances()["mine"]
        assert_equal(node0_new_balance["trusted"][self.asset], self.issue_amount - Decimal('2') - Decimal('0.00049820'))
        assert_equal(node0_new_balance["trusted"]["gasset"], node0_balance["trusted"]["gasset"])
        assert_equal(node0_new_balance["immature"][self.asset], Decimal('0.00049820'))

        node1_balance = self.nodes[1].getbalances()["mine"]
        assert len(node1_balance["trusted"]) == 1
        assert len(node1_balance["immature"]) == 0
        assert_equal(node1_balance["trusted"][self.asset], Decimal('2'))

        self.nodes[1].sendtoaddress(
            address=self.node0_address,
            amount=1.0,
            assetlabel=self.asset,
            fee_assetlabel=self.asset)

        self.generatetoaddress(self.nodes[1], 1, self.node1_address)
        self.sync_all()

        node1_new_balance = self.nodes[1].getbalances()["mine"]
        assert len(node1_new_balance["trusted"]) == 1
        assert_equal(node1_new_balance["trusted"][self.asset], Decimal('2') - Decimal('1')  - Decimal('0.00049820'))
        assert_equal(node1_new_balance["immature"][self.asset], Decimal('0.00049820'))

    def multiple_asset_fees_transfers(self):
        node0_balance = self.nodes[0].getbalances()["mine"]
        node1_balance = self.nodes[1].getbalances()["mine"]
        assert len(node0_balance["trusted"]) == 3
        assert len(node1_balance["trusted"]) == 1

        self.nodes[0].sendtoaddress(
            address=self.node1_address,
            amount=1.0,
            assetlabel=self.asset,
            fee_assetlabel=self.asset)

        self.nodes[0].sendtoaddress(
            address=self.node1_address,
            amount=2.0,
            assetlabel=self.asset,
            fee_assetlabel="gasset")

        self.nodes[0].sendtoaddress(
            address=self.node1_address,
            amount=3.0,
            assetlabel="gasset",
            fee_assetlabel=self.asset)

        self.nodes[0].sendtoaddress(
            address=self.node1_address,
            amount=4.0,
            assetlabel="gasset",
            fee_assetlabel="gasset")

        self.generatetoaddress(self.nodes[0], 1, self.node0_address)
        self.sync_all()

        node0_new_balance = self.nodes[0].getbalances()["mine"]
        assert_equal(node0_new_balance["trusted"][self.asset], node0_balance["trusted"][self.asset] - Decimal('3') - Decimal('0.00125160'))
        assert_equal(node0_new_balance["trusted"]["gasset"], node0_balance["trusted"]["gasset"] - Decimal('7') - Decimal('0.00125160'))

        node1_new_balance = self.nodes[1].getbalances()["mine"]
        assert len(node1_new_balance["trusted"]) == 2
        assert_equal(node1_new_balance["trusted"]["gasset"], Decimal('7'))
        assert_equal(node1_new_balance["trusted"][self.asset], node1_balance["trusted"][self.asset] + Decimal('3'))

    def transfer_asset_amount_including_fee(self):
        node1_balance = self.nodes[1].getbalances()["mine"]
        assert len(node1_balance["trusted"]) == 2

        self.nodes[1].sendtoaddress(
            address=self.node0_address,
            amount=self.nodes[1].getbalance()[self.asset],
            assetlabel=self.asset,
            subtractfeefromamount=True)

        self.nodes[1].sendtoaddress(
            address=self.node0_address,
            amount=self.nodes[1].getbalance()["gasset"],
            assetlabel="gasset",
            subtractfeefromamount=True)

        self.generatetoaddress(self.nodes[1], 1, self.node0_address)
        self.sync_all()
        node1_new_balance = self.nodes[1].getbalances()["mine"]
        assert len(node1_new_balance["trusted"]) == 0

    def run_test(self):
        self.init()

        self.transfer_asset_to_node1()

        self.multiple_asset_fees_transfers()

        self.transfer_asset_amount_including_fee()

if __name__ == '__main__':
    AnyAssetFeeTest().main()
