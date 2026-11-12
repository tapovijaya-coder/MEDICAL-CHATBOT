import React, { useState, useEffect, useCallback } from 'react';
import Header from '../components/Header';
import Sidebar from '../components/Sidebar';
import ChatWindow from '../components/ChatWindow';
import ChatInput from '../components/ChatInput';
import DocumentUpload from '../components/DocumentUpload';
import DatasetReview from '../components/DatasetReview';
import api from '../services/api';
import { AlertTriangle, CheckCircle, AlertCircle, X, Filter } from 'lucide-react';

const STORAGE_KEY_SESSIONS = 'medibot_sessions';
const STORAGE_KEY_MESSAGES = 'medibot_session_messages_';

export default function Dashboard() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('chat'); // 'chat' | 'knowledge' | 'evaluation'
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState('all');

  // Health and System State
  const [isConnected, setIsConnected] = useState(true);
  const [isCheckingHealth, setIsCheckingHealth] = useState(false);
  const [healthData, setHealthData] = useState(null);

  // Documents State
  const [documents, setDocuments] = useState([]);
  const [isLoadingDocuments, setIsLoadingDocuments] = useState(false);

  // Session & Chat State
  const [sessionId, setSessionId] = useState(() => `session_${Date.now()}`);
  const [sessions, setSessions] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY_SESSIONS);
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  const [messages, setMessages] = useState(() => {
    try {
      const initialId = `session_${Date.now()}`;
      const saved = localStorage.getItem(`${STORAGE_KEY_MESSAGES}${initialId}`);
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  const [isLoading, setIsLoading] = useState(false);
  const [toasts, setToasts] = useState([]);

  // Toast Helper
  const showToast = useCallback((text, type = 'info') => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, text, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  }, []);

  // Fetch Health Check
  const checkHealth = useCallback(async () => {
    setIsCheckingHealth(true);
    try {
      const data = await api.checkHealth();
      setIsConnected(true);
      setHealthData(data);
    } catch (err) {
      setIsConnected(false);
    } finally {
      setIsCheckingHealth(false);
    }
  }, []);

  // Fetch Documents
  const loadDocuments = useCallback(async () => {
    setIsLoadingDocuments(true);
    try {
      const res = await api.getDocuments();
      setDocuments(res.documents || []);
    } catch (err) {
      console.warn('Could not load documents:', err);
    } finally {
      setIsLoadingDocuments(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    checkHealth();
    loadDocuments();

    const interval = setInterval(checkHealth, 30000); // 30s background health ping
    return () => clearInterval(interval);
  }, [checkHealth, loadDocuments]);

  // Persist sessions
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY_SESSIONS, JSON.stringify(sessions));
    } catch (e) {
      console.error(e);
    }
  }, [sessions]);

  // Persist messages for active session
  useEffect(() => {
    try {
      localStorage.setItem(`${STORAGE_KEY_MESSAGES}${sessionId}`, JSON.stringify(messages));
    } catch (e) {
      console.error(e);
    }
  }, [messages, sessionId]);

  // Start a new conversation
  const handleNewChat = () => {
    const newSessionId = `session_${Date.now()}`;
    setSessionId(newSessionId);
    setMessages([]);
    setActiveTab('chat');
    if (window.innerWidth < 900) setSidebarOpen(false);
  };

  // Switch to an existing session
  const handleSelectSession = (id) => {
    setSessionId(id);
    try {
      const saved = localStorage.getItem(`${STORAGE_KEY_MESSAGES}${id}`);
      setMessages(saved ? JSON.parse(saved) : []);
    } catch {
      setMessages([]);
    }
    setActiveTab('chat');
    if (window.innerWidth < 900) setSidebarOpen(false);
  };

  // Send message
  const handleSendMessage = async (text) => {
    if (!text.trim() || isLoading) return;

    const userMessage = {
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    // Save session title if this is the first message
    if (messages.length === 0) {
      const titleSnippet = text.length > 32 ? `${text.substring(0, 32)}...` : text;
      setSessions((prev) => {
        const existing = prev.find((s) => s.id === sessionId);
        if (existing) return prev;
        return [{ id: sessionId, title: titleSnippet, timestamp: new Date().toISOString() }, ...prev];
      });
    }

    try {
      const response = await api.sendMessage(text, sessionId, selectedCategory);

      const aiMessage = {
        role: 'assistant',
        content: response.answer,
        sources: response.sources || [],
        is_emergency: response.is_emergency || false,
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, aiMessage]);
    } catch (err) {
      const errorMessage = {
        role: 'assistant',
        content: `**Error:** ${err.message || 'Unable to retrieve answer. Please verify backend connection and Groq credentials.'}`,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
      showToast(err.message, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  // Handle document upload success
  const handleUploadSuccess = (newDoc) => {
    setDocuments((prev) => [newDoc, ...prev]);
    showToast(`"${newDoc.filename}" successfully indexed into vector database.`, 'success');
    checkHealth();
  };

  // Handle document deletion
  const handleDeleteDocument = async (docId) => {
    try {
      await api.deleteDocument(docId);
      setDocuments((prev) => prev.filter((d) => d.document_id !== docId));
      showToast('Document and its vector embeddings removed.', 'success');
      checkHealth();
    } catch (err) {
      showToast(err.message || 'Failed to delete document.', 'error');
    }
  };

  const CATEGORY_OPTIONS = [
    'all',
    'General Medicine',
    'Cardiology',
    'Endocrinology',
    'Respiratory Diseases',
    'Infectious Diseases',
    'Neurology',
    'Gastroenterology',
    'Dermatology',
    'Emergency Medicine',
    'Preventive Healthcare'
  ];

  return (
    <div className="app-container">
      {/* Sidebar */}
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onNewChat={handleNewChat}
        documents={documents}
        onDeleteDocument={handleDeleteDocument}
        onOpenUpload={() => setIsUploadModalOpen(true)}
        sessions={sessions}
        currentSessionId={sessionId}
        onSelectSession={handleSelectSession}
        isConnected={isConnected}
      />

      {/* Main Dashboard */}
      <div className="main-dashboard">
        <Header
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
          isConnected={isConnected}
          isCheckingHealth={isCheckingHealth}
          onRefreshHealth={checkHealth}
          totalDocuments={documents.length}
          groqConfigured={healthData?.groq_configured || false}
        />

        {/* Global Medical Disclaimer Banner */}
        <div className="disclaimer-banner">
          <div className="disclaimer-content">
            <AlertTriangle size={15} style={{ flexShrink: 0 }} />
            <span>
              <strong>Medical Disclaimer:</strong> MediBot AI provides educational medical information and document search. It does not provide medical diagnoses or prescribe treatments. In an emergency, call your local emergency services immediately.
            </span>
          </div>
        </div>

        {/* Dynamic View depending on Active Tab */}
        {activeTab === 'evaluation' ? (
          <div className="evaluation-scroll-area">
            <DatasetReview showToast={showToast} />
          </div>
        ) : activeTab === 'knowledge' ? (
          <div className="knowledge-library-view">
            <div className="library-header">
              <div>
                <h2>Clinical Knowledge Base & Document Registry</h2>
                <p>
                  All indexed medical references, authoritative clinical guidelines, and encyclopedias indexed in FAISS + BM25.
                </p>
              </div>
              <button 
                className="new-chat-btn" 
                style={{ width: 'auto', padding: '10px 18px' }}
                onClick={() => setIsUploadModalOpen(true)}
              >
                + Upload New PDF
              </button>
            </div>

            <div className="docs-grid-cards">
              {documents.map((doc) => (
                <div key={doc.document_id} className="doc-detail-card">
                  <div className="doc-card-top">
                    <span className={`pill-evidence ${doc.is_historical ? 'historical' : 'current'}`}>
                      {doc.is_historical ? 'Historical Reference (2002)' : `${doc.publication_year || 2024} Guideline`}
                    </span>
                    <span className="doc-pages-badge">{doc.pages} Pages</span>
                  </div>
                  <h4 className="doc-card-title">{doc.filename}</h4>
                  <div className="doc-card-stats">
                    <div>
                      <span className="stat-label">Chunks</span>
                      <span className="stat-val">{doc.chunks}</span>
                    </div>
                    <div>
                      <span className="stat-label">Edition</span>
                      <span className="stat-val">{doc.edition || 'Reference'}</span>
                    </div>
                    <div>
                      <span className="stat-label">Type</span>
                      <span className="stat-val">{doc.source_type || 'clinical_pdf'}</span>
                    </div>
                  </div>
                  <div className="doc-card-footer">
                    <span className="indexed-date">Indexed into FAISS</span>
                    <button 
                      className="doc-delete-btn"
                      onClick={() => {
                        if (window.confirm(`Delete "${doc.filename}" and its embeddings?`)) {
                          handleDeleteDocument(doc.document_id);
                        }
                      }}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          /* Normal Chat View */
          <>
            {/* Category Filter Pills */}
            <div className="category-filter-bar">
              <span className="category-bar-label"><Filter size={13} /> Focus:</span>
              <div className="category-pills-row">
                {CATEGORY_OPTIONS.map((cat) => (
                  <button
                    key={cat}
                    className={`cat-pill ${selectedCategory === cat ? 'active' : ''}`}
                    onClick={() => setSelectedCategory(cat)}
                  >
                    {cat === 'all' ? 'All Medical Specialties' : cat}
                  </button>
                ))}
              </div>
            </div>

            {/* Chat Conversation Area */}
            <ChatWindow
              messages={messages}
              isLoading={isLoading}
              onSelectSuggestion={(q) => handleSendMessage(q)}
              hasDocuments={documents.length > 0}
              onOpenUpload={() => setIsUploadModalOpen(true)}
            />

            {/* Chat Input Bar */}
            <ChatInput
              onSendMessage={handleSendMessage}
              onOpenUpload={() => setIsUploadModalOpen(true)}
              isLoading={isLoading}
              disabled={false}
            />
          </>
        )}
      </div>

      {/* PDF Upload Modal */}
      <DocumentUpload
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        onUploadSuccess={handleUploadSuccess}
      />

      {/* Toast Notifications */}
      <div className="toast-container">
        {toasts.map((t) => (
          <div key={t.id} className={`toast ${t.type}`}>
            {t.type === 'error' ? (
              <AlertCircle size={16} color="#DC2626" />
            ) : (
              <CheckCircle size={16} color="#16A34A" />
            )}
            <span>{t.text}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

