import React, { useState, useRef, useEffect } from 'react';
import styled from 'styled-components';
import { Send, Bot, User, Code, FileText, AlertTriangle } from 'lucide-react';
import { useWebSocket } from '../contexts/WebSocketContext';
import { useAnalysis } from '../contexts/AnalysisContext';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';

const ChatContainer = styled.div`
  max-width: 1000px;
  margin: 0 auto;
  padding: 2rem;
  height: calc(100vh - 120px);
  display: flex;
  flex-direction: column;
`;

const ChatHeader = styled.div`
  text-align: center;
  margin-bottom: 2rem;
`;

const Title = styled.h1`
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  color: #1e293b;
`;

const Subtitle = styled.p`
  color: #64748b;
  font-size: 1rem;
`;

const MessagesContainer = styled.div`
  flex: 1;
  background: white;
  border-radius: 1rem;
  padding: 1.5rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  overflow-y: auto;
  margin-bottom: 1rem;
`;

const Message = styled.div`
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
  
  ${props => props.$isUser && `
    flex-direction: row-reverse;
  `}
`;

const MessageIcon = styled.div`
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  
  ${props => props.$isUser ? `
    background: #667eea;
    color: white;
  ` : `
    background: #f1f5f9;
    color: #64748b;
  `}
`;

const MessageContent = styled.div`
  flex: 1;
  max-width: 70%;
`;

const MessageBubble = styled.div`
  padding: 1rem 1.25rem;
  border-radius: 1rem;
  
  ${props => props.$isUser ? `
    background: #667eea;
    color: white;
    border-bottom-right-radius: 0.25rem;
  ` : `
    background: #f8fafc;
    color: #1e293b;
    border-bottom-left-radius: 0.25rem;
  `}
`;

const MessageTime = styled.div`
  font-size: 0.75rem;
  color: #94a3b8;
  margin-top: 0.5rem;
  
  ${props => props.$isUser && `
    text-align: right;
  `}
`;

const InputContainer = styled.div`
  background: white;
  border-radius: 1rem;
  padding: 1rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  display: flex;
  gap: 1rem;
  align-items: end;
`;

const InputWrapper = styled.div`
  flex: 1;
  position: relative;
`;

const TextArea = styled.textarea`
  width: 100%;
  min-height: 60px;
  max-height: 120px;
  padding: 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.75rem;
  font-size: 1rem;
  font-family: inherit;
  resize: none;
  
  &:focus {
    outline: none;
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
  }
  
  &::placeholder {
    color: #94a3b8;
  }
`;

const SendButton = styled.button`
  width: 48px;
  height: 48px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.2s ease;
  
  &:hover {
    background: #5a67d8;
  }
  
  &:disabled {
    background: #9ca3af;
    cursor: not-allowed;
  }
`;

const SuggestedQuestions = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1rem;
`;

const SuggestedQuestion = styled.button`
  padding: 0.5rem 1rem;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 2rem;
  font-size: 0.875rem;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    background: #667eea;
    color: white;
    border-color: #667eea;
  }
`;

const EmptyState = styled.div`
  text-align: center;
  padding: 3rem 1rem;
  color: #64748b;
`;

const EmptyIcon = styled.div`
  font-size: 3rem;
  margin-bottom: 1rem;
`;

const Chat = () => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);
  const { sendChatMessage, isConnected } = useWebSocket();
  const { currentAnalysis } = useAnalysis();
  
  const suggestedQuestions = [
    "What are the main security issues in my code?",
    "Which files have the highest complexity?",
    "Show me performance bottlenecks",
    "What testing gaps exist?",
    "How can I improve code quality?",
    "Explain the most critical issues",
  ];
  
  useEffect(() => {
    const handleChatResponse = (event) => {
      const { response, timestamp } = event.detail;
      setMessages(prev => [...prev, {
        id: Date.now(),
        content: response,
        isUser: false,
        timestamp: new Date(timestamp),
      }]);
      setIsTyping(false);
    };
    
    window.addEventListener('chat_response', handleChatResponse);
    return () => window.removeEventListener('chat_response', handleChatResponse);
  }, []);
  
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  const handleSendMessage = () => {
    if (!inputValue.trim() || !isConnected) return;
    
    const message = {
      id: Date.now(),
      content: inputValue,
      isUser: true,
      timestamp: new Date(),
    };
    
    setMessages(prev => [...prev, message]);
    setIsTyping(true);
    
    sendChatMessage(inputValue, currentAnalysis?.id);
    setInputValue('');
  };
  
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };
  
  const handleSuggestedQuestion = (question) => {
    setInputValue(question);
  };
  
  const renderMessage = (message) => (
    <Message key={message.id} $isUser={message.isUser}>
      <MessageIcon $isUser={message.isUser}>
        {message.isUser ? <User size={20} /> : <Bot size={20} />}
      </MessageIcon>
      <MessageContent>
        <MessageBubble $isUser={message.isUser}>
          {message.isUser ? (
            message.content
          ) : (
            <ReactMarkdown
              components={{
                code({ node, inline, className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || '');
                  return !inline && match ? (
                    <SyntaxHighlighter
                      style={tomorrow}
                      language={match[1]}
                      PreTag="div"
                      {...props}
                    >
                      {String(children).replace(/\n$/, '')}
                    </SyntaxHighlighter>
                  ) : (
                    <code className={className} {...props}>
                      {children}
                    </code>
                  );
                },
              }}
            >
              {message.content}
            </ReactMarkdown>
          )}
        </MessageBubble>
        <MessageTime $isUser={message.isUser}>
          {message.timestamp.toLocaleTimeString()}
        </MessageTime>
      </MessageContent>
    </Message>
  );
  
  return (
    <ChatContainer>
      <ChatHeader>
        <Title>Code Quality Assistant</Title>
        <Subtitle>
          Ask questions about your code quality, get insights, and receive actionable recommendations
        </Subtitle>
      </ChatHeader>
      
      <MessagesContainer>
        {messages.length === 0 ? (
          <EmptyState>
            <EmptyIcon>💬</EmptyIcon>
            <h3>Start a conversation</h3>
            <p>Ask me anything about your code quality analysis</p>
            
            {currentAnalysis && (
              <SuggestedQuestions>
                {suggestedQuestions.map((question, index) => (
                  <SuggestedQuestion
                    key={index}
                    onClick={() => handleSuggestedQuestion(question)}
                  >
                    {question}
                  </SuggestedQuestion>
                ))}
              </SuggestedQuestions>
            )}
          </EmptyState>
        ) : (
          <>
            {messages.map(renderMessage)}
            {isTyping && (
              <Message>
                <MessageIcon>
                  <Bot size={20} />
                </MessageIcon>
                <MessageContent>
                  <MessageBubble>
                    <div className="animate-pulse">Thinking...</div>
                  </MessageBubble>
                </MessageContent>
              </Message>
            )}
          </>
        )}
        <div ref={messagesEndRef} />
      </MessagesContainer>
      
      <InputContainer>
        <InputWrapper>
          <TextArea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={
              currentAnalysis 
                ? "Ask about your code analysis..." 
                : "Run an analysis first to ask specific questions about your code"
            }
            disabled={!isConnected}
          />
        </InputWrapper>
        <SendButton
          onClick={handleSendMessage}
          disabled={!inputValue.trim() || !isConnected}
        >
          <Send size={20} />
        </SendButton>
      </InputContainer>
    </ChatContainer>
  );
};

export default Chat;