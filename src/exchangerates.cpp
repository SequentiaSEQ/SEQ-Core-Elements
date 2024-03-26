#include <asset.h>
#include <consensus/amount.h>
#include <cstdint>
#include <exchangerates.h>
#include <policy/policy.h>
#include <uint256.h>

// TODO: Do we need a lock to protect this?
std::map<CAsset, CAssetExchangeRate> EXCHANGE_RATE_MAP = {};

/**
 * Calculate the exchange value
 *
 * @param[out]  value        Corresponds to CTxMemPoolEntry.nFee      
 * @param[in]   amount       Corresponds to CTxMemPoolEntry.nFeeAmount
 * @param[in]   asset        Corresponds to CTxMemPoolEntry.nFeeAsset
 */
CAmount CalculateExchangeValue(const CAmount& amount, const CAsset& asset) {
    auto it = EXCHANGE_RATE_MAP.find(asset); 
    if (it == EXCHANGE_RATE_MAP.end()) {
        return 0;
    }
    auto scaledValue = it->second.scaledValue;
    // TODO: Find cleaner alternative if possible.
    __uint128_t value = ((__uint128_t)amount * (__uint128_t)scaledValue) / (__uint128_t)EXCHANGE_RATE_SCALE;
    if (value > UINT64_MAX) {
        return UINT64_MAX;
    } else {
        return (uint64_t) value;
    }
}
