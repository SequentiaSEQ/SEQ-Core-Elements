#include <asset.h>
#include <assetsdir.h>
#include <consensus/amount.h>
#include <cstdint>
#include <exchangerates.h>
#include <fs.h>
#include <fstream>
#include <logging.h>
#include <policy/policy.h>
#include <uint256.h>
#include <univalue.h>

CAmount ExchangeRateMap::CalculateExchangeValue(const CAmount& amount, const CAsset& asset) {
    auto it = this->find(asset);
    if (it == this->end()) {
        return 0;
    }
    auto scaled_value = it->second.m_scaled_value;
    __uint128_t value = ((__uint128_t)amount * (__uint128_t)scaled_value) / (__uint128_t)exchange_rate_scale;
    if (value > UINT64_MAX) {
        return UINT64_MAX;
    } else {
        return (uint64_t) value;
    }
}

bool ExchangeRateMap::LoadExchangeRatesFromJSONFile(fs::path file_path, std::string& error) {
    // Read config file
    std::ifstream ifs(file_path);
    if (!ifs.is_open()) {
        error = "Failed to open file";
        return false;
    }
    std::stringstream buffer;
    buffer << ifs.rdbuf();

    // Parse as JSON
    std::string rawJson = buffer.str();
    UniValue json;
    if (!json.read(rawJson)) {
        error = "Cannot parse JSON";
        return false;
    }
    std::map<std::string, UniValue> assetMap;
    json.getObjMap(assetMap);

    // Load exchange rates into map
    this->clear();
    for (auto assetEntry : assetMap) {
        auto assetIdentifier = assetEntry.first;
        auto assetData = assetEntry.second;
        CAsset asset = GetAssetFromString(assetIdentifier);
        if (asset.IsNull()) {
            error = strprintf("Unknown label and invalid asset hex: %s", assetIdentifier);
            return false;
        }
        CAmount exchangeRateValue;
        if (assetData.isNum()) {
            exchangeRateValue = assetData.get_int64();
        } else {
            error = strprintf("Invalid value for asset %s: %d", assetIdentifier, assetData.getValStr());
            return false;
        }
        (*this)[asset] = exchangeRateValue;
    }
    return true;
}
