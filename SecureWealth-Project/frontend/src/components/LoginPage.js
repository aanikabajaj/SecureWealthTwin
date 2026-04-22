import React, { useState } from 'react';
import { authAPI } from '../services/api';

// Inline SVG for a minimal shield brand mark (matches Sidebar aesthetic, red version)
const BrandMark = () => (
  <div
    className="flex items-center justify-center w-[52px] h-[52px] rounded-md bg-[#c8102e]"
    data-testid="brand-mark"
  >
    <svg width="26" height="26" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <path
        d="M8 1.5L2 4.5V9C2 12.2 4.6 14.8 8 15.5C11.4 14.8 14 12.2 14 9V4.5L8 1.5Z"
        stroke="#ffffff"
        strokeWidth="1.4"
        fill="none"
      />
      <path
        d="M5.5 8.2l1.8 1.8L10.8 6.5"
        stroke="#ffffff"
        strokeWidth="1.4"
        fill="none"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  </div>
);

const KeyboardIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
    <rect x="2.5" y="6" width="19" height="12" rx="2" stroke="#c8102e" strokeWidth="1.6" />
    <path
      d="M6 10h.01M9 10h.01M12 10h.01M15 10h.01M18 10h.01M7 14h10"
      stroke="#c8102e"
      strokeWidth="1.6"
      strokeLinecap="round"
    />
  </svg>
);

const ShieldIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
  </svg>
);

const SearchIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
    <circle cx="11" cy="11" r="7" stroke="#c8102e" strokeWidth="1.8" />
    <path d="M20 20l-3.2-3.2" stroke="#c8102e" strokeWidth="1.8" strokeLinecap="round" />
  </svg>
);

const NAV_ITEMS = [
  'My Account',
  'Cards',
  'Investments',
  'Insurance',
  'Rewards & Benefits',
  'Business'
];

const ACCOUNT_TYPES = [
  { value: 'personal', label: 'Personal - My Account' },
  { value: 'wealth', label: 'Wealth - Premium' },
  { value: 'work', label: 'SecureWealth @ Work' }
];

