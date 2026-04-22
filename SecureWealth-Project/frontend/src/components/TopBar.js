import React, { useMemo } from 'react';

const TabButton = ({ tab, activeSection, onClick }) => (
  <button
    onClick={onClick}
    className={`px-3.5 py-1.5 rounded-full text-xs cursor-pointer border transition-colors ${
      activeSection === tab.key
        ? 'bg-[#c8102e] border-[#c8102e] text-white font-semibold'
        : 'bg-white border-[#e5e5e5] text-[#3a3a3a] hover:bg-[#fde8ec] hover:text-[#c8102e] hover:border-[#f5c7cf]'
    }`}
    data-testid={`topbar-tab-${tab.key}`}
  >
    {tab.label}
  </button>
);

const LanguageSelector = ({ language, onToggle, onSelect }) => (
  <div className="flex gap-2 items-center">
    <button
      onClick={onToggle}
      className="text-[11px] px-3 py-1.5 bg-white border border-[#e5e5e5] text-[#3a3a3a] rounded-full cursor-pointer hover:bg-[#fde8ec] hover:text-[#c8102e] hover:border-[#f5c7cf] transition-colors"
      data-testid="topbar-language-toggle"
    >
      ENG / हिंदी
    </button>
  </div>
);

const KYCBadge = () => (
  <div className="flex items-center gap-1 bg-[#15803d]/10 px-3 py-1.5 rounded-full border border-[#15803d]/20">
    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#15803d" strokeWidth="3">
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
      <polyline points="22 4 12 14.01 9 11.01" />
    </svg>
    <span className="text-[10px] text-[#15803d] font-bold uppercase tracking-wider">KYC Verified</span>
  </div>
);

const SandboxIndicator = () => (
  <div className="flex items-center gap-1 bg-[#f59e0b]/10 px-3 py-1.5 rounded-full border border-[#f59e0b]/20">
    <span className="w-[6px] h-[6px] rounded-full bg-[#f59e0b] animate-pulse" />
    <span className="text-[10px] text-[#f59e0b] font-bold uppercase tracking-wider">Simulation Mode</span>
  </div>
);

const TopBar = ({ activeSection, setActiveSection, language, setLanguage, t, onLogout, isBusinessMode, setBusinessMode }) => {
  const tabs = useMemo(() => [
    { key: 'spending', label: t.f1 },
    { key: 'risk', label: t.f2 },
    { key: 'market', label: t.f3 },
    { key: 'bank', label: t.f4 },
    { key: 'assets', label: t.f5 },
    { key: 'suggestions', label: t.f6 },
    { key: 'security', label: t.f7 }
  ], [t]);

  const handleLangToggle = () => {
    setLanguage(language === 'en' ? 'hi' : 'en');
  };

  return (
    <div
      className="flex justify-between items-center px-6 py-3.5 border-b border-[#e5e5e5] bg-white"
      data-testid="topbar"
    >
      <div className="flex gap-1 flex-wrap">
        {tabs.map((tab) => (
          <TabButton
            key={tab.key}
            tab={tab}
            activeSection={activeSection}
            onClick={() => setActiveSection(tab.key)}
          />
        ))}
      </div>
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 mr-2 pr-4 border-r border-[#eeeeee]">
          <span className="text-[10px] font-bold text-[#8a8a8a] uppercase tracking-tighter">View</span>
          <button 
            onClick={() => setBusinessMode(!isBusinessMode)}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-[10px] font-bold transition-all ${
              isBusinessMode 
                ? 'bg-[#1a1a1a] text-white' 
                : 'bg-[#f5f5f5] text-[#4a4a4a] hover:bg-[#eeeeee]'
            }`}
          >
            {isBusinessMode ? 'Corporate' : 'Individual'}
          </button>
        </div>
        
        <KYCBadge />
        <SandboxIndicator />
        
        <LanguageSelector
          language={language}
          onToggle={handleLangToggle}
        />
        
        {onLogout && (
          <button
            type="button"
            onClick={onLogout}
            className="text-[11px] px-3 py-1.5 bg-[#c8102e] text-white rounded-full cursor-pointer hover:bg-[#a80d26] font-semibold transition-colors"
            data-testid="topbar-logout-button"
          >
            Log Out
          </button>
        )}
      </div>
    </div>
  );
};

export default TopBar;
