// Copyright (c) 2021 The Bitcoin Core developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#include <assetsdir.h>
#include <exchangerates.h>
#include <rpc/register.h>
#include <rpc/server.h>
#include <rpc/server_util.h>
#include <rpc/util.h>
#include <txmempool.h>

using node::NodeContext;

static std::string CreateExchangeRatesDescription() {
    return "A key-value pair. The key (string) is the asset hex, the value (integer) represents how many atoms of "
           "the asset are equal to " + strprintf("1 %s or %d %ss", CURRENCY_UNIT, COIN, CURRENCY_ATOM_FULL) + ".";
}

static RPCHelpMan getfeeexchangerates()
{
    return RPCHelpMan{"getfeeexchangerates",
                "\nGet the whitelist of assets and their current exchange rates, for use by the mempool when valuating fee payments.\n",
                {},
                {
                    RPCResult{"rates", RPCResult::Type::OBJ, "", "",
                        {
                            RPCResult{RPCResult::Type::NUM, "asset", CreateExchangeRatesDescription()},
                            RPCResult{RPCResult::Type::ELISION, "", ""}
                        }
                    }
                },
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
                "\nSet the whitelist of assets and their exchange rates, for use by the mempool when valuating fee payments.\n",
                {
                    {"rates", RPCArg::Type::OBJ_USER_KEYS, RPCArg::Optional::OMITTED, "",
                        {
                            {"asset", RPCArg::Type::NUM, RPCArg::Optional::NO, CreateExchangeRatesDescription()}
                        },
                    },
                },
                RPCResult{RPCResult::Type::NONE, "", ""},
                RPCExamples{
                    HelpExampleCli("setfeeexchangerates", "{\"b2e15d0d7a0c94e4e2ce0fe6e8691b9e451377f6e46e8045a86f7c4b5d4f0f23\": 100000000}")
                  + HelpExampleRpc("setfeeexchangerates", "{\"b2e15d0d7a0c94e4e2ce0fe6e8691b9e451377f6e46e8045a86f7c4b5d4f0f23\": 100000000}")
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
}
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