const LoginPage = ({ onLogin, onShowRegister }) => {
  const [userId, setUserId] = useState('');
  const [password, setPassword] = useState('');
  const [accountType, setAccountType] = useState('personal');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  // 2FA State
  const [showOtp, setShowOtp] = useState(false);
  const [otpCode, setOtpCode] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!userId.trim() || !password.trim()) {
      setError('Please enter both User ID and Password.');
      return;
    }
    
    setError('');
    setIsLoading(true);
    
    try {
      const response = await authAPI.login(userId, password);
      
      if (response.data.otp_required) {
        setShowOtp(true);
      } else {
        // Direct login (if 2FA was disabled)
        const { access_token, refresh_token } = response.data;
        localStorage.setItem('access_token', access_token);
        localStorage.setItem('refresh_token', refresh_token);
        onLogin({ userId, accountType });
      }
    } catch (err) {
      setError(err.message || 'Invalid credentials. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleOtpVerify = async (e) => {
    e.preventDefault();
    if (otpCode.length !== 6) {
      setError('Please enter a valid 6-digit verification code.');
      return;
    }

    setError('');
    setIsLoading(true);

    try {
      const response = await authAPI.verifyOtp(userId, otpCode);
      const { access_token, refresh_token } = response.data;
      
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      
      onLogin({ userId, accountType });
    } catch (err) {
      setError(err.message || 'Invalid verification code.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-white text-[#1a1a1a] flex flex-col" data-testid="login-page">
      {/* Top Navigation */}
      <header className="w-full border-b border-[#eeeeee] bg-white">
        <div className="max-w-[1200px] mx-auto flex items-center px-6 py-4 gap-8">
          <div className="flex items-center gap-3" data-testid="brand-wrapper">
            <BrandMark />
            <div className="leading-tight">
              <div className="text-[16px] font-semibold text-[#c8102e]">SecureWealth</div>
              <div className="text-[10px] tracking-[0.22em] text-[#c8102e]/80">DIGITAL TWIN</div>
            </div>
          </div>

          <nav className="hidden md:flex items-center gap-6 flex-1">
            {NAV_ITEMS.map((item) => (
              <a
                key={item}
                href="#"
                onClick={(e) => e.preventDefault()}
                className="text-[13.5px] text-[#c8102e] hover:underline underline-offset-4"
              >
                {item}
              </a>
            ))}
          </nav>

          <div className="flex items-center gap-5 ml-auto">
            <button type="button" className="text-[#c8102e] hover:opacity-80">
              <SearchIcon />
            </button>
            <a href="#" onClick={(e) => e.preventDefault()} className="text-[13.5px] text-[#c8102e] hover:underline underline-offset-4">
              Help
            </a>
            <button
              type="button"
              className="px-4 py-2 rounded-md bg-[#c8102e] text-white text-[13px] font-medium hover:bg-[#a80d26] transition-colors"
            >
              Log In
            </button>
          </div>
        </div>
      </header>

      {/* Body */}
      <div className="flex-1 bg-[#f5f5f5]">
        <div className="max-w-[1050px] mx-auto grid grid-cols-1 md:grid-cols-2 gap-8 px-6 py-12">
          {/* Login Card */}
          <div className="bg-white border border-[#e5e5e5] rounded-lg p-8 md:p-10 shadow-sm">
            {!showOtp ? (
              <>
                <h1 className="text-center text-[22px] font-medium text-[#1a1a1a] mb-8">
                  Log In to My Account
                </h1>

                <form onSubmit={handleSubmit} noValidate>
                  <label htmlFor="userId" className="block text-[14px] font-semibold text-[#1a1a1a] mb-2">
                    User ID
                  </label>
                  <input
                    id="userId"
                    type="text"
                    value={userId}
                    onChange={(e) => setUserId(e.target.value)}
                    className="w-full h-[58px] px-3 border border-[#b0b0b0] rounded-sm mb-6 text-[15px] text-[#1a1a1a] bg-white focus:outline-none focus:border-[#c8102e]"
                  />

                  <label htmlFor="password" className="block text-[14px] font-semibold text-[#1a1a1a] mb-2">
                    Password
                  </label>
                  <div className="relative mb-6">
                    <input
                      id="password"
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="w-full h-[58px] pl-3 pr-12 border border-[#b0b0b0] rounded-sm text-[15px] text-[#1a1a1a] bg-white focus:outline-none focus:border-[#c8102e]"
                    />
                    <span className="absolute right-3 top-1/2 -translate-y-1/2">
                      <KeyboardIcon />
                    </span>
                  </div>

                  <label htmlFor="accountType" className="block text-[14px] font-semibold text-[#1a1a1a] mb-2">
                    Account Type
                  </label>
                  <select
                    id="accountType"
                    value={accountType}
                    onChange={(e) => setAccountType(e.target.value)}
                    className="w-full h-[52px] px-3 border border-[#b0b0b0] rounded-sm mb-6 text-[15px] text-[#1a1a1a] bg-white focus:outline-none focus:border-[#c8102e]"
                  >
                    {ACCOUNT_TYPES.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>

                  {error && <div className="mb-4 text-[13px] text-[#c8102e]">{error}</div>}

                  <button
                    type="submit"
                    disabled={isLoading}
                    className="w-full h-[52px] bg-[#c8102e] text-white font-medium rounded-sm hover:bg-[#a80d26] transition-colors mb-6 disabled:opacity-50"
                  >
                    {isLoading ? 'Processing...' : 'Log In'}
                  </button>
                </form>
              </>
            ) : (
              <div className="animate-in fade-in slide-in-from-right-10 duration-500">
                <div className="flex justify-center mb-6">
                  <div className="w-16 h-16 bg-[#c8102e]/10 rounded-full flex items-center justify-center text-[#c8102e]">
                    <ShieldIcon />
                  </div>
                </div>
                <h1 className="text-center text-[22px] font-medium text-[#1a1a1a] mb-2">
                  2-Step Verification
                </h1>
                <p className="text-center text-[14px] text-[#666666] mb-8">
                  We've sent a 6-digit code to <br />
                  <span className="font-semibold text-[#1a1a1a]">{userId}</span>
                </p>

                <form onSubmit={handleOtpVerify}>
                  <label htmlFor="otpCode" className="block text-[14px] font-semibold text-[#1a1a1a] mb-2">
                    Enter Code
                  </label>
                  <input
                    id="otpCode"
                    type="text"
                    maxLength="6"
                    placeholder="000000"
                    value={otpCode}
                    onChange={(e) => setOtpCode(e.target.value.replace(/[^0-9]/g, ''))}
                    className="w-full h-[58px] px-3 border border-[#b0b0b0] rounded-sm mb-6 text-[24px] text-center tracking-[1em] font-bold text-[#1a1a1a] bg-white focus:outline-none focus:border-[#c8102e]"
                  />

                  {error && <div className="mb-4 text-[13px] text-[#c8102e] text-center">{error}</div>}

                  <button
                    type="submit"
                    disabled={isLoading}
                    className="w-full h-[52px] bg-[#c8102e] text-white font-medium rounded-sm hover:bg-[#a80d26] transition-colors mb-6 disabled:opacity-50"
                  >
                    {isLoading ? 'Verifying...' : 'Authorize Secure Action'}
                  </button>

                  <div className="text-center">
                    <button 
                      type="button" 
                      onClick={() => setShowOtp(false)}
                      className="text-[13px] text-[#c8102e] hover:underline"
                    >
                      Back to Login
                    </button>
                  </div>
                </form>
              </div>
            )}

            <div className="flex flex-col gap-3 mt-6 pt-6 border-t border-[#eeeeee]">
              <a href="#" onClick={(e) => e.preventDefault()} className="text-[13.5px] text-[#c8102e] hover:underline">
                Forgot your User ID or Password?
              </a>
              <a
                href="#"
                onClick={(e) => {
                  e.preventDefault();
                  onShowRegister();
                }}
                className="text-[13.5px] text-[#c8102e] hover:underline"
              >
                Register for Online Services
              </a>
            </div>
          </div>

          {/* Welcome Panel */}
          <div className="bg-white border border-[#e5e5e5] rounded-lg p-10 flex flex-col justify-center items-start shadow-sm relative overflow-hidden">
            <div className="absolute top-0 left-0 h-full w-[6px] bg-[#c8102e]" aria-hidden="true" />
            <div className="text-[12px] tracking-[0.24em] text-[#c8102e] font-semibold mb-4">SECUREWEALTH</div>
            <h2 className="text-[34px] md:text-[40px] font-semibold text-[#1a1a1a] leading-tight mb-4">
              Welcome to <span className="text-[#c8102e]">Digital Twin</span>
            </h2>
            <p className="text-[15px] text-[#4a4a4a] leading-relaxed mb-6 max-w-[420px]">
              Your intelligent financial mirror — track spending, monitor risk, watch the market,
              grow your assets, and secure your wealth, all in one place.
            </p>

            <ul className="space-y-3 text-[14px] text-[#2a2a2a]">
              {['Real-time spending & asset insights', 'Personalized investment suggestions', 'Continuous security & fraud monitoring'].map((feat) => (
                <li key={feat} className="flex items-start gap-3">
                  <span className="mt-[6px] w-[8px] h-[8px] rounded-full bg-[#c8102e] flex-shrink-0" />
                  <span>{feat}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
