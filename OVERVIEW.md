# No Coin: Technical Overview

## Introduction

### Abstract

There should be no specific transaction fee currency on the sidechain. Thus, users can propose transactions to block signers with the fee expressed as any amount of any asset issued on the sidechain. In the most common expected use cases, transaction fees on the sidechain would ideally be paid as a fraction of the same asset(s) being transferred.

### Motivation

In many blockchains, the requirement for users to have a “gas bank” in a native cryptocurrency (or peg) in order to transfer any other token creates barriers to entry and introduces frictions in user experience, preventing a broader network effect. In Sequentia, block proposers have incentives to accept any token as long as it has a recognized value and sufficient liquidity. They will retrieve and compare fee values by querying price data from CEXs or DEX oracles. If a transaction is taking too long to be included in a block or seems like it might never be included, the user may broadcast a new one with Replace-by-fee. To facilitate users’ choice, every block proposer may also signal the list of tokens that will be accepted according to a selection dictated by purely free-market logic. This freedom also improves scalability since there will be far fewer transactions made with the only purpose of providing “gas” to a wallet, which implies higher transaction costs and pollution for the network (UTXO dust). 

## Specification

Network participants will be able to specify the asset used to pay fees when constructing a transaction using a new `fee_asset` parameter that will be added to existing RPCs for creating and modifying transactions. If left unspecified, the wallet will default to the asset being sent in the transaction.

Node operators will be able to assign weight values to issued assets on the network using a new RPC named `setfeeexchangerates`. These exchange rates are then used by the mempool to prioritize transactions during block assembly. If the exchange rate for certain asset has not been specified by the node operator, then it is considered blacklisted, and all transactions using that asset for fee payment will not be added to their mempool nor relayed to other nodes.

To assist wallets with fee asset selection, nodes will expose their current valuations with a new RPC named `getfeeexchangerates`. Additionally, node operators will be able to statically configure their exchange rates using a JSON config file which also will use the same schema as both `getfeeexchangerates` and `setfeeexchangerates`.

For the initial prototype, this schema will simply be a key value map, where the keys are the asset identifiers and the values are the weight value. An asset identifier can either be the hex id or a label specified by the user using Element's `assetdir` parameter. The weight value is a 64-bit integer[^1] that will be divided by one billion to enable high-enough precision without resorting to floating point numbers.

Here is an example config file that valuates `USDt`, a wrapped Bitcoin `S-BTC`, and an unlabelled asset:
```json
{ 
      "S-BTC": 5,
      "USDt": 10,
      "33244cc19dd9df0fd901e27246e3413c8f6a560451e2f3721fb6f636791087c7": 3
}
```

All of the weight values are translated into an abstract reference unit so they can be directly compared by the node's mempool. In the future, we might want to extend this schema to allow an explicit reference unit, as well as per-asset denominations to handle a wider breadth of asset valuations.

## Implementation

