// Chart configuration constants and styles
import { useMemo } from 'react';

// Net Worth Chart Data Constants
export const NET_WORTH_DATA = [
  { month: 'Jul', value: 450 },
  { month: 'Aug', value: 458 },
  { month: 'Sep', value: 462 },
  { month: 'Oct', value: 475 },
  { month: 'Nov', value: 488 },
  { month: 'Dec', value: 500 },
  { month: 'Jan', value: 515 },
  { month: 'Feb', value: 535 },
  { month: 'Mar', value: 560 }
];

// Allocation palette (tuned for white background visibility)
export const ALLOCATION_COLORS = {
  EQUITIES: '#c8102e',
  BONDS: '#1d4ed8',
  REAL_ESTATE: '#b45309',
  CASH: '#6b6b6b',
  CRYPTO: '#15803d'
};

// Brand color used across charts
export const BRAND_RED = '#c8102e';

// Allocation Bar Width Constants (percentage multipliers)
export const ALLOCATION_WIDTHS = {
  EQUITIES: 84, // 42% * 2
  BONDS: 50,    // 25% * 2
  REAL_ESTATE: 36, // 18% * 2
  CASH: 20,     // 10% * 2
  CRYPTO: 10    // 5% * 2
};

// Chart Style Hooks (light theme)
export const useChartStyles = () => {
  const tickStyle = useMemo(() => ({ fill: '#4a4a4a', fontSize: 11 }), []);

  const tooltipContentStyle = useMemo(() => ({
    backgroundColor: '#ffffff',
    border: '1px solid #e5e5e5',
    borderRadius: '8px',
    color: '#1a1a1a',
    boxShadow: '0 4px 12px rgba(0,0,0,0.08)'
  }), []);

  const tooltipLabelStyle = useMemo(() => ({ color: '#c8102e', fontWeight: 600 }), []);

  return {
    tickStyle,
    tooltipContentStyle,
    tooltipLabelStyle
  };
};
