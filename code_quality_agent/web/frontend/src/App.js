import React, { useState } from 'react';
import styled from 'styled-components';

const Container = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: radial-gradient(1000px 600px at 10% -20%, #e8f1ff 0%, transparent 60%),
              radial-gradient(900px 500px at 110% -10%, #f7eaff 0%, transparent 60%);
  min-height: 100vh;
`;

const Header = styled.header`
  text-align: center;
  margin-bottom: 40px;
  padding: 28px 20px;
  background: linear-gradient(135deg, #f6f8ff 0%, #f9f5ff 100%);
  border-radius: 16px;
  border: 1px solid #eef2ff;
  box-shadow: 0 10px 30px rgba(31, 47, 70, 0.06);
`;

const Title = styled.h1`
  margin: 0 0 10px 0;
  font-size: 34px;
  line-height: 1.2;
  background: linear-gradient(90deg, #1f3a93 0%, #6c5ce7 50%, #00a8ff 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
`;

const Subtitle = styled.p`
  color: #596275;
  font-size: 16px;
`;

const InputSection = styled.div`
  background: rgba(255, 255, 255, 0.85);
  padding: 28px;
  border-radius: 16px;
  backdrop-filter: blur(6px);
  box-shadow: 0 12px 30px rgba(31, 47, 70, 0.08);
  border: 1px solid rgba(226, 232, 240, 0.8);
  margin-bottom: 30px;
`;

const InputGroup = styled.div`
  margin-bottom: 20px;
`;

const Label = styled.label`
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #2c3e50;
`;

const Input = styled.input`
  width: 100%;
  padding: 12px;
  border: 2px solid #e1e8ed;
  border-radius: 8px;
  font-size: 16px;
  transition: border-color 0.3s;

  &:focus {
    outline: none;
    border-color: #3498db;
  }
`;

const Button = styled.button`
  background: #3498db;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.3s;

  &:hover {
    background: #2980b9;
  }

  &:disabled {
    background: #bdc3c7;
    cursor: not-allowed;
  }
`;

const ResultsSection = styled.div`
  background: rgba(255, 255, 255, 0.9);
  padding: 28px;
  border-radius: 16px;
  backdrop-filter: blur(6px);
  box-shadow: 0 12px 30px rgba(31, 47, 70, 0.08);
  border: 1px solid rgba(226, 232, 240, 0.8);
`;

const ScoreCard = styled.div`
  background: linear-gradient(135deg, #5b8cff 0%, #7a5cff 100%);
  color: white;
  padding: 28px;
  border-radius: 14px;
  text-align: center;
  margin-bottom: 30px;
  box-shadow: 0 14px 28px rgba(91, 140, 255, 0.25);
`;

const Score = styled.div`
  font-size: 56px;
  font-weight: 800;
  margin-bottom: 6px;
`;

const IssuesGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
`;

const IssueCard = styled.div`
  background: ${props => {
    if (props.severity === 'high') return 'linear-gradient(135deg, #ff6b6b 0%, #e74c3c 100%)';
    if (props.severity === 'medium') return 'linear-gradient(135deg, #feca57 0%, #f39c12 100%)';
    if (props.severity === 'low') return 'linear-gradient(135deg, #54a0ff 0%, #3498db 100%)';
    return 'linear-gradient(135deg, #c8d6e5 0%, #95a5a6 100%)';
  }};
  color: white;
  padding: 20px;
  border-radius: 12px;
  text-align: center;
  box-shadow: 0 10px 20px rgba(0,0,0,0.08);
`;

const IssueCount = styled.div`
  font-size: 32px;
  font-weight: bold;
  margin-bottom: 5px;
`;

const IssueLabel = styled.div`
  font-size: 14px;
  opacity: 0.9;
`;

const IssuesList = styled.div`
  margin-top: 20px;
`;

const IssueItem = styled.div`
  background: #f9fbfd;
  border-left: 4px solid ${props => {
    if (props.severity === 'HIGH') return '#e74c3c';
    if (props.severity === 'MEDIUM') return '#f39c12';
    if (props.severity === 'LOW') return '#3498db';
    return '#95a5a6';
  }};
  padding: 16px;
  margin-bottom: 12px;
  border-radius: 0 12px 12px 0;
  box-shadow: 0 6px 16px rgba(31, 47, 70, 0.05);
`;

const IssueHeader = styled.div`
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 5px;
`;

const IssueDetails = styled.div`
  color: #7f8c8d;
  font-size: 14px;
  margin-bottom: 5px;
`;

const IssueSuggestion = styled.div`
  color: #27ae60;
  font-size: 14px;
  font-style: italic;
`;

const LoadingSpinner = styled.div`
  text-align: center;
  padding: 40px;
  color: #7f8c8d;
`;

const ErrorMessage = styled.div`
  background: #e74c3c;
  color: white;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 20px;
`;

const TabContainer = styled.div`
  display: flex;
  margin-bottom: 20px;
  border-bottom: 2px solid #e1e8ed;
`;

const Tab = styled.button`
  background: ${props => props.active ? 'rgba(52, 152, 219, 0.12)' : 'transparent'};
  border: none;
  padding: 12px 18px;
  font-size: 15px;
  font-weight: 700;
  color: ${props => props.active ? '#3498db' : '#7f8c8d'};
  border-bottom: 2px solid ${props => props.active ? '#3498db' : 'transparent'};
  cursor: pointer;
  border-radius: 10px 10px 0 0;
  transition: all 0.2s ease;

  &:hover {
    color: #3498db;
    background: rgba(52, 152, 219, 0.08);
  }
`;

// Chat UI
const ChatWrapper = styled.div`
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  padding: 24px;
  border-radius: 20px;
  min-height: 400px;
  max-height: 500px;
  overflow-y: auto;
  margin-bottom: 24px;
  border: 1px solid rgba(226, 232, 240, 0.8);
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.06);
  position: relative;
  
  &::-webkit-scrollbar {
    width: 6px;
  }
  
  &::-webkit-scrollbar-track {
    background: rgba(0, 0, 0, 0.05);
    border-radius: 3px;
  }
  
  &::-webkit-scrollbar-thumb {
    background: rgba(52, 152, 219, 0.3);
    border-radius: 3px;
  }
  
  &::-webkit-scrollbar-thumb:hover {
    background: rgba(52, 152, 219, 0.5);
  }
`;

const ChatRow = styled.div`
  margin-bottom: 16px;
  display: flex;
  flex-direction: ${props => props.user ? 'row-reverse' : 'row'};
  align-items: flex-start;
  gap: 8px;
  animation: slideIn 0.3s ease-out;
  
  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateY(10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
`;

const ChatBubble = styled.div`
  background: ${props => props.user 
    ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' 
    : 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)'};
  color: ${props => props.user ? 'white' : '#2d3748'};
  padding: 16px 20px;
  border-radius: ${props => props.user ? '20px 20px 4px 20px' : '20px 20px 20px 4px'};
  max-width: 75%;
  word-wrap: break-word;
  box-shadow: ${props => props.user 
    ? '0 4px 12px rgba(102, 126, 234, 0.3)' 
    : '0 4px 12px rgba(0, 0, 0, 0.1)'};
  border: ${props => props.user ? 'none' : '1px solid rgba(226, 232, 240, 0.8)'};
  position: relative;
  line-height: 1.6;
  font-size: 15px;
  
  /* Code and file path styling */
  code {
    background: ${props => props.user ? 'rgba(255, 255, 255, 0.2)' : '#f1f5f9'};
    color: ${props => props.user ? '#fff' : '#e11d48'};
    padding: 2px 6px;
    border-radius: 4px;
    font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace;
    font-size: 13px;
    font-weight: 500;
  }
  
  /* File paths */
  .file-path {
    background: ${props => props.user ? 'rgba(255, 255, 255, 0.15)' : '#e0f2fe'};
    color: ${props => props.user ? '#e0f2fe' : '#0369a1'};
    padding: 3px 8px;
    border-radius: 6px;
    font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace;
    font-size: 12px;
    font-weight: 600;
    display: inline-block;
    margin: 2px 0;
  }
  
  /* Issue severity badges */
  .severity-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    margin-right: 6px;
    
    &.high {
      background: #fef2f2;
      color: #dc2626;
      border: 1px solid #fecaca;
    }
    
    &.medium {
      background: #fffbeb;
      color: #d97706;
      border: 1px solid #fed7aa;
    }
    
    &.low {
      background: #eff6ff;
      color: #2563eb;
      border: 1px solid #bfdbfe;
    }
  }
  
  /* Category badges */
  .category-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
    margin-right: 6px;
    background: ${props => props.user ? 'rgba(255, 255, 255, 0.2)' : '#f1f5f9'};
    color: ${props => props.user ? '#fff' : '#64748b'};
  }
  
  /* Lists */
  ul, ol {
    margin: 8px 0;
    padding-left: 20px;
  }
  
  li {
    margin: 4px 0;
  }
  
  /* Strong text */
  strong, b {
    font-weight: 700;
    color: ${props => props.user ? '#fff' : '#1e293b'};
  }
  
  /* Links */
  a {
    color: ${props => props.user ? '#e0f2fe' : '#0369a1'};
    text-decoration: underline;
    font-weight: 500;
  }
  
  &::before {
    content: '';
    position: absolute;
    bottom: -1px;
    ${props => props.user ? 'right: 8px;' : 'left: 8px;'}
    width: 0;
    height: 0;
    border: 6px solid transparent;
    border-top-color: ${props => props.user ? '#764ba2' : '#ffffff'};
    border-right-color: ${props => props.user ? '#764ba2' : '#ffffff'};
    transform: ${props => props.user ? 'rotate(45deg)' : 'rotate(-45deg)'};
  }
`;

const ChatAvatar = styled.div`
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: ${props => props.user 
    ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' 
    : 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)'};
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  color: white;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  flex-shrink: 0;
`;

const ChatInputRow = styled.div`
  display: flex;
  gap: 12px;
  align-items: flex-end;
  background: white;
  padding: 16px;
  border-radius: 16px;
  border: 1px solid rgba(226, 232, 240, 0.8);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
`;

const ChatInput = styled.input`
  flex: 1;
  padding: 14px 16px;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  font-size: 16px;
  transition: all 0.2s ease;
  background: #f8fafc;
  
  &:focus { 
    outline: none; 
    border-color: #667eea;
    background: white;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
  }
  
  &::placeholder {
    color: #a0aec0;
  }
`;

const ChatSendButton = styled.button`
  padding: 14px 20px;
  background: ${props => props.disabled 
    ? 'linear-gradient(135deg, #cbd5e0 0%, #a0aec0 100%)' 
    : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'};
  color: white;
  border: none;
  border-radius: 12px;
  cursor: ${props => props.disabled ? 'not-allowed' : 'pointer'};
  font-size: 16px;
  font-weight: 600;
  transition: all 0.2s ease;
  box-shadow: ${props => props.disabled 
    ? 'none' 
    : '0 4px 12px rgba(102, 126, 234, 0.3)'};
  
  &:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
  }
  
  &:active:not(:disabled) {
    transform: translateY(0);
  }
`;

const ChatHeader = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.6);
`;

const ChatTitle = styled.h3`
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
`;

const ChatSubtitle = styled.p`
  margin: 0;
  color: #64748b;
  font-size: 14px;
`;

const TypingIndicator = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  color: #64748b;
  font-size: 14px;
  margin-top: 8px;
  
  .dots {
    display: flex;
    gap: 4px;
  }
  
  .dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #667eea;
    animation: typing 1.4s infinite ease-in-out;
  }
  
  .dot:nth-child(1) { animation-delay: -0.32s; }
  .dot:nth-child(2) { animation-delay: -0.16s; }
  
  @keyframes typing {
    0%, 80%, 100% {
      transform: scale(0.8);
      opacity: 0.5;
    }
    40% {
      transform: scale(1);
      opacity: 1;
    }
  }
`;

const EmptyState = styled.div`
  text-align: center;
  color: #64748b;
  padding: 40px 20px;
  
  .icon {
    font-size: 48px;
    margin-bottom: 16px;
    opacity: 0.6;
  }
  
  .title {
    font-size: 18px;
    font-weight: 600;
    margin-bottom: 8px;
    color: #4a5568;
  }
  
  .subtitle {
    font-size: 14px;
    line-height: 1.5;
  }
`;

const FileUpload = styled.input`
  width: 100%;
  padding: 12px;
  border: 2px dashed #e1e8ed;
  border-radius: 8px;
  background: #f8f9fa;
  cursor: pointer;
  transition: border-color 0.3s;

  &:hover {
    border-color: #3498db;
  }
`;

function App() {
  const [inputType, setInputType] = useState('github');
  const [githubUrl, setGithubUrl] = useState('');
  const [localPath, setLocalPath] = useState('');
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('issues');
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [currentJobId, setCurrentJobId] = useState(null); // Store job_id for Q&A

  const readFileAsText = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => resolve(e.target.result);
      reader.onerror = (e) => reject(new Error('Failed to read file'));
      reader.readAsText(file);
    });
  };

  const startAnalysis = async () => {
    let pathToAnalyze = '';
    
    if (inputType === 'local' && localPath.trim()) {
      pathToAnalyze = localPath.trim();
    } else if (inputType === 'github' && githubUrl.trim()) {
      pathToAnalyze = githubUrl.trim();
    } else if (inputType === 'upload' && selectedFiles.length > 0) {
      pathToAnalyze = selectedFiles.map(f => f.name).join(', ');
    } else {
      alert('Please provide a valid path, URL, or upload files to analyze');
      return;
    }

    setIsAnalyzing(true);
    setAnalysis(null);
    setError(null);
    setCurrentJobId(null); // Reset job ID
    
    try {
      let cliResult;
      
      if (inputType === 'upload' && selectedFiles.length > 0) {
        // NEW: Use /analyze/files endpoint for uploads
        console.log('📤 Uploading files for analysis...');
        
        // Read file contents
        const fileContents = {};
        const fileNames = [];
        for (const file of selectedFiles) {
          try {
            console.log('Reading file:', file.name, 'Type:', typeof file, 'Is File:', file instanceof File);
            const content = await readFileAsText(file);
            fileContents[file.name] = content;
            fileNames.push(file.name);
            console.log('✓ Read', file.name, ':', content.length, 'bytes');
          } catch (err) {
            console.error('Failed to read file:', file.name, err);
            throw new Error(`Failed to read file ${file.name}: ${err.message}`);
          }
        }
        
        // Get API key first
        const apiKeyResponse = await fetch('http://127.0.0.1:8000/demo/api-key');
        const { api_key } = await apiKeyResponse.json();
        
        // Call /analyze/files endpoint
        const analyzeResponse = await fetch('http://127.0.0.1:8000/analyze/files', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${api_key}`
          },
          body: JSON.stringify({
            request: {
              files: fileNames,
              content: fileContents,
              analysis_types: ['security', 'performance', 'complexity', 'duplication', 'testing', 'documentation']
            },
            config: {
              enable_ai_explanations: false,
              enable_severity_scoring: false
            }
          })
        });
        
        if (!analyzeResponse.ok) {
          const errorData = await analyzeResponse.json();
          throw new Error(errorData.message || 'Analysis failed');
        }
        
        const { job_id } = await analyzeResponse.json();
        console.log('✓ Job created:', job_id);
        setCurrentJobId(job_id); // Store job ID for Q&A
        
        // Poll for results
        let attempts = 0;
        while (attempts < 60) {
          await new Promise(resolve => setTimeout(resolve, 1000));
          
          const statusResponse = await fetch(`http://127.0.0.1:8000/analyze/${job_id}`, {
            headers: { 'Authorization': `Bearer ${api_key}` }
          });
          
          const statusData = await statusResponse.json();
          console.log('Poll attempt', attempts, '- Status:', statusData.status);
          
          if (statusData.status === 'completed') {
            // statusData IS the AnalysisResult (issues at top level)
            // Use smart priority: skip overall_score if it's 0, use maintainability_index instead
            let qualityScore = 0;
            if (statusData.metrics?.overall_score && statusData.metrics.overall_score > 0) {
              qualityScore = statusData.metrics.overall_score;
            } else if (statusData.metrics?.maintainability_index) {
              qualityScore = statusData.metrics.maintainability_index;
            } else {
              qualityScore = Math.max(0, 100 - (statusData.issues?.length || 0) * 2);
            }
            
            cliResult = {
              issues: statusData.issues || [],
              quality_score: qualityScore
            };
            console.log('✓ Analysis completed:', cliResult.issues.length, 'issues, score:', qualityScore);
            break;
          } else if (statusData.status === 'failed') {
            throw new Error(statusData.error_message || 'Analysis failed');
          }
          
          attempts++;
        }
        
        if (attempts >= 60) {
          throw new Error('Analysis timed out');
        }
        
      } else if (inputType === 'github' && githubUrl.trim()) {
        // For GitHub repositories - use /analyze/repository endpoint
        console.log('📤 Analyzing GitHub repository...');
        let repoUrl = githubUrl.trim();
        if (!repoUrl.startsWith('http')) {
          repoUrl = `https://github.com/${repoUrl}`;
        }
        
        // Get API key
        const apiKeyResponse = await fetch('http://127.0.0.1:8000/demo/api-key');
        const { api_key } = await apiKeyResponse.json();
        
        // Start repository analysis (let backend auto-detect default branch)
        const analyzeResponse = await fetch('http://127.0.0.1:8000/analyze/repository', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${api_key}`
          },
          body: JSON.stringify({
            url: repoUrl,
            branch: null,  // Let backend auto-detect (will try main, master, etc.)
            config: {
              enable_ai_explanations: false,
              enable_severity_scoring: false
            }
          })
        });
        
        if (!analyzeResponse.ok) {
          const errorData = await analyzeResponse.json();
          throw new Error(errorData.message || 'Repository analysis failed');
        }
        
        const { job_id } = await analyzeResponse.json();
        console.log('✓ Job created:', job_id);
        setCurrentJobId(job_id); // Store job ID for Q&A
        
        // Poll for results
        let attempts = 0;
        while (attempts < 120) { // Longer timeout for GitHub repos
          await new Promise(resolve => setTimeout(resolve, 2000)); // Check every 2 seconds
          
          const statusResponse = await fetch(`http://127.0.0.1:8000/analyze/${job_id}`, {
            headers: { 'Authorization': `Bearer ${api_key}` }
          });
          
          const statusData = await statusResponse.json();
          console.log('Poll attempt', attempts, '- Status:', statusData.status);
          
          if (statusData.status === 'completed') {
            // Use smart priority: skip overall_score if it's 0, use maintainability_index instead
            let qualityScore = 0;
            if (statusData.metrics?.overall_score && statusData.metrics.overall_score > 0) {
              qualityScore = statusData.metrics.overall_score;
            } else if (statusData.metrics?.maintainability_index) {
              qualityScore = statusData.metrics.maintainability_index;
            } else {
              qualityScore = Math.max(0, 100 - (statusData.issues?.length || 0) * 2);
            }
            
            cliResult = {
              issues: statusData.issues || [],
              quality_score: qualityScore
            };
            console.log('✓ Analysis completed:', cliResult.issues.length, 'issues, score:', qualityScore);
            break;
          } else if (statusData.status === 'failed') {
            throw new Error(statusData.error_message || 'Analysis failed');
          }
          
          attempts++;
        }
        
        if (attempts >= 120) {
          throw new Error('Analysis timed out');
        }
        
      } else {
        // For local paths - use /analyze/path endpoint
        console.log('📤 Analyzing local path...');
        let path = localPath.trim();
        
        // Get API key
        const apiKeyResponse = await fetch('http://127.0.0.1:8000/demo/api-key');
        const { api_key } = await apiKeyResponse.json();
        
        // Start path analysis
        const analyzeResponse = await fetch('http://127.0.0.1:8000/analyze/path', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${api_key}`
          },
          body: JSON.stringify({ path: path })
        });
        
        if (!analyzeResponse.ok) {
          const errorData = await analyzeResponse.json();
          throw new Error(errorData.message || 'Path analysis failed');
        }
        
        const { job_id } = await analyzeResponse.json();
        console.log('✓ Job created:', job_id);
        setCurrentJobId(job_id); // Store job ID for Q&A
        
        // Poll for results
        let attempts = 0;
        while (attempts < 60) {
          await new Promise(resolve => setTimeout(resolve, 1000));
          
          const statusResponse = await fetch(`http://127.0.0.1:8000/analyze/${job_id}`, {
            headers: { 'Authorization': `Bearer ${api_key}` }
          });
          
          const statusData = await statusResponse.json();
          console.log('Poll attempt', attempts, '- Status:', statusData.status);
          
          if (statusData.status === 'completed') {
            // Use smart priority: skip overall_score if it's 0, use maintainability_index instead
            let qualityScore = 0;
            if (statusData.metrics?.overall_score && statusData.metrics.overall_score > 0) {
              qualityScore = statusData.metrics.overall_score;
            } else if (statusData.metrics?.maintainability_index) {
              qualityScore = statusData.metrics.maintainability_index;
            } else {
              qualityScore = Math.max(0, 100 - (statusData.issues?.length || 0) * 2);
            }
            
            cliResult = {
              issues: statusData.issues || [],
              quality_score: qualityScore
            };
            console.log('✓ Analysis completed:', cliResult.issues.length, 'issues, score:', qualityScore);
            break;
          } else if (statusData.status === 'failed') {
            throw new Error(statusData.error_message || 'Analysis failed');
          }
          
          attempts++;
        }
        
        if (attempts >= 60) {
          throw new Error('Analysis timed out');
        }
      }
      
      // Process CLI results
      const issues = cliResult.issues || [];
      const highIssues = issues.filter(issue => issue.severity === 'high').length;
      const mediumIssues = issues.filter(issue => issue.severity === 'medium').length;
      const lowIssues = issues.filter(issue => issue.severity === 'low').length;
      
      console.log('CLI Analysis completed:', {
        totalIssues: issues.length,
        highIssues,
        mediumIssues,
        lowIssues,
        qualityScore: cliResult.quality_score
      });
        
        // Calculate realistic quality score based on issues
        let qualityScore = cliResult.quality_score;
        
        // Use the exact score from CLI - no fallback calculation
        // This ensures consistency between CLI and Web UI
        if (qualityScore === 0 || !qualityScore) {
          qualityScore = 0; // Keep the CLI score of 0
        }
        
        setAnalysis({
          path: pathToAnalyze,
          type: inputType,
          qualityScore: Math.round(qualityScore),
          issues: {
            high: highIssues,
            medium: mediumIssues,
            low: lowIssues,
            total: issues.length
          },
          details: issues.map(issue => ({
            type: issue.category || 'General',
            severity: issue.severity?.toUpperCase() || 'MEDIUM',
            file: issue.location?.file_path || 'unknown',
            line: issue.location?.line_number || 0,
            message: issue.description || issue.title || 'Issue detected',
            suggestion: issue.suggestions?.[0] || 'No suggestion available'
          })),
          timestamp: new Date().toLocaleString()
        });
        
        setIsAnalyzing(false);
    } catch (error) {
      console.error('Analysis failed:', error);
      setError(error.message);
      setIsAnalyzing(false);
    }
  };

  const handleFileSelect = (event) => {
    const files = event.target.files;
    if (files && files.length > 0) {
      const fileArray = Array.from(files);
      setSelectedFiles(fileArray);
    }
  };

  const sendChatMessage = async () => {
    if (!chatInput.trim()) return;
    
    if (!analysis) {
      setChatMessages(prev => [...prev, { 
        type: 'ai', 
        message: 'Please run an analysis first to get meaningful answers about your code. Click on "Local Path" tab, enter a path like "/Users/rajkumarmahto/Atlan Kiro/sample-python", and click "Start Analysis".'
      }]);
      setChatInput('');
      return;
    }
    
    const userMessage = chatInput.trim();
    setChatInput('');
    setIsChatLoading(true);
    
    // Add user message to chat
    setChatMessages(prev => [...prev, { type: 'user', message: userMessage }]);
    
    try {
      // Get API key first
      const apiKeyResponse = await fetch('http://127.0.0.1:8000/demo/api-key');
      const apiKeyData = await apiKeyResponse.json();
      const apiKey = apiKeyData.api_key;
      
      console.log('Chat: Analysis data available:', !!analysis);
      console.log('Chat: Analysis details count:', analysis?.details?.length || 0);
      
      // Send question to backend with job_id
      const response = await fetch('http://127.0.0.1:8000/qa/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${apiKey}`
        },
        body: JSON.stringify({
          question: userMessage,
          job_id: currentJobId || undefined  // Use the stored job_id from analysis
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to get answer');
      }
      
      const answerData = await response.json();
      
      console.log('Chat: Received response:', answerData);
      
      // Add AI response to chat
      setChatMessages(prev => [...prev, { 
        type: 'ai', 
        message: answerData.answer || 'I apologize, but I could not generate a response to your question.'
      }]);
      
    } catch (error) {
      console.error('Chat error:', error);
      setChatMessages(prev => [...prev, { 
        type: 'ai', 
        message: 'Sorry, I encountered an error while processing your question. Please try again.'
      }]);
    } finally {
      setIsChatLoading(false);
    }
  };

  const handleChatKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendChatMessage();
    }
  };

  const formatChatMessage = (message) => {
    if (!message) return message;
    
    let formatted = message;
    
    // Format code blocks (triple backticks)
    formatted = formatted.replace(
      /```(\w+)?\n([\s\S]*?)```/g,
      '<pre><code>$2</code></pre>'
    );
    
    // Format bold text
    formatted = formatted.replace(
      /\*\*([^\*]+)\*\*/g,
      '<strong>$1</strong>'
    );
    
    // Format italic text
    formatted = formatted.replace(
      /\*([^\*]+)\*/g,
      '<em>$1</em>'
    );
    
    // Format file paths with styling
    formatted = formatted.replace(
      /([\/\w\-\.]+\.(py|js|ts|jsx|tsx|java|cpp|c|h|go|rs|php|rb|swift|kt|scala|sh|yaml|yml|json|xml|html|css|md|txt)):(\d+)/g,
      '<span style="background:#2d2d2d;color:#6c9ef8;padding:2px 6px;border-radius:3px;font-family:monospace;font-size:0.9em">$1:$3</span>'
    );
    
    // Format inline code
    formatted = formatted.replace(
      /`([^`]+)`/g,
      '<code style="background:#f4f4f4;padding:2px 6px;border-radius:3px;font-family:monospace;color:#d73a49">$1</code>'
    );
    
    // Format numbered lists (1. 2. 3. etc.)
    formatted = formatted.replace(
      /^\s*(\d+)\.\s+(.+)$/gm,
      '<li><strong>$1.</strong> $2</li>'
    );
    
    // Format bullet points
    formatted = formatted.replace(
      /^\s*[-•]\s+(.+)$/gm,
      '<li>$1</li>'
    );
    
    // Wrap consecutive list items in ul/ol
    formatted = formatted.replace(
      /(<li>.*?<\/li>\s*)+/gs,
      (match) => `<ul style="margin:10px 0;padding-left:20px">${match}</ul>`
    );
    
    // Format section headers (### or **)
    formatted = formatted.replace(
      /###\s+(.+)/g,
      '<h4 style="margin-top:15px;margin-bottom:8px;color:#2c3e50">$1</h4>'
    );
    
    // Preserve line breaks
    formatted = formatted.replace(/\n\n/g, '<br><br>');
    formatted = formatted.replace(/\n/g, '<br>');
    
    return formatted;
  };

  return (
    <Container>
      <Header>
        <Title>Code Quality Intelligence Agent</Title>
        <Subtitle>AI-powered code analysis and quality insights</Subtitle>
      </Header>

      <InputSection>
        <TabContainer>
          <Tab 
            active={inputType === 'github'} 
            onClick={() => setInputType('github')}
          >
            GitHub Repository
          </Tab>
          <Tab 
            active={inputType === 'local'} 
              onClick={() => setInputType('local')}
          >
            Local Path
          </Tab>
          <Tab 
            active={inputType === 'upload'} 
              onClick={() => setInputType('upload')}
          >
            Upload Files
          </Tab>
        </TabContainer>
            
            {inputType === 'github' && (
          <InputGroup>
            <Label>GitHub Repository URL</Label>
            <Input
                  type="text"
              placeholder="https://github.com/owner/repo or owner/repo"
                  value={githubUrl}
                  onChange={(e) => setGithubUrl(e.target.value)}
            />
          </InputGroup>
        )}

        {inputType === 'local' && (
          <InputGroup>
            <Label>Local Path</Label>
            <Input
              type="text"
              placeholder="/path/to/your/code"
              value={localPath}
              onChange={(e) => setLocalPath(e.target.value)}
            />
          </InputGroup>
            )}
            
            {inputType === 'upload' && (
          <InputGroup>
            <Label>Upload Files</Label>
            <FileUpload
                  type="file"
                  multiple
                  onChange={handleFileSelect}
            />
            {selectedFiles.length > 0 && (
              <div style={{ marginTop: '10px', color: '#27ae60' }}>
                {selectedFiles.length} file(s) selected
              </div>
            )}
          </InputGroup>
        )}

        <Button onClick={startAnalysis} disabled={isAnalyzing}>
          {isAnalyzing ? 'Analyzing...' : 'Start Analysis'}
        </Button>
      </InputSection>

      {error && (
        <ErrorMessage>
          Error: {error}
        </ErrorMessage>
      )}

      {isAnalyzing && (
        <LoadingSpinner>
          <div>🔍 Analyzing your code...</div>
          <div>This may take a few moments</div>
        </LoadingSpinner>
      )}

      {analysis && (
        <ResultsSection>
          <TabContainer>
            <Tab 
              active={activeTab === 'issues'} 
              onClick={() => setActiveTab('issues')}
            >
              Issues Found
            </Tab>
            <Tab 
              active={activeTab === 'chat'} 
              onClick={() => setActiveTab('chat')}
            >
              AI Chat
            </Tab>
          </TabContainer>

          {activeTab === 'issues' && (
            <>
              <ScoreCard>
                <Score>{analysis.qualityScore}/100</Score>
                <div>Overall Quality Score</div>
              </ScoreCard>

              <IssuesGrid>
                <IssueCard severity="high">
                  <IssueCount>{analysis.issues.high}</IssueCount>
                  <IssueLabel>High Priority</IssueLabel>
                </IssueCard>
                <IssueCard severity="medium">
                  <IssueCount>{analysis.issues.medium}</IssueCount>
                  <IssueLabel>Medium Priority</IssueLabel>
                </IssueCard>
                <IssueCard severity="low">
                  <IssueCount>{analysis.issues.low}</IssueCount>
                  <IssueLabel>Low Priority</IssueLabel>
                </IssueCard>
                <IssueCard>
                  <IssueCount>{analysis.issues.total}</IssueCount>
                  <IssueLabel>Total Issues</IssueLabel>
                </IssueCard>
              </IssuesGrid>

              <div>
                <h3>Detailed Issues:</h3>
                <IssuesList>
                  {analysis.details.map((issue, index) => (
                    <IssueItem key={index} severity={issue.severity}>
                      <IssueHeader>
                        {issue.type} - {issue.severity} Severity
                      </IssueHeader>
                      <IssueDetails>
                        📁 {issue.file}:{issue.line}
                      </IssueDetails>
                      <IssueDetails>
                        {issue.message}
                      </IssueDetails>
                      <IssueSuggestion>
                        💡 {issue.suggestion}
                      </IssueSuggestion>
                    </IssueItem>
                  ))}
                </IssuesList>
              </div>
            </>
          )}

          {activeTab === 'chat' && (
            <div>
              <ChatHeader>
                <ChatAvatar>
                  🤖
                </ChatAvatar>
                <div>
                  <ChatTitle>AI Chat Assistant</ChatTitle>
                  <ChatSubtitle>Ask questions about your code analysis results!</ChatSubtitle>
                </div>
              </ChatHeader>
              
              {/* Chat Messages */}
              <ChatWrapper>
                {chatMessages.length === 0 ? (
                  <EmptyState>
                    <div className="icon">💬</div>
                    <div className="title">
                      {analysis ? 'Start a conversation!' : 'Ready to help!'}
                    </div>
                    <div className="subtitle">
                      {analysis ? 
                        'Ask me about your code analysis results. I can help explain issues, suggest fixes, and answer questions about your codebase.' :
                        'Please run an analysis first to get meaningful answers about your code. Use the "Local Path" tab above to analyze your code.'
                      }
                    </div>
                  </EmptyState>
                ) : (
                  chatMessages.map((msg, index) => (
                    <ChatRow key={index} user={msg.type === 'user'}>
                      <ChatAvatar user={msg.type === 'user'}>
                        {msg.type === 'user' ? '👤' : '🤖'}
                      </ChatAvatar>
                      <ChatBubble 
                        user={msg.type === 'user'}
                        dangerouslySetInnerHTML={{
                          __html: msg.type === 'ai' ? formatChatMessage(msg.message) : msg.message
                        }}
                      />
                    </ChatRow>
                  ))
                )}
                {isChatLoading && (
                  <ChatRow>
                    <ChatAvatar>
                      🤖
                    </ChatAvatar>
                    <TypingIndicator>
                      <span>AI is thinking</span>
                      <div className="dots">
                        <div className="dot"></div>
                        <div className="dot"></div>
                        <div className="dot"></div>
                      </div>
                    </TypingIndicator>
                  </ChatRow>
                )}
              </ChatWrapper>
              
              {/* Chat Input */}
              <ChatInputRow>
                <ChatInput
                  type="text"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyPress={handleChatKeyPress}
                  placeholder="Ask a question about your code analysis..."
                  disabled={isChatLoading}
                />
                <ChatSendButton onClick={sendChatMessage} disabled={!chatInput.trim() || isChatLoading}>
                  {isChatLoading ? '⏳' : '🚀'}
                </ChatSendButton>
              </ChatInputRow>
            </div>
          )}
        </ResultsSection>
      )}
    </Container>
  );
}

export default App;