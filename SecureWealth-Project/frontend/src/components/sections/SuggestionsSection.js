import React, { useState } from 'react';
import SecurityChallengeModal from '../SecurityChallengeModal';

const SuggestionCard = ({ title, description, category, action, icon, onClick }) => (
  <div className="bg-white border border-[#e5e5e5] rounded-xl p-5 hover:border-[#c8102e]/30 transition-all group">
    <div className="flex items-start gap-4 mb-4">
      <div className="w-10 h-10 bg-[#f5f5f5] rounded-lg flex items-center justify-center text-xl group-hover:bg-[#fde8ec] transition-colors">
        {icon}
      </div>
      <div>
        <div className="text-[10px] font-bold text-[#c8102e] uppercase tracking-widest mb-0.5">{category}</div>
        <h3 className="text-[14px] font-bold text-[#1a1a1a]">{title}</h3>
      </div>
    </div>
    <p className="text-[13px] text-[#4a4a4a] leading-relaxed mb-5">
      {description}
    </p>
    <button 
      onClick={() => onClick(title)}
      className="w-full py-2.5 bg-[#f5f5f5] text-[#1a1a1a] text-[12px] font-bold rounded-lg hover:bg-[#c8102e] hover:text-white transition-all"
    >
      {action}
    </button>
  </div>
);

const SuggestionsSection = ({ t }) => {
  const [challengeData, setChallengeData] = useState(null);
  const [activeAction, setActiveAction] = useState(null);

  const handleActionClick = (title) => {
    setActiveAction(title);
    // Simulate a security challenge for wealth-building actions
    // Higher risk score for SIP adjustments to demonstrate the shield
    const riskScore = title.includes('SIP') ? 82 : 45;
    setChallengeData({
      risk_score: riskScore,
      reasons: [
        { signal_name: "Transaction Urgency", contribution: 0.4, description: "High-value wealth rebalancing detected." },
        { signal_name: "Behavioral Sync", contribution: -0.2, description: "Verified human interaction pattern." }
      ]
    });
  };

  const handleAuthorized = () => {
    setChallengeData(null);
    alert(`Success! "${activeAction}" has been securely authorized and initiated.`);
  };

  const suggestions = [
    {
      title: "Optimize Your SIPs",
      category: "Investment",
      icon: "📈",
      description: "Based on your current saving rate of 32%, you can safely increase your Monthly SIP by ₹5,000 to reach your Retirement goal 3 years earlier.",
      action: "Adjust SIP Amount"
    },
    {
      title: "Smart Tax-Saving (Section 80C)",
      category: "Tax Planning",
      icon: "📑",
      description: "You have only utilized ₹80,000 of your ₹1.5L limit. Investing in ELSS funds can save you an additional ₹21,000 in taxes this year.",
      action: "Explore ELSS Funds"
    },
    {
      title: "Portfolio Rebalancing",
      category: "Portfolio",
      icon: "⚖️",
      description: "Your equity exposure has grown to 65% due to market trends. Rebalancing 10% to Debt/Gold is recommended to maintain your Moderate risk profile.",
      action: "Start Rebalance"
    },
    {
      title: "Emergency Fund Buffer",
      category: "Risk Management",
      icon: "🛡️",
      description: "Your current liquidity covers 4 months of expenses. Aim for 6 months (₹2.5L) to improve your financial resilience score.",
      action: "Set Aside Savings"
    },
    {
      title: "Healthy Habit: Subscription Cleanup",
      category: "Spending",
      icon: "✂️",
      description: "AI detected 3 unused media subscriptions (₹1,200/mo). Canceling these could add ₹1.4L to your wealth over 5 years.",
      action: "Review Subscriptions"
    },
    {
      title: "Goal Opportunity: Home Loan Pre-pay",
      category: "Goals",
      icon: "🏠",
      description: "With your recent bonus, making a ₹2L pre-payment on your home loan could save you ₹4.5L in long-term interest.",
      action: "Make Pre-payment"
    }
  ];

  return (
    <div className="space-y-6">
      <div className="mb-6">
        <h2 className="text-[20px] font-bold text-[#1a1a1a]">Intelligent Suggestions</h2>
        <p className="text-[13px] text-[#8a8a8a] mt-1">AI-driven insights based on your spending, market trends, and life goals.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {suggestions.map((s, i) => (
          <SuggestionCard key={i} {...s} onClick={handleActionClick} />
        ))}
      </div>

      <div className="mt-8 bg-gradient-to-r from-[#c8102e] to-[#a80d26] rounded-2xl p-8 text-white">
        <div className="max-w-2xl">
          <h3 className="text-xl font-bold mb-3">Responsible AI Disclaimer</h3>
          <p className="text-white/80 text-[13px] leading-relaxed mb-0">
            SecureWealth Twin provides recommendations based on historical data and market indicators. 
            Every suggestion includes an "Explain" link to show you the logic behind the advice, ensuring data transparency 
            and explainable AI (XAI) standards. These insights are for simulation purposes only.
          </p>
        </div>
      </div>

      {/* Mandatory Wealth Protection Shield */}
      <SecurityChallengeModal 
        isOpen={!!challengeData}
        onClose={() => setChallengeData(null)}
        onVerify={handleAuthorized}
        riskScore={challengeData?.risk_score}
        reasons={challengeData?.reasons}
      />
    </div>
  );
};

export default SuggestionsSection;
