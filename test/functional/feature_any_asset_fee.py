#!/usr/bin/env python3
# Copyright (c) 2017-2020 The Bitcoin Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Tests fees being paid in any asset feature"""

from test_framework.blocktools import COINBASE_MATURITY
from test_framework.test_framework import BitcoinTestFramework
from decimal import Decimal
from test_framework.util import (
    assert_equal,
)

class AnyAssetFeeTest(BitcoinTestFramework):
    def set_test_params(self):
        self.setup_clean_chain = True
        self.num_nodes = 2
        self.extra_args = [[
            "-blindedaddresses=1",
            "-initialfreecoins=10000000000",
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
        assert self.nodes[0].getfeeexchangerates() == { 'gasset': 100000000 }

        self.node0_address = self.nodes[0].getnewaddress()
        self.node1_address = self.nodes[1].getnewaddress()

        self.issue_amount = Decimal('100')
        self.issuance = self.nodes[0].issueasset(
            assetamount = self.issue_amount,
            tokenamount = 1,
            blind = False,
            denomination = 2)
        self.asset = self.issuance['asset']
        #token = issuance['token']
        self.issuance_txid = self.issuance['txid']
        self.issuance_vin = self.issuance['vin']

        self.generatetoaddress(self.nodes[0], 1, self.node0_address)  # confirm the tx

        assert len(self.nodes[0].listissuances()) == 2  # asset & devcoin
        issuances = self.nodes[0].listissuances()
        assert (issuances[0]['denomination'] == 2 and issuances[1]['denomination'] == 8) \
            or (issuances[0]['denomination'] == 8 and issuances[1]['denomination'] == 2)

        self.issuance_addr = self.nodes[0].gettransaction(self.issuance_txid)['details'][0]['address']
        self.nodes[1].importaddress(self.issuance_addr)

        issuance_key = self.nodes[0].dumpissuanceblindingkey(self.issuance_txid, self.issuance_vin)
        self.nodes[1].importissuanceblindingkey(self.issuance_txid, self.issuance_vin, issuance_key)
        issuances = self.nodes[1].listissuances()
        assert (issuances[0]['tokenamount'] == 1 and issuances[0]['assetamount'] == self.issue_amount) \
            or (issuances[1]['tokenamount'] == 1 and issuances[1]['assetamount'] == self.issue_amount)

        new_rates = { "gasset": 100000000, self.asset: 100000000 }
        self.nodes[0].setfeeexchangerates(new_rates)
        assert self.nodes[0].getfeeexchangerates() == new_rates
        self.nodes[1].setfeeexchangerates(new_rates)
        assert self.nodes[1].getfeeexchangerates() == new_rates

    def transfer_asset_to_node1(self):
        node0_balance = self.nodes[0].getbalances()["mine"]
        assert len(node0_balance["trusted"]) == 3
        assert_equal(node0_balance["trusted"][self.asset], self.issue_amount)

        self.nodes[0].sendtoaddress(
            address=self.node1_address,
            amount=2.0,
            assetlabel=self.asset,
            fee_asset_label=self.asset)

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
            fee_asset_label=self.asset)

        self.generatetoaddress(self.nodes[1], 1, self.node1_address)
        self.sync_all()

        node1_new_balance = self.nodes[1].getbalances()["mine"]
        assert len(node1_new_balance["trusted"]) == 1
        assert_equal(node1_new_balance["trusted"][self.asset], Decimal('2') - Decimal('1')  - Decimal('0.00049820'))
        assert_equal(node1_new_balance["immature"][self.asset], Decimal('0.00049820'))

    def multiple_asset_fees_transfers_with_sendtoaddress(self):
        node0_balance = self.nodes[0].getbalances()["mine"]
        node1_balance = self.nodes[1].getbalances()["mine"]
        assert len(node0_balance["trusted"]) == 3
        assert len(node1_balance["trusted"]) == 1

        self.nodes[0].sendtoaddress(
            address=self.node1_address,
            amount=1.0,
            assetlabel=self.asset,
            fee_asset_label=self.asset)

        self.nodes[0].sendtoaddress(
            address=self.node1_address,
            amount=2.0,
            assetlabel=self.asset,
            fee_asset_label="gasset")

        self.nodes[0].sendtoaddress(
            address=self.node1_address,
            amount=3.0,
            assetlabel="gasset",
            fee_asset_label=self.asset)

        self.nodes[0].sendtoaddress(
            address=self.node1_address,
            amount=4.0,
            assetlabel="gasset",
            fee_asset_label="gasset")

        self.generatetoaddress(self.nodes[0], 1, self.node0_address)
        self.sync_all()

        node0_new_balance = self.nodes[0].getbalances()["mine"]
        assert_equal(node0_new_balance["trusted"][self.asset], node0_balance["trusted"][self.asset] - Decimal('3') - Decimal('0.00125160'))
        assert_equal(node0_new_balance["trusted"]["gasset"], node0_balance["trusted"]["gasset"] - Decimal('7') - Decimal('0.00125160'))

        node1_new_balance = self.nodes[1].getbalances()["mine"]
        assert len(node1_new_balance["trusted"]) == 2
        assert_equal(node1_new_balance["trusted"]["gasset"], Decimal('7'))
        assert_equal(node1_new_balance["trusted"][self.asset], node1_balance["trusted"][self.asset] + Decimal('3'))

    def multiple_asset_fees_transfers_with_sendmany(self):
        node0_balance = self.nodes[0].getbalances()["mine"]["trusted"]
        node1_balance = self.nodes[1].getbalances()["mine"]["trusted"]
        assert len(node0_balance) == 3
        assert len(node1_balance) == 2

        tx1_id = self.nodes[0].sendmany(
            amounts={ self.node1_address: 1.0 },
            output_assets={ self.node1_address: self.asset },
            fee_asset=self.asset)
        tx1 = self.nodes[0].gettransaction(tx1_id)

        tx2_id = self.nodes[0].sendmany(
            amounts={ self.node1_address: 2.0 },
            output_assets={ self.node1_address: self.asset },
            fee_asset='gasset')
        tx2 = self.nodes[0].gettransaction(tx2_id)

        self.generatetoaddress(self.nodes[0], 1, self.node0_address)
        self.sync_all()

        node0_new_balance = self.nodes[0].getbalances()['mine']['trusted']
        assert_equal(node0_new_balance[self.asset], node0_balance[self.asset] - Decimal('3') + tx1['fee'][self.asset])
        assert_equal(node0_new_balance['gasset'], node0_balance['gasset'] + tx2['fee']['gasset'])

        node1_new_balance = self.nodes[1].getbalances()['mine']['trusted']
        assert len(node1_new_balance) == 2
        assert_equal(node1_new_balance['gasset'], Decimal('7'))
        assert_equal(node1_new_balance[self.asset], node1_balance[self.asset] + Decimal('3'))

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

    def raw_transfer_asset_to_node1(self):
        node0 = self.nodes[0]
        node1 = self.nodes[1]

        raw_tx = node0.createrawtransaction(outputs=[{self.node1_address: 1.0, 'asset': self.asset }])
        funded_tx = node0.fundrawtransaction(raw_tx)['hex']
        assert node0.decoderawtransaction(funded_tx)['fee'] == { self.asset: Decimal('0.00049820')}
        blinded_tx = node0.blindrawtransaction(funded_tx)
        signed_tx = node0.signrawtransactionwithwallet(blinded_tx)['hex']
        sent_tx = node0.sendrawtransaction(signed_tx)
        tx = node0.gettransaction(sent_tx)
        assert tx['fee'] ==  { self.asset: Decimal('-0.00049820') }

        self.generatetoaddress(node0, 1, self.node1_address)
        self.sync_all()
        node1_new_balance = node1.getbalances()['mine']
        assert_equal(node1_new_balance['trusted'][self.asset], Decimal('1'))

    def run_test(self):
        self.init()

        self.transfer_asset_to_node1()

        self.multiple_asset_fees_transfers_with_sendtoaddress()

        self.multiple_asset_fees_transfers_with_sendmany()

        self.transfer_asset_amount_including_fee()

        self.raw_transfer_asset_to_node1()

if __name__ == '__main__':
    AnyAssetFeeTest().main()
