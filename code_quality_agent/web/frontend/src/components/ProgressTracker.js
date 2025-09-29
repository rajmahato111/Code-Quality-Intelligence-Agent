import React from 'react';
import styled from 'styled-components';
import { Activity, CheckCircle, AlertCircle } from 'lucide-react';
import { useAnalysis } from '../contexts/AnalysisContext';

const ProgressContainer = styled.div`
  background: white;
  border-radius: 1rem;
  padding: 2rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  margin-bottom: 2rem;
`;

const ProgressHeader = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
`;

const ProgressIcon = styled.div`
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: #667eea;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
`;

const ProgressInfo = styled.div`
  flex: 1;
`;

const ProgressTitle = styled.h3`
  font-size: 1.25rem;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 0.25rem;
`;

const ProgressSubtitle = styled.p`
  color: #64748b;
  font-size: 0.875rem;
`;

const ProgressBarContainer = styled.div`
  background: #f1f5f9;
  border-radius: 0.5rem;
  height: 8px;
  overflow: hidden;
  margin-bottom: 1rem;
`;

const ProgressBar = styled.div`
  height: 100%;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  border-radius: 0.5rem;
  transition: width 0.3s ease;
  width: ${props => props.$progress}%;
`;

const ProgressText = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.875rem;
  color: #64748b;
`;

const StagesList = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-top: 1.5rem;
`;

const Stage = styled.div`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  border-radius: 0.5rem;
  background: ${props => {
    if (props.$status === 'completed') return '#f0fdf4';
    if (props.$status === 'active') return '#fef3c7';
    return '#f8fafc';
  }};
  border: 1px solid ${props => {
    if (props.$status === 'completed') return '#bbf7d0';
    if (props.$status === 'active') return '#fde68a';
    return '#e2e8f0';
  }};
`;

const StageIcon = styled.div`
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  
  ${props => {
    if (props.$status === 'completed') {
      return `
        background: #22c55e;
        color: white;
      `;
    }
    if (props.$status === 'active') {
      return `
        background: #f59e0b;
        color: white;
      `;
    }
    return `
      background: #e2e8f0;
      color: #64748b;
    `;
  }}
`;

const StageName = styled.span`
  font-weight: 500;
  color: ${props => {
    if (props.$status === 'completed') return '#166534';
    if (props.$status === 'active') return '#92400e';
    return '#64748b';
  }};
`;

const ProgressTracker = () => {
  const { progress, currentAnalysis, isAnalyzing } = useAnalysis();
  
  const stages = [
    { name: 'File Discovery', threshold: 10 },
    { name: 'Code Parsing', threshold: 25 },
    { name: 'Security Analysis', threshold: 40 },
    { name: 'Complexity Analysis', threshold: 55 },
    { name: 'Performance Analysis', threshold: 70 },
    { name: 'Documentation Check', threshold: 85 },
    { name: 'Report Generation', threshold: 100 },
  ];
  
  const getStageStatus = (threshold) => {
    if (progress >= threshold) return 'completed';
    if (progress >= threshold - 15) return 'active';
    return 'pending';
  };
  
  const getCurrentStage = () => {
    const activeStage = stages.find(stage => 
      progress < stage.threshold && progress >= stage.threshold - 15
    );
    return activeStage?.name || 'Initializing...';
  };
  
  if (!isAnalyzing) return null;
  
  return (
    <ProgressContainer>
      <ProgressHeader>
        <ProgressIcon>
          <Activity size={24} className="animate-spin" />
        </ProgressIcon>
        <ProgressInfo>
          <ProgressTitle>Analyzing Code Quality</ProgressTitle>
          <ProgressSubtitle>
            {currentAnalysis?.path && `Analyzing: ${currentAnalysis.path}`}
          </ProgressSubtitle>
        </ProgressInfo>
      </ProgressHeader>
      
      <ProgressBarContainer>
        <ProgressBar $progress={progress} />
      </ProgressBarContainer>
      
      <ProgressText>
        <span>{getCurrentStage()}</span>
        <span>{Math.round(progress)}% Complete</span>
      </ProgressText>
      
      <StagesList>
        {stages.map((stage, index) => (
          <Stage key={index} $status={getStageStatus(stage.threshold)}>
            <StageIcon $status={getStageStatus(stage.threshold)}>
              {getStageStatus(stage.threshold) === 'completed' ? (
                <CheckCircle size={16} />
              ) : getStageStatus(stage.threshold) === 'active' ? (
                <Activity size={16} className="animate-spin" />
              ) : (
                index + 1
              )}
            </StageIcon>
            <StageName $status={getStageStatus(stage.threshold)}>
              {stage.name}
            </StageName>
          </Stage>
        ))}
      </StagesList>
    </ProgressContainer>
  );
};

export default ProgressTracker;