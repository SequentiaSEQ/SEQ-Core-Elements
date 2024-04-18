#!/usr/bin/env python3
# Copyright (c) 2017-2020 The Bitcoin Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Tests exchange rates RPCs"""

from test_framework.blocktools import COINBASE_MATURITY
from test_framework.test_framework import BitcoinTestFramework
from decimal import Decimal
from test_framework.util import (
    assert_equal,
    assert_raises_rpc_error,
)
import json
import os
from pathlib import Path

TESTSDIR = os.path.dirname(os.path.realpath(__file__))

class ExchangeRatesTest(BitcoinTestFramework):
    def set_test_params(self):
        self.setup_clean_chain = True
        self.num_nodes = 1
        self.exchange_rates_json_file = os.path.join(TESTSDIR, "data/initialexchangerates.json")
        self.extra_args = [[
            "-con_any_asset_fees=1",
            "-defaultpeggedassetname=gasset",
            "-initialexchangeratesjsonfile=%s" % self.exchange_rates_json_file
        ]]

    def skip_test_if_missing_module(self):
        self.skip_if_no_wallet()

    def run_test(self):
        node = self.nodes[0]
        self.generate(node, COINBASE_MATURITY + 1)
        
        # Initial rates
        assert node.dumpassetlabels() == {'gasset': 'b2e15d0d7a0c94e4e2ce0fe6e8691b9e451377f6e46e8045a86f7c4b5d4f0f23'}
        initial_rates = { 'gasset': 100000000 }
        assert node.getfeeexchangerates() == initial_rates
        assert self.get_exchange_rates_from_database(node) == initial_rates

        # Add issued asset
        self.issue_amount = Decimal('100')
        self.issuance = node.issueasset(self.issue_amount, 1)
        self.asset = self.issuance['asset']
        self.test_exchange_rates_update(node, initial_rates | { self.asset: 100000000 })

        # Clear rates
        self.test_exchange_rates_update(node, {})

        # Invalid rates
        self.test_invalid_exchange_rates_update(node, "invalid", 1)
        self.test_invalid_exchange_rates_update(node, 1, "invalid")

        # Restore rates
        self.test_exchange_rates_update(node, initial_rates | { self.asset: 100000000 })

    def test_exchange_rates_update(self, node, new_rates):
        node.setfeeexchangerates(new_rates)
        assert node.getfeeexchangerates() == new_rates
        assert self.get_exchange_rates_from_database(node) == new_rates

    def test_invalid_exchange_rates_update(self, node, asset_name, value):
        current_rates = node.getfeeexchangerates()
        assert_raises_rpc_error(-4, "Error loading rates from JSON: - Unknown label and invalid asset hex: %s" % asset_name, node.setfeeexchangerates, { asset_name: value })
        assert node.getfeeexchangerates() == current_rates

    def get_exchange_rates_from_database(self, node):
        database_file_path = Path(node.datadir, self.chain, "exchangerates.json")
        database_file = open(database_file_path)
        data = json.load(database_file)
        database_file.close()
        return data

if __name__ == '__main__':
    ExchangeRatesTest().main()
