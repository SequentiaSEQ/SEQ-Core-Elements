#!/usr/bin/env python3
# Copyright (c) 2017-2020 The Bitcoin Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Tests that fee rates are interpreted in node's RFU (reference fee unit)"""

from test_framework.blocktools import COINBASE_MATURITY
from test_framework.test_framework import BitcoinTestFramework
from decimal import Decimal
from test_framework.util import (
    assert_equal,
)

class AnyAssetFeeRatesTest(BitcoinTestFramework):
    def set_test_params(self):
        self.setup_clean_chain = True
        self.num_nodes = 6
        self.base_args = [
            "-blindedaddresses=1",
            "-initialfreecoins=100000000000",
            "-con_blocksubsidy=0",
            "-con_connect_genesis_outputs=1",
            "-con_any_asset_fees=1",
            "-defaultpeggedassetname=gasset",
            "-txindex=1",
        ]
        self.extra_args = [
            self.base_args + ["-mintxfee=0.001"],
            self.base_args + ["-mintxfee=0.002"],
            self.base_args + ["-paytxfee=0.003"],
            self.base_args + ["-paytxfee=0.004"],
            self.base_args + ["-blockmintxfee=0.001"],
            self.base_args + ["-blockmintxfee=0.001"]]
        self.extra_args[0].append("-anyonecanspendaremine=1")

    def skip_test_if_missing_module(self):
        self.skip_if_no_wallet()

    def init(self):
        self.generate(self.nodes[0], COINBASE_MATURITY + 1)
        self.sync_all()

        self.gasset = 'b2e15d0d7a0c94e4e2ce0fe6e8691b9e451377f6e46e8045a86f7c4b5d4f0f23'

        self.issue_amount = Decimal('100')
        self.issuance = self.nodes[0].issueasset(self.issue_amount, 1)
        self.asset = self.issuance['asset']
        self.issuance_txid = self.issuance['txid']
        self.issuance_vin = self.issuance['vin']

        assert len(self.nodes[0].listissuances()) == 2  # asset & reisuance token

        self.nodes[0].generatetoaddress(1, self.nodes[0].getnewaddress(), invalid_call=False)  # confirm the tx

        self.issuance_addr = self.nodes[0].gettransaction(self.issuance_txid)['details'][0]['address']
        issuance_key = self.nodes[0].dumpissuanceblindingkey(self.issuance_txid, self.issuance_vin)

        new_rates = { "gasset": 100000000, self.asset: 200000000 }
        for node in self.nodes:
            node.address = node.getnewaddress()
            node.importaddress(self.issuance_addr)
            node.importissuanceblindingkey(self.issuance_txid, self.issuance_vin, issuance_key)
            node.setfeeexchangerates(new_rates)

    def test_fee_rates(self):
        # Fee rate parameter

        # First, test fee_rate parameter for fundrawtransaction
        node0 = self.nodes[0]
        self.test_fund_fee(node0, self.gasset, 0.1, Decimal('0.00124550'), options={'fee_rate':50})
        self.test_fund_fee(node0, self.asset, 0.1, Decimal('0.00062275'), options={'fee_rate':50})

        # Without fee rate parameter, it should fallback to the node's minimum tx fee
        self.test_fund_fee(node0, self.gasset, 0.1, Decimal('0.00249100'))
        self.test_fund_fee(node0, self.asset, 0.1, Decimal('0.00124550'))

        # Now test node1, which has a higher minimum tx fee
        node1 = self.nodes[1]
        self.fund_node(node1)
        self.test_fund_fee(node1, self.gasset, 0.1, Decimal('0.00498200'))
        self.test_fund_fee(node1, self.asset, 0.1, Decimal('0.00249100'))

        # Now test node2, which has a higher paytxfee
        node2 = self.nodes[2]
        self.fund_node(node2)
        self.test_fund_fee(node2, self.gasset, 0.1, Decimal('0.00747300'))
        self.test_fund_fee(node2, self.asset, 0.1, Decimal('0.00373650'))

        # Now test node3, which has a (still) higher paytxfee
        node3 = self.nodes[3]
        self.fund_node(node3)
        self.test_fund_fee(node3, self.gasset, 0.1, Decimal('0.00996400'))
        self.test_fund_fee(node3, self.asset, 0.1, Decimal('0.00498200'))

        # Now test that transactions don't get included in a block if fees don't satisfy blockmintxfee
        node4 = self.nodes[4]
        self.fund_node(node4)
        self.test_send_fee(node4, self.asset, 0.1, Decimal('0.00024910'))
        block_hashes = node4.generatetoaddress(1, node4.address, invalid_call=False)
        block = node4.getblock(block_hashes[0])
        assert_equal(block['nTx'], 1)

        # Force a higher fee rate to demonstrate a transaction that does get included
        self.test_send_fee(node4, self.asset, 0.1, Decimal('0.01245500'), options={'fee_rate': 1000})
        block_hashes = node4.generatetoaddress(1, node4.address, invalid_call=False)
        block = node4.getblock(block_hashes[0])
        assert_equal(block['nTx'], 3)

        # Demonstrate that blockmintxfee scales correctly with higher valuations of the same asset,
        # since a transaction with a higher fee amount than the previous transaction is not accepted
        # into a block
        node5 = self.nodes[5]
        self.fund_node(node5)
        node5.setfeeexchangerates({ self.asset: 200000 })
        self.test_send_fee(node5, self.asset, 0.1, Decimal('0.249100'))
        block_hashes = node5.generatetoaddress(1, node5.address, invalid_call=False)
        block = node5.getblock(block_hashes[0])
        assert_equal(block['nTx'], 1)

    def test_fund_fee(self, node, asset, amount, expected_fee, options=None):
        raw_tx = node.createrawtransaction(outputs=[
            {self.nodes[0].address: amount, 'asset': asset},
            {'fee': 0,'fee_asset': asset}])
        funded_tx = node.fundrawtransaction(hexstring=raw_tx, options=options)['hex']
        tx = node.decoderawtransaction(funded_tx)
        assert_equal(tx['fee'], {asset: expected_fee})

    def test_send_fee(self, node, asset, amount, expected_fee, options=None):
        raw_tx = node.createrawtransaction(outputs=[
            {self.nodes[0].address: amount, 'asset': asset},
            {'fee': 0,'fee_asset': asset}])
        funded_tx = node.fundrawtransaction(hexstring=raw_tx, options=options)['hex']
        tx = node.decoderawtransaction(funded_tx)
        assert_equal(tx['fee'], {asset: expected_fee})
        blinded_tx = node.blindrawtransaction(funded_tx)
        signed_tx = node.signrawtransactionwithwallet(blinded_tx)['hex']
        node.sendrawtransaction(signed_tx)

    def fund_node(self, node):
        self.nodes[0].sendtoaddress(
            address=node.address,
            amount=5.0,
            assetlabel=self.gasset)
        self.nodes[0].sendtoaddress(
            address=node.address,
            amount=5.0,
            assetlabel=self.asset)
        self.generatetoaddress(self.nodes[0], 1, self.nodes[0].address)
        self.sync_all()

    def run_test(self):
        self.init()
        self.test_fee_rates()

if __name__ == '__main__':
    AnyAssetFeeRatesTest().main()
