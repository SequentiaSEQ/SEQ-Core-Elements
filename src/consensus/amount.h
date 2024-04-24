// Copyright (c) 2009-2010 Satoshi Nakamoto
// Copyright (c) 2009-2021 The Bitcoin Core developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#ifndef BITCOIN_CONSENSUS_AMOUNT_H
#define BITCOIN_CONSENSUS_AMOUNT_H

#include <cstdint>
#include <ostream>

/** Amount in satoshis (Can be negative) */
typedef int64_t CAmount;

/** Amount denominated in the node's RFU (reference fee unit) */
struct CValue 
{ 

    int64_t value;

    CValue(): value(0) {}
    CValue(const int64_t value): value(value) {}

    CValue operator -(const CValue& operand)
    {
        return CValue(value - operand.value);
    }

    CValue operator -=(const CValue& operand)
    {
        value -= operand.value;
        return *this;
    }

    CValue operator +(const CValue& operand)
    {
        return CValue(value + operand.value);
    }

    CValue operator +=(const CValue& operand)
    {
        value += operand.value;
        return *this;
    }

    bool operator ==(const CValue& operand)
    {
        return value == operand.value;
    }

    bool operator !=(const CValue& operand)
    {
        return value != operand.value;
    }

    bool operator !=(int operand)
    {
        return value != operand;
    }

    bool operator <(const CValue& operand)
    {
        return value < operand.value;
    }

    bool operator >(const CValue& operand)
    {
        return value > operand.value;
    }
};

std::ostream &operator<<(std::ostream &out, const CValue& operand)
{
    out << operand.value;
    return out;
}

/** The amount of satoshis in one BTC. */
static constexpr CAmount COIN = 100000000;

/** No amount larger than this (in satoshi) is valid.
 *
 * Note that this constant is *not* the total money supply, which in Bitcoin
 * currently happens to be less than 21,000,000 BTC for various reasons, but
 * rather a sanity check. As this sanity check is used by consensus-critical
 * validation code, the exact value of the MAX_MONEY constant is consensus
 * critical; in unusual circumstances like a(nother) overflow bug that allowed
 * for the creation of coins out of thin air modification could lead to a fork.
 * */
static constexpr CAmount MAX_MONEY = 21000000 * COIN;
inline bool MoneyRange(const CAmount& nValue) { return (nValue >= 0 && nValue <= MAX_MONEY); }

#endif // BITCOIN_CONSENSUS_AMOUNT_H
