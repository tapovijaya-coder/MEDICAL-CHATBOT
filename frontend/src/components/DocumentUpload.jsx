import React, { useState, useRef } from 'react';
import {
  UploadCloud,
  X,
  FileCheck,
  AlertCircle,
  File,
  CheckCircle2,
  Loader2,
} from 'lucide-react';
import api from '../services/api';

export default function DocumentUpload({ isOpen, onClose, onUploadSuccess }) {
  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState(null);
  const [successInfo, setSuccessInfo] = useState(null);
  const fileInputRef = useRef(null);

  if (!isOpen) return null;

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const validateAndSetFile = (selectedFile) => {
    setError(null);
    setSuccessInfo(null);

    if (!selectedFile) return;

    if (!selectedFile.name.toLowerCase().endsWith('.pdf')) {
      setError('Please select a valid PDF file (.pdf).');
      return;
    }

    if (selectedFile.size > 25 * 1024 * 1024) {
      setError('File size exceeds the 25 MB limit.');
      return;
    }

    setFile(selectedFile);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setIsUploading(true);
    setUploadProgress(0);
    setError(null);

    try {
      const response = await api.uploadDocument(file, (progress) => {
        setUploadProgress(progress);
      });

      setSuccessInfo(response.document);
      setFile(null);
      if (onUploadSuccess) {
        onUploadSuccess(response.document);
      }
    } catch (err) {
      setError(err.message || 'Failed to upload and index document.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleReset = () => {
    setFile(null);
    setError(null);
    setSuccessInfo(null);
    setUploadProgress(0);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Upload Medical Documents</h3>
          <button className="modal-close-btn" onClick={onClose} aria-label="Close modal">
            <X size={20} />
          </button>
        </div>

        <div className="modal-body">
          {/* Dropzone */}
          {!file && !successInfo && (
            <div
              className={`dropzone-area ${dragActive ? 'dragging' : ''}`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,application/pdf"
                style={{ display: 'none' }}
                onChange={handleFileChange}
              />
              <div className="dropzone-icon">
                <UploadCloud size={28} />
              </div>
              <div className="dropzone-text">
                <h4>Drop medical PDF here or click to browse</h4>
                <p>Supports clinical guidelines, research papers, anatomy textbooks (Up to 25 MB)</p>
              </div>
            </div>
          )}

          {/* Selected File Card */}
          {file && !successInfo && (
            <div style={{ marginTop: '10px' }}>
              <div
                style={{
                  background: '#F7FAF9',
                  border: '1px solid #DCE8E3',
                  borderRadius: '10px',
                  padding: '14px 16px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <File size={24} color="#148B68" />
                  <div>
                    <h5 style={{ fontSize: '0.88rem', fontWeight: 600, color: '#1A3430' }}>
                      {file.name}
                    </h5>
                    <p style={{ fontSize: '0.75rem', color: '#829D97' }}>
                      {(file.size / (1024 * 1024)).toFixed(2)} MB
                    </p>
                  </div>
                </div>

                {!isUploading && (
                  <button
                    onClick={handleReset}
                    style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: '#829D97' }}
                  >
                    <X size={18} />
                  </button>
                )}
              </div>

              {/* Upload Progress */}
              {isUploading && (
                <div className="upload-progress-wrapper">
                  <div className="progress-bar-bg">
                    <div className="progress-bar-fill" style={{ width: `${uploadProgress}%` }} />
                  </div>
                  <div className="progress-text">
                    <span>Extracting & Indexing Embeddings...</span>
                    <span>{uploadProgress}%</span>
                  </div>
                </div>
              )}

              {/* Upload Submit Button */}
              <div style={{ marginTop: '20px', display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
                <button
                  type="button"
                  className="tab-btn"
                  onClick={handleReset}
                  disabled={isUploading}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  className="new-chat-btn"
                  style={{ margin: 0 }}
                  onClick={handleUpload}
                  disabled={isUploading}
                >
                  {isUploading ? (
                    <>
                      <Loader2 size={16} className="spin" />
                      <span>Processing...</span>
                    </>
                  ) : (
                    <>
                      <UploadCloud size={16} />
                      <span>Process & Index PDF</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

          {/* Success State */}
          {successInfo && (
            <div style={{ textAlign: 'center', padding: '20px 0' }}>
              <CheckCircle2 size={48} color="#16A34A" style={{ margin: '0 auto 12px' }} />
              <h4 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#1A3430' }}>
                Document Indexed Successfully!
              </h4>
              <p style={{ fontSize: '0.85rem', color: '#52706A', marginTop: '6px' }}>
                "{successInfo.filename}" is now part of the RAG knowledge base.
              </p>

              <div
                style={{
                  display: 'flex',
                  justifyContent: 'center',
                  gap: '16px',
                  margin: '20px 0',
                  fontSize: '0.8rem',
                }}
              >
                <div style={{ background: '#EAF6F1', padding: '8px 16px', borderRadius: '8px', color: '#148B68', fontWeight: 600 }}>
                  {successInfo.pages} Page{successInfo.pages === 1 ? '' : 's'}
                </div>
                <div style={{ background: '#EAF6F1', padding: '8px 16px', borderRadius: '8px', color: '#148B68', fontWeight: 600 }}>
                  {successInfo.chunks} Vector Chunks
                </div>
              </div>

              <div style={{ display: 'flex', gap: '10px', justifyContent: 'center' }}>
                <button
                  className="tab-btn"
                  onClick={handleReset}
                >
                  Upload Another
                </button>
                <button
                  className="new-chat-btn"
                  style={{ margin: 0 }}
                  onClick={onClose}
                >
                  Done
                </button>
              </div>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div
              style={{
                marginTop: '14px',
                background: '#FEF2F2',
                border: '1px solid #FCA5A5',
                borderRadius: '8px',
                padding: '10px 14px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                color: '#DC2626',
                fontSize: '0.82rem',
              }}
            >
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

