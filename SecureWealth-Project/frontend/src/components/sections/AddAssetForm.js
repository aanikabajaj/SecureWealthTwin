import React, { useState } from 'react';
import { assetsAPI } from '../../services/api';
import SecurityChallengeModal from '../SecurityChallengeModal';

const AddAssetForm = ({ t, onAssetAdded }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [challengeData, setChallengeData] = useState(null); // Stores risk info if challenged
  const [formData, setFormData] = useState({
    category: 'real_estate',
    name: '',
    current_value: '',
    valuation_method: 'self_declared'
  });

  const categories = [
    { value: 'real_estate', label: 'Real Estate' },
    { value: 'gold', label: 'Gold / Precious Metals' },
    { value: 'vehicle', label: 'Vehicle' },
    { value: 'jewellery', label: 'Jewellery' },
    { value: 'art_collectible', label: 'Art & Collectibles' },
    { value: 'business', label: 'Business Ownership' },
    { value: 'other', label: 'Other Physical Asset' }
  ];

  const handleSubmit = async (e, securityToken = null) => {
    if (e) e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const payload = {
        ...formData,
        current_value: parseFloat(formData.current_value),
        description: `Registered via Digital Twin`,
        valuation_date: new Date().toISOString().split('T')[0],
        ownership_type: 'sole',
        ownership_percentage: 100,
        outstanding_loan: 0
      };

      // 🛡️ Call the API
      // If securityToken is provided, it will bypass the high-risk block
      await assetsAPI.create(payload, securityToken);
      
      // Success!
      setFormData({
        category: 'real_estate',
        name: '',
        current_value: '',
        valuation_method: 'self_declared'
      });
      setChallengeData(null);
      
      if (onAssetAdded) onAssetAdded();
      alert('Asset registered successfully!');
    } catch (err) {
      // Check for Security Challenge from backend
      if (err.message.includes('SECURITY_CHALLENGE_REQUIRED')) {
        try {
          const detail = JSON.parse(err.message.split(' - ')[0] || '{}');
          setChallengeData(detail);
        } catch (pErr) {
          setError('Security challenge required, but failed to parse details.');
        }
      } else {
        setError(err.message || 'Failed to register asset');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleAuthorizedSubmit = () => {
    // Retry with a simulated security token
    handleSubmit(null, 'VERIFIED-DEVICE-TRUST-2026');
  };

  return (
    <div className="bg-white border border-[#e5e5e5] rounded-xl p-5 shadow-sm mb-5">
      <div className="text-[14px] font-semibold text-[#1a1a1a] mb-4 flex items-center gap-2">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#c8102e" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 5v14M5 12h14"/>
        </svg>
        Register New Physical Asset
      </div>
      
      <form onSubmit={(e) => handleSubmit(e)} className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div>
          <label className="block text-[11px] text-[#8a8a8a] uppercase font-bold mb-1">Category</label>
          <select 
            value={formData.category}
            onChange={(e) => setFormData({...formData, category: e.target.value})}
            className="w-full h-10 px-3 border border-[#eeeeee] rounded bg-[#fafafa] text-[13px] outline-none focus:border-[#c8102e]"
          >
            {categories.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
          </select>
        </div>
        
        <div>
          <label className="block text-[11px] text-[#8a8a8a] uppercase font-bold mb-1">Asset Name</label>
          <input 
            type="text"
            placeholder="e.g. Mumbai Flat, 24K Gold"
            value={formData.name}
            onChange={(e) => setFormData({...formData, name: e.target.value})}
            className="w-full h-10 px-3 border border-[#eeeeee] rounded bg-[#fafafa] text-[13px] outline-none focus:border-[#c8102e]"
            required
          />
        </div>
        
        <div>
          <label className="block text-[11px] text-[#8a8a8a] uppercase font-bold mb-1">Current Value (₹)</label>
          <input 
            type="number"
            placeholder="Amount in INR"
            value={formData.current_value}
            onChange={(e) => setFormData({...formData, current_value: e.target.value})}
            className="w-full h-10 px-3 border border-[#eeeeee] rounded bg-[#fafafa] text-[13px] outline-none focus:border-[#c8102e]"
            required
          />
        </div>
        
        <div className="flex items-end">
          <button 
            type="submit"
            disabled={loading}
            className="w-full h-10 bg-[#c8102e] text-white text-[13px] font-semibold rounded hover:bg-[#a80d26] transition-colors disabled:opacity-50"
          >
            {loading ? 'Analyzing Risk...' : 'Register Asset'}
          </button>
        </div>
      </form>
      
      {error && <p className="mt-3 text-[12px] text-[#c8102e]">{error}</p>}
      
      <div className="mt-4 pt-4 border-t border-[#f5f5f5] flex items-center gap-2 text-[11px] text-[#8a8a8a]">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
        </svg>
        AI-driven risk assessment is enabled for this action.
      </div>

      {/* Security Challenge Interceptor */}
      <SecurityChallengeModal 
        isOpen={!!challengeData}
        onClose={() => setChallengeData(null)}
        onVerify={handleAuthorizedSubmit}
        riskScore={challengeData?.risk_score}
        reasons={challengeData?.reasons}
      />
    </div>
  );
};

export default AddAssetForm;
