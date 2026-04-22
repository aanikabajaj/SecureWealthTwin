import React from 'react';
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip } from 'recharts';
import MetricCard from '../MetricCard';
import AllocationBar from '../AllocationBar';
import AddAssetForm from './AddAssetForm';
import RegisteredAssetsList from './RegisteredAssetsList';
import {
  NET_WORTH_DATA,
  ALLOCATION_WIDTHS,
  ALLOCATION_COLORS,
  BRAND_RED,
  useChartStyles
} from './chartConfigs';
import { useWealth } from '../../context/WealthContext';

const BRAND = '#c8102e';

const AssetMetricCards = ({ t }) => {
  const { formatted } = useWealth();
  
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
      <MetricCard
        icon={
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <circle cx="8" cy="8" r="6" stroke={BRAND} strokeWidth="1.4" />
            <path d="M8 5v2l1.5 1.5" stroke={BRAND} strokeWidth="1.4" />
          </svg>
        }
        badge="+8.2%"
        badgeColor="text-[#15803d]"
        value={formatted.netWorth || "₹0"}
        label={t.networth}
      />
      <MetricCard
        icon={
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <rect x="2" y="3" width="12" height="9" rx="1.5" stroke={BRAND} strokeWidth="1.4" />
            <path d="M2 7h12" stroke={BRAND} strokeWidth="1.4" />
          </svg>
        }
        badge="+3.1%"
        badgeColor="text-[#15803d]"
        value="₹12,400"
        label={t.income}
      />
      <MetricCard
        icon={
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M3 12V8a5 5 0 0110 0v4" stroke={BRAND} strokeWidth="1.4" />
          </svg>
        }
        badge="+2.4%"
        badgeColor="text-[#15803d]"
        value="34.2%"
        label={t.savings}
      />
      <MetricCard
        icon={
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <polyline points="2,12 5,7 9,9 14,3" stroke={BRAND} strokeWidth="1.6" fill="none" />
          </svg>
        }
        badge="Stable"
        badgeColor="text-[#1d4ed8]"
        value="Low"
        valueColor="text-[#15803d]"
        label={t.risk}
      />
    </div>
  );
};

const AssetChart = ({ t }) => {
  const { tickStyle, tooltipContentStyle, tooltipLabelStyle } = useChartStyles();
  const { nwChartData } = useWealth();

  return (
    <div className="bg-white border border-[#e5e5e5] rounded-xl p-5 shadow-sm h-full">
      <div className="text-[13px] font-semibold text-[#1a1a1a] mb-4">{t.nwtrend}</div>
      <div className="w-full h-[220px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={nwChartData || NET_WORTH_DATA}>
            <XAxis
              dataKey="month"
              stroke="#9a9a9a"
              style={{ fontSize: '11px' }}
              tick={tickStyle}
            />
            <YAxis
              stroke="#9a9a9a"
              style={{ fontSize: '11px' }}
              tick={tickStyle}
              tickFormatter={(value) => `₹${value}k`}
            />
            <Tooltip
              contentStyle={tooltipContentStyle}
              labelStyle={tooltipLabelStyle}
            />
            <Line
              type="monotone"
              dataKey="value"
              stroke={BRAND_RED}
              strokeWidth={2.5}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

const AssetAllocationPanel = ({ t }) => (
  <div className="bg-white border border-[#e5e5e5] rounded-xl p-5 shadow-sm h-full">
    <div className="text-[13px] font-semibold text-[#1a1a1a] mb-4">{t.alloc}</div>
    <AllocationBar label={t.equities} percentage="42%" color={ALLOCATION_COLORS.EQUITIES} width={ALLOCATION_WIDTHS.EQUITIES} />
    <AllocationBar label={t.bonds} percentage="25%" color={ALLOCATION_COLORS.BONDS} width={ALLOCATION_WIDTHS.BONDS} />
    <AllocationBar label={t.realestate} percentage="18%" color={ALLOCATION_COLORS.REAL_ESTATE} width={ALLOCATION_WIDTHS.REAL_ESTATE} />
    <AllocationBar label={t.cash} percentage="10%" color={ALLOCATION_COLORS.CASH} width={ALLOCATION_WIDTHS.CASH} />
    <AllocationBar label={t.crypto} percentage="5%" color={ALLOCATION_COLORS.CRYPTO} width={ALLOCATION_WIDTHS.CRYPTO} />
  </div>
);

const AssetsSection = ({ t }) => {
  const { reload, recompute } = useWealth();

  const handleAssetAdded = () => {
    reload();
    recompute();
  };

  return (
    <div>
      <div className="mb-5">
        <div className="text-xl font-semibold text-[#1a1a1a]">{t.f5}</div>
        <div className="text-[13px] text-[#4a4a4a] mt-1">{t.wisub}</div>
      </div>
      
      <AddAssetForm t={t} onAssetAdded={handleAssetAdded} />

      <AssetMetricCards t={t} />
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_260px] gap-4 mb-5">
        <AssetChart t={t} />
        <AssetAllocationPanel t={t} />
      </div>

      <RegisteredAssetsList t={t} />
    </div>
  );
};

export default AssetsSection;
