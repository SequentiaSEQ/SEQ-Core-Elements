#include <asset.h>
#include <assetsdir.h>
#include <boost/program_options.hpp>
#include <boost/program_options/variables_map.hpp>
#include <consensus/amount.h>
#include <cstdint>
#include <exchangerates.h>
#include <fs.h>
#include <policy/policy.h>
#include <uint256.h>

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

bool LoadExchangeRatesFromConfigFile(std::string file_path, std::string& error)
{
    // Parse config file
    boost::program_options::variables_map options;
    boost::program_options::options_description options_description;
    boost::program_options::store(boost::program_options::parse_config_file(file_path.c_str(), options_description), options);
    boost::program_options::notify(options);

    // Load exchange rates into global map
    for (auto option : options) {
        CAsset asset = GetAssetFromString(option.first);
        if (asset.IsNull()) {
            error = strprintf("Unknown label and invalid asset hex: %s", asset.GetHex());
            return false;
        }
        CAmount exchangeRateValue = option.second.as<int>();
        g_exchange_rate_map[asset] = exchangeRateValue;
    }
    return true;
}
