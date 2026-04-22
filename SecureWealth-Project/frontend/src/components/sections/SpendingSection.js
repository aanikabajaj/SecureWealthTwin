import React from 'react';
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, Cell, LineChart, Line } from 'recharts';
import MetricCard from '../MetricCard';
import ListItem from '../ListItem';
import { useChartStyles } from './chartConfigs';

const BRAND = '#c8102e';

const SpendingSection = ({ t, isBusinessMode }) => {
  const { tickStyle, tooltipContentStyle, tooltipLabelStyle } = useChartStyles();

  // Simulated Business Data
  const businessMetrics = [
    { label: 'Current Liquidity', value: '₹4.2 Cr', badge: 'Optimal', badgeColor: 'text-[#15803d]' },
    { label: 'Operating Cash Flow', value: '₹82.5 L', badge: '+12%', badgeColor: 'text-[#15803d]' },
    { label: 'Payables (30d)', value: '₹18.2 L', badge: 'Due', badgeColor: 'text-[#b91c1c]' },
    { label: 'Receivables', value: '₹34.8 L', badge: 'Pending', badgeColor: 'text-[#f59e0b]' },
  ];

  const cashFlowData = [
    { month: 'Oct', inflow: 45, outflow: 38 },
    { month: 'Nov', inflow: 52, outflow: 41 },
    { month: 'Dec', inflow: 48, outflow: 44 },
    { month: 'Jan', inflow: 61, outflow: 39 },
    { month: 'Feb', inflow: 55, outflow: 42 },
    { month: 'Mar', inflow: 72, outflow: 45 },
  ];

  if (isBusinessMode) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {businessMetrics.map((m, i) => (
            <MetricCard key={i} label={m.label} value={m.value} badge={m.badge} badgeColor={m.badgeColor} />
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="bg-white border border-[#e5e5e5] rounded-xl p-5 shadow-sm">
            <div className="text-[13px] font-semibold text-[#1a1a1a] mb-4">Cash Flow Analysis (Inflow vs Outflow)</div>
            <div className="w-full h-[250px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={cashFlowData}>
                  <XAxis dataKey="month" stroke="#9a9a9a" tick={tickStyle} />
                  <YAxis stroke="#9a9a9a" tick={tickStyle} tickFormatter={(v) => `₹${v}L`} />
                  <Tooltip contentStyle={tooltipContentStyle} />
                  <Bar dataKey="inflow" fill="#15803d" radius={[4, 4, 0, 0]} name="Inflow" />
                  <Bar dataKey="outflow" fill="#b91c1c" radius={[4, 4, 0, 0]} name="Outflow" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="bg-[#1a1a1a] rounded-xl p-6 text-white">
            <h3 className="text-[15px] font-bold mb-4">Corporate Treasury Suggestions</h3>
            <div className="space-y-4">
              <div className="p-4 bg-white/5 rounded-lg border border-white/10">
                <div className="text-[#15803d] text-[10px] font-bold uppercase mb-1">Surplus Alert</div>
                <p className="text-[13px] text-white/80">You have ₹1.2 Cr in idle funds. Moving this to a Liquid Fund could generate ₹45,000 additional monthly interest.</p>
              </div>
              <div className="p-4 bg-white/5 rounded-lg border border-white/10">
                <div className="text-[#f59e0b] text-[10px] font-bold uppercase mb-1">Risk Indicator</div>
                <p className="text-[13px] text-white/80">High concentration of receivables (42%) from a single client. Diversification is recommended to protect liquidity.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Default Individual View (Existing code)
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <MetricCard label="Monthly Spend" value="₹42,850" badge="-12%" badgeColor="text-[#15803d]" />
        <MetricCard label="Daily Average" value="₹1,428" badge="Normal" badgeColor="text-[#15803d]" />
        <MetricCard label="Saving Rate" value="32%" badge="+4%" badgeColor="text-[#15803d]" />
        <MetricCard label="Budget Left" value="₹12,150" badge="On Track" badgeColor="text-[#15803d]" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-white border border-[#e5e5e5] rounded-xl p-5 shadow-sm">
          <div className="text-[13px] font-semibold text-[#1a1a1a] mb-4">Spending by Category</div>
          <div className="w-full h-[250px]">
             {/* Simplified Bar Chart */}
             <ResponsiveContainer width="100%" height="100%">
                <BarChart data={[
                  { name: 'Food', value: 12500 },
                  { name: 'Rent', value: 25000 },
                  { name: 'Travel', value: 4500 },
                  { name: 'Health', value: 2000 },
                  { name: 'Other', value: 3850 }
                ]}>
                  <XAxis dataKey="name" stroke="#9a9a9a" tick={tickStyle} />
                  <YAxis hide />
                  <Tooltip contentStyle={tooltipContentStyle} />
                  <Bar dataKey="value" fill={BRAND} radius={[4, 4, 0, 0]} />
                </BarChart>
             </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white border border-[#e5e5e5] rounded-xl p-5 shadow-sm">
          <div className="text-[13px] font-semibold text-[#1a1a1a] mb-4">Recent Habits</div>
          <div className="space-y-1">
            <ListItem label="Swiggy/Zomato" value="₹8,420" badgeType="down" />
            <ListItem label="Utility Bills" value="₹4,150" badgeType="up" />
            <ListItem label="Grocery" value="₹12,400" badgeType="up" />
            <ListItem label="Entertainment" value="₹2,100" badgeType="down" />
          </div>
        </div>
      </div>
    </div>
  );
};

export default SpendingSection;
