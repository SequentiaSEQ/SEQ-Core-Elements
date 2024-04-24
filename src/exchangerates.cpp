#include <assetsdir.h>
#include <exchangerates.h>
#include <policy/policy.h>
#include <util/settings.h>
#include <util/system.h>
#include <univalue.h>

#include <fstream>

CAmount ExchangeRateMap::CalculateExchangeValue(const CAmount& amount, const CAsset& asset) {
    auto it = this->find(asset);
    if (it == this->end()) {
        return 0;
    }
    auto scaled_value = it->second.m_scaled_value;
    __uint128_t value = ((__uint128_t)amount * (__uint128_t)scaled_value) / (__uint128_t)exchange_rate_scale;
    int64_t int64_max = std::numeric_limits<int64_t>::max();
    if (value > int64_max) {
        return int64_max;
    } else {
        return (int64_t) value;
    }
}

bool ExchangeRateMap::LoadFromDefaultJSONFile(std::vector<std::string>& errors) {
    fs::path file_path = AbsPathForConfigVal(fs::PathFromString(exchange_rates_config_file));    
    if (fs::exists(file_path)) {
        return LoadFromJSONFile(file_path, errors);
    } else {
        return true;
    }
}

bool ExchangeRateMap::LoadFromJSONFile(fs::path file_path, std::vector<std::string>& errors) {
    std::map <std::string, UniValue> json;
    if (!util::ReadSettings(file_path, json, errors)) {
        return false;
    }
    return this->LoadFromJSON(json, errors);
}

bool ExchangeRateMap::SaveToJSONFile(std::vector<std::string>& errors) {
    UniValue json = this->ToJSON();
    std::map<std::string, util::SettingsValue> settings;
    json.getObjMap(settings);
    fs::path file_path = AbsPathForConfigVal(fs::PathFromString(exchange_rates_config_file));
    return util::WriteSettings(file_path, settings, errors);
}

UniValue ExchangeRateMap::ToJSON() {
    UniValue json = UniValue{UniValue::VOBJ};
    for (auto rate : *this) {
        std::string label = gAssetsDir.GetLabel(rate.first);
        if (label == "") {
            label = rate.first.GetHex();
        }
        json.pushKV(label, rate.second.m_scaled_value);
    }
    return json;
}

bool ExchangeRateMap::LoadFromJSON(std::map<std::string, UniValue> json, std::vector<std::string>& errors) {
    bool hasError = false;
    std::map<CAsset, CAmount> parsedRates;
    for (auto rate : json) {
        CAsset asset = GetAssetFromString(rate.first);
        if (asset.IsNull()) {
            errors.push_back(strprintf("Unknown label and invalid asset hex: %s", rate.first));
            hasError = true;
        } else {
            CAmount newRateValue = rate.second.get_int64();
            parsedRates[asset] = newRateValue;
        }
    }
    if (hasError) return false;
    this->clear();
    for (auto rate : parsedRates) {
        (*this)[rate.first] = rate.second;
    }
    return true; 
}
