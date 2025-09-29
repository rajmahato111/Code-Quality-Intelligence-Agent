import React, { useState } from 'react';
import styled from 'styled-components';
import { 
  Shield, 
  Zap, 
  Code, 
  FileText, 
  TestTube, 
  Copy,
  ChevronDown,
  ChevronRight,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Info
} from 'lucide-react';
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement } from 'chart.js';
import { Doughnut, Bar } from 'react-chartjs-2';

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement);

const ResultsContainer = styled.div`
  background: white;
  border-radius: 1rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  margin-bottom: 2rem;
`;

const ResultsHeader = styled.div`
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 2rem;
  text-align: center;
`;

const QualityScore = styled.div`
  font-size: 3rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
`;

const ScoreLabel = styled.div`
  font-size: 1.125rem;
  opacity: 0.9;
`;

const MetricsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  padding: 2rem;
`;

const MetricCard = styled.div`
  text-align: center;
  padding: 1.5rem;
  border-radius: 0.75rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
`;

const MetricIcon = styled.div`
  width: 48px;
  height: 48px;
  border-radius: 50%;
  margin: 0 auto 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: ${props => props.$color || '#667eea'};
  color: white;
`;

const MetricValue = styled.div`
  font-size: 2rem;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 0.25rem;
`;

const MetricLabel = styled.div`
  color: #64748b;
  font-weight: 500;
`;

const ChartsSection = styled.div`
  padding: 2rem;
  border-top: 1px solid #e2e8f0;
`;

const ChartsGrid = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
`;

const ChartContainer = styled.div`
  background: #f8fafc;
  border-radius: 0.75rem;
  padding: 1.5rem;
`;

const ChartTitle = styled.h3`
  font-size: 1.125rem;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 1rem;
  text-align: center;
`;

const IssuesSection = styled.div`
  border-top: 1px solid #e2e8f0;
`;

const CategoryTabs = styled.div`
  display: flex;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
`;

const CategoryTab = styled.button`
  flex: 1;
  padding: 1rem 1.5rem;
  border: none;
  background: none;
  font-weight: 500;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s ease;
  border-bottom: 2px solid transparent;
  
  ${props => props.$active && `
    color: #667eea;
    border-bottom-color: #667eea;
    background: white;
  `}
  
  &:hover {
    color: #667eea;
  }
`;

const IssuesList = styled.div`
  max-height: 600px;
  overflow-y: auto;
`;

const IssueItem = styled.div`
  padding: 1.5rem;
  border-bottom: 1px solid #f1f5f9;
  
  &:last-child {
    border-bottom: none;
  }
`;

const IssueHeader = styled.div`
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  cursor: pointer;
`;

const IssueIcon = styled.div`
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 0.25rem;
  
  ${props => {
    switch (props.$severity) {
      case 'HIGH':
        return 'background: #ef4444; color: white;';
      case 'MEDIUM':
        return 'background: #f59e0b; color: white;';
      case 'LOW':
        return 'background: #3b82f6; color: white;';
      default:
        return 'background: #6b7280; color: white;';
    }
  }}
`;

const IssueContent = styled.div`
  flex: 1;
`;

const IssueTitle = styled.h4`
  font-size: 1rem;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 0.5rem;
`;

const IssueLocation = styled.div`
  font-size: 0.875rem;
  color: #64748b;
  margin-bottom: 0.5rem;
`;

const IssueDescription = styled.div`
  font-size: 0.875rem;
  color: #374151;
  line-height: 1.5;
  
  ${props => !props.$expanded && `
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  `}
`;

const IssueSuggestion = styled.div`
  margin-top: 1rem;
  padding: 1rem;
  background: #f0f9ff;
  border-radius: 0.5rem;
  border-left: 4px solid #0ea5e9;
  font-size: 0.875rem;
  color: #0c4a6e;
`;

const ExpandButton = styled.button`
  background: none;
  border: none;
  color: #667eea;
  cursor: pointer;
  font-size: 0.875rem;
  margin-top: 0.5rem;
  
  &:hover {
    text-decoration: underline;
  }
`;