The No Coin feature will be implemented as an extension to the [Elements blockchain platform](https://elementsproject.org/), which is itself an extension of Bitcoin. The most relevant feature that Elements adds to Bitcoin is asset issuance, which enables new types of assets to be issued and transferred between network participants. 

Elements also uses a federation of block signers as a low-cost alternative to proof-of-work mining process. This interacts positively with No Coin since it increases the predictability of whether a transaction will be accepted in a given block. Wallets can use the block signer's published exchange rates to perform fee estimations, and can infer the schedule of block proposers based on the deterministic round robin algorithm used to select the next proposer.

All this being said, Elements enforces that transaction fees are paid in what it refers to as the policy asset, which in most cases is a pegged Bitcoin asset. Consequently, No Coins requires that this restriction be removed, which will require a number of changes to policy code. Consensus, however, will remain unchanged.

### Transaction

No structural changes to the transaction model will need to be made since Elements already requires fees to be explicitly specified as a transaction output[^2]. And since the output already has an asset field, it will just be a matter of softcoding its value rather than hardcoding it to the chain’s policy asset.

The hardcoding of the fee asset can be found in [src/rpc/rawtransaction_util.cpp#L295-L297](https://github.com/ElementsProject/elements/blob/2d298f7e3f76bc6c19d9550af4fd1ef48cf0b2a6/src/rpc/rawtransaction_util.cpp#L295-L297).

To softcode it, we will need to make changes to the fee output parser found in [src/rpc/rawtransaction_util.cpp#L321-L327](
https://github.com/ElementsProject/elements/blob/2d298f7e3f76bc6c19d9550af4fd1ef48cf0b2a6/).

### Mempool

There are both structural and behavioral changes that need to be made to the mempool in order for transactions to be correctly valuated in the presence of transactions paid with different assets.

Just as with transaction construction described before, the mempool must use the softcoded asset specified in the fee output rather than the chain's hardcoded policy asset. The hardcoding of the fee asset can be found in [src/validation.cpp#L885-L886](https://github.com/ElementsProject/elements/blob/2d298f7e3f76bc6c19d9550af4fd1ef48cf0b2a6/src/validation.cpp#L885-L886).

It also must separate the fee value from the fee amount. This is where structural changes are required. The `CtxMemPoolEntry` class requires two additional fields[^3] `nFeeAsset` and `nFeeValue` to be added after [src/txmempool.h#L98](https://github.com/ElementsProject/elements/blob/2d298f7e3f76bc6c19d9550af4fd1ef48cf0b2a6/src/txmempool.h#L98).

`nFeeAsset` is the asset used to pay the transaction fees, and `nFeeValue` is the value of `nFee` in the node's abstract reference unit. `nFee` is insufficient on its own because transactions with fees paid in different assets aren't directly comparable. Additionally, `nFeeValue` needs to be updated whenever the exchange rates change. When this happens, the fees of all transactions currently in the mempool must be recomputed. Since transactions can sit in a mempool indefinitely, it's important that transactions with depreciated fee assets are evicted. Likewise, transactions with appreciating fee assets should be bumped in priority in order to maximize the value of fee rewards to block proposers.

Recomputing fees is non-trivial because transactions are weighted by not only their own value but also by their ancestors and descendents. Fortunately, there is a similar functionality already in place for prioritizing transactions based on off-chain payments, so the solution will end up looking very similar to the `CtxMemPool:PrioritiseTransaction` method defined at [src/txmempool.cpp#L1003-L1031](https://github.com/ElementsProject/elements/blob/2d298f7e3f76bc6c19d9550af4fd1ef48cf0b2a6/src/txmempool.cpp#L1003-L1031).

### Price server

In the simplest case, a block signer can statically configure their node with an exchange rate map which never changes. This would require no external program, just a single JSON file as described previously in the specification.

As the value of the network grows, however, block signers will want to dynamically change update these exchange rates. Thus the need for a price server: an external service which queries one or many exchanges to find the current market value of a given asset, and then feeds this value to the node via the aforementioned `setfeeexchangerates` RPC.

Being an external service and not integrated into the node, the pricing algorithm can be as simple or as complicated as needed. A simple algorithm may just compute the median of the exchange values over a certain interval of time. A more advanced algorithm might store historical data and use it to compute volatility and liquidity.

The utility of a price server is not limited to block signers. Even though they are the only participants that collect fees, every node on the network will maintain its own mempool, and therefore will need to perform some sort of asset valuation in order to make meaningful decisions about which transctions to add to it.

One solution is for nodes to simply ask the block signers what their exchange rates are. Since block proposers are selected deterministically, the price server can inherit the published exchange rates of the next block proposer. With this setup, the node's mempool will represent not the transactions it deems most valuable, but rather, the transactions that are most likely to end up in the next block, thereby benefitting the network by broadcasting transactions that are most relevant to it.

Alternatively, a node operator may choose to set up its own exchange rate map in the same way that a block signer would. I.e., with a static config file or a price server.

The objective here is not to prescribe a single solution for all use cases, but to demonstrate the range of possibilities enabled by this setup. For the testnet launch, Sequentia will implement a minimal price server to use as an example and baseline, optimizing for simplicity and extensibility.

### Exchange rate RPCs

The exchange RPCs will provide a read and write interface to the node's exchange rate map used for comparing fees. `getfeeexchangerates` returns the entire exchange rate map, and `setfeeeexchangerates` overrides the current exchange rate map with whatever is provided as its inputs. Note that there is no union between the current and new exchange rate map: the new map completely overrides the current.

| Category | Name | Changes |
| -------- | ---- | ------- |
| `exchangerates` | `getfeeexchangerates` | Returns the node's exchange rate map of assets to reference weight values |
| `exchangerates` | `setfeeexchangerates` | Updates the nodes exchange rate map with new mapping provided as input |

Example usage, with the same data as the config file shown previously:
```bash
$ sequentia-cli setfeeexchangerates '{ "S-BTC": 5, "USDt": 10, "33244cc19dd9df0fd901e27246e3413c8f6a560451e2f3721fb6f636791087c7": 3 }'

$ sequentia-cli getfeeexchangerates
{
  "S-BTC": 5,
  "USDt": 10,
  "33244cc19dd9df0fd901e27246e3413c8f6a560451e2f3721fb6f636791087c7": 3
}
```

### Chain parameters

To enable the No Coin feature, two additional chain parameters will be added. They can be configured using command line arguments passed to the node daemon at startup. The arguments are defined as follows:

| Name | Type | Purpose |
| -------- | ---- | ------- |
| `con_any_asset_fees` | BOOL | Global flag for enabling the No Coin feature |
| `exchangeratesjsonfile` | STR | File path to JSON file for configuring the fee exchange rate map | 

### Changes to existing RPCs

Of course, none of these features are meaningful without being exposed in some way to network participants. To that end, we will be extending the existing RPCs to enable specifying which asset fees are paid with, and change defaults to be consistent with this new capability.

Broadly speaking, there are two categories of RPCs that need to be changed: RPCs which create and/or modify transaction fees, and read-only RPCs that provide information about those fees.

The former category includes:

| Category | Name | Changes |
| -------- | ---- | ------- |
| `rawtransactions` | `createrawtransaction` | Add `fee_asset` field to specify the asset used for fee payment |
| `rawtransactions` | `fundrawtransaction` | Reinterpret or rename `fee_rate` and `feeRate` to be in fee asset and in fee value unit respectively. Add `fee_asset` field to specify the fee asset. In the result, make `fee` denominated in the fee asset, add a `fee_asset` field, then add a `fee_value` for the value as interpreted by the node. |
| `wallet` | `walletcreatefundedpsbt` | Reinterpret or rename `fee_rate` and `feeRate` to be in fee asset and in fee value unit respectively. Add `fee_asset` field to specify the fee asset. In the result, make `fee` denominated in the fee asset, add a `fee_asset` field, then add a `fee_value` for the value as interpreted by the node. | 
| `wallet` | `sendtoaddress` | Add `fee_asset` field to specify the asset used for fee payment, otherwise default to the asset being sent in the transaction |
| `wallet` | `sendmany` | Add `fee_asset` field to specify the asset used for fee payment, otherwise default to the asset being sent in the transaction |

And the latter:

| Category | Name | Changes |
| -------- | ---- | ------- |
| `blockchain` | `getblock` | Add a `fee_details` field that is a breakdown of fees per fee asset (map from fee_asset tag to fee_amount CAmount, e.g. `{"wbtc":"123","wusd":"456"}`, except with nAsset tags rather than symbolic names) | 
| `blockchain` | `getblockstats` | Make all the sums, totals, averages, etc., denominated in fee value unit, and only available if the rates have been recorded or otherwise provided. For totals, add a field `fee_details` with breakdown per fee asset. |
| `blockchain` | `getmempoolinfo` | The `total_fee`, `mempoolinfee`, `minrelaytxfee` fields will be denominated in the implicit fee value unit as defined by the node's current exchange rates. | 
| `blockchain` | `getmempoolancestors` | The `fees` sub-element in the result needs an additional `fee_asset` field | 
| `blockchain` | `getmempooldescendents` | The `fees` sub-element in the result needs an additional `fee_asset` field | 
| `blockchain` | `getmempoolentry` | The `fees` sub-element  in the result needs an additional `fee_asset` field | 
| `blockchain` | `getrawmempool` | The `fees` sub-element in the result needs an additional `fee_asset` field |
| `blockchain` | `savemempool` | The `fees` sub-element in the result needs an additional `fee_asset` field | 
| `blockchain` | `gettxoutsetinfo` | Add field `unclaimed_rewards_details` with a breakdown by fee asset | 
| `mining` | `getblocktemplate` | In the result, make `fee` denominated in the fee asset, add a `fee_asset` field, then add a `fee_value` for the value as interpreted by the node. | 
| `mining` | `prioritisetransaction` | Add an optional fourth parameter, only valid if the dummy parameter is present, that specifies the `fee_asset` used for the prioritization. If absent, assume the node's fee value unit. | 
| `rawtransactions` | `analyzepsbt` | Add `fee_asset` field in result to specify the asset used for fee payment | 
| `rawtransactions` | `decodepsbt` | Add `fee_asset` field in result to specify the asset used for fee payment | 
| `rawtransactions` | `testmempoolaccept` | Add  | 
| `util` | `estimatesmartfee` |  Add an optional parameter for the `fee_asset`, defaulting to the fee value unit for the node, and use it for the estimate. In the result, add a `fee_asset` field. | 
| `wallet` | `bumpfee` | Add an options field for the `fee_asset`, defaulting to the same fee asset as the existing transaction, and return `fee_asset` field with the same value | 
| `wallet` | `psbtbumpfee` | Add an options field for the `fee_asset`, defaulting to the same fee asset as the existing transaction, and return `fee_asset` field with the same value |  
| `wallet` | `gettransaction` | Add a `fee_asset` field in the result, and in each of the details |
| `wallet` | `listsinceblock` | In each of the returned transactions, add a `fee_asset` field |
| `wallet` | `listtransactions` | In each of the returned transactions, add a `fee_asset` field |

There are also a few RPCs where only the documentation needs to be updated:

| Category | Name | Changes |
| -------- | ---- | ------- |
| `network` | `getpeerinfo` | Declare `minfeefilter` field as being in the node's fee value unit | 
| `wallet` | `getbalances` | Document support for multiple assets |
| `wallet` | `getwalletinfo` | Declare `getwallet` field as being in the node's fee value unit |
| `wallet` | `listunspent` | Declare `ancestorfees` as being in the node's fee value unit | 

## Appendix

### Time estimates

Our current estimate is that that it will take three weeks / 120 man hours to implement the core protocol changes and build functional tests for them, assuming the developers are familiar with the Elements codebase and the particular modules mentioned in this document. An additional three weeks / 120 man hours will be needed for the pricing server, including integrations with existing currency exchanges and thorough documentation for node operators. Finally, updating and documenting RPCs will likely take another two weeks / 80 man hours, though many of them will need to be updated to enable functional tests for previous tasks, so will have already been happening in parallel with the core protocol changes.

This adds up to a total of eight weeks / 320 man hours. Then another two weeks / 80 man hours for unknown unknowns, the total estimate comes to ten weeks / 400 man hours. 

### Bootstrapping

A sidechain with no native asset means that no assets are generated in the genesis block and there is no block subsidy for block signers. However, there still needs to be a way for network participants to issue assets, which require UTXOs as inputs for entropy and commitment. A more invasive protocol change might be possible that could remove the requirement for inputs during asset issuance, but we don't consider this worthwhile for the purposes of No Coin.  

To that end, we will be creating an asset named GENESIS to bootstrap asset creation on the network. There will be no hardcoding of GENESIS as the asset required for asset issuance, however, so as soon as other assets populate the network they can be used instead. GENESIS tokens will most likely remain indefinitely as collectibles or burnt after some to be determined block height.

### Overflow protection

Bitcoin and after it Elements uses a CAmount (uint64_t) for adding up fees (in sat) and computing fee rates (in sat/kvB). With a total amount MAX_MONEY a max total number of coins 2.1e15 (<2^51), so there can't be overflow when adding fewer than 8784 numbers.

### Asset denominations

When issuing a USD-indexed token, you'll probably want fewer than 10⁸ subdivisions as with BTC and satoshis, or you'll be limited to 21 million dollars total. Maybe only 10² subdivisions (cents) and then the limit is a relatively comfortable 21 trillion (which should last a few decades despite the current exponential inflation). Similarly for all currencies (for VES and similar shitcoins, have 10^-4 "subdivisions" or such). That gives them all assets a common range of utility so the exchange rates should stay within range of what makes sense with a divisor of 10^9 (and actually, with three extra decimals of precision possible considering the MAX_MONEY constraint).

[^1]: See section on [overflow protections](#overflow-protection) for how this interacts with max total number of coins enforced by consensus code.

[^2]: In Elements, the reason that the transaction fees must have an explicit output rather than be implicit as in Bitcoin is due to its Confidential Transactions feature. Confidential Transactions enable network participates are able to "blind" the amounts and assets involved in a transaction to anyone who doesn't have a blinding key. The transaction fees must still be exposed to mempools, however, so the fee output must be made explicit and unblinded. See https://elementsproject.org/features/confidential-transactions for more information about this feature.

[^3]: In `CtxMempoolEntry`, the fee asset and amount can be retrieved from the transaction reference, so both of these values are effectively a cache to avoid expensive parent transaction lookups. The performance impact has not been measured, but since Bitcoin and Elements both cache `nFee`, it seemed rational to follow suit and cache these values as well.
