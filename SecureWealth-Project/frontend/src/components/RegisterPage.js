import React, { useState } from 'react';
import { authAPI } from '../services/api';

const BrandMark = () => (
  <div className="flex items-center justify-center w-[52px] h-[52px] rounded-md bg-[#c8102e]">
    <svg width="26" height="26" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <path d="M8 1.5L2 4.5V9C2 12.2 4.6 14.8 8 15.5C11.4 14.8 14 12.2 14 9V4.5L8 1.5Z" stroke="#ffffff" strokeWidth="1.4" fill="none" />
      <path d="M5.5 8.2l1.8 1.8L10.8 6.5" stroke="#ffffff" strokeWidth="1.4" fill="none" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  </div>
);

const RegisterPage = ({ onRegister, onBackToLogin }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email.trim() || !password.trim()) {
      setError('Please enter both Email and Password.');
      return;
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters long.');
      return;
    }
    
    setError('');
    setIsLoading(true);
    
    try {
      const response = await authAPI.register(email, password, fullName);
      const { access_token, refresh_token } = response.data;
      
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      
      onRegister();
    } catch (err) {
      setError(err.message || 'Registration failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#f5f5f5] text-[#1a1a1a] flex flex-col">
      <header className="w-full border-b border-[#eeeeee] bg-white">
        <div className="max-w-[1200px] mx-auto flex items-center px-6 py-4">
          <div className="flex items-center gap-3">
            <BrandMark />
            <div className="leading-tight">
              <div className="text-[16px] font-semibold text-[#c8102e]">SecureWealth</div>
              <div className="text-[10px] tracking-[0.22em] text-[#c8102e]/80">DIGITAL TWIN</div>
            </div>
          </div>
        </div>
      </header>

      <div className="flex-1 flex items-center justify-center py-12 px-6">
        <div className="bg-white border border-[#e5e5e5] rounded-lg p-8 md:p-10 shadow-sm w-full max-w-[500px]">
          <h1 className="text-center text-[22px] font-medium text-[#1a1a1a] mb-8">
            Create Your Account
          </h1>

          <form onSubmit={handleSubmit}>
            <label className="block text-[14px] font-semibold text-[#1a1a1a] mb-2">Full Name</label>
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="w-full h-[52px] px-3 border border-[#b0b0b0] rounded-sm mb-6 text-[15px]"
            />

            <label className="block text-[14px] font-semibold text-[#1a1a1a] mb-2">Email (User ID)</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full h-[52px] px-3 border border-[#b0b0b0] rounded-sm mb-6 text-[15px]"
              required
            />

            <label className="block text-[14px] font-semibold text-[#1a1a1a] mb-2">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full h-[52px] px-3 border border-[#b0b0b0] rounded-sm mb-6 text-[15px]"
              required
            />

            {error && <div className="mb-4 text-[13px] text-[#c8102e]">{error}</div>}

            <button
              type="submit"
              disabled={isLoading}
              className="w-full h-[52px] bg-[#c8102e] text-white font-medium rounded-sm hover:bg-[#a80d26] transition-colors mb-6 disabled:opacity-50"
            >
              {isLoading ? 'Registering...' : 'Register'}
            </button>

            <div className="text-center">
              <button
                type="button"
                onClick={onBackToLogin}
                className="text-[13.5px] text-[#c8102e] hover:underline"
              >
                Already have an account? Log In
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;
