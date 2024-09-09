#!/usr/bin/env python3
# Copyright (c) 2017-2020 The Bitcoin Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Tests fees being paid in any asset feature"""

from test_framework.blocktools import COINBASE_MATURITY
from test_framework.test_framework import BitcoinTestFramework
from decimal import Decimal
from test_framework.util import (
    assert_raises_rpc_error,
)

class AnyAssetFeeScenariosTest(BitcoinTestFramework):
    def set_test_params(self):
        self.setup_clean_chain = True
        self.num_nodes = 2
        self.extra_args = [[
            "-blindedaddresses=0",
            "-walletrbf=1",
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

        self.issue_amount1 = Decimal('100')
        self.issuance1 = self.nodes[0].issueasset(self.issue_amount1, 1, False)
        self.asset1 = self.issuance1['asset']
        self.issuance_txid1 = self.issuance1['txid']
        self.issuance_vin1 = self.issuance1['vin']

        assert len(self.nodes[0].listissuances()) == 2  # asset & reisuance token

        self.nodes[0].generatetoaddress(1, self.node0_address, invalid_call=False)  # confirm the tx

        new_rates = { "gasset": 100000000, self.asset1: 100000000}
        self.nodes[0].setfeeexchangerates(new_rates)
        assert self.nodes[0].getfeeexchangerates() == new_rates
        self.nodes[1].setfeeexchangerates(new_rates)
        assert self.nodes[1].getfeeexchangerates() == new_rates

        self.nodes[0].sendtoaddress(address=self.node0_address, amount=100.0, assetlabel=self.asset1, subtractfeefromamount=True)

        self.nodes[0].generatetoaddress(1, self.node0_address, invalid_call=False)  # confirm the tx

        self.issuance_addr1 = self.nodes[0].gettransaction(self.issuance_txid1)['details'][0]['address']
        self.nodes[1].importaddress(self.issuance_addr1)

        issuance_key1 = self.nodes[0].dumpissuanceblindingkey(self.issuance_txid1, self.issuance_vin1)
        self.nodes[1].importissuanceblindingkey(self.issuance_txid1, self.issuance_vin1, issuance_key1)
        issuances = self.nodes[1].listissuances()
        assert (issuances[0]['tokenamount'] == 1 and issuances[0]['assetamount'] == self.issue_amount1) \
            or (issuances[1]['tokenamount'] == 1 and issuances[1]['assetamount'] == self.issue_amount1)

        self.issue_amount2 = Decimal('10')
        self.issuance2 = self.nodes[0].issueasset(
                assetamount=self.issue_amount2,
                tokenamount=1,
                blind=False,
                fee_asset = self.asset1)
        self.asset2 = self.issuance2['asset']
        self.issuance_txid2 = self.issuance2['txid']
        self.issuance_vin2 = self.issuance2['vin']

        self.nodes[0].generatetoaddress(1, self.node0_address, invalid_call=False)  # confirm the tx

        new_rates = { "gasset": 100000000, self.asset1: 100000000, self.asset2: 200000000}
        self.nodes[0].setfeeexchangerates(new_rates)

        assert self.nodes[0].getfeeexchangerates() == new_rates
        assert self.nodes[1].getfeeexchangerates() != new_rates

        asset1amount = self.nodes[0].getbalance()[self.asset1]
        self.nodes[0].sendtoaddress(address=self.node0_address, amount=asset1amount, assetlabel=self.asset1, subtractfeefromamount=True)
        self.nodes[0].sendtoaddress(address=self.node0_address, amount=10.0, assetlabel=self.asset2, subtractfeefromamount=True)

        self.nodes[0].generatetoaddress(1, self.node0_address, invalid_call=False)

    def scenario1(self):
        self.nodes[0].sendtoaddress(
            address=self.node1_address,
            amount=2.0,
            assetlabel=self.asset1,
            fee_asset_label=self.asset1)

        self.sync_all()

        self.nodes[1].generatetoaddress(1, self.node1_address, invalid_call=False)

        balance = self.nodes[1].getreceivedbyaddress(address=self.node1_address, assetlabel=self.asset1)

        assert balance == Decimal(2.0)

        self.sync_all()

    def scenario2(self):
        tx = self.nodes[0].sendtoaddress(
            address=self.node1_address,
            amount=1.0,
            assetlabel=self.asset2,
            fee_asset_label=self.asset2)

        assert len(self.nodes[0].getrawmempool()) == 1

        assert_raises_rpc_error(-26, "min relay fee not met,", self.nodes[1].sendrawtransaction, self.nodes[0].getrawtransaction(tx))

        assert len(self.nodes[1].getrawmempool()) == 0

        self.nodes[0].generatetoaddress(1, self.node0_address, invalid_call=False)
        self.sync_all()

    def scenario3(self):
        new_rates = { "gasset": 100000000, self.asset1: 100000000, self.asset2: 1000000}
        self.nodes[1].setfeeexchangerates(new_rates)

        tx = self.nodes[0].sendtoaddress(
            address=self.node1_address,
            amount=1.0,
            assetlabel=self.asset2,
            fee_asset_label=self.asset2)

        assert len(self.nodes[0].getrawmempool()) == 1

        assert_raises_rpc_error(-26, "min relay fee not met,", self.nodes[1].sendrawtransaction, self.nodes[0].getrawtransaction(tx))

        assert len(self.nodes[1].getrawmempool()) == 0

        self.nodes[0].generatetoaddress(1, self.node0_address, invalid_call=False)
        self.sync_all()

    def scenario4(self):
        new_rates = { "gasset": 100000000, self.asset1: 100000000, self.asset2: 100000000}
        self.nodes[1].setfeeexchangerates(new_rates)

        tx = self.nodes[0].sendtoaddress(
            address=self.node1_address,
            amount=1.0,
            assetlabel=self.asset2,
            fee_asset_label=self.asset2)

        self.sync_all()

        assert self.nodes[0].getrawmempool(True)[tx]['fees']['base'] == Decimal('0.00002570')
        assert self.nodes[1].getrawmempool(True)[tx]['fees']['base'] == Decimal('0.00002570')

        tx1 = self.nodes[0].bumpfee(tx)['txid']
        self.sync_all()

        assert self.nodes[0].getrawmempool(True)[tx1]['fees']['base'] == Decimal('0.00003213')
        assert self.nodes[1].getrawmempool(True)[tx1]['fees']['base'] == Decimal('0.00003213')

        self.nodes[0].generatetoaddress(1, self.node0_address, invalid_call=False)
        self.sync_all()

    def scenario5(self):
        new_rates = { "gasset": 100000000, self.asset1: 100000000, self.asset2: 1000000}
        self.nodes[1].setfeeexchangerates(new_rates)

        tx = self.nodes[0].sendtoaddress(
            address=self.node1_address,
            amount=1.0,
            assetlabel=self.asset2,
            fee_asset_label=self.asset2)

        assert self.nodes[0].getrawmempool(True)[tx]['fees']['base'] == Decimal('0.00002570')
        assert_raises_rpc_error(-26, "min relay fee not met,", self.nodes[1].sendrawtransaction, self.nodes[0].getrawtransaction(tx))

        tx1 = self.nodes[0].bumpfee(tx, {'fee_asset': self.asset1})['txid']
        self.sync_all()

        assert self.nodes[0].getrawmempool(True)[tx1]['fees']['asset'] == self.asset1
        assert self.nodes[0].getrawmempool(True)[tx1]['fees']['base'] == Decimal('0.00009801')
        assert self.nodes[1].getrawmempool(True)[tx1]['fees']['asset'] == self.asset1
        assert self.nodes[1].getrawmempool(True)[tx1]['fees']['base'] == Decimal('0.00009801')

        self.nodes[0].generatetoaddress(1, self.node0_address, invalid_call=False)
        self.sync_all()


    def run_test(self):
        self.init()

        # Send asset1 with paying fees in asset1
        self.scenario1()

        # Send asset2 with paying fees in asset2, accetped on node0 not accepted on node1 without price set
        self.scenario2()

        # Send asset2 with paying fees in asset2, accetped on node0 not accepted on node1 with price set lower on node1
        self.scenario3()

        # Bump fee amount for tx, check that the tx is on node1 after bumping the fee
        self.scenario4()

        # RBF, bumpf fee with changing the asset to pay the fee, check that the tx is on node1 after RBF
        self.scenario5()

if __name__ == '__main__':
    AnyAssetFeeScenariosTest().main()
