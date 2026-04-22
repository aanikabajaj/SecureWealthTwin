import React, { useState } from 'react';
import ListItem from '../ListItem';
import { useWealth } from '../../context/WealthContext';
import { aggregatorAPI } from '../../services/api';

const BankSection = ({ t }) => {
  const { aaAccounts, formatted, reload } = useWealth();
  const [isLinking, setIsLinking] = useState(false);
  const [showModal, setShowModal] = useState(false);

  const handleLinkBank = async () => {
    setIsLinking(true);
    try {
      // 1. Create a simulated consent request
      const consentRes = await aggregatorAPI.createConsent({
        aa_id: "finvu@aa",
        fi_types: ["DEPOSIT", "TERM_DEPOSIT"],
        data_range_months: 6
      });
      
      const consentId = consentRes.data.id;
      
      // 2. In sandbox mode, the consent auto-approves. We initiate the fetch immediately.
      await aggregatorAPI.fetch(consentId);
      
      // 3. Reload the global wealth state to show new accounts
      await reload();
      
      setShowModal(false);
      alert("Successfully linked accounts via Account Aggregator (Finvu)!");
    } catch (err) {
      console.error("Failed to link bank:", err);
      alert("Linking failed: " + err.message);
    } finally {
      setIsLinking(false);
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-5">
        <div className="text-xl font-semibold text-[#1a1a1a]">{t.f4}</div>
        <button 
          onClick={() => setShowModal(true)}
          className="px-4 py-2 bg-[#c8102e] text-white text-[12px] font-bold rounded-lg hover:bg-[#a80d26] transition-colors flex items-center gap-2"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <path d="M12 5v14M5 12h14"/>
          </svg>
          Connect New Bank (AA)
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-5">
        <div className="bg-white border border-[#e5e5e5] rounded-xl p-4 shadow-sm">
          <div className="text-[11px] text-[#6b6b6b] mb-2 font-semibold uppercase tracking-wider">Total Linked Balance</div>
          <div className="text-[22px] font-semibold text-[#1a1a1a]">{formatted.aaBalance || "₹0"}</div>
        </div>
        <div className="bg-white border border-[#e5e5e5] rounded-xl p-4 shadow-sm">
          <div className="text-[11px] text-[#6b6b6b] mb-2 font-semibold uppercase tracking-wider">Linked Institutions</div>
          <div className="text-[22px] font-semibold text-[#1d4ed8]">{aaAccounts.length}</div>
        </div>
        <div className="bg-white border border-[#e5e5e5] rounded-xl p-4 shadow-sm">
          <div className="text-[11px] text-[#6b6b6b] mb-2 font-semibold uppercase tracking-wider">AA Sync Status</div>
          <div className="text-[22px] font-semibold text-[#15803d]">Active</div>
        </div>
      </div>
      
      {aaAccounts.length > 0 ? (
        <div className="bg-white border border-[#e5e5e5] rounded-xl p-5 shadow-sm">
          <div className="text-[13px] font-semibold text-[#1a1a1a] mb-4">Linked Bank Accounts (Verified via AA)</div>
          <div className="space-y-1">
            {aaAccounts.map((acc, i) => (
              <ListItem 
                key={i}
                label={`${acc.fip_name} (${acc.masked_account_number})`} 
                value={`₹${new Intl.NumberFormat('en-IN').format(acc.current_balance)}`} 
                badgeType="info" 
              />
            ))}
          </div>
        </div>
      ) : (
        <div className="bg-white border border-[#e5e5e5] border-dashed rounded-xl p-16 text-center shadow-sm">
          <div className="w-16 h-16 bg-[#f5f5f5] rounded-full flex items-center justify-center mx-auto mb-4">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#9a9a9a" strokeWidth="2">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
            </svg>
          </div>
          <h3 className="text-[16px] font-bold text-[#1a1a1a] mb-2">No bank accounts linked via AA yet</h3>
          <p className="text-[13px] text-[#8a8a8a] max-w-xs mx-auto mb-6">
            Link your external bank accounts through the Account Aggregator ecosystem to get a full view of your net worth.
          </p>
          <button 
            onClick={() => setShowModal(true)}
            className="px-6 py-2.5 bg-white border border-[#e5e5e5] text-[#1a1a1a] text-[13px] font-bold rounded-lg hover:bg-[#fde8ec] hover:text-[#c8102e] transition-all"
          >
            Start Linking Process
          </button>
        </div>
      )}

      {/* AA Connection Modal (Simulation) */}
      {showModal && (
        <div className="fixed inset-0 z-[1000] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-white rounded-3xl w-full max-w-md overflow-hidden shadow-2xl animate-in zoom-in-95 duration-200">
            <div className="bg-[#1a1a1a] p-8 text-white text-center">
              <div className="text-[10px] font-bold uppercase tracking-[3px] opacity-60 mb-2">Account Aggregator</div>
              <h2 className="text-xl font-bold">Connect your Banks</h2>
              <p className="text-white/60 text-[13px] mt-2">Grant SecureWealth Digital Twin permission to access your financial information.</p>
            </div>
            
            <div className="p-8">
              <div className="text-[11px] font-bold text-[#8a8a8a] uppercase tracking-wider mb-4">Select AA Provider</div>
              <div className="grid grid-cols-1 gap-3">
                {['Finvu', 'OneMoney', 'Sahamati'].map(provider => (
                  <button 
                    key={provider}
                    className="flex items-center justify-between p-4 border border-[#eeeeee] rounded-xl hover:border-[#c8102e] hover:bg-[#fde8ec]/30 transition-all text-left"
                  >
                    <div>
                      <div className="font-bold text-[14px]">{provider}</div>
                      <div className="text-[11px] text-[#8a8a8a]">Reserve Bank of India Licensed AA</div>
                    </div>
                    <div className="text-[#c8102e] opacity-0 group-hover:opacity-100">→</div>
                  </button>
                ))}
              </div>
              
              <div className="mt-8">
                <button 
                  onClick={handleLinkBank}
                  disabled={isLinking}
                  className="w-full py-4 bg-[#c8102e] text-white font-bold rounded-xl shadow-lg shadow-[#c8102e]/20 hover:bg-[#a80d26] transition-all disabled:opacity-50"
                >
                  {isLinking ? 'Verifying Consent...' : 'Authorize & Link All Banks'}
                </button>
                <button 
                  onClick={() => setShowModal(false)}
                  className="w-full mt-3 py-2 text-[12px] text-[#8a8a8a] font-bold hover:text-[#1a1a1a]"
                >
                  Cancel Process
                </button>
              </div>
              
              <div className="mt-6 flex items-center gap-2 justify-center opacity-40">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                  <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                </svg>
                <span className="text-[10px] font-bold uppercase tracking-widest">End-to-End Encrypted</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default BankSection;
