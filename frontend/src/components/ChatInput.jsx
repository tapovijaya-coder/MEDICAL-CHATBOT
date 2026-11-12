import React, { useState, useRef, useEffect } from 'react';
import { Send, Paperclip, Loader2, Mic, MicOff, Sparkles, X } from 'lucide-react';

export default function ChatInput({ 
  onSendMessage, 
  onOpenUpload, 
  isLoading, 
  disabled,
  onQuickPrompt
}) {
  const [input, setInput] = useState('');
  const [isListening, setIsListening] = useState(false);
  const textareaRef = useRef(null);
  const recognitionRef = useRef(null);

  // Auto-resize textarea height
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 140)}px`;
    }
  }, [input]);

  // Setup Web Speech API for voice dictation
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      recognition.onstart = () => {
        setIsListening(true);
      };

      recognition.onresult = (event) => {
        const transcript = Array.from(event.results)
          .map((r) => r[0].transcript)
          .join('');
        setInput(transcript);
      };

      recognition.onerror = (event) => {
        console.warn('Speech recognition error:', event.error);
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = recognition;
    }
  }, []);

  const toggleListening = () => {
    if (!recognitionRef.current) {
      alert('Speech recognition is not supported in this browser. Please use Chrome, Edge, or Safari.');
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      try {
        recognitionRef.current.start();
        setIsListening(true);
      } catch (err) {
        console.warn('Recognition start failed:', err);
      }
    }
  };

  const handleSubmit = (e) => {
    if (e) e.preventDefault();
    if (!input.trim() || isLoading || disabled) return;

    if (isListening && recognitionRef.current) {
      recognitionRef.current.stop();
    }

    onSendMessage(input.trim());
    setInput('');

    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const QUICK_TRIAGE_CHIPS = [
    { label: '🩺 Blood Pressure Guide', prompt: 'What are the 2023 WHO guidelines for hypertension thresholds and management?' },
    { label: '🩸 Type 2 Diabetes', prompt: 'What are the diagnostic criteria and symptoms for Type 2 Diabetes Mellitus?' },
    { label: '🫁 Bronchitis & Antibiotics', prompt: 'Why are antibiotics contraindicated for acute bronchitis according to CDC guidelines?' },
    { label: '📖 Gale Encyclopedia Lookup', prompt: 'What does the Gale Encyclopedia of Medicine say about diagnosing appendicitis?' },
    { label: '🚨 Chest Discomfort Triage', prompt: 'What are the emergency red-flag symptoms for acute chest pain?' },
  ];

  return (
    <div className="chat-input-area">
      {/* Interactive Quick Prompts Carousel Bar */}
      <div className="quick-triage-carousel">
        <div className="quick-carousel-track">
          {QUICK_TRIAGE_CHIPS.map((chip, idx) => (
            <button
              key={idx}
              type="button"
              className="quick-chip-btn animated-btn"
              onClick={() => {
                setInput(chip.prompt);
                textareaRef.current?.focus();
              }}
              title="Click to insert prompt"
            >
              <span>{chip.label}</span>
            </button>
          ))}
        </div>
      </div>

      <form onSubmit={handleSubmit} className="input-box-wrapper glass-card">
        {/* Attachment Upload Button */}
        <button
          type="button"
          className="attach-btn animated-btn icon-pulse-hover"
          onClick={onOpenUpload}
          title="Upload medical PDF document to knowledge base"
          disabled={isLoading}
        >
          <Paperclip size={18} />
        </button>

        {/* Input Textarea */}
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={isListening ? '🎙️ Listening to your medical question... speak now...' : "Ask a medical question (e.g. 'What are the symptoms and causes of hypertension?')..."}
          className={`chat-textarea ${isListening ? 'listening-active' : ''}`}
          rows={1}
          disabled={isLoading || disabled}
        />

        {/* Clear Button if input has text */}
        {input.trim() && !isLoading && (
          <button
            type="button"
            className="clear-input-btn"
            onClick={() => setInput('')}
            title="Clear text"
          >
            <X size={15} />
          </button>
        )}

        {/* Voice Dictation (Mic) Button */}
        <button
          type="button"
          className={`mic-btn animated-btn ${isListening ? 'mic-active' : ''}`}
          onClick={toggleListening}
          title={isListening ? 'Stop voice recording' : 'Dictate question via microphone'}
          disabled={isLoading || disabled}
        >
          {isListening ? (
            <div className="mic-pulse-wrapper">
              <span className="mic-wave" />
              <MicOff size={18} color="#FFFFFF" />
            </div>
          ) : (
            <Mic size={18} />
          )}
        </button>

        {/* Animated Shimmer Send Button */}
        <div className="input-actions">
          <button
            type="submit"
            className={`send-btn shimmer-btn animated-btn ${input.trim() ? 'active-ready' : ''}`}
            disabled={!input.trim() || isLoading || disabled}
            title="Send medical query"
          >
            {isLoading ? (
              <Loader2 size={18} className="spin" />
            ) : (
              <div className="send-icon-wrapper">
                <Send size={18} />
              </div>
            )}
          </button>
        </div>
      </form>

      <div className="input-footnote">
        <Sparkles size={12} className="inline-sparkle" />
        <span>MediBot Clinical AI integrates <strong>FAISS + BM25 Hybrid RAG</strong>. Answers are for educational use. In emergencies, call local emergency services immediately.</span>
      </div>
    </div>
  );
}