const AnalysisResults = ({ analysis }) => {
  const [activeCategory, setActiveCategory] = useState('all');
  const [expandedIssues, setExpandedIssues] = useState(new Set());
  
  if (!analysis || !analysis.issues) {
    return null;
  }
  
  const { issues, metrics } = analysis;
  
  // Group issues by category
  const issuesByCategory = issues.reduce((acc, issue) => {
    const category = issue.category || 'OTHER';
    if (!acc[category]) acc[category] = [];
    acc[category].push(issue);
    return acc;
  }, {});
  
  // Calculate metrics
  const totalIssues = issues.length;
  const severityCounts = issues.reduce((acc, issue) => {
    acc[issue.severity] = (acc[issue.severity] || 0) + 1;
    return acc;
  }, {});
  
  const categoryCounts = Object.entries(issuesByCategory).map(([category, categoryIssues]) => ({
    category,
    count: categoryIssues.length,
  }));
  
  // Chart data
  const severityChartData = {
    labels: ['High', 'Medium', 'Low'],
    datasets: [{
      data: [
        severityCounts.HIGH || 0,
        severityCounts.MEDIUM || 0,
        severityCounts.LOW || 0,
      ],
      backgroundColor: ['#ef4444', '#f59e0b', '#3b82f6'],
      borderWidth: 0,
    }],
  };
  
  const categoryChartData = {
    labels: categoryCounts.map(c => c.category),
    datasets: [{
      label: 'Issues',
      data: categoryCounts.map(c => c.count),
      backgroundColor: '#667eea',
      borderRadius: 4,
    }],
  };
  
  const categories = [
    { id: 'all', label: 'All Issues', icon: <Code size={16} /> },
    { id: 'SECURITY', label: 'Security', icon: <Shield size={16} /> },
    { id: 'PERFORMANCE', label: 'Performance', icon: <Zap size={16} /> },
    { id: 'COMPLEXITY', label: 'Complexity', icon: <Code size={16} /> },
    { id: 'TESTING', label: 'Testing', icon: <TestTube size={16} /> },
    { id: 'DOCUMENTATION', label: 'Documentation', icon: <FileText size={16} /> },
    { id: 'DUPLICATION', label: 'Duplication', icon: <Copy size={16} /> },
  ];
  
  const getFilteredIssues = () => {
    if (activeCategory === 'all') return issues;
    return issuesByCategory[activeCategory] || [];
  };
  
  const toggleIssueExpansion = (issueId) => {
    const newExpanded = new Set(expandedIssues);
    if (newExpanded.has(issueId)) {
      newExpanded.delete(issueId);
    } else {
      newExpanded.add(issueId);
    }
    setExpandedIssues(newExpanded);
  };
  
  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'HIGH': return <XCircle size={14} />;
      case 'MEDIUM': return <AlertTriangle size={14} />;
      case 'LOW': return <Info size={14} />;
      default: return <CheckCircle size={14} />;
    }
  };
  
  return (
    <ResultsContainer>
      <ResultsHeader>
        <QualityScore>{metrics?.overall_score || 0}/100</QualityScore>
        <ScoreLabel>Overall Quality Score</ScoreLabel>
      </ResultsHeader>
      
      <MetricsGrid>
        <MetricCard>
          <MetricIcon $color="#ef4444">
            <XCircle size={24} />
          </MetricIcon>
          <MetricValue>{severityCounts.HIGH || 0}</MetricValue>
          <MetricLabel>High Priority</MetricLabel>
        </MetricCard>
        
        <MetricCard>
          <MetricIcon $color="#f59e0b">
            <AlertTriangle size={24} />
          </MetricIcon>
          <MetricValue>{severityCounts.MEDIUM || 0}</MetricValue>
          <MetricLabel>Medium Priority</MetricLabel>
        </MetricCard>
        
        <MetricCard>
          <MetricIcon $color="#3b82f6">
            <Info size={24} />
          </MetricIcon>
          <MetricValue>{severityCounts.LOW || 0}</MetricValue>
          <MetricLabel>Low Priority</MetricLabel>
        </MetricCard>
        
        <MetricCard>
          <MetricIcon $color="#10b981">
            <CheckCircle size={24} />
          </MetricIcon>
          <MetricValue>{totalIssues}</MetricValue>
          <MetricLabel>Total Issues</MetricLabel>
        </MetricCard>
      </MetricsGrid>
      
      <ChartsSection>
        <ChartsGrid>
          <ChartContainer>
            <ChartTitle>Issues by Severity</ChartTitle>
            <Doughnut 
              data={severityChartData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: {
                    position: 'bottom',
                  },
                },
              }}
              height={200}
            />
          </ChartContainer>
          
          <ChartContainer>
            <ChartTitle>Issues by Category</ChartTitle>
            <Bar 
              data={categoryChartData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: {
                    display: false,
                  },
                },
                scales: {
                  y: {
                    beginAtZero: true,
                    ticks: {
                      stepSize: 1,
                    },
                  },
                },
              }}
              height={200}
            />
          </ChartContainer>
        </ChartsGrid>
      </ChartsSection>
      
      <IssuesSection>
        <CategoryTabs>
          {categories.map((category) => (
            <CategoryTab
              key={category.id}
              $active={activeCategory === category.id}
              onClick={() => setActiveCategory(category.id)}
            >
              {category.icon}
              {category.label}
              {category.id !== 'all' && issuesByCategory[category.id] && 
                ` (${issuesByCategory[category.id].length})`
              }
            </CategoryTab>
          ))}
        </CategoryTabs>
        
        <IssuesList>
          {getFilteredIssues().map((issue) => {
            const isExpanded = expandedIssues.has(issue.id);
            
            return (
              <IssueItem key={issue.id}>
                <IssueHeader onClick={() => toggleIssueExpansion(issue.id)}>
                  <IssueIcon $severity={issue.severity}>
                    {getSeverityIcon(issue.severity)}
                  </IssueIcon>
                  <IssueContent>
                    <IssueTitle>{issue.title}</IssueTitle>
                    <IssueLocation>
                      {issue.location?.file_path}:{issue.location?.line_start}
                    </IssueLocation>
                    <IssueDescription $expanded={isExpanded}>
                      {issue.description}
                    </IssueDescription>
                    {!isExpanded && issue.description.length > 100 && (
                      <ExpandButton onClick={(e) => {
                        e.stopPropagation();
                        toggleIssueExpansion(issue.id);
                      }}>
                        Show more
                      </ExpandButton>
                    )}
                    {isExpanded && issue.suggestion && (
                      <IssueSuggestion>
                        <strong>Suggestion:</strong> {issue.suggestion}
                      </IssueSuggestion>
                    )}
                  </IssueContent>
                  {isExpanded ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
                </IssueHeader>
              </IssueItem>
            );
          })}
        </IssuesList>
      </IssuesSection>
    </ResultsContainer>
  );
};

export default AnalysisResults;