import React, { useState, useEffect } from 'react';
import { authAPI } from '../services/api';

const SecurityChallengeModal = ({ isOpen, onClose, onVerify, riskScore, reasons }) => {
  const [verifying, setVerifying] = useState(false);
  const [success, setSuccess] = useState(false);
  
  // Step-up Challenge States
  const [showChallenge, setShowChallenge] = useState(false);
  const [password, setPassword] = useState('');
  const [captchaInput, setCaptchaInput] = useState('');
  const [captchaText, setCaptchaText] = useState('');
  const [error, setError] = useState('');

  // Generate random captcha
  const generateCaptcha = () => {
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
    let result = '';
    for (let i = 0; i < 6; i++) {
      result += chars.charAt(Math.floor(randomInt(0, chars.length)));
    }
    setCaptchaText(result);
  };

  const randomInt = (min, max) => {
    return Math.floor(Math.random() * (max - min) + min);
  };

  useEffect(() => {
    if (isOpen && !showChallenge) {
      generateCaptcha();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleStartChallenge = () => {
    setShowChallenge(true);
    setError('');
  };

  const handleFinalVerify = async (e) => {
    e.preventDefault();
    if (!password || !captchaInput) {
      setError('Please fill in all fields.');
      return;
    }

    setError('');
    setVerifying(true);

    try {
      await authAPI.verifyChallenge(password, captchaInput, captchaText);
      setVerifying(false);
      setSuccess(true);
      setTimeout(() => {
        onVerify(); // Proceed with the asset registration
      }, 1500);
    } catch (err) {
      setError(err.message || 'Verification failed. Please check your password and captcha.');
      generateCaptcha(); // Refresh captcha on failure
      setCaptchaInput('');
    } finally {
      setVerifying(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-300">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden animate-in zoom-in-95 duration-300">
        {/* Header */}
        <div className="bg-[#c8102e] p-6 text-center relative">
          <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center mx-auto mb-3">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              <path d="M12 8v4M12 16h.01" />
            </svg>
          </div>
          <h2 className="text-white text-xl font-bold">Wealth Protection Shield</h2>
          <p className="text-white/80 text-[13px] mt-1">High-Risk Activity Detected</p>
          
          <div className="absolute top-4 right-4">
            <div className="bg-white/10 px-2 py-1 rounded text-[10px] text-white font-mono">
              RISK: {riskScore}/100
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="p-8">
          {!success ? (
            <>
              {!showChallenge ? (
                <>
                  <div className="bg-red-50 border-l-4 border-[#c8102e] p-6 mb-8 text-center rounded-r-xl">
                    <p className="text-[16px] text-[#c8102e] font-bold leading-relaxed">
                      this security shield is to avoid adding assets via bot
                    </p>
                  </div>

                  <button
                    onClick={handleStartChallenge}
                    className="w-full py-4 bg-[#1a1a1a] text-white rounded-xl font-semibold text-[15px] hover:bg-[#333] transition-all active:scale-[0.98] flex items-center justify-center gap-3"
                  >
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <rect x="5" y="11" width="14" height="10" rx="2" ry="2"/>
                      <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                    </svg>
                    Authorize Secure Action
                  </button>
                  
                  <button onClick={onClose} className="w-full mt-3 py-2 text-[13px] text-[#8a8a8a] hover:text-[#4a4a4a] transition-colors">
                    Cancel Transaction
                  </button>
                </>
              ) : (
                <form onSubmit={handleFinalVerify} className="animate-in slide-in-from-right-10 duration-500">
                  <div className="mb-6">
                    <label className="block text-[13px] font-bold text-[#1a1a1a] uppercase tracking-wider mb-2">Login Password</label>
                    <input 
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Enter your password"
                      className="w-full p-4 border border-[#e5e5e5] rounded-xl focus:outline-none focus:border-[#c8102e] focus:ring-2 focus:ring-[#c8102e]/20"
                    />
                  </div>

                  <div className="mb-6">
                    <label className="block text-[13px] font-bold text-[#1a1a1a] uppercase tracking-wider mb-2">Human Verification</label>
                    <div className="flex items-center gap-4 mb-3">
                      <div className="bg-[#f3f4f6] px-6 py-3 rounded-xl font-mono text-2xl tracking-[0.3em] text-[#1a1a1a] select-none italic border border-[#e5e5e5] flex-1 text-center shadow-inner">
                        {captchaText}
                      </div>
                      <button 
                        type="button" 
                        onClick={generateCaptcha}
                        className="p-3 text-[#c8102e] hover:bg-red-50 rounded-xl transition-colors"
                        title="Refresh Captcha"
                      >
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
                        </svg>
                      </button>
                    </div>
                    <input 
                      type="text"
                      value={captchaInput}
                      onChange={(e) => setCaptchaInput(e.target.value.toUpperCase())}
                      placeholder="Type the characters above"
                      className="w-full p-4 border border-[#e5e5e5] rounded-xl focus:outline-none focus:ring-2 focus:ring-[#c8102e]/20"
                    />
                  </div>

                  {error && <div className="mb-4 text-[13px] text-[#c8102e] font-medium text-center">{error}</div>}

                  <button
                    type="submit"
                    disabled={verifying}
                    className="w-full py-4 bg-[#c8102e] text-white rounded-xl font-semibold text-[15px] hover:bg-[#a80d26] transition-all disabled:opacity-50 flex items-center justify-center gap-3"
                  >
                    {verifying ? (
                      <>
                        <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                        Verifying...
                      </>
                    ) : (
                      'Confirm Identity'
                    )}
                  </button>

                  <button 
                    type="button"
                    onClick={() => setShowChallenge(false)}
                    className="w-full mt-3 py-2 text-[13px] text-[#8a8a8a] hover:text-[#4a4a4a] transition-colors"
                  >
                    Go Back
                  </button>
                </form>
              )}
            </>
          ) : (
            <div className="text-center py-8 animate-in zoom-in duration-500">
              <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#15803d" strokeWidth="3">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-[#1a1a1a]">Action Authorized</h3>
              <p className="text-[14px] text-[#6b6b6b] mt-2">Identity verified via Multi-Factor Challenge</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-8 py-4 bg-[#f9fafb] border-t border-[#eeeeee] flex items-center justify-center gap-2">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#8a8a8a" strokeWidth="2">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
          </svg>
          <span className="text-[11px] text-[#8a8a8a]">Immutable Audit Trail Active</span>
        </div>
      </div>
    </div>
  );
};

export default SecurityChallengeModal;
