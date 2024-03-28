
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
    CAmount scaledValue;

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
 * @param[in]   amount       Corresponds to CTxMemPoolEntry.nFeeAmount
 * @param[in]   asset        Corresponds to CTxMemPoolEntry.nFeeAsset
 * @return the value at current exchange rate. Corresponds to CTxMemPoolEntry.nFee      
 */
CAmount CalculateExchangeValue(const CAmount& amount, const CAsset& asset);

/**
 * Populate the exchange rate map using a config file.
 *
 * @param[in]   file_path     File path to INI config file where keys are asset labels and values are exchange rates.
 * @param[in]   error         String reference for storing error message, if there is any.
 * @return true on success
 */
bool LoadExchangeRatesFromJSONFile(std::string file_path, std::string& error);


#endif // BITCOIN_EXCHANGERATES_H
