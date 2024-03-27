
#ifndef BITCOIN_EXCHANGERATES_H
#define BITCOIN_EXCHANGERATES_H

#include <asset.h>
#include <consensus/amount.h>
#include <policy/policy.h>
#include <uint256.h>

class CAssetExchangeRate
{
public:
    /** Fee rate. */
    CAmount scaledValue; // TODO: Maybe use exatoken (10^18) rather than gigatoken (10^9).

    CAssetExchangeRate() : scaledValue(0) { }
    CAssetExchangeRate(CAmount amount) : scaledValue(amount) { }
    CAssetExchangeRate(uint64_t amount) : scaledValue(amount) { }
};

// TODO: Do we need a lock to protect this?
extern std::map<CAsset, CAssetExchangeRate> g_exchange_rate_map;

const CAmount g_exchange_rate_scale = 1000000000L;

/**
 * Calculate the exchange value
 *
 * @param[out]  value        Corresponds to CTxMemPoolEntry.nFee      
 * @param[in]   amount       Corresponds to CTxMemPoolEntry.nFeeAmount
 * @param[in]   asset        Corresponds to CTxMemPoolEntry.nFeeAsset
 */
CAmount CalculateExchangeValue(const CAmount& amount, const CAsset& asset);

#endif // BITCOIN_EXCHANGERATES_H
