// Copyright (c) 2009-2010 Satoshi Nakamoto
// Copyright (c) 2009-2021 The Bitcoin Core developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#ifndef BITCOIN_POLICY_VALUE_H
#define BITCOIN_POLICY_VALUE_H

#include <cstdint>
#include <ostream>

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

    bool operator ==(const CValue operand)
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

#endif // BITCOIN_POLICY_VALUE
