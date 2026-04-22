import React, { useState } from 'react';
import { simulatorAPI } from '../../services/api';

const SimulatorSection = ({ t }) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [params, setParams] = useState({
    monthly_savings: 25000,
    target_goal: 50000000,
    time_horizon: 120, // 10 years
    allocation: {
      equity: 0.6,
      fixed_income: 0.3,
      gold: 0.1
    }
  });

  const runSimulation = async () => {
    setLoading(true);
    try {
      const payload = {
        monthly_savings_rate_inr: params.monthly_savings,
        target_goal_inr: params.target_goal,
        time_horizon_months: params.time_horizon,
        investment_allocation: params.allocation,
        what_if_scenarios: [
          { label: "Optimistic Market", investment_allocation: { equity: 0.8, fixed_income: 0.1, gold: 0.1 } },
          { label: "Conservative Market", investment_allocation: { equity: 0.2, fixed_income: 0.7, gold: 0.1 } }
        ]
      };
      const response = await simulatorAPI.run(payload);
      setResult(response.data);
    } catch (err) {
      alert('Simulation failed: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="mb-6">
        <h2 className="text-xl font-bold text-[#1a1a1a]">Wealth Scenario Simulator</h2>
        <p className="text-[13px] text-[#6b6b6b] mt-1">Project your financial future using AI-driven market simulations.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Controls */}
        <div className="lg:col-span-1 space-y-6 bg-white p-6 border border-[#eeeeee] rounded-2xl shadow-sm">
          <div>
            <label className="flex justify-between text-[11px] font-bold uppercase text-[#8a8a8a] mb-3">
              Monthly Savings <span>₹{params.monthly_savings.toLocaleString()}</span>
            </label>
            <input 
              type="range" min="0" max="500000" step="5000"
              value={params.monthly_savings}
              onChange={(e) => setParams({...params, monthly_savings: parseInt(e.target.value)})}
              className="w-full h-1.5 bg-[#fde8ec] rounded-lg appearance-none cursor-pointer accent-[#c8102e]"
            />
          </div>

          <div>
            <label className="flex justify-between text-[11px] font-bold uppercase text-[#8a8a8a] mb-3">
              Target Goal <span>₹{(params.target_goal / 10000000).toFixed(1)} Cr</span>
            </label>
            <input 
              type="range" min="1000000" max="500000000" step="1000000"
              value={params.target_goal}
              onChange={(e) => setParams({...params, target_goal: parseInt(e.target.value)})}
              className="w-full h-1.5 bg-[#fde8ec] rounded-lg appearance-none cursor-pointer accent-[#c8102e]"
            />
          </div>

          <div>
            <label className="flex justify-between text-[11px] font-bold uppercase text-[#8a8a8a] mb-3">
              Time Horizon <span>{Math.floor(params.time_horizon / 12)} Years</span>
            </label>
            <input 
              type="range" min="12" max="360" step="12"
              value={params.time_horizon}
              onChange={(e) => setParams({...params, time_horizon: parseInt(e.target.value)})}
              className="w-full h-1.5 bg-[#fde8ec] rounded-lg appearance-none cursor-pointer accent-[#c8102e]"
            />
          </div>

          <button 
            onClick={runSimulation}
            disabled={loading}
            className="w-full py-4 bg-[#c8102e] text-white rounded-xl font-bold text-[15px] hover:bg-[#a80d26] transition-all active:scale-[0.98] shadow-lg shadow-red-100 flex items-center justify-center gap-2"
          >
            {loading ? (
              <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div> Running Projection...</>
            ) : "Run AI Simulation"}
          </button>
        </div>

        {/* Results */}
        <div className="lg:col-span-2 space-y-6">
          {!result ? (
            <div className="h-full flex flex-col items-center justify-center bg-[#fcfcfc] border-2 border-dashed border-[#eeeeee] rounded-2xl p-12 text-center">
              <div className="w-16 h-16 bg-[#fde8ec] rounded-full flex items-center justify-center mb-4">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#c8102e" strokeWidth="2">
                  <path d="M21.21 15.89A10 10 0 1 1 8 2.83" />
                  <path d="M22 12A10 10 0 0 0 12 2v10z" />
                </svg>
              </div>
              <h3 className="text-lg font-bold text-[#1a1a1a]">Ready to Project</h3>
              <p className="text-[13px] text-[#8a8a8a] max-w-xs mt-2">Adjust your parameters and click "Run AI Simulation" to see your wealth trajectory.</p>
            </div>
          ) : (
            <div className="space-y-6 animate-in fade-in zoom-in-95 duration-500">
              {/* Primary Result */}
              <div className="bg-[#1a1a1a] rounded-2xl p-8 text-white relative overflow-hidden">
                <div className="relative z-10">
                  <div className="text-[11px] font-bold uppercase text-white/50 tracking-widest mb-1">Projected Net Worth</div>
                  <div className="text-4xl font-bold mb-6">₹{(result.projected_wealth_inr / 10000000).toFixed(2)} <span className="text-xl text-white/60">Cr</span></div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-white/10 p-4 rounded-xl">
                      <div className="text-[10px] text-white/50 uppercase font-bold mb-1">Goal Probability</div>
                      <div className="text-2xl font-bold text-green-400">{result.goal_achievement_probability.toFixed(1)}%</div>
                    </div>
                    <div className="bg-white/10 p-4 rounded-xl">
                      <div className="text-[10px] text-white/50 uppercase font-bold mb-1">Simulation Label</div>
                      <div className="text-lg font-bold">{result.simulation_label}</div>
                    </div>
                  </div>
                </div>
                {/* Background Decor */}
                <div className="absolute top-[-20%] right-[-10%] w-64 h-64 bg-[#c8102e] opacity-20 blur-[100px] rounded-full"></div>
              </div>

              {/* What-If Scenarios */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {result.scenario_results && result.scenario_results.map((s, i) => (
                  <div key={i} className="bg-white border border-[#eeeeee] p-5 rounded-2xl">
                    <div className="flex justify-between items-start mb-4">
                      <span className="text-[12px] font-bold text-[#1a1a1a]">{s.label}</span>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${s.goal_achievement_probability > 70 ? 'bg-green-100 text-green-700' : 'bg-orange-100 text-orange-700'}`}>
                        {s.goal_achievement_probability.toFixed(0)}% Odds
                      </span>
                    </div>
                    <div className="text-xl font-bold text-[#1a1a1a]">₹{(s.projected_wealth_inr / 10000000).toFixed(2)} Cr</div>
                    <div className="mt-2 h-1 bg-gray-100 rounded-full overflow-hidden">
                      <div className="h-full bg-[#c8102e]" style={{ width: `${Math.min(100, (s.projected_wealth_inr / result.projected_wealth_inr) * 100)}%` }}></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SimulatorSection;
