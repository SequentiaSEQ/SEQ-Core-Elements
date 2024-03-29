
#ifndef BITCOIN_EXCHANGERATES_H
#define BITCOIN_EXCHANGERATES_H

#include <asset.h>
#include <consensus/amount.h>
#include <fs.h>
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

class ExchangeRateMap : public std::map<CAsset, CAssetExchangeRate>
{
private:
    static ExchangeRateMap* _instance;
    const CAmount exchange_rate_scale = 1000000000L;

    ExchangeRateMap() {}
public:
    static ExchangeRateMap& GetInstance();
    void Initialize(); 

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
    bool LoadExchangeRatesFromJSONFile(fs::path file_path, std::string& error);
};

#endif // BITCOIN_EXCHANGERATES_H
