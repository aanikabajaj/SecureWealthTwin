import React, { useState } from 'react';
import { useWealth } from '../../context/WealthContext';
import SecurityChallengeModal from '../SecurityChallengeModal';

const CategoryIcon = ({ category }) => {
  const icons = {
    real_estate: '🏠',
    gold: '📀',
    jewellery: '💎',
    vehicle: '🚗',
    art_collectible: '🎨',
    business: '💼',
    other: '📦'
  };
  return <span className="mr-1.5">{icons[category.toLowerCase()] || '💰'}</span>;
};

const RegisteredAssetsList = ({ t }) => {
  const { assetList, reload, recompute } = useWealth();
  const [selectedAsset, setSelectedAsset] = useState(null);
  const [challengeData, setChallengeData] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const fmt = (n) =>
    new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 }).format(Number(n) || 0);

  const handleManageClick = (asset) => {
    setSelectedAsset(asset);
  };

  const handleSellInitiate = () => {
    // 🛡️ High-stakes action: Sell/Liquidate asset
    // Simulate high risk score for selling physical assets
    setChallengeData({
      risk_score: 89,
      reasons: [
        { signal_name: "Asset Liquidation", contribution: 0.6, description: "High-value physical asset disposal detected." },
        { signal_name: "Urgency Pattern", contribution: 0.3, description: "Action deviates from typical holding patterns." }
      ]
    });
  };

  const handleAuthorizedSale = async () => {
    setIsProcessing(true);
    try {
      // In a real app, we'd call assetsAPI.delete(selectedAsset.id)
      // Here we simulate the successful sale
      setChallengeData(null);
      alert(`Success! "${selectedAsset.name}" has been sold. The proceeds (₹${fmt(selectedAsset.current_value)}) have been credited to your linked bank account.`);
      setSelectedAsset(null);
      
      // Refresh state to show asset removed
      // reload(); 
      // recompute();
    } catch (err) {
      alert("Sale failed: " + err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  if (assetList.length === 0) {
    return (
      <div className="bg-white border border-dashed border-[#e5e5e5] rounded-xl p-10 text-center mt-5">
        <div className="w-12 h-12 bg-[#f5f5f5] rounded-full flex items-center justify-center mx-auto mb-3">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#9a9a9a" strokeWidth="2">
            <path d="M3 3h18v18H3z" />
            <path d="M12 8v8M8 12h8" />
          </svg>
        </div>
        <p className="text-[14px] text-[#8a8a8a]">No registered assets yet. Use the form above to add your first asset.</p>
      </div>
    );
  }

  return (
    <div className="mt-5">
      <div className="text-[13px] font-semibold text-[#1a1a1a] mb-4 flex justify-between items-center">
        <span>Your Registered Assets</span>
        <span className="text-[11px] text-[#8a8a8a] font-normal">{assetList.length} Items Tracked</span>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {assetList.map((asset) => (
          <div 
            key={asset.id} 
            className="bg-white border border-[#e5e5e5] rounded-xl p-4 shadow-sm hover:border-[#c8102e]/30 transition-all group relative overflow-hidden"
          >
            <div className="flex justify-between items-start mb-3">
              <div className="bg-[#f5f5f5] px-2 py-1 rounded text-[10px] font-bold text-[#c8102e] uppercase tracking-wider flex items-center">
                <CategoryIcon category={asset.category} />
                {asset.category.replace('_', ' ')}
              </div>
              <div className="text-[15px] font-bold text-[#1a1a1a]">₹{fmt(asset.current_value)}</div>
            </div>

            <div className="text-[14px] font-bold text-[#1a1a1a] mb-1 group-hover:text-[#c8102e] transition-colors">
              {asset.name}
            </div>
            <div className="text-[11px] text-[#8a8a8a]">
              Added: {new Date(asset.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
            </div>

            <div className="mt-4 pt-3 border-t border-[#f5f5f5] flex justify-between items-center">
              <div className="flex items-center gap-1.5 text-[10px] text-[#15803d] font-bold uppercase tracking-tight">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                </svg>
                Blockchain Verified
              </div>
              <button 
                onClick={() => handleManageClick(asset)}
                className="text-[11px] font-bold text-[#c8102e] hover:underline"
              >
                Manage
              </button>
            </div>
            <div className={`absolute top-0 right-0 w-1 h-full ${asset.category === 'gold' ? 'bg-yellow-400' : 'bg-[#c8102e]/20'}`} />
          </div>
        ))}
      </div>

      {/* Asset Management Modal */}
      {selectedAsset && (
        <div className="fixed inset-0 z-[1000] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-white rounded-3xl w-full max-w-md overflow-hidden shadow-2xl animate-in zoom-in-95 duration-200">
            <div className="bg-[#f5f5f5] p-8 text-center border-b border-[#eeeeee]">
              <div className="text-[32px] mb-2"><CategoryIcon category={selectedAsset.category} /></div>
              <h2 className="text-xl font-bold text-[#1a1a1a]">{selectedAsset.name}</h2>
              <p className="text-[#8a8a8a] text-[13px] uppercase font-bold tracking-widest mt-1">{selectedAsset.category.replace('_', ' ')}</p>
            </div>
            
            <div className="p-8">
              <div className="grid grid-cols-2 gap-4 mb-8">
                <div className="p-4 bg-[#f9f9f9] rounded-2xl">
                  <div className="text-[10px] font-bold text-[#8a8a8a] uppercase mb-1">Current Value</div>
                  <div className="text-[16px] font-bold text-[#1a1a1a]">₹{fmt(selectedAsset.current_value)}</div>
                </div>
                <div className="p-4 bg-[#f9f9f9] rounded-2xl">
                  <div className="text-[10px] font-bold text-[#8a8a8a] uppercase mb-1">Status</div>
                  <div className="text-[16px] font-bold text-[#15803d]">Verified</div>
                </div>
              </div>

              <div className="space-y-3">
                <button 
                  className="w-full py-4 bg-[#1a1a1a] text-white font-bold rounded-xl hover:bg-black transition-all flex items-center justify-center gap-2"
                >
                  Update Valuation
                </button>
                <button 
                  onClick={handleSellInitiate}
                  className="w-full py-4 bg-white border border-[#c8102e] text-[#c8102e] font-bold rounded-xl hover:bg-[#fde8ec] transition-all"
                >
                  Sell / Liquidate Asset
                </button>
                <button 
                  onClick={() => setSelectedAsset(null)}
                  className="w-full py-2 text-[12px] text-[#8a8a8a] font-bold hover:text-[#1a1a1a]"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Mandatory Wealth Protection Shield for Liquidation */}
      <SecurityChallengeModal 
        isOpen={!!challengeData}
        onClose={() => setChallengeData(null)}
        onVerify={handleAuthorizedSale}
        riskScore={challengeData?.risk_score}
        reasons={challengeData?.reasons}
      />
    </div>
  );
};

export default RegisteredAssetsList;
