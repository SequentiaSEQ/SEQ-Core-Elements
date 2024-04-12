
#ifndef BITCOIN_EXCHANGERATES_H
#define BITCOIN_EXCHANGERATES_H

#include <fs.h>
#include <policy/policy.h>

constexpr const CAmount exchange_rate_scale = 1000000000L;

class CAssetExchangeRate
{
public:
    /** Fee rate. */
    CAmount m_scaled_value;

    CAssetExchangeRate() : m_scaled_value(0) { }
    CAssetExchangeRate(CAmount amount) : m_scaled_value(amount) { }
    CAssetExchangeRate(uint64_t amount) : m_scaled_value(amount) { }
};

class ExchangeRateMap : public std::map<CAsset, CAssetExchangeRate>
{
private:
    ExchangeRateMap() {}
    ExchangeRateMap(const CAmount& default_asset_rate) {
        (*this)[::policyAsset] = default_asset_rate;
    }
public:
    static ExchangeRateMap& GetInstance() {
        static ExchangeRateMap instance(exchange_rate_scale); // Guaranteed to be destroyed and instantiated only once
        return instance;
    }

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
