import React, { createContext, useContext, useEffect, useState } from 'react';
import { io } from 'socket.io-client';
import { useAnalysis } from './AnalysisContext';
import toast from 'react-hot-toast';

const WebSocketContext = createContext();

export const WebSocketProvider = ({ children }) => {
  const [socket, setSocket] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const { updateProgress, completeAnalysis, setError } = useAnalysis();
  
  useEffect(() => {
    // Initialize WebSocket connection
    const newSocket = io(process.env.REACT_APP_WS_URL || 'ws://localhost:8000', {
      transports: ['websocket'],
    });
    
    newSocket.on('connect', () => {
      setIsConnected(true);
      toast.success('Connected to analysis server');
    });
    
    newSocket.on('disconnect', () => {
      setIsConnected(false);
      toast.error('Disconnected from analysis server');
    });
    
    newSocket.on('analysis_progress', (data) => {
      updateProgress(data.progress);
      if (data.message) {
        toast.loading(data.message, { id: 'analysis-progress' });
      }
    });
    
    newSocket.on('analysis_complete', (data) => {
      toast.dismiss('analysis-progress');
      toast.success('Analysis completed successfully!');
      completeAnalysis(data.result);
    });
    
    newSocket.on('analysis_error', (data) => {
      toast.dismiss('analysis-progress');
      toast.error(`Analysis failed: ${data.error}`);
      setError(data.error);
    });
    
    newSocket.on('chat_response', (data) => {
      // Handle chat responses
      window.dispatchEvent(new CustomEvent('chat_response', { detail: data }));
    });
    
    setSocket(newSocket);
    
    return () => {
      newSocket.close();
    };
  }, [updateProgress, completeAnalysis, setError]);
  
  const startAnalysis = (path, options = {}) => {
    if (socket && isConnected) {
      socket.emit('start_analysis', { path, options });
      toast.loading('Starting analysis...', { id: 'analysis-progress' });
    } else {
      toast.error('Not connected to server');
    }
  };
  
  const sendChatMessage = (message, analysisId = null) => {
    if (socket && isConnected) {
      socket.emit('chat_message', { message, analysisId });
    } else {
      toast.error('Not connected to server');
    }
  };
  
  const value = {
    socket,
    isConnected,
    startAnalysis,
    sendChatMessage,
  };
  
  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
};