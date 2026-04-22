import React from 'react';

const MetricCard = ({
  icon,
  badge,
  value,
  label,
  badgeColor = 'text-[#c8102e]',
  valueColor = 'text-[#1a1a1a]'
}) => {
  return (
    <div className="bg-white border border-[#e5e5e5] rounded-xl p-4 shadow-sm">
      <div className="flex justify-between items-center mb-3">
        <div className="w-8 h-8 rounded-lg bg-[#fde8ec] flex items-center justify-center">
          {icon}
        </div>
        <span className={`text-[11px] font-semibold ${badgeColor}`}>{badge}</span>
      </div>
      <div className={`text-[22px] font-semibold ${valueColor} mb-1`}>{value}</div>
      <div className="text-[11px] text-[#6b6b6b]">{label}</div>
    </div>
  );
};

export default MetricCard;
