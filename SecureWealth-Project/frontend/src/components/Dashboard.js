import React, { useState } from 'react';
import { translations } from '../translations';
import Sidebar from './Sidebar';
import TopBar from './TopBar';
import SpendingSection from './sections/SpendingSection';
import RiskSection from './sections/RiskSection';
import MarketSection from './sections/MarketSection';
import BankSection from './sections/BankSection';
import AssetsSection from './sections/AssetsSection';
import SuggestionsSection from './sections/SuggestionsSection';
import SecuritySection from './sections/SecuritySection';
import SimulatorSection from './sections/SimulatorSection';
import GoalsSection from './sections/GoalsSection';
import AuditTrail from './AuditTrail';
import AIChatAdvisor from './AIChatAdvisor';

const Dashboard = ({ onLogout }) => {
  const [activeSection, setActiveSection] = useState('spending');
  const [language, setLanguage] = useState('en');
  const [isBusinessMode, setBusinessMode] = useState(false);

  const t = translations[language] || translations.en;

  const renderSection = () => {
    switch (activeSection) {
      case 'spending':
        return <SpendingSection t={t} isBusinessMode={isBusinessMode} />;
      case 'goals':
        return <GoalsSection t={t} setActiveSection={setActiveSection} />;
      case 'risk':
        return <RiskSection t={t} />;
      case 'market':
        return <MarketSection t={t} />;
      case 'bank':
        return <BankSection t={t} />;
      case 'assets':
        return <AssetsSection t={t} />;
      case 'suggestions':
        return <SuggestionsSection t={t} />;
      case 'simulator':
        return <SimulatorSection t={t} />;
      case 'security':
        return <SecuritySection t={t} />;
      case 'audit':
        return (
          <div className="space-y-6">
            <h2 className="text-[24px] font-semibold text-[#1a1a1a]">Security & Audit</h2>
            <p className="text-[14px] text-[#4a4a4a]">
              View all immutable records of your financial actions and security events stored on the blockchain.
            </p>
            <AuditTrail />
          </div>
        );
      default:
        return <SpendingSection t={t} isBusinessMode={isBusinessMode} />;
    }
  };

  return (
    <div className="flex min-h-screen bg-[#f7f7f8] text-[#1a1a1a]">
      <Sidebar
        activeSection={activeSection}
        setActiveSection={setActiveSection}
        t={t}
        onLogout={onLogout}
      />
      <div className="flex-1 flex flex-col overflow-hidden">
        <TopBar
          activeSection={activeSection}
          setActiveSection={setActiveSection}
          language={language}
          setLanguage={setLanguage}
          t={t}
          onLogout={onLogout}
          isBusinessMode={isBusinessMode}
          setBusinessMode={setBusinessMode}
        />
        
        {/* Business Mode Banner */}
        {isBusinessMode && (
          <div className="bg-[#1a1a1a] text-white px-6 py-2 flex items-center gap-3 animate-in slide-in-from-top duration-300">
            <div className="bg-white/20 p-1 rounded">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                <rect x="2" y="7" width="20" height="14" rx="2" ry="2"/>
                <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>
              </svg>
            </div>
            <span className="text-[10px] font-bold uppercase tracking-widest">Corporate Liquidity View Active</span>
          </div>
        )}

        <div className="flex-1 p-6 overflow-y-auto">
          {activeSection === 'spending' && !isBusinessMode && (
             <div className="mb-6 flex gap-4">
                <button 
                  onClick={() => setActiveSection('goals')}
                  className="bg-white border border-[#e5e5e5] px-4 py-3 rounded-xl flex items-center gap-3 hover:border-[#c8102e]/30 transition-all shadow-sm"
                >
                  <div className="text-xl">🎯</div>
                  <div className="text-left">
                    <div className="text-[10px] font-bold text-[#8a8a8a] uppercase">Action</div>
                    <div className="text-[13px] font-bold text-[#1a1a1a]">View Financial Goals</div>
                  </div>
                </button>
             </div>
          )}
          {renderSection()}
        </div>
      </div>
      
      {/* Floating AI Chat Advisor */}
      <AIChatAdvisor />
    </div>
  );
};

export default Dashboard;
