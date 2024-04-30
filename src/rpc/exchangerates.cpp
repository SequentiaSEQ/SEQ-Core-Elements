// Copyright (c) 2021 The Bitcoin Core developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#include <rpc/server_util.h>

#include <assetsdir.h>
#include <exchangerates.h>
#include <rpc/register.h>
#include <rpc/server.h>
#include <rpc/server_util.h>
#include <rpc/util.h>
#include <txmempool.h>

using node::NodeContext;

static RPCHelpMan getfeeexchangerates()
{
    return RPCHelpMan{"getfeeexchangerates",
                "\nReturns a map of assets with their current exchange rates, for use in valuating fee payments.\n",
                {},
                RPCResult{
                    RPCResult::Type::OBJ, "", "",
                    {
                        {RPCResult::Type::STR_HEX, "rates", "A table mapping asset tag to rate of exchange for one unit of the asset in terms of the reference fee asset."},
                    }},
                RPCExamples{
                    HelpExampleCli("getfeeexchangerates", "")
                  + HelpExampleRpc("getfeeexchangerates", "")
                },
        [&](const RPCHelpMan& self, const JSONRPCRequest& request) -> UniValue
    {
        return ExchangeRateMap::GetInstance().ToJSON();
    }
    };
}

static RPCHelpMan setfeeexchangerates()
{
    return RPCHelpMan{"setfeeexchangerates",
                "\nPrivileged call to set the set of accepted assets for paying fees, and the exchange rate for each of these assets.\n",
                {
                    {"rates", RPCArg::Type::OBJ, RPCArg::Optional::NO, "Exchange rates for assets",
                        {
                            {"asset", RPCArg::Type::AMOUNT, RPCArg::Optional::NO, "The asset hex is the key, the numeric amount (can be string) is the value"},
                        },
                    },
                },
                RPCResult{RPCResult::Type::NONE, "", ""},
                RPCExamples{
                    HelpExampleCli("setfeeexchangerates", "")
                  + HelpExampleRpc("setfeeexchangerates", "")
                },
        [&](const RPCHelpMan& self, const JSONRPCRequest& request) -> UniValue
{
    UniValue json = request.params[0].get_obj();
    std::map<std::string, UniValue> jsonRates;
    json.getObjMap(jsonRates);
    auto& exchangeRateMap = ExchangeRateMap::GetInstance();
    std::vector<std::string> errors;
    if (!exchangeRateMap.LoadFromJSON(jsonRates, errors)) {
        throw JSONRPCError(RPC_WALLET_ERROR, strprintf("Error loading rates from JSON: %s", MakeUnorderedList(errors)));
    }
    if (!exchangeRateMap.SaveToJSONFile(errors)) {
        return JSONRPCError(RPC_WALLET_ERROR, strprintf("Error saving exchange rates to JSON file %s: \n%s\n", exchange_rates_config_file, MakeUnorderedList(errors)));
    };
    EnsureAnyMemPool(request.context).RecomputeFees();
    return NullUniValue;
},
    };
}

void RegisterExchangeRatesRPCCommands(CRPCTable &t)
{
// clang-format off

static const CRPCCommand commands[] =
{ //  category              actor (function)
  //  --------------------- ------------------------
    { "exchangerates",      &getfeeexchangerates,                  },
    { "exchangerates",      &setfeeexchangerates,                  },
};
// clang-format on
    for (const auto& c : commands) {
        t.appendCommand(c.name, &c);
    }
}
