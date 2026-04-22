import React, { useState } from 'react';

const GoalsSection = ({ t, setActiveSection }) => {
  const [goals, setGoals] = useState([
    { id: 1, title: 'Child Education', target: 5000000, current: 1250000, color: '#c8102e', icon: '🎓' },
    { id: 2, title: 'Retirement Fund', target: 100000000, current: 15000000, color: '#1a1a1a', icon: '👴' },
    { id: 3, title: 'New Luxury Home', target: 25000000, current: 8000000, color: '#15803d', icon: '🏠' },
  ]);

  const fmt = (n) => new Intl.NumberFormat('en-IN').format(n);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {goals.map(goal => {
          const progress = (goal.current / goal.target) * 100;
          return (
            <div key={goal.id} className="bg-white border border-[#e5e5e5] rounded-2xl p-6 shadow-sm hover:shadow-md transition-all">
              <div className="flex justify-between items-start mb-4">
                <div className="w-12 h-12 bg-[#f5f5f5] rounded-xl flex items-center justify-center text-2xl">
                  {goal.icon}
                </div>
                <div className="text-right">
                  <div className="text-[10px] font-bold text-[#8a8a8a] uppercase tracking-wider">Progress</div>
                  <div className="text-[16px] font-bold text-[#1a1a1a]">{Math.round(progress)}%</div>
                </div>
              </div>
              
              <h3 className="text-[15px] font-bold text-[#1a1a1a] mb-1">{goal.title}</h3>
              <div className="flex justify-between text-[11px] text-[#4a4a4a] mb-4">
                <span>₹{fmt(goal.current)}</span>
                <span className="text-[#8a8a8a]">Target: ₹{fmt(goal.target)}</span>
              </div>

              {/* Progress Bar */}
              <div className="w-full h-2 bg-[#f0f0f0] rounded-full overflow-hidden mb-4">
                <div 
                  className="h-full transition-all duration-1000 ease-out" 
                  style={{ width: `${progress}%`, backgroundColor: goal.color }}
                />
              </div>

              <div className="bg-blue-50/50 p-3 rounded-lg border border-blue-100/50">
                <p className="text-[11px] text-blue-700 leading-relaxed font-medium">
                  💡 SecureWealth Tip: Increase your SIP by ₹2,500 to reach this goal 14 months faster.
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Goal Simulation Feature */}
      <div className="bg-[#1a1a1a] rounded-2xl p-8 text-white relative overflow-hidden">
        <div className="relative z-10 max-w-xl">
          <h2 className="text-2xl font-bold mb-2">Simulate Your Future Wealth</h2>
          <p className="text-white/70 text-[14px] mb-6 leading-relaxed">
            Adjust your monthly savings and expected returns to see how they impact your 10-year wealth projection.
          </p>
          <div className="flex gap-4">
            <button 
              onClick={() => setActiveSection('simulator')}
              className="px-6 py-3 bg-[#c8102e] rounded-xl font-bold text-[13px] hover:bg-[#e01234] transition-colors"
            >
              Start Simulation
            </button>
            <button 
              onClick={() => setActiveSection('suggestions')}
              className="px-6 py-3 bg-white/10 rounded-xl font-bold text-[13px] hover:bg-white/20 transition-colors"
            >
              View Tax-Saving Options
            </button>
          </div>
        </div>
        {/* Abstract decoration */}
        <div className="absolute top-[-50%] right-[-10%] w-[400px] h-[400px] bg-[#c8102e]/10 rounded-full blur-[100px]" />
      </div>
    </div>
  );
};

export default GoalsSection;
