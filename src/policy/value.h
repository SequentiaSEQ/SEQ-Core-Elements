// Copyright (c) 2009-2010 Satoshi Nakamoto
// Copyright (c) 2009-2021 The Bitcoin Core developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#ifndef BITCOIN_POLICY_VALUE_H
#define BITCOIN_POLICY_VALUE_H

#include <cstdint>

/** ELEMENTS: Amount denominated in rfas (reference fee atoms). Used only when
 *  con_any_asset_fees is enabled in order to distinguish from amounts in an actual
 *  asset. rfa is needed to make amounts comparable when sorting transactions in
 *  the mempool, as well as for fee estimation and subsequent validation of those 
 *  fees according to various limits (e.g., mintxfee, paytsxfee, blockmintxfee, 
 *  incrementalrelaytxfee, etc.).
 */
struct CValue 
{ 
    private: 
        int64_t value;

    public:
        CValue(): value(0) {}
        CValue(const int64_t value): value(value) {}

        int64_t GetValue() const
        {
            return value;
        }

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
};

#endif // BITCOIN_POLICY_VALUE_H
