/**
 * API client service for communicating with the MediBot AI FastAPI backend.
 */
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 60s timeout for model inference
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  // System Health
  checkHealth: async () => {
    try {
      const response = await apiClient.get('/health');
      return response.data;
    } catch (error) {
      console.error('Health check failed:', error);
      throw error;
    }
  },

  // Chat Query
  sendMessage: async (question, sessionId, categoryFilter = null) => {
    try {
      const payload = {
        question,
        session_id: sessionId,
      };
      if (categoryFilter && categoryFilter !== 'all') {
        payload.category_filter = categoryFilter;
      }
      const response = await apiClient.post('/chat', payload);
      return response.data;
    } catch (error) {
      console.error('Send message failed:', error);
      const message = error.response?.data?.detail || error.message || 'Error communicating with medical AI assistant.';
      throw new Error(message);
    }
  },

  // Document Upload
  uploadDocument: async (file, onProgress) => {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await apiClient.post('/documents/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (onProgress && progressEvent.total) {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            onProgress(percentCompleted);
          }
        },
      });
      return response.data;
    } catch (error) {
      console.error('Document upload failed:', error);
      const message = error.response?.data?.detail || error.message || 'Failed to upload document.';
      throw new Error(message);
    }
  },

  // Get Uploaded Documents
  getDocuments: async () => {
    try {
      const response = await apiClient.get('/documents');
      return response.data;
    } catch (error) {
      console.error('Get documents failed:', error);
      throw error;
    }
  },

  // Delete Document
  deleteDocument: async (documentId) => {
    try {
      const response = await apiClient.delete(`/documents/${documentId}`);
      return response.data;
    } catch (error) {
      console.error('Delete document failed:', error);
      const message = error.response?.data?.detail || error.message || 'Failed to delete document.';
      throw new Error(message);
    }
  },

  // Session History
  getSessionHistory: async (sessionId) => {
    try {
      const response = await apiClient.get(`/sessions/${sessionId}/history`);
      return response.data;
    } catch (error) {
      console.error('Get history failed:', error);
      throw error;
    }
  },

  // Clear Session
  clearSession: async (sessionId) => {
    try {
      const response = await apiClient.delete(`/sessions/${sessionId}`);
      return response.data;
    } catch (error) {
      console.error('Clear session failed:', error);
      throw error;
    }
  },

  // Categories
  getCategories: async () => {
    try {
      const response = await apiClient.get('/categories');
      return response.data;
    } catch (error) {
      console.error('Get categories failed:', error);
      throw error;
    }
  },

  // Evaluation Dataset
  getEvaluationDataset: async (difficulty = null, reviewStatus = null) => {
    try {
      const params = {};
      if (difficulty && difficulty !== 'all') params.difficulty = difficulty;
      if (reviewStatus && reviewStatus !== 'all') params.review_status = reviewStatus;
      const response = await apiClient.get('/evaluation/dataset', { params });
      return response.data;
    } catch (error) {
      console.error('Get evaluation dataset failed:', error);
      throw error;
    }
  },

  // Review Evaluation Item
  reviewEvaluationItem: async (id, reviewStatus, expertNotes = '') => {
    try {
      const response = await apiClient.post('/evaluation/review', {
        id,
        review_status: reviewStatus,
        expert_notes: expertNotes,
      });
      return response.data;
    } catch (error) {
      console.error('Review item failed:', error);
      const message = error.response?.data?.detail || error.message || 'Failed to update review status.';
      throw new Error(message);
    }
  },

  // Evaluation & Knowledge Quality Report
  getEvaluationReport: async () => {
    try {
      const response = await apiClient.get('/evaluation/report');
      return response.data;
    } catch (error) {
      console.error('Get evaluation report failed:', error);
      throw error;
    }
  },

  // Trigger Live Evaluation Run
  runEvaluation: async () => {
    try {
      const response = await apiClient.post('/evaluation/run');
      return response.data;
    } catch (error) {
      console.error('Run evaluation failed:', error);
      throw error;
    }
  },
};

export default api;

