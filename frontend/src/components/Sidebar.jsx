import React from 'react';
import {
  Plus,
  MessageSquare,
  BookOpen,
  FileText,
  Trash2,
  Upload,
  HeartPulse,
  User,
  CheckCircle,
  HelpCircle,
  ShieldCheck,
} from 'lucide-react';

export default function Sidebar({
  isOpen,
  onClose,
  activeTab,
  setActiveTab,
  onNewChat,
  documents,
  onDeleteDocument,
  onOpenUpload,
  sessions,
  currentSessionId,
  onSelectSession,
  isConnected,
}) {
  const formatFileSize = (bytes) => {
    if (!bytes) return '0 KB';
    const kb = bytes / 1024;
    if (kb < 1024) return `${kb.toFixed(1)} KB`;
    return `${(kb / 1024).toFixed(1)} MB`;
  };

  return (
    <>
      {isOpen && <div className="sidebar-backdrop" onClick={onClose} />}

      <aside className={`sidebar ${isOpen ? 'open' : ''}`}>
        {/* Brand Header */}
        <div className="sidebar-header">
          <div className="brand">
            <div className="brand-icon-wrapper">
              <HeartPulse size={22} />
            </div>
            <div className="brand-text">
              <h1>MediBot AI</h1>
              <span className="brand-badge">Clinical RAG</span>
            </div>
          </div>
        </div>

        {/* New Conversation Button */}
        <button className="new-chat-btn" onClick={onNewChat}>
          <Plus size={18} />
          <span>New Conversation</span>
        </button>

        {/* Navigation Tabs */}
        <div className="sidebar-tabs">
          <button
            className={`tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
            onClick={() => setActiveTab('chat')}
          >
            <MessageSquare size={16} />
            <span>Assistant</span>
          </button>
          <button
            className={`tab-btn ${activeTab === 'knowledge' ? 'active' : ''}`}
            onClick={() => setActiveTab('knowledge')}
          >
            <BookOpen size={16} />
            <span>Documents</span>
          </button>
          <button
            className={`tab-btn ${activeTab === 'evaluation' ? 'active' : ''}`}
            onClick={() => setActiveTab('evaluation')}
          >
            <ShieldCheck size={16} />
            <span>QA Review</span>
          </button>
        </div>

        {/* Sidebar Main Content Area */}
        <div className="sidebar-content">
          {activeTab === 'chat' ? (
            <>
              {/* Chat Sessions History */}
              <div className="sidebar-section">
                <div className="sidebar-section-title">
                  <span>Recent Consultations</span>
                  <span className="badge-count">{sessions.length}</span>
                </div>

                <div className="doc-list">
                  {sessions.length === 0 ? (
                    <div className="doc-empty-state">
                      <MessageSquare size={24} style={{ margin: '0 auto 6px' }} />
                      <p>No previous conversations.</p>
                      <p style={{ fontSize: '0.72rem' }}>Start asking questions to build your history.</p>
                    </div>
                  ) : (
                    sessions.map((sess) => (
                      <div
                        key={sess.id}
                        className={`doc-item ${sess.id === currentSessionId ? 'active-session' : ''}`}
                        onClick={() => onSelectSession(sess.id)}
                        style={{
                          cursor: 'pointer',
                          borderColor: sess.id === currentSessionId ? '#148B68' : '#E2ECE8',
                          background: sess.id === currentSessionId ? '#EAF6F1' : '#F7FAF9',
                        }}
                      >
                        <div className="doc-info">
                          <MessageSquare size={16} color={sess.id === currentSessionId ? '#148B68' : '#829D97'} />
                          <div className="doc-text">
                            <div className="doc-name">{sess.title || 'Medical Consultation'}</div>
                            <div className="doc-meta">
                              {new Date(sess.timestamp).toLocaleDateString([], { month: 'short', day: 'numeric' })}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Quick Document Summary */}
              <div className="sidebar-section">
                <div className="sidebar-section-title">
                  <span>Active Knowledge Base</span>
                  <span className="badge-count">{documents.length}</span>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <button
                    className="tab-btn"
                    style={{ border: '1px dashed #148B68', color: '#148B68', padding: '10px' }}
                    onClick={onOpenUpload}
                  >
                    <Upload size={16} />
                    <span>Upload Medical PDF</span>
                  </button>

                  <div style={{ fontSize: '0.75rem', color: '#829D97', textAlign: 'center' }}>
                    {documents.length} reference document{documents.length === 1 ? '' : 's'} loaded in FAISS.
                  </div>
                </div>
              </div>
            </>
          ) : (
            /* Knowledge Base Tab */
            <div className="sidebar-section">
              <div className="sidebar-section-title">
                <span>Medical PDFs ({documents.length})</span>
                <button
                  onClick={onOpenUpload}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: '#148B68',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    fontSize: '0.75rem',
                    fontWeight: 600,
                  }}
                >
                  <Plus size={14} /> Add
                </button>
              </div>

              <div className="doc-list">
                {documents.length === 0 ? (
                  <div className="doc-empty-state">
                    <FileText size={28} style={{ margin: '0 auto 8px', color: '#829D97' }} />
                    <p style={{ fontWeight: 600 }}>No documents uploaded yet.</p>
                    <p style={{ fontSize: '0.72rem', marginTop: '4px' }}>
                      Upload clinical guides or books to enable evidence-based RAG answers.
                    </p>
                    <button
                      className="new-chat-btn"
                      style={{ margin: '14px auto 0', padding: '8px 14px', fontSize: '0.8rem' }}
                      onClick={onOpenUpload}
                    >
                      <Upload size={14} /> Upload PDF
                    </button>
                  </div>
                ) : (
                  documents.map((doc) => (
                    <div key={doc.document_id} className="doc-item">
                      <div className="doc-info">
                        <FileText size={18} className="doc-icon" />
                        <div className="doc-text">
                          <div className="doc-name" title={doc.filename}>
                            {doc.filename}
                          </div>
                          <div className="doc-meta">
                            {doc.pages} pgs • {doc.chunks} chunks • {formatFileSize(doc.file_size_bytes)}
                          </div>
                        </div>
                      </div>

                      <button
                        className="doc-delete-btn"
                        onClick={(e) => {
                          e.stopPropagation();
                          if (window.confirm(`Remove "${doc.filename}" and its vector embeddings?`)) {
                            onDeleteDocument(doc.document_id);
                          }
                        }}
                        title="Delete document and vector embeddings"
                      >
                        <Trash2 size={15} />
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* Sidebar Footer User Profile */}
        <div className="sidebar-footer">
          <div className="user-profile">
            <div className="user-avatar">
              <User size={18} />
            </div>
            <div className="user-details">
              <h4>Healthcare User</h4>
              <div className="user-status">
                <span className={`status-dot ${isConnected ? '' : 'offline'}`} />
                <span>{isConnected ? 'System Ready' : 'Service Offline'}</span>
              </div>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}

