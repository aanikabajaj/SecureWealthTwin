import React, { useState, useEffect, useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, Cell } from 'recharts';
import ListItem from '../ListItem';
import { useChartStyles } from './chartConfigs';
import { marketAPI } from '../../services/api';

const MarketSection = ({ t }) => {
  const [marketData, setMarketData] = useState(null);
  const [loading, setLoading] = useState(true);
  const { tickStyle, tooltipContentStyle, tooltipLabelStyle } = useChartStyles();

  useEffect(() => {
    const fetchMarketData = async () => {
      try {
        const response = await marketAPI.live();
        setMarketData(response.data.data);
      } catch (err) {
        console.error("Failed to fetch market data:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchMarketData();
    
    // Refresh every 60 seconds
    const interval = setInterval(fetchMarketData, 60000);
    return () => clearInterval(interval);
  }, []);

  const indices = useMemo(() => {
    if (!marketData || !marketData.indices) return [];
    return marketData.indices;
  }, [marketData]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-[#c8102e] border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-5 flex justify-between items-end">
        <div>
          <div className="text-xl font-semibold text-[#1a1a1a]">{t.f3}</div>
          <div className="text-[11px] text-[#8a8a8a] mt-1 uppercase tracking-wider">
            Live Feed • Updated {new Date(marketData?.last_updated || Date.now()).toLocaleTimeString()}
          </div>
        </div>
      </div>

      {/* Market Indices */}
      <div className="bg-white border border-[#e5e5e5] rounded-xl p-5 mb-4 shadow-sm">
        <div className="text-[13px] font-semibold text-[#1a1a1a] mb-4">Market Indices</div>
        {indices.map((idx) => (
          <React.Fragment key={idx.name}>
            <ListItem 
              label={idx.name} 
              value={idx.change} 
              badgeType={idx.trend} 
            />
            <div className="flex justify-end text-[13px] text-[#4a4a4a] py-2.5 border-b border-[#eeeeee] last:border-b-0">
              <span className="font-mono">₹{new Intl.NumberFormat('en-IN').format(idx.value.toFixed(2))}</span>
            </div>
          </React.Fragment>
        ))}
      </div>

      {/* Market Overview Chart */}
      <div className="bg-white border border-[#e5e5e5] rounded-xl p-5 shadow-sm">
        <div className="text-[13px] font-semibold text-[#1a1a1a] mb-4">Market Overview (% Change)</div>
        <div className="w-full h-[200px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={indices} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
              <XAxis
                dataKey="name"
                stroke="#9a9a9a"
                style={{ fontSize: '11px' }}
                tick={tickStyle}
              />
              <YAxis
                stroke="#9a9a9a"
                style={{ fontSize: '11px' }}
                tick={tickStyle}
                tickFormatter={(val) => `${val}%`}
              />
              <Tooltip
                contentStyle={tooltipContentStyle}
                labelStyle={tooltipLabelStyle}
                cursor={{ fill: '#fde8ec' }}
                formatter={(val) => [`${val.toFixed(2)}%`, 'Change']}
              />
              <Bar dataKey="change_raw">
                {indices.map((entry, index) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={entry.trend === 'up' ? '#15803d' : entry.trend === 'down' ? '#b91c1c' : '#9a9a9a'} 
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default MarketSection;
