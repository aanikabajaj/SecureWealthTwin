import React from 'react';

const AllocationBar = ({ label, percentage, color, width }) => {
  return (
    <div className="flex items-center gap-2.5 mb-3">
      <span className="text-[13px] text-[#1a1a1a] w-20 flex-shrink-0">{label}</span>
      <div className="flex-1 h-[6px] bg-[#f1f1f1] rounded-[3px] overflow-hidden">
        <div
          className="h-full rounded-[3px]"
          style={{ width: `${width}%`, backgroundColor: color }}
        ></div>
      </div>
      <span className="text-xs text-[#4a4a4a] w-8 text-right font-semibold">{percentage}</span>
    </div>
  );
};

export default AllocationBar;
