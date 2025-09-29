import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import AnalysisResults from '../AnalysisResults';

const mockAnalysis = {
  id: 'test-analysis',
  path: '/test/path',
  metrics: {
    overall_score: 75,
  },
  issues: [
    {
      id: 'issue-1',
      title: 'Security Issue',
      description: 'This is a security vulnerability that needs to be fixed.',
      category: 'SECURITY',
      severity: 'HIGH',
      location: {
        file_path: '/test/file.py',
        line_start: 10,
      },
      suggestion: 'Use parameterized queries to prevent SQL injection.',
    },
    {
      id: 'issue-2',
      title: 'Performance Issue',
      description: 'This code has performance implications.',
      category: 'PERFORMANCE',
      severity: 'MEDIUM',
      location: {
        file_path: '/test/file.py',
        line_start: 25,
      },
      suggestion: 'Consider using a more efficient algorithm.',
    },
  ],
};

describe('AnalysisResults Component', () => {
  test('renders analysis results with quality score', () => {
    render(<AnalysisResults analysis={mockAnalysis} />);
    
    expect(screen.getByText('75/100')).toBeInTheDocument();
    expect(screen.getByText('Overall Quality Score')).toBeInTheDocument();
  });
  
  test('displays issue metrics correctly', () => {
    render(<AnalysisResults analysis={mockAnalysis} />);
    
    expect(screen.getByText('1')).toBeInTheDocument(); // High priority count
    expect(screen.getByText('High Priority')).toBeInTheDocument();
    expect(screen.getByText('Medium Priority')).toBeInTheDocument();
  });
  
  test('shows issues in the list', () => {
    render(<AnalysisResults analysis={mockAnalysis} />);
    
    expect(screen.getByText('Security Issue')).toBeInTheDocument();
    expect(screen.getByText('Performance Issue')).toBeInTheDocument();
  });
  
  test('filters issues by category', () => {
    render(<AnalysisResults analysis={mockAnalysis} />);
    
    // Click on Security tab
    fireEvent.click(screen.getByText('Security'));
    
    expect(screen.getByText('Security Issue')).toBeInTheDocument();
    expect(screen.queryByText('Performance Issue')).not.toBeInTheDocument();
  });
  
  test('expands issue details when clicked', () => {
    render(<AnalysisResults analysis={mockAnalysis} />);
    
    // Click on the first issue
    fireEvent.click(screen.getByText('Security Issue'));
    
    expect(screen.getByText('Suggestion:')).toBeInTheDocument();
    expect(screen.getByText('Use parameterized queries to prevent SQL injection.')).toBeInTheDocument();
  });
  
  test('returns null when no analysis provided', () => {
    const { container } = render(<AnalysisResults analysis={null} />);
    expect(container.firstChild).toBeNull();
  });
});