
#ifndef BITCOIN_EXCHANGERATES_H
#define BITCOIN_EXCHANGERATES_H

#include <fs.h>
#include <policy/policy.h>
#include <univalue.h>

constexpr const CAmount exchange_rate_scale = COIN;
const std::string exchange_rates_config_file = "exchangerates.json";

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
     * Load the exchange rate map from the default JSON config file in <datadir>/exchangerates.json.
     *
     * @param[in]   errors        Vector for storing error messages, if there are any.
     * @return true on success
     */
    bool LoadFromDefaultJSONFile(std::vector<std::string>& errors);
    
    /**
     * Load the exchange rate map from a JSON config file.
     *
     * @param[in]   file_path     File path to JSON config file where keys are asset labels and values are exchange rates.
     * @param[in]   errors        Vector for storing error messages, if there are any.
     * @return true on success
     */
    bool LoadFromJSONFile(fs::path file_path, std::vector<std::string>& errors);

    /**
     * Save the exchange rate map to a JSON config file in the node's data directory.
     *
     * @param[in]   errors        Vector for storing error messages, if there are any.
     * @return true on success
     */
    bool SaveToJSONFile(std::vector<std::string>& errors);

    UniValue ToJSON();

    bool LoadFromJSON(std::map<std::string, UniValue> json, std::vector<std::string>& error);
};

#endif // BITCOIN_EXCHANGERATES_H
