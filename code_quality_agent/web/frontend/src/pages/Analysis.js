import React, { useEffect } from 'react';
import { useParams, Navigate } from 'react-router-dom';
import styled from 'styled-components';
import { ArrowLeft, Download, Share2 } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useAnalysis } from '../contexts/AnalysisContext';
import AnalysisResults from '../components/AnalysisResults';

const AnalysisContainer = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
`;

const AnalysisHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #e2e8f0;
`;

const HeaderLeft = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
`;

const BackButton = styled(Link)`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  text-decoration: none;
  color: #64748b;
  font-weight: 500;
  transition: all 0.2s ease;
  
  &:hover {
    background: #f1f5f9;
    color: #1e293b;
  }
`;

const AnalysisTitle = styled.div`
`;

const Title = styled.h1`
  font-size: 1.75rem;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 0.25rem;
`;

const Subtitle = styled.p`
  color: #64748b;
  font-size: 0.875rem;
`;

const HeaderActions = styled.div`
  display: flex;
  gap: 1rem;
`;

const ActionButton = styled.button`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  background: white;
  color: #64748b;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    border-color: #667eea;
    color: #667eea;
  }
`;

const LoadingState = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  text-align: center;
`;

const LoadingSpinner = styled.div`
  width: 48px;
  height: 48px;
  border: 4px solid #f1f5f9;
  border-top: 4px solid #667eea;
  border-radius: 50%;
  margin-bottom: 1rem;
`;

const ErrorState = styled.div`
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 0.75rem;
  padding: 2rem;
  text-align: center;
  color: #dc2626;
`;

const Analysis = () => {
  const { analysisId } = useParams();
  const { currentAnalysis, analysisHistory, loadAnalysis } = useAnalysis();
  
  useEffect(() => {
    // Try to find the analysis in history or current analysis
    if (currentAnalysis?.id === analysisId) {
      return; // Already loaded
    }
    
    const historicalAnalysis = analysisHistory.find(a => a.id === analysisId);
    if (historicalAnalysis) {
      loadAnalysis(historicalAnalysis);
      return;
    }
    
    // If not found, try to fetch from API
    // This would be implemented with actual API call
    console.log('Analysis not found in local state, would fetch from API:', analysisId);
  }, [analysisId, currentAnalysis, analysisHistory, loadAnalysis]);
  
  const analysis = currentAnalysis?.id === analysisId ? 
    currentAnalysis : 
    analysisHistory.find(a => a.id === analysisId);
  
  if (!analysis) {
    return (
      <AnalysisContainer>
        <AnalysisHeader>
          <HeaderLeft>
            <BackButton to="/">
              <ArrowLeft size={18} />
              Back to Dashboard
            </BackButton>
          </HeaderLeft>
        </AnalysisHeader>
        
        <ErrorState>
          <h3>Analysis Not Found</h3>
          <p>The requested analysis could not be found. It may have been deleted or the ID is incorrect.</p>
        </ErrorState>
      </AnalysisContainer>
    );
  }
  
  const handleExport = () => {
    // Export analysis results as JSON
    const dataStr = JSON.stringify(analysis, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `analysis-${analysis.id}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };
  
  const handleShare = async () => {
    // Share analysis URL
    const url = window.location.href;
    
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'Code Quality Analysis',
          text: `Check out this code quality analysis for ${analysis.path}`,
          url: url,
        });
      } catch (err) {
        console.log('Error sharing:', err);
      }
    } else {
      // Fallback: copy to clipboard
      try {
        await navigator.clipboard.writeText(url);
        // You could show a toast notification here
        console.log('URL copied to clipboard');
      } catch (err) {
        console.log('Error copying to clipboard:', err);
      }
    }
  };
  
  const formatDate = (date) => {
    if (!date) return '';
    return new Date(date).toLocaleString();
  };
  
  return (
    <AnalysisContainer>
      <AnalysisHeader>
        <HeaderLeft>
          <BackButton to="/">
            <ArrowLeft size={18} />
            Back to Dashboard
          </BackButton>
          
          <AnalysisTitle>
            <Title>Analysis Results</Title>
            <Subtitle>
              {analysis.path || analysis.codebase_path} • {formatDate(analysis.endTime || analysis.timestamp)}
            </Subtitle>
          </AnalysisTitle>
        </HeaderLeft>
        
        <HeaderActions>
          <ActionButton onClick={handleExport}>
            <Download size={16} />
            Export
          </ActionButton>
          
          <ActionButton onClick={handleShare}>
            <Share2 size={16} />
            Share
          </ActionButton>
        </HeaderActions>
      </AnalysisHeader>
      
      <AnalysisResults analysis={analysis} />
    </AnalysisContainer>
  );
};

export default Analysis;