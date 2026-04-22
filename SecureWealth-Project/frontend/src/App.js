import React, { useState } from "react";
import "@/App.css";
import Dashboard from "./components/Dashboard";
import LoginPage from "./components/LoginPage";
import RegisterPage from "./components/RegisterPage";
import { WealthProvider } from "./context/WealthContext";

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(
    !!localStorage.getItem("access_token")
  );
  const [showRegister, setShowRegister] = useState(false);

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setIsAuthenticated(false);
  };

  if (isAuthenticated) {
    return (
      <div className="App relative min-h-screen">
        {/* Mandatory Rule #2: Simulation Disclaimer */}
        <div className="fixed bottom-4 left-4 z-[9999] pointer-events-none opacity-40">
          <div className="bg-[#1a1a1a] text-white px-4 py-2 rounded-full text-[10px] font-bold tracking-widest uppercase border border-white/20 shadow-2xl">
            FOR SIMULATION / DEMO ONLY
          </div>
        </div>
        
        <WealthProvider onSessionExpired={handleLogout}>
          <Dashboard onLogout={handleLogout} />
        </WealthProvider>
      </div>
    );
  }

  return (
    <div className="App">
      {showRegister ? (
        <RegisterPage
          onRegister={() => setIsAuthenticated(true)}
          onBackToLogin={() => setShowRegister(false)}
        />
      ) : (
        <LoginPage
          onLogin={() => setIsAuthenticated(true)}
          onShowRegister={() => setShowRegister(true)}
        />
      )}
    </div>
  );
}

export default App;
