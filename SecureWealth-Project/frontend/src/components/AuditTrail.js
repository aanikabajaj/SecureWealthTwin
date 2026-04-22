import React, { useState, useEffect } from 'react';
import { auditAPI } from '../services/api';

const AuditTrail = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const response = await auditAPI.getTrail();
        setLogs(response.data.logs);
      } catch (error) {
        console.error('Failed to fetch audit trail:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchLogs();
  }, []);

  if (loading) return <div className="p-4 text-center">Loading Immutable Audit Trail...</div>;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-[#eeeeee] overflow-hidden">
      <div className="bg-[#f8f9fa] px-4 py-3 border-b border-[#eeeeee] flex justify-between items-center">
        <h3 className="text-[14px] font-semibold text-[#1a1a1a] flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-[#c8102e]"></span>
          Immutable Audit Ledger (Blockchain)
        </h3>
        <span className="text-[10px] text-[#8a8a8a] font-mono">PROVIDER: ETHEREUM_TESTNET</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-[12px]">
          <thead>
            <tr className="bg-[#fafafa] text-[#8a8a8a] border-b border-[#eeeeee]">
              <th className="px-4 py-2 font-medium">TIMESTAMP</th>
              <th className="px-4 py-2 font-medium">ACTION</th>
              <th className="px-4 py-2 font-medium">DATA HASH</th>
              <th className="px-4 py-2 font-medium text-center">RISK</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#eeeeee]">
            {logs.map((log) => (
              <tr key={log.id} className="hover:bg-[#fcfcfc] transition-colors">
                <td className="px-4 py-3 text-[#4a4a4a] font-mono">
                  {new Date(log.timestamp * 1000).toLocaleString()}
                </td>
                <td className="px-4 py-3">
                  <span className="px-2 py-0.5 rounded bg-[#f0f0f0] text-[#1a1a1a] font-medium">
                    {log.action_type}
                  </span>
                </td>
                <td className="px-4 py-3 text-[#8a8a8a] font-mono max-w-[150px] truncate" title={log.data_hash}>
                  {log.data_hash}
                </td>
                <td className="px-4 py-3 text-center">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                    log.risk_label === 'Low' ? 'bg-green-100 text-green-700' : 
                    log.risk_label === 'Medium' ? 'bg-orange-100 text-orange-700' : 
                    'bg-red-100 text-red-700'
                  }`}>
                    {log.risk_label}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="p-3 bg-[#fff9f9] border-t border-[#eeeeee]">
        <p className="text-[11px] text-[#c8102e] flex items-center gap-2">
          <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor">
            <path d="M8 0a8 8 0 100 16A8 8 0 008 0zm.75 12h-1.5v-1.5h1.5V12zm0-3h-1.5V4h1.5v5z" />
          </svg>
          These records are stored on a decentralized ledger and cannot be modified or deleted.
        </p>
      </div>
    </div>
  );
};

export default AuditTrail;
