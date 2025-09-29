import React, { useState } from 'react';
import styled from 'styled-components';
import { Upload, FolderOpen, Github, Play } from 'lucide-react';
import { useAnalysis } from '../contexts/AnalysisContext';
import { useWebSocket } from '../contexts/WebSocketContext';
import AnalysisResults from '../components/AnalysisResults';
import ProgressTracker from '../components/ProgressTracker';
import RecentAnalyses from '../components/RecentAnalyses';

const DashboardContainer = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
`;

const Header = styled.div`
  text-align: center;
  margin-bottom: 3rem;
`;

const Title = styled.h1`
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 1rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
`;

const Subtitle = styled.p`
  font-size: 1.125rem;
  color: #64748b;
  max-width: 600px;
  margin: 0 auto;
`;

const AnalysisSection = styled.div`
  background: white;
  border-radius: 1rem;
  padding: 2rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  margin-bottom: 2rem;
`;

const SectionTitle = styled.h2`
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 1.5rem;
  color: #1e293b;
`;

const InputOptions = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
`;

const InputOption = styled.div`
  border: 2px dashed #cbd5e1;
  border-radius: 0.75rem;
  padding: 2rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    border-color: #667eea;
    background: #f8fafc;
  }
  
  ${props => props.$active && `
    border-color: #667eea;
    background: #f0f4ff;
  `}
`;

const OptionIcon = styled.div`
  display: flex;
  justify-content: center;
  margin-bottom: 1rem;
  color: #667eea;
`;

const OptionTitle = styled.h3`
  font-size: 1.125rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: #1e293b;
`;

const OptionDescription = styled.p`
  color: #64748b;
  font-size: 0.875rem;
`;

const InputForm = styled.div`
  display: flex;
  gap: 1rem;
  align-items: end;
`;

const InputGroup = styled.div`
  flex: 1;
`;

const Label = styled.label`
  display: block;
  font-weight: 500;
  margin-bottom: 0.5rem;
  color: #374151;
`;

const Input = styled.input`
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.5rem;
  font-size: 1rem;
  
  &:focus {
    outline: none;
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
  }
`;

const Button = styled.button`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 0.5rem;
  font-weight: 500;
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

const Dashboard = () => {
  const [inputType, setInputType] = useState('local');
  const [inputValue, setInputValue] = useState('');
  const { currentAnalysis, isAnalyzing } = useAnalysis();
  const { startAnalysis, isConnected } = useWebSocket();
  
  const handleAnalyze = () => {
    if (!inputValue.trim()) return;
    
    startAnalysis(inputValue, {
      type: inputType,
      includeTests: true,
      maxDepth: 10,
    });
  };
  
  const inputOptions = [
    {
      id: 'local',
      icon: <FolderOpen size={32} />,
      title: 'Local Path',
      description: 'Analyze files or folders on your local system',
    },
    {
      id: 'github',
      icon: <Github size={32} />,
      title: 'GitHub Repository',
      description: 'Analyze a public GitHub repository by URL',
    },
    {
      id: 'upload',
      icon: <Upload size={32} />,
      title: 'Upload Files',
      description: 'Upload and analyze your code files directly',
    },
  ];
  
  return (
    <DashboardContainer>
      <Header>
        <Title>Code Quality Intelligence</Title>
        <Subtitle>
          AI-powered code analysis that provides actionable insights, 
          detects quality issues, and helps improve your codebase
        </Subtitle>
      </Header>
      
      <AnalysisSection>
        <SectionTitle>Start New Analysis</SectionTitle>
        
        <InputOptions>
          {inputOptions.map((option) => (
            <InputOption
              key={option.id}
              $active={inputType === option.id}
              onClick={() => setInputType(option.id)}
            >
              <OptionIcon>{option.icon}</OptionIcon>
              <OptionTitle>{option.title}</OptionTitle>
              <OptionDescription>{option.description}</OptionDescription>
            </InputOption>
          ))}
        </InputOptions>
        
        <InputForm>
          <InputGroup>
            <Label>
              {inputType === 'local' && 'File or Folder Path'}
              {inputType === 'github' && 'GitHub Repository URL'}
              {inputType === 'upload' && 'Select Files'}
            </Label>
            <Input
              type={inputType === 'upload' ? 'file' : 'text'}
              value={inputType === 'upload' ? undefined : inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder={
                inputType === 'local' ? '/path/to/your/code' :
                inputType === 'github' ? 'https://github.com/user/repo' :
                'Select files to upload'
              }
              multiple={inputType === 'upload'}
              disabled={isAnalyzing}
            />
          </InputGroup>
          
          <Button
            onClick={handleAnalyze}
            disabled={!inputValue.trim() || isAnalyzing || !isConnected}
          >
            <Play size={18} />
            {isAnalyzing ? 'Analyzing...' : 'Analyze'}
          </Button>
        </InputForm>
      </AnalysisSection>
      
      {isAnalyzing && <ProgressTracker />}
      
      {currentAnalysis && !isAnalyzing && (
        <AnalysisResults analysis={currentAnalysis} />
      )}
      
      <RecentAnalyses />
    </DashboardContainer>
  );
};

export default Dashboard;