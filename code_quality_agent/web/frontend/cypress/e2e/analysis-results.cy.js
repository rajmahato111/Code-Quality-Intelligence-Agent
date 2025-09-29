describe('Analysis Results', () => {
  const mockAnalysis = {
    id: 'test-analysis-1',
    path: '/test/sample-code',
    metrics: {
      overall_score: 75
    },
    issues: [
      {
        id: 'issue-1',
        title: 'Hardcoded Password',
        description: 'Found hardcoded password in source code. This is a security risk.',
        category: 'SECURITY',
        severity: 'HIGH',
        location: {
          file_path: '/test/app.py',
          line_start: 15
        },
        suggestion: 'Move password to environment variables.'
      },
      {
        id: 'issue-2',
        title: 'High Complexity Function',
        description: 'Function has high cyclomatic complexity.',
        category: 'COMPLEXITY',
        severity: 'MEDIUM',
        location: {
          file_path: '/test/utils.py',
          line_start: 42
        },
        suggestion: 'Break down into smaller functions.'
      },
      {
        id: 'issue-3',
        title: 'Missing Docstring',
        description: 'Function is missing documentation.',
        category: 'DOCUMENTATION',
        severity: 'LOW',
        location: {
          file_path: '/test/helpers.py',
          line_start: 8
        },
        suggestion: 'Add docstring to explain function purpose.'
      }
    ]
  };

  beforeEach(() => {
    cy.mockWebSocket();
    cy.mockAnalysisData(mockAnalysis);
  });

  it('displays quality score and metrics', () => {
    cy.visit('/');
    
    // Simulate analysis completion
    cy.window().then((win) => {
      win.postMessage({
        type: 'ANALYSIS_COMPLETE',
        payload: { result: mockAnalysis }
      }, '*');
    });

    cy.contains('75/100').should('be.visible');
    cy.contains('Overall Quality Score').should('be.visible');
    
    // Check metric cards
    cy.contains('1').should('be.visible'); // High priority count
    cy.contains('High Priority').should('be.visible');
    cy.contains('Medium Priority').should('be.visible');
    cy.contains('Low Priority').should('be.visible');
  });

  it('shows issues grouped by category', () => {
    cy.visit('/');
    
    cy.window().then((win) => {
      win.postMessage({
        type: 'ANALYSIS_COMPLETE',
        payload: { result: mockAnalysis }
      }, '*');
    });

    // Check category tabs
    cy.contains('All Issues').should('be.visible');
    cy.contains('Security').should('be.visible');
    cy.contains('Complexity').should('be.visible');
    cy.contains('Documentation').should('be.visible');
    
    // Check issues are displayed
    cy.contains('Hardcoded Password').should('be.visible');
    cy.contains('High Complexity Function').should('be.visible');
    cy.contains('Missing Docstring').should('be.visible');
  });

  it('filters issues by category when tab is clicked', () => {
    cy.visit('/');
    
    cy.window().then((win) => {
      win.postMessage({
        type: 'ANALYSIS_COMPLETE',
        payload: { result: mockAnalysis }
      }, '*');
    });

    // Click Security tab
    cy.contains('Security').click();
    
    // Should show only security issues
    cy.contains('Hardcoded Password').should('be.visible');
    cy.contains('High Complexity Function').should('not.exist');
    cy.contains('Missing Docstring').should('not.exist');
  });

  it('expands issue details when clicked', () => {
    cy.visit('/');
    
    cy.window().then((win) => {
      win.postMessage({
        type: 'ANALYSIS_COMPLETE',
        payload: { result: mockAnalysis }
      }, '*');
    });

    // Click on first issue
    cy.contains('Hardcoded Password').click();
    
    // Should show suggestion
    cy.contains('Suggestion:').should('be.visible');
    cy.contains('Move password to environment variables').should('be.visible');
  });

  it('displays charts for issue distribution', () => {
    cy.visit('/');
    
    cy.window().then((win) => {
      win.postMessage({
        type: 'ANALYSIS_COMPLETE',
        payload: { result: mockAnalysis }
      }, '*');
    });

    cy.contains('Issues by Severity').should('be.visible');
    cy.contains('Issues by Category').should('be.visible');
  });
});

describe('Analysis Page', () => {
  const mockAnalysis = {
    id: 'test-analysis-1',
    path: '/test/sample-code',
    metrics: { overall_score: 85 },
    issues: [],
    timestamp: new Date().toISOString()
  };

  beforeEach(() => {
    cy.mockWebSocket();
    cy.mockAnalysisData(mockAnalysis);
  });

  it('displays analysis page with correct information', () => {
    cy.visit('/analysis/test-analysis-1');
    
    cy.contains('Analysis Results').should('be.visible');
    cy.contains('/test/sample-code').should('be.visible');
    cy.contains('Back to Dashboard').should('be.visible');
  });

  it('allows exporting analysis results', () => {
    cy.visit('/analysis/test-analysis-1');
    
    cy.contains('Export').should('be.visible').click();
    
    // Note: In a real test, you might check for file download
    // This is a simplified test
  });

  it('allows sharing analysis results', () => {
    cy.visit('/analysis/test-analysis-1');
    
    cy.contains('Share').should('be.visible').click();
    
    // Note: In a real test, you might check clipboard or share API
  });

  it('navigates back to dashboard', () => {
    cy.visit('/analysis/test-analysis-1');
    
    cy.contains('Back to Dashboard').click();
    cy.url().should('eq', Cypress.config().baseUrl + '/');
  });
});