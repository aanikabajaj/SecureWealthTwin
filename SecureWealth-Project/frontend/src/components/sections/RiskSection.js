import React from 'react';
import ListItem from '../ListItem';

const RiskSection = ({ t }) => {
  return (
    <div>
      <div className="mb-5">
        <div className="text-xl font-semibold text-[#1a1a1a]">{t.f2}</div>
        <div className="text-[13px] text-[#4a4a4a] mt-1">{t.wisub}</div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-5">
        <div className="bg-white border border-[#e5e5e5] rounded-xl p-4 shadow-sm">
          <div className="text-[11px] text-[#6b6b6b] mb-2 font-semibold uppercase tracking-wider">{t.debtinc}</div>
          <div className="text-[22px] font-semibold text-[#1a1a1a]">28%</div>
        </div>
        <div className="bg-white border border-[#e5e5e5] rounded-xl p-4 shadow-sm">
          <div className="text-[11px] text-[#6b6b6b] mb-2 font-semibold uppercase tracking-wider">{t.emfund}</div>
          <div className="text-[22px] font-semibold text-[#15803d]">4.2 mo</div>
        </div>
        <div className="bg-white border border-[#e5e5e5] rounded-xl p-4 shadow-sm">
          <div className="text-[11px] text-[#6b6b6b] mb-2 font-semibold uppercase tracking-wider">{t.insurance}</div>
          <div className="text-[22px] font-semibold text-[#1d4ed8]">Active</div>
        </div>
      </div>
      <div className="bg-white border border-[#e5e5e5] rounded-xl p-5 shadow-sm">
        <div className="text-[13px] font-semibold text-[#1a1a1a] mb-4">{t.riskmod}</div>
        <ListItem label={t.debtinc} value="28%" badgeType="ok" />
        <ListItem label={t.emfund} value="4.2 months" badgeType="ok" />
        <ListItem label="Loan EMI" value="₹4,200/mo" badgeType="warn" />
        <ListItem label={t.insurance} value="₹10L" badgeType="ok" />
      </div>
    </div>
  );
};

export default RiskSection;
