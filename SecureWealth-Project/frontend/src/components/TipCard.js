import React from 'react';

const TipCard = ({ number, text }) => {
  return (
    <div className="bg-white border border-[#e5e5e5] rounded-xl p-4 mb-3 flex gap-3 items-start shadow-sm">
      <div className="w-[28px] h-[28px] rounded-full bg-[#c8102e] text-white text-xs font-semibold flex items-center justify-center flex-shrink-0">
        {number}
      </div>
      <div className="text-[13.5px] text-[#1a1a1a] leading-relaxed">{text}</div>
    </div>
  );
};

export default TipCard;
