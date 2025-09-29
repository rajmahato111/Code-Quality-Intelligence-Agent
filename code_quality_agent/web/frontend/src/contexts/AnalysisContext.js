import React, { createContext, useContext, useReducer } from 'react';

const AnalysisContext = createContext();

const initialState = {
  currentAnalysis: null,
  analysisHistory: [],
  isAnalyzing: false,
  progress: 0,
  error: null,
};

const analysisReducer = (state, action) => {
  switch (action.type) {
    case 'START_ANALYSIS':
      return {
        ...state,
        isAnalyzing: true,
        progress: 0,
        error: null,
        currentAnalysis: {
          id: action.payload.id,
          path: action.payload.path,
          startTime: new Date(),
        },
      };
      
    case 'UPDATE_PROGRESS':
      return {
        ...state,
        progress: action.payload.progress,
      };
      
    case 'ANALYSIS_COMPLETE':
      return {
        ...state,
        isAnalyzing: false,
        progress: 100,
        currentAnalysis: {
          ...state.currentAnalysis,
          ...action.payload.result,
          endTime: new Date(),
        },
        analysisHistory: [
          action.payload.result,
          ...state.analysisHistory.slice(0, 9), // Keep last 10
        ],
      };
      
    case 'ANALYSIS_ERROR':
      return {
        ...state,
        isAnalyzing: false,
        error: action.payload.error,
      };
      
    case 'CLEAR_ERROR':
      return {
        ...state,
        error: null,
      };
      
    case 'LOAD_ANALYSIS':
      return {
        ...state,
        currentAnalysis: action.payload.analysis,
      };
      
    default:
      return state;
  }
};

export const AnalysisProvider = ({ children }) => {
  const [state, dispatch] = useReducer(analysisReducer, initialState);
  
  const startAnalysis = (path, options = {}) => {
    const analysisId = `analysis_${Date.now()}`;
    dispatch({
      type: 'START_ANALYSIS',
      payload: { id: analysisId, path, options },
    });
    return analysisId;
  };
  
  const updateProgress = (progress) => {
    dispatch({
      type: 'UPDATE_PROGRESS',
      payload: { progress },
    });
  };
  
  const completeAnalysis = (result) => {
    dispatch({
      type: 'ANALYSIS_COMPLETE',
      payload: { result },
    });
  };
  
  const setError = (error) => {
    dispatch({
      type: 'ANALYSIS_ERROR',
      payload: { error },
    });
  };
  
  const clearError = () => {
    dispatch({ type: 'CLEAR_ERROR' });
  };
  
  const loadAnalysis = (analysis) => {
    dispatch({
      type: 'LOAD_ANALYSIS',
      payload: { analysis },
    });
  };
  
  const value = {
    ...state,
    startAnalysis,
    updateProgress,
    completeAnalysis,
    setError,
    clearError,
    loadAnalysis,
  };
  
  return (
    <AnalysisContext.Provider value={value}>
      {children}
    </AnalysisContext.Provider>
  );
};

export const useAnalysis = () => {
  const context = useContext(AnalysisContext);
  if (!context) {
    throw new Error('useAnalysis must be used within an AnalysisProvider');
  }
  return context;
};