import React from 'react';
import { Menu, Activity, ShieldCheck, RefreshCw, AlertTriangle } from 'lucide-react';

export default function Header({
  onToggleSidebar,
  isConnected,
  isCheckingHealth,
  onRefreshHealth,
  totalDocuments,
  groqConfigured,
}) {
  return (
    <header className="dashboard-header">
      <div className="header-left">
        <button
          className="menu-toggle-btn"
          onClick={onToggleSidebar}
          aria-label="Toggle navigation menu"
        >
          <Menu size={22} />
        </button>

        <div className="session-title">
          <h2>
            <Activity size={20} color="#148B68" />
            MediBot Clinical AI
          </h2>
        </div>
      </div>

      <div className="header-right">
        {/* Knowledge Base Documents Count */}
        <div
          className="connection-badge"
          title={`${totalDocuments} medical document(s) indexed in FAISS`}
          style={{ background: '#EAF6F1', color: '#148B68' }}
        >
          <ShieldCheck size={14} />
          <span>{totalDocuments} PDF{totalDocuments === 1 ? '' : 's'} Indexed</span>
        </div>

        {/* Backend Status Pill */}
        <div
          className={`connection-badge ${isConnected ? '' : 'offline'}`}
          title={isConnected ? 'Backend connected & healthy' : 'Backend offline or unreachable'}
        >
          <span className={`status-dot ${isConnected ? '' : 'offline'}`} />
          <span>{isConnected ? 'API Connected' : 'Offline'}</span>
          <button
            onClick={onRefreshHealth}
            disabled={isCheckingHealth}
            style={{ background: 'transparent', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', padding: 0 }}
            title="Refresh backend connection status"
          >
            <RefreshCw size={12} className={isCheckingHealth ? 'spin' : ''} />
          </button>
        </div>
      </div>
    </header>
  );
}

