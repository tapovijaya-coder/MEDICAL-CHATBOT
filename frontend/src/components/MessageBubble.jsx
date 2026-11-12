import React, { useState } from 'react';
import {
  Bot,
  User,
  FileText,
  ChevronDown,
  ChevronUp,
  AlertOctagon,
  Copy,
  Check,
  ExternalLink,
} from 'lucide-react';

export default function MessageBubble({ message }) {
  const isUser = message.role === 'user';
  const [sourcesOpen, setSourcesOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const hasSources = message.sources && message.sources.length > 0;

  // Format simple markdown bolding and line breaks
  const renderFormattedContent = (content) => {
    if (!content) return null;

    const paragraphs = content.split('\n\n');
    return paragraphs.map((para, idx) => {
      // Check for bullet lists
      if (para.trim().startsWith('- ') || para.trim().startsWith('* ')) {
        const items = para.split('\n').filter((item) => item.trim());
        return (
          <ul key={idx} style={{ marginBottom: '8px', paddingLeft: '20px' }}>
            {items.map((it, itemIdx) => {
              const text = it.replace(/^[-*]\s+/, '');
              return <li key={itemIdx}>{renderInlineMarkdown(text)}</li>;
            })}
          </ul>
        );
      }

      // Check for numbered lists
      if (/^\d+\.\s+/.test(para.trim())) {
        const items = para.split('\n').filter((item) => item.trim());
        return (
          <ol key={idx} style={{ marginBottom: '8px', paddingLeft: '20px' }}>
            {items.map((it, itemIdx) => {
              const text = it.replace(/^\d+\.\s+/, '');
              return <li key={itemIdx}>{renderInlineMarkdown(text)}</li>;
            })}
          </ol>
        );
      }

      return (
        <p key={idx} style={{ marginBottom: '8px' }}>
          {renderInlineMarkdown(para)}
        </p>
      );
    });
  };

  // Helper for inline **bold** and *italic*
  const renderInlineMarkdown = (text) => {
    const parts = text.split(/(\*\*.*?\*\*|\*.*?\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i}>{part.slice(2, -2)}</strong>;
      }
      if (part.startsWith('*') && part.endsWith('*')) {
        return <em key={i}>{part.slice(1, -1)}</em>;
      }
      return part;
    });
  };

  return (
    <div className={`message-bubble-row ${isUser ? 'user' : 'ai'}`}>
      <div className="message-avatar">
        {isUser ? <User size={18} /> : <Bot size={20} />}
      </div>

      <div className="message-card">
        {/* Emergency Alert Banner if detected */}
        {message.is_emergency && (
          <div className="emergency-alert-box">
            <AlertOctagon size={20} style={{ flexShrink: 0 }} />
            <div>
              <strong>Potential Medical Emergency Detected</strong>
              <p style={{ marginTop: '4px', fontSize: '0.8rem', fontWeight: 'normal' }}>
                If you are experiencing severe or life-threatening symptoms, immediately contact local emergency services (e.g. 911 / 112).
              </p>
            </div>
          </div>
        )}

        {/* Message Content */}
        <div className="message-body">
          {renderFormattedContent(message.content)}
        </div>

        {/* Citations & Sources */}
        {!isUser && hasSources && (
          <div className="sources-container">
            <button
              className="sources-toggle-btn"
              onClick={() => setSourcesOpen(!sourcesOpen)}
            >
              <FileText size={14} />
              <span>
                {message.sources.length} Referenced Medical Source{message.sources.length === 1 ? '' : 's'}
              </span>
              {sourcesOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            </button>

            {sourcesOpen && (
              <div className="sources-chips-list">
                {message.sources.map((src, i) => (
                  <div key={i} className={`source-chip ${src.is_historical ? 'historical-chip' : ''}`}>
                    <div className="source-header">
                      <div className="source-title-row">
                        <span className="source-name">{src.source}</span>
                        {src.page && (
                          <span className="source-page-badge">
                            Page {src.page}
                          </span>
                        )}
                      </div>
                      
                      {/* Meta badges: Historical vs Current, Category */}
                      <div className="source-meta-badges">
                        {src.is_historical ? (
                          <span className="badge-temporal historical" title="Published in 2002. Historical medical reference.">
                            Historical (2002 Gale)
                          </span>
                        ) : src.publication_year ? (
                          <span className="badge-temporal current" title="Modern clinical guidance">
                            {src.publication_year} Guideline
                          </span>
                        ) : null}

                        {src.medical_category && (
                          <span className="badge-cat">{src.medical_category}</span>
                        )}

                        {src.section_title && (
                          <span className="badge-section">{src.section_title}</span>
                        )}
                      </div>
                    </div>

                    {src.excerpt && (
                      <div className="source-excerpt">
                        "{src.excerpt}"
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Footer Meta & Copy */}
        <div className="message-meta">
          <span>{message.timestamp ? new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Just now'}</span>
          {!isUser && (
            <button
              onClick={handleCopy}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'inherit',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                padding: '2px 4px',
              }}
              title="Copy answer to clipboard"
            >
              {copied ? <Check size={12} color="#16A34A" /> : <Copy size={12} />}
              <span style={{ fontSize: '0.68rem' }}>{copied ? 'Copied' : 'Copy'}</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

