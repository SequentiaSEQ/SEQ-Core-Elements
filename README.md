# Sequentia Project blockchain platform
Sequentia is a Bitcoin sidechain dedicated to asset tokenization and decentralized exchanges.

https://sequentia.io/

Current code is based on Elements Version: 23.2.1

## Installing Prerequisistes

### Install build tools
On Ubuntu (and probably Debian), you should be able to install the prerequisite
build tools with the following command:
```bash
sudo apt install ccache build-essential libtool autotools-dev automake pkg-config bsdmainutils python3
```
YMMV on other software distributions.

### Setup ccache
You may achieve speedups when building and rebuilding by using ccache,
that you may install and configure as follows:
```bash
sudo /usr/sbin/update-ccache-symlinks
echo 'export PATH="/usr/lib/ccache:$PATH"' | tee -a ~/.bashrc
source ~/.bashrc
```

## Configure and Build

### Prepare configuration

```bash
./autogen.sh
make -j$(nproc) -C depends NO_QT=1 NO_NATPMP=1 NO_UPNP=1 NO_ZMQ=1 NO_USDT=1
export CONFIG_SITE=$PWD/depends/x86_64-pc-linux-gnu/share/config.site NOWARN_CXXFLAGS='-Wno-deprecated -Wno-unused-result'
```

### Configure
Simple configuration:
```bash
./configure --enable-any-asset-fees --enable-debug --disable-bench --disable-tests --disable-fuzz-binary
```

I (@fare) have been configuring my test systems this way, enabling tests and extended functional tests:
```bash
./configure --enable-any-asset-fees --enable-debug --disable-bench --disable-fuzz-binary --enable-extended-functional-tests
```

Note that the `--enable-any-asset-fees` flag is an addition by Sequentia,
that will configure RPC documentation to denominate fee rates
using RFU and rfa instead of BTC and sat.

### Last But Not Least, Build
```bash
make -j$(nproc)
```

## Modes
Elements supports a few different pre-set chains for syncing.
Note though some are intended for QA and debugging only:

* Liquid mode: `elementsd -chain=liquidv1` (syncs with Liquid network)
* Bitcoin mainnet mode: `elementsd -chain=main` (not intended to be run for commerce)
* Bitcoin testnet mode: `elementsd -chain=testnet3`
* Bitcoin regtest mode: `elementsd -chain=regtest`
* Elements custom chains: Any other `-chain=` argument. It has regtest-like default parameters that can be over-ridden by the user by a rich set of start-up options.

## Confidential Assets
The latest feature in the Elements blockchain platform is Confidential Assets,
the ability to issue multiple assets on a blockchain where asset identifiers
and amounts are blinded yet auditable through the use of applied cryptography.

 * [Announcement of Confidential Assets](https://blockstream.com/2017/04/03/blockstream-releases-elements-confidential-assets.html)
 * [Confidential Assets Whitepaper](https://blockstream.com/bitcoin17-final41.pdf) to be presented [April 7th at Financial Cryptography 2017](http://fc17.ifca.ai/bitcoin/schedule.html) in Malta
 * [Confidential Assets Tutorial](contrib/assets_tutorial/assets_tutorial.py)
 * [Confidential Assets Demo](https://github.com/ElementsProject/confidential-assets-demo)
 * [Elements Code Tutorial](https://elementsproject.org/elements-code-tutorial/overview) covering blockchain configuration and how to use the main features.

## Features of the Elements blockchain platform

Compared to Bitcoin itself, Elements adds the following features:
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

## License
Elements is released under the terms of the MIT license. See [COPYING](COPYING) for more
information or see http://opensource.org/licenses/MIT.

[confidential-transactions]: https://elementsproject.org/features/confidential-transactions
[opcodes]: https://elementsproject.org/features/opcodes
[federated-peg]: https://elementsproject.org/features#federatedpeg
[signed-blocks]: https://elementsproject.org/features#signedblocks
[asset-issuance]: https://elementsproject.org/features/issued-assets
[schnorr-signatures]: https://elementsproject.org/features/schnorr-signatures

## What is the Elements Project?
Elements is an open source, sidechain-capable blockchain platform. It also allows experiments to more rapidly bring technical innovation to the Bitcoin ecosystem.

Learn more on the [Elements Project website](https://elementsproject.org)

https://github.com/ElementsProject/elementsproject.github.io

## Secure Reporting
See [our vulnerability reporting guide](SECURITY.md)
