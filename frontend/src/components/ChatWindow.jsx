import React, { useEffect, useRef } from 'react';
import MessageBubble from './MessageBubble';
import {
  HeartPulse,
  BrainCircuit,
  FileSearch,
  Sparkles,
  HelpCircle,
  FileCheck2,
} from 'lucide-react';

const SUGGESTED_QUESTIONS = [
  'What are the primary symptoms and diagnostic criteria for Type 2 Diabetes?',
  'How is stage 1 hypertension typically managed through lifestyle interventions?',
  'What is the fundamental difference between bacterial and viral bronchitis?',
  'When should emergency medical evaluation be sought for acute chest discomfort?',
];

export default function ChatWindow({
  messages,
  isLoading,
  onSelectSuggestion,
  hasDocuments,
  onOpenUpload,
}) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
    <div className="chat-window">
      <div className="chat-content-wrapper">
        {messages.length === 0 ? (
          /* Empty / Welcome State */
          <div className="welcome-hero">
            <div className="hero-icon-bubble">
              <HeartPulse size={34} />
            </div>

            <h2>Intelligent Medical Information Assistant</h2>
            <p>
              Ask clinical and healthcare questions grounded in your uploaded medical PDF literature,
              synthesized accurately using Groq LLM inference and FAISS vector retrieval.
            </p>

            {/* Feature Pills */}
            <div className="features-pill-row">
              <div className="feature-pill">
                <FileSearch size={14} color="#148B68" />
                <span>PDF Evidence-Grounded</span>
              </div>
              <div className="feature-pill">
                <BrainCircuit size={14} color="#148B68" />
                <span>FAISS Semantic Search</span>
              </div>
              <div className="feature-pill">
                <Sparkles size={14} color="#148B68" />
                <span>Groq High-Speed LLM</span>
              </div>
              <div className="feature-pill">
                <FileCheck2 size={14} color="#148B68" />
                <span>Page-Level Citations</span>
              </div>
            </div>

            {/* Knowledge base prompt if no documents uploaded */}
            {!hasDocuments && (
              <div
                style={{
                  background: '#EAF6F1',
                  border: '1.5px dashed #148B68',
                  borderRadius: '12px',
                  padding: '16px 20px',
                  marginBottom: '28px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: '16px',
                  textAlign: 'left',
                }}
              >
                <div>
                  <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: '#1A3430' }}>
                    No medical documents uploaded yet
                  </h4>
                  <p style={{ fontSize: '0.78rem', color: '#52706A', marginTop: '2px' }}>
                    Upload medical textbooks or journals so MediBot AI can retrieve and cite exact sources for your answers.
                  </p>
                </div>
                <button
                  className="new-chat-btn"
                  style={{ margin: 0, padding: '8px 14px', fontSize: '0.8rem', flexShrink: 0 }}
                  onClick={onOpenUpload}
                >
                  Upload PDF
                </button>
              </div>
            )}

            {/* Suggested Questions */}
            <div>
              <div className="suggested-section-title">
                Suggested Medical Questions
              </div>
              <div className="suggested-grid">
                {SUGGESTED_QUESTIONS.map((q, idx) => (
                  <button
                    key={idx}
                    className="suggestion-card"
                    onClick={() => onSelectSuggestion(q)}
                  >
                    <HelpCircle size={16} color="#148B68" style={{ flexShrink: 0, marginTop: '2px' }} />
                    <span>{q}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          /* Message Stream */
          <>
            {messages.map((msg, index) => (
              <MessageBubble key={index} message={msg} />
            ))}

            {/* Typing Loader Indicator */}
            {isLoading && (
              <div className="message-bubble-row ai">
                <div className="message-avatar">
                  <HeartPulse size={18} />
                </div>
                <div className="message-card" style={{ padding: '12px 18px' }}>
                  <div className="typing-indicator">
                    <span className="typing-dot" />
                    <span className="typing-dot" />
                    <span className="typing-dot" />
                  </div>
                  <span style={{ fontSize: '0.72rem', color: '#829D97' }}>
                    Consulting medical knowledge base & synthesizing response...
                  </span>
                </div>
              </div>
            )}
          </>
        )}

        <div ref={bottomRef} style={{ height: '1px' }} />
      </div>
    </div>
  );
}

