import React, { createContext, useContext, useState, useCallback } from 'react';

const DocumentContext = createContext();

export const useDocument = () => {
  const context = useContext(DocumentContext);
  if (!context) {
    throw new Error('useDocument must be used within a DocumentProvider');
  }
  return context;
};

export const DocumentProvider = ({ children }) => {
  const [documentState, setDocumentState] = useState({
    isUploaded: false,
    fileName: '',
    fileSize: 0,
    summary: '',
    documentId: null,
    sessionId: null,
    chatHistory: [],
    challenges: [],
    currentChallenge: null,
    userAnswers: [],
    isLoading: false,
    error: null
  });

  const API_BASE_URL = '/api';

  const uploadDocument = useCallback(async (file) => {
    setDocumentState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${API_BASE_URL}/upload`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) throw new Error('Upload failed');
      const data = await response.json();

      setDocumentState(prev => ({
        ...prev,
        isUploaded: true,
        fileName: file.name,
        fileSize: file.size,
        documentId: data.document_id,
        summary: data.summary || '',
        sessionId: null,
        chatHistory: [],
        challenges: [],
        userAnswers: [],
        isLoading: false
      }));

      return data;
    } catch (error) {
      setDocumentState(prev => ({
        ...prev,
        documentId: null,
        isLoading: false,
        error: error.message
      }));
      throw error;
    }
  }, []);

  const askQuestion = useCallback(async (question) => {
    if (!documentState.isUploaded) throw new Error('Please upload a document first');

    setDocumentState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const response = await fetch(`${API_BASE_URL}/qa/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question,
          document_id: documentState.documentId,
          conversation_history: []
        })
      });

      if (!response.ok) throw new Error('Failed to get answer');
      const data = await response.json();

      setDocumentState(prev => ({
        ...prev,
        chatHistory: [
          ...prev.chatHistory,
          { type: 'user', content: question, timestamp: new Date() },
          {
            type: 'assistant',
            content: data.answer,
            justification: data.justification,
            source_snippets: data.source_snippets,
            sourceText: data.source_text,
            timestamp: new Date()
          }
        ],
        isLoading: false
      }));

      return data;
    } catch (error) {
      setDocumentState(prev => ({ ...prev, isLoading: false, error: error.message }));
      throw error;
    }
  }, [documentState.isUploaded, documentState.documentId]);

  const generateChallenges = useCallback(async () => {
    if (!documentState.isUploaded) throw new Error('Please upload a document first');

    setDocumentState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const response = await fetch(`${API_BASE_URL}/challenge/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          document_id: documentState.documentId
        })
      });

      if (!response.ok) throw new Error('Failed to generate challenges');
      const data = await response.json();

      setDocumentState(prev => ({
        ...prev,
        challenges: data.questions || [],
        sessionId: data.session_id,
        currentChallenge: 0,
        userAnswers: [],
        isLoading: false
      }));

      return data;
    } catch (error) {
      setDocumentState(prev => ({ ...prev, isLoading: false, error: error.message }));
      throw error;
    }
  }, [documentState.isUploaded, documentState.documentId]);

  const submitChallengeAnswer = useCallback(async (questionIndex, answer) => {
    const question = documentState.challenges[questionIndex];
    const { sessionId, documentId } = documentState;

    if (!question || !sessionId || !documentId) {
      throw new Error('Missing required fields: sessionId, documentId or question');
    }

    setDocumentState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const response = await fetch(`${API_BASE_URL}/challenge/evaluate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          question_id: question.id,
          user_answer: answer,
          document_id: documentId
        })
      });

      if (!response.ok) throw new Error('Failed to evaluate answer');
      const evaluation = await response.json();

      const newAnswer = {
        questionIndex,
        userAnswer: answer,
        evaluation,
        timestamp: new Date()
      };

      setDocumentState(prev => ({
        ...prev,
        userAnswers: [
          ...prev.userAnswers.filter(a => a.questionIndex !== questionIndex),
          newAnswer
        ],
        isLoading: false
      }));

      return evaluation;
    } catch (error) {
      setDocumentState(prev => ({ ...prev, isLoading: false, error: error.message }));
      throw error;
    }
  }, [documentState.challenges, documentState.sessionId, documentState.documentId]);

  const setCurrentChallenge = useCallback((index) => {
    setDocumentState(prev => ({ ...prev, currentChallenge: index }));
  }, []);

  const clearChatHistory = useCallback(() => {
    setDocumentState(prev => ({ ...prev, chatHistory: [] }));
  }, []);

  const resetDocument = useCallback(() => {
    setDocumentState({
      isUploaded: false,
      fileName: '',
      fileSize: 0,
      summary: '',
      documentId: null,
      sessionId: null,
      chatHistory: [],
      challenges: [],
      currentChallenge: null,
      userAnswers: [],
      isLoading: false,
      error: null
    });
  }, []);

  const clearError = useCallback(() => {
    setDocumentState(prev => ({ ...prev, error: null }));
  }, []);

  const value = {
    ...documentState,
    uploadDocument,
    askQuestion,
    generateChallenges,
    submitChallengeAnswer,
    setCurrentChallenge,
    clearChatHistory,
    resetDocument,
    clearError
  };

  return (
    <DocumentContext.Provider value={value}>
      {children}
    </DocumentContext.Provider>
  );
};
