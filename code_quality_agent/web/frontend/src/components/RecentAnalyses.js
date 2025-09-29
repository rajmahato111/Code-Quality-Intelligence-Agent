import React from 'react';
import styled from 'styled-components';
import { Clock, FolderOpen, ExternalLink } from 'lucide-react';
import { useAnalysis } from '../contexts/AnalysisContext';
import { Link } from 'react-router-dom';

const RecentContainer = styled.div`
  background: white;
  border-radius: 1rem;
  padding: 2rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
`;

const SectionTitle = styled.h2`
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 1.5rem;
  color: #1e293b;
`;

const AnalysesList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1rem;
`;

const AnalysisItem = styled(Link)`
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.75rem;
  text-decoration: none;
  color: inherit;
  transition: all 0.2s ease;
  
  &:hover {
    border-color: #667eea;
    background: #f8fafc;
  }
`;

const AnalysisIcon = styled.div`
  width: 40px;
  height: 40px;
  border-radius: 0.5rem;
  background: #f1f5f9;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #64748b;
`;

const AnalysisInfo = styled.div`
  flex: 1;
`;

const AnalysisPath = styled.div`
  font-weight: 500;
  color: #1e293b;
  margin-bottom: 0.25rem;
`;

const AnalysisDetails = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
  font-size: 0.875rem;
  color: #64748b;
`;

const AnalysisTime = styled.div`
  display: flex;
  align-items: center;
  gap: 0.25rem;
`;

const AnalysisStats = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const StatBadge = styled.span`
  padding: 0.125rem 0.5rem;
  border-radius: 1rem;
  font-size: 0.75rem;
  font-weight: 500;
  
  ${props => {
    switch (props.$type) {
      case 'high':
        return 'background: #fef2f2; color: #dc2626;';
      case 'medium':
        return 'background: #fffbeb; color: #d97706;';
      case 'low':
        return 'background: #eff6ff; color: #2563eb;';
      default:
        return 'background: #f1f5f9; color: #64748b;';
    }
  }}
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

const RecentAnalyses = () => {
  const { analysisHistory } = useAnalysis();
  
  const formatTime = (date) => {
    if (!date) return '';
    const now = new Date();
    const diff = now - new Date(date);
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    
    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return `${days}d ago`;
  };
  
  const getIssueStats = (analysis) => {
    if (!analysis.issues) return { high: 0, medium: 0, low: 0 };
    
    return analysis.issues.reduce((acc, issue) => {
      const severity = issue.severity?.toLowerCase() || 'low';
      acc[severity] = (acc[severity] || 0) + 1;
      return acc;
    }, { high: 0, medium: 0, low: 0 });
  };
  
  if (!analysisHistory || analysisHistory.length === 0) {
    return (
      <RecentContainer>
        <SectionTitle>Recent Analyses</SectionTitle>
        <EmptyState>
          <EmptyIcon>📊</EmptyIcon>
          <h3>No analyses yet</h3>
          <p>Your recent code quality analyses will appear here</p>
        </EmptyState>
      </RecentContainer>
    );
  }
  
  return (
    <RecentContainer>
      <SectionTitle>Recent Analyses</SectionTitle>
      <AnalysesList>
        {analysisHistory.slice(0, 5).map((analysis) => {
          const stats = getIssueStats(analysis);
          
          return (
            <AnalysisItem
              key={analysis.id}
              to={`/analysis/${analysis.id}`}
            >
              <AnalysisIcon>
                <FolderOpen size={20} />
              </AnalysisIcon>
              
              <AnalysisInfo>
                <AnalysisPath>
                  {analysis.path || analysis.codebase_path || 'Unknown path'}
                </AnalysisPath>
                <AnalysisDetails>
                  <AnalysisTime>
                    <Clock size={14} />
                    {formatTime(analysis.endTime || analysis.timestamp)}
                  </AnalysisTime>
                  
                  <AnalysisStats>
                    {stats.high > 0 && (
                      <StatBadge $type="high">{stats.high} high</StatBadge>
                    )}
                    {stats.medium > 0 && (
                      <StatBadge $type="medium">{stats.medium} medium</StatBadge>
                    )}
                    {stats.low > 0 && (
                      <StatBadge $type="low">{stats.low} low</StatBadge>
                    )}
                    {stats.high === 0 && stats.medium === 0 && stats.low === 0 && (
                      <StatBadge>No issues</StatBadge>
                    )}
                  </AnalysisStats>
                </AnalysisDetails>
              </AnalysisInfo>
              
              <ExternalLink size={16} color="#94a3b8" />
            </AnalysisItem>
          );
        })}
      </AnalysesList>
    </RecentContainer>
  );
};

export default RecentAnalyses;