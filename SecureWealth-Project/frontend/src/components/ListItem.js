import React from 'react';

const ListItem = ({ label, value, badgeType = 'ok' }) => {
  const badgeColors = {
    up: 'text-[#15803d]',
    down: 'text-[#b91c1c]',
    warn: 'text-[#b45309]',
    ok: 'text-[#15803d]',
    info: 'text-[#1d4ed8]'
  };

  return (
    <div className="flex justify-between items-center py-2.5 border-b border-[#eeeeee] text-[13px] text-[#1a1a1a] last:border-b-0">
      <span>{label}</span>
      <span className={`text-[12px] font-semibold ${badgeColors[badgeType]}`}>{value}</span>
    </div>
  );
};

export default ListItem;
