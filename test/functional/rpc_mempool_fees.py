#!/usr/bin/env python3
# Copyright (c) 2017-2020 The Bitcoin Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Tests mempool RPCs"""

from test_framework.blocktools import COINBASE_MATURITY
from test_framework.test_framework import BitcoinTestFramework
from decimal import Decimal

class MempoolFeesTest(BitcoinTestFramework):
    def set_test_params(self):
        self.setup_clean_chain = True
        self.num_nodes = 1
        self.extra_args = [[
            "-con_any_asset_fees=1",
            "-defaultpeggedassetname=gasset",
        ]]

    def skip_test_if_missing_module(self):
        self.skip_if_no_wallet()

    def run_test(self):
        node = self.nodes[0]
        self.generate(node, COINBASE_MATURITY + 1)
        gasset_hexid = 'b2e15d0d7a0c94e4e2ce0fe6e8691b9e451377f6e46e8045a86f7c4b5d4f0f23'

        assert node.dumpassetlabels() == { 'gasset': gasset_hexid }
        initial_rates = { 'gasset': 100000000 }
        assert node.getfeeexchangerates() == initial_rates

        self.issue_amount = Decimal('100')
        self.issuance = node.issueasset(self.issue_amount, 1)
        self.asset = self.issuance['asset']
        txid = self.issuance['txid']
       
        assert node.getmempoolinfo()['minrelaytxfee'] == Decimal('0.00001')

        fees1 = node.getrawmempool(verbose=True)[txid]['fees']
        assert fees1['asset'] == gasset_hexid
        assert fees1['value'] == Decimal('0.00120320')
        
        node.setfeeexchangerates({ 'gasset': 200000000 })
        fees2 = node.getrawmempool(verbose=True)[txid]['fees']
        assert fees2['asset'] == gasset_hexid
        assert fees2['value'] == Decimal('0.00240640')

if __name__ == '__main__':
    MempoolFeesTest().main()
