import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import ProgressTracker from '../ProgressTracker';
import { AnalysisProvider } from '../../contexts/AnalysisContext';

const renderWithProvider = (component, initialState = {}) => {
  return render(
    <AnalysisProvider>
      {component}
    </AnalysisProvider>
  );
};

// Mock the useAnalysis hook
jest.mock('../../contexts/AnalysisContext', () => ({
  ...jest.requireActual('../../contexts/AnalysisContext'),
  useAnalysis: () => ({
    progress: 45,
    currentAnalysis: { path: '/test/path' },
    isAnalyzing: true,
  }),
}));

describe('ProgressTracker Component', () => {
  test('renders progress tracker when analyzing', () => {
    render(<ProgressTracker />);
    
    expect(screen.getByText('Analyzing Code Quality')).toBeInTheDocument();
    expect(screen.getByText('45% Complete')).toBeInTheDocument();
  });
  
  test('displays current analysis path', () => {
    render(<ProgressTracker />);
    
    expect(screen.getByText('Analyzing: /test/path')).toBeInTheDocument();
  });
  
  test('shows analysis stages', () => {
    render(<ProgressTracker />);
    
    expect(screen.getByText('File Discovery')).toBeInTheDocument();
    expect(screen.getByText('Code Parsing')).toBeInTheDocument();
    expect(screen.getByText('Security Analysis')).toBeInTheDocument();
    expect(screen.getByText('Report Generation')).toBeInTheDocument();
  });
});