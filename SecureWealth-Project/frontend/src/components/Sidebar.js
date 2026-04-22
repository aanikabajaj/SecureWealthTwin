import React from 'react';
import { useWealth } from '../context/WealthContext';

// Navigation item icons
const DashboardIcon = () => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
    <rect x="1" y="1" width="6" height="6" rx="1" stroke="currentColor" strokeWidth="1.2" />
    <rect x="9" y="1" width="6" height="6" rx="1" stroke="currentColor" strokeWidth="1.2" />
    <rect x="1" y="9" width="6" height="6" rx="1" stroke="currentColor" strokeWidth="1.2" />
    <rect x="9" y="9" width="6" height="6" rx="1" stroke="currentColor" strokeWidth="1.2" />
  </svg>
);

const TrendIcon = () => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
    <path d="M2 12l4-4 3 3 5-7" stroke="currentColor" strokeWidth="1.4" fill="none" />
  </svg>
);

const ChartIcon = () => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
    <polyline points="2,12 5,6 9,9 13,3 15,5" stroke="currentColor" strokeWidth="1.4" fill="none" />
  </svg>
);

const AlertIcon = () => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
    <path d="M8 2L1 14h14L8 2z" stroke="currentColor" strokeWidth="1.2" fill="none" />
    <path d="M8 7v3M8 11.5v.5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
  </svg>
);

const AssetIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
    <polyline points="9 22 9 12 15 12 15 22" />
  </svg>
);

const AuditIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    <path d="M12 8v4" />
    <path d="M12 16h.01" />
  </svg>
);

const LogoutIcon = () => (
  <svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true">
    <path d="M6 2H3a1 1 0 00-1 1v10a1 1 0 001 1h3" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
    <path d="M10 5l3 3-3 3M13 8H7" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const BrandLogo = () => (
  <div className="flex items-center gap-2.5" data-testid="sidebar-brand">
    <div className="w-[34px] h-[34px] rounded-md bg-[#c8102e] flex items-center justify-center">
      <svg width="18" height="18" viewBox="0 0 16 16" fill="none">
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
    <div>
      <div className="text-[15px] font-semibold text-[#c8102e]">SecureWealth</div>
      <div className="text-[10px] text-[#c8102e]/70 tracking-[0.22em] mt-0.5">DIGITAL TWIN</div>
    </div>
  </div>
);

const UserProfile = ({ onLogout }) => {
  const { user } = useWealth();
  if (!user) return null;

  const initials = user.full_name
    ? user.full_name.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2)
    : '??';

  return (
    <div className="flex items-center gap-2.5" data-testid="sidebar-user-profile">
      <div className="w-9 h-9 rounded-full bg-[#fde8ec] flex items-center justify-center text-xs font-semibold text-[#c8102e]">
        {initials}
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-[13px] font-semibold text-[#1a1a1a] truncate">{user.full_name}</div>
        <div className="text-[11px] text-[#6b6b6b]">Premium Account</div>
      </div>
      {onLogout && (
        <button
          type="button"
          onClick={onLogout}
          aria-label="Log out"
          title="Log out"
          className="p-2 rounded-md text-[#c8102e] hover:bg-[#fde8ec] transition-colors"
          data-testid="sidebar-logout-button"
        >
          <LogoutIcon />
        </button>
      )}
    </div>
  );
};

const NavigationItem = ({ item, activeSection, onClick }) => {
  const isActive = activeSection === item.key;
  return (
    <div
      onClick={onClick}
      className={`flex items-center gap-2.5 px-5 py-2.5 cursor-pointer text-[13px] border-l-[3px] transition-colors ${
        isActive
          ? 'text-[#c8102e] bg-[#fde8ec] border-[#c8102e] font-semibold'
          : 'text-[#3a3a3a] border-transparent hover:text-[#c8102e] hover:bg-[#fff4f6]'
      }`}
      data-testid={`sidebar-nav-${item.key}`}
    >
      <span
        className={`w-4 h-4 flex-shrink-0 ${isActive ? 'opacity-100' : 'opacity-80'}`}
        style={{ color: isActive ? '#c8102e' : 'currentColor' }}
      >
        {item.icon}
      </span>
      <span>{item.label}</span>
    </div>
  );
};

const Sidebar = ({ activeSection, setActiveSection, t, onLogout }) => {
  const navItems = [
    { key: 'spending', label: t.dashboard, icon: <DashboardIcon /> },
    { key: 'assets', label: 'Physical Assets', icon: <AssetIcon /> },
    { key: 'suggestions', label: t.wi, icon: <TrendIcon /> },
    { key: 'simulator', label: 'Wealth Simulator', icon: <ChartIcon /> },
    { key: 'market', label: t.inv, icon: <ChartIcon /> },
    { key: 'security', label: t.fraud, icon: <AlertIcon /> },
    { key: 'audit', label: 'Blockchain Audit', icon: <AuditIcon /> }
  ];

  return (
    <div
      className="w-[220px] flex-shrink-0 bg-white border-r border-[#e5e5e5] flex flex-col"
      data-testid="sidebar"
    >
      <div className="p-5 pb-6 border-b border-[#e5e5e5]">
        <BrandLogo />
      </div>
      <div className="text-[10px] text-[#6b6b6b] tracking-wider px-5 pt-5 pb-2 uppercase font-semibold">
        Navigation
      </div>
      <div>
        {navItems.map((item) => (
          <NavigationItem
            key={item.key}
            item={item}
            activeSection={activeSection}
            onClick={() => setActiveSection(item.key)}
          />
        ))}
      </div>
      <div className="mt-auto px-5 py-4 border-t border-[#e5e5e5]">
        <UserProfile onLogout={onLogout} />
      </div>
    </div>
  );
};

export default Sidebar;
