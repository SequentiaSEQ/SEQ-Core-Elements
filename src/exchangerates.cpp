#include <asset.h>
#include <assetsdir.h>
#include <consensus/amount.h>
#include <cstdint>
#include <exchangerates.h>
#include <fs.h>
#include <fstream>
#include <policy/policy.h>
#include <uint256.h>
#include <univalue.h>

// TODO: Do we need a lock to protect this?
std::map<CAsset, CAssetExchangeRate> g_exchange_rate_map = {};

CAmount CalculateExchangeValue(const CAmount& amount, const CAsset& asset) {
    auto it = g_exchange_rate_map.find(asset);
    if (it == g_exchange_rate_map.end()) {
        return 0;
    }
    auto scaledValue = it->second.scaledValue;
    // TODO: Find cleaner alternative if possible.
    __uint128_t value = ((__uint128_t)amount * (__uint128_t)scaledValue) / (__uint128_t)g_exchange_rate_scale;
    if (value > UINT64_MAX) {
        return UINT64_MAX;
    } else {
        return (uint64_t) value;
    }
}

bool LoadExchangeRatesFromJSONFile(std::string file_path, std::string& error)
{
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

    // Load exchange rates into global map
    for (auto assetEntry : assetMap) {
        auto assetIdentifier = assetEntry.first;
        auto assetData = assetEntry.second;
        CAsset asset = GetAssetFromString(assetIdentifier);
        if (asset.IsNull()) {
            error = strprintf("Unknown label and invalid asset hex: %s", asset.GetHex());
            return false;
        }
        CAmount exchangeRateValue;
        if (assetData.isNum()) {
            exchangeRateValue = assetData.get_int();
        } else if (assetData.isObject()) {
            std::map<std::string, UniValue> assetFields;
            assetData.getObjMap(assetFields);
            exchangeRateValue = assetFields["value"].get_int();
        } else {
            error = strprintf("Invalid value for asset %s: %d", assetIdentifier, assetData.getValStr());
            return false;
        }
        g_exchange_rate_map[asset] = exchangeRateValue;
    }
    return true;
}
