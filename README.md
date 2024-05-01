Sequentia Project blockchain platform
====================================

https://sequentia.io/

Sequentia is a Bitcoin sidechain dedicated to asset tokenization and decentralized exchanges.

Current code is based on Elements Version: 23.2.1

Quick Ubuntu build instructions for development:
-----

Install build tools
```bash
sudo apt install ccache build-essential libtool autotools-dev automake pkg-config bsdmainutils python3 libevent-dev libboost-dev
```
Install clang 15:
```bash
wget -O - "https://apt.llvm.org/llvm.sh" | sudo bash -s 15
```
Setup ccache:
```bash
sudo /usr/sbin/update-ccache-symlinks
echo 'export PATH="/usr/lib/ccache:$PATH"' | tee -a ~/.bashrc
source ~/.bashrc
```
Build:
```bash
./autogen.sh
./contrib/install_db4.sh .
export CC=clang-15 CXX=clang++-15 BDB_LIBS="-L${BDB_PREFIX}/lib -ldb_cxx-4.8" BDB_CFLAGS="-I${BDB_PREFIX}/include"
./configure --without-gui --without-natpmp --without-miniupnpc
make -j$(nproc)
```
To speed up the build if not necessary, disable bench and tests in configure:
```bash
./configure --without-gui --without-natpmp --without-miniupnpc --disable-bench --disable-tests
```

Modes
-----

Elements supports a few different pre-set chains for syncing. Note though some are intended for QA and debugging only:

* Liquid mode: `elementsd -chain=liquidv1` (syncs with Liquid network)
* Bitcoin mainnet mode: `elementsd -chain=main` (not intended to be run for commerce)
* Bitcoin testnet mode: `elementsd -chain=testnet3`
* Bitcoin regtest mode: `elementsd -chain=regtest`
* Elements custom chains: Any other `-chain=` argument. It has regtest-like default parameters that can be over-ridden by the user by a rich set of start-up options.

Confidential Assets
----------------
The latest feature in the Elements blockchain platform is Confidential Assets,
the ability to issue multiple assets on a blockchain where asset identifiers
and amounts are blinded yet auditable through the use of applied cryptography.

 * [Announcement of Confidential Assets](https://blockstream.com/2017/04/03/blockstream-releases-elements-confidential-assets.html)
 * [Confidential Assets Whitepaper](https://blockstream.com/bitcoin17-final41.pdf) to be presented [April 7th at Financial Cryptography 2017](http://fc17.ifca.ai/bitcoin/schedule.html) in Malta
 * [Confidential Assets Tutorial](contrib/assets_tutorial/assets_tutorial.py)
 * [Confidential Assets Demo](https://github.com/ElementsProject/confidential-assets-demo)
 * [Elements Code Tutorial](https://elementsproject.org/elements-code-tutorial/overview) covering blockchain configuration and how to use the main features.

Features of the Elements blockchain platform
----------------

Compared to Bitcoin itself, it adds the following features:
 * [Confidential Assets][asset-issuance]
 * [Confidential Transactions][confidential-transactions]
 * [Federated Two-Way Peg][federated-peg]
 * [Signed Blocks][signed-blocks]
 * [Additional opcodes][opcodes]

Previous elements that have been integrated into Bitcoin:
 * Segregated Witness
 * Relative Lock Time

Elements deferred for additional research and standardization:
 * [Schnorr Signatures][schnorr-signatures]

Additional RPC commands and parameters:
* [RPC Docs](https://elementsproject.org/en/doc/)

The CI (Continuous Integration) systems make sure that every pull request is built for Windows, Linux, and macOS,
and that unit/sanity tests are run automatically.

License
-------
Elements is released under the terms of the MIT license. See [COPYING](COPYING) for more
information or see http://opensource.org/licenses/MIT.

[confidential-transactions]: https://elementsproject.org/features/confidential-transactions
[opcodes]: https://elementsproject.org/features/opcodes
[federated-peg]: https://elementsproject.org/features#federatedpeg
[signed-blocks]: https://elementsproject.org/features#signedblocks
[asset-issuance]: https://elementsproject.org/features/issued-assets
[schnorr-signatures]: https://elementsproject.org/features/schnorr-signatures

What is the Elements Project?
-----------------
Elements is an open source, sidechain-capable blockchain platform. It also allows experiments to more rapidly bring technical innovation to the Bitcoin ecosystem.

Learn more on the [Elements Project website](https://elementsproject.org)

https://github.com/ElementsProject/elementsproject.github.io

Secure Reporting
------------------
See [our vulnerability reporting guide](SECURITY.md)

