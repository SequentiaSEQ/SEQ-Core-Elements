#!/usr/bin/env python3
# Copyright (c) 2020-2021 The Bitcoin Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Test transaction relay behavior during IBD:
- Set fee filters to MAX_MONEY
- Don't request transactions
- Ignore all transaction messages
"""

from decimal import Decimal
import time

from test_framework.messages import (
        CInv,
        COIN,
        CTransaction,
        from_hex,
        msg_inv,
        msg_tx,
        MSG_WTX,
)
from test_framework.p2p import (
        NONPREF_PEER_TX_DELAY,
        P2PDataStore,
        P2PInterface,
        p2p_lock
)
from test_framework.test_framework import BitcoinTestFramework

# ELEMENTS: this number is implied by DEFAULT_MIN_RELAY_TX_FEE in src/net_processing.cpp
#  which is different in Elements/Bitcoin and cannot be changed by command-line args
MAX_FEE_FILTER = Decimal(9936506) / COIN
NORMAL_FEE_FILTER = Decimal(100) / COIN


class P2PIBDTxRelayTest(BitcoinTestFramework):
    def set_test_params(self):
        self.setup_clean_chain = True
        self.num_nodes = 2
        self.extra_args = [
            ["-minrelaytxfee={}".format(NORMAL_FEE_FILTER)],
            ["-minrelaytxfee={}".format(NORMAL_FEE_FILTER)],
        ]

    def run_test(self):
        self.log.info("Check that nodes set minfilter to MAX_MONEY while still in IBD")
        for node in self.nodes:
            assert node.getblockchaininfo()['initialblockdownload']
            self.wait_until(lambda: all(peer['minfeefilter'] == MAX_FEE_FILTER for peer in node.getpeerinfo()))

        self.log.info("Check that nodes don't send getdatas for transactions while still in IBD")
        peer_inver = self.nodes[0].add_p2p_connection(P2PDataStore())
        txid = 0xdeadbeef
        peer_inver.send_and_ping(msg_inv([CInv(t=MSG_WTX, h=txid)]))
        # The node should not send a getdata, but if it did, it would first delay 2 seconds
        self.nodes[0].setmocktime(int(time.time() + NONPREF_PEER_TX_DELAY))
        peer_inver.sync_send_with_ping()
        with p2p_lock:
            assert txid not in peer_inver.getdata_requests
        self.nodes[0].disconnect_p2ps()

        self.log.info("Check that nodes don't process unsolicited transactions while still in IBD")
        # A transaction hex pulled from tx_valid.json. There are no valid transactions since no UTXOs
        # exist yet, but it should be a well-formed transaction.
        # ELEMENTS: this is an arbitrary transaction pulled from a dummy regtest network
        rawhex = "0200000001010000000000000000000000000000000000000000000000000000000000000000ffffffff0502ca000101" + \
            "ffffffff0201230f4f5d4b7c6fa845806ee4f67713459e1b69e8e60fcee2e4940c7a0d5de1b201000000000000000000016" + \
            "a01230f4f5d4b7c6fa845806ee4f67713459e1b69e8e60fcee2e4940c7a0d5de1b201000000000000000000266a24aa21a9" + \
            "ed94f15ed3a62165e4a0b99699cc28b48e19cb5bc1b1f47155db62d63f1e047d45000000000000012000000000000000000" + \
            "000000000000000000000000000000000000000000000000000000000"
        assert self.nodes[1].decoderawtransaction(rawhex) # returns a dict, should not throw
        tx = from_hex(CTransaction(), rawhex)
        peer_txer = self.nodes[0].add_p2p_connection(P2PInterface())
        with self.nodes[0].assert_debug_log(expected_msgs=["received: tx"], unexpected_msgs=["was not accepted"]):
            peer_txer.send_and_ping(msg_tx(tx))
        self.nodes[0].disconnect_p2ps()

        # Come out of IBD by generating a block
        self.generate(self.nodes[0], 1)

        self.log.info("Check that nodes reset minfilter after coming out of IBD")
        for node in self.nodes:
            assert not node.getblockchaininfo()['initialblockdownload']
            self.wait_until(lambda: all(peer['minfeefilter'] == NORMAL_FEE_FILTER for peer in node.getpeerinfo()))

        self.log.info("Check that nodes process the same transaction, even when unsolicited, when no longer in IBD")
        peer_txer = self.nodes[0].add_p2p_connection(P2PInterface())
        # ELEMENTS FIXME:
        # with self.nodes[0].assert_debug_log(expected_msgs=["was not accepted"]):
        #   peer_txer.send_and_ping(msg_tx(tx))

if __name__ == '__main__':
    P2PIBDTxRelayTest().main()
