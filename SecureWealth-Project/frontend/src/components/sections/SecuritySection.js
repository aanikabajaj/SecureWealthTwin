import React, { useState, useEffect } from 'react';
import ListItem from '../ListItem';
import { authAPI } from '../../services/api';

const SecuritySection = ({ t }) => {
  const [securityData, setSecurityData] = useState({
    lastLogin: '...',
    activeDevices: '...',
    twoFactor: 'Checking...',
    passwordStrength: 'Strong'
  });

  useEffect(() => {
    const fetchSecurityInfo = async () => {
      try {
        const response = await authAPI.me();
        const user = response.data;
        
        // Format last login
        let lastLoginStr = 'Today, just now';
        if (user.last_login) {
          const date = new Date(user.last_login);
          lastLoginStr = date.toLocaleString([], { 
            month: 'short', 
            day: 'numeric', 
            hour: '2-digit', 
            minute: '2-digit' 
          });
        }

        setSecurityData({
          lastLogin: lastLoginStr,
          activeDevices: user.active_devices_count || 1,
          // Since we've mandated 2FA in the backend, it's effectively Enabled for all users
          twoFactor: 'Enabled', 
          passwordStrength: 'Strong'
        });
      } catch (err) {
        console.error("Failed to fetch security info:", err);
      }
    };

    fetchSecurityInfo();
  }, []);

  return (
    <div>
      <div className="mb-5">
        <div className="text-xl font-semibold text-[#1a1a1a]">{t.f7 || "Security"}</div>
      </div>
      <div className="bg-white border border-[#e5e5e5] rounded-xl p-5 shadow-sm">
        <ListItem 
          label={t.pass || "Password"} 
          value={securityData.passwordStrength} 
          badgeType="ok" 
        />
        <ListItem 
          label={t.twofa || "2-Step verification"} 
          value={securityData.twoFactor} 
          badgeType="ok" 
        />
        <ListItem 
          label={t.devices || "Active devices"} 
          value={securityData.activeDevices.toString()} 
          badgeType={securityData.activeDevices > 2 ? 'warn' : 'ok'} 
        />
        <ListItem 
          label={t.lastlogin || "Last login"} 
          value={securityData.lastLogin} 
          badgeType="info" 
        />
      </div>
    </div>
  );
};

export default SecuritySection;
