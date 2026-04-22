/**
 * SecureWealth Twin — Wealth Data Context
 * Fetches all live data from the backend once on login and exposes it to all sections.
 */

import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { networthAPI, aggregatorAPI, assetsAPI, authAPI } from '../services/api';

const WealthContext = createContext(null);

const fmt = (n) =>
  new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 }).format(Number(n) || 0);

export const WealthProvider = ({ children, onSessionExpired }) => {
  const [user,           setUser]           = useState(null);
  const [netWorth,       setNetWorth]       = useState(null);
  const [nwHistory,      setNwHistory]      = useState([]);
  const [aaAccounts,     setAaAccounts]     = useState([]);
  const [assetList,      setAssetList]      = useState([]);
  const [assetSummary,   setAssetSummary]   = useState([]);
  const [loading,        setLoading]        = useState(true);
  const [error,          setError]          = useState(null);

  const loadAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [
        userRes, nwRes, nwHistRes, accountsRes, assetsRes, assetSumRes
      ] = await Promise.allSettled([
        authAPI.me(),
        networthAPI.get(),
        networthAPI.history(12),
        aggregatorAPI.accounts(),
        assetsAPI.list(),
        assetsAPI.summary(),
      ]);

      if (userRes.status       === 'fulfilled') setUser(userRes.value.data);
      if (nwRes.status         === 'fulfilled') setNetWorth(nwRes.value.data);
      if (nwHistRes.status     === 'fulfilled') setNwHistory(nwHistRes.value.data);
      if (accountsRes.status   === 'fulfilled') setAaAccounts(accountsRes.value.data);
      if (assetsRes.status     === 'fulfilled') setAssetList(assetsRes.value.data);
      if (assetSumRes.status   === 'fulfilled') setAssetSummary(assetSumRes.value.data);
    } catch (err) {
      if (err.message?.includes('401') || err.message?.includes('403')) {
        onSessionExpired?.();
      }
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [onSessionExpired]);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  // ── Recompute net worth then refresh ──────────────────────────────────────
  const recompute = useCallback(async () => {
    try {
      await networthAPI.recompute();
      const [nwRes, nwHistRes] = await Promise.all([
        networthAPI.get(),
        networthAPI.history(12),
      ]);
      setNetWorth(nwRes.data);
      setNwHistory(nwHistRes.data);
    } catch (_) {}
  }, []);

  // ── Derived helpers ───────────────────────────────────────────────────────

  // Net worth trend chart data shaped for recharts
  const nwChartData = nwHistory.length > 0
    ? nwHistory
        .slice()
        .reverse()
        .map((snap) => ({
          month: new Date(snap.computed_at).toLocaleString('default', { month: 'short' }),
          value: Math.round(parseFloat(snap.net_worth) / 1000),
        }))
    : null; // null = use static fallback

  // AA total balance
  const aaTotalBalance = aaAccounts.reduce(
    (sum, a) => sum + parseFloat(a.current_balance || 0), 0
  );

  // Physical assets total value
  const physicalTotal = assetList.reduce(
    (sum, a) => sum + parseFloat(a.current_value || 0), 0
  );

  // Formatted shorthand values for metric cards
  const formatted = {
    netWorth:       netWorth ? `₹${fmt(netWorth.net_worth)}`        : null,
    aaBalance:      `₹${fmt(aaTotalBalance)}`,
    physicalTotal:  `₹${fmt(physicalTotal)}`,
    liabilities:    netWorth ? `₹${fmt(netWorth.total_liabilities)}` : null,
    financialAssets:netWorth ? `₹${fmt(netWorth.financial_assets)}`  : null,
  };

  return (
    <WealthContext.Provider
      value={{
        user, netWorth, nwHistory, nwChartData,
        aaAccounts, aaTotalBalance,
        assetList, assetSummary, physicalTotal,
        formatted, loading, error,
        reload: loadAll, recompute,
      }}
    >
      {children}
    </WealthContext.Provider>
  );
};

export const useWealth = () => {
  const ctx = useContext(WealthContext);
  if (!ctx) throw new Error('useWealth must be used inside WealthProvider');
  return ctx;
};

export default WealthContext;
