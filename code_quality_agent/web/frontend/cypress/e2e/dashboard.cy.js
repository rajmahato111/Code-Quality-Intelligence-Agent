describe('Dashboard', () => {
  beforeEach(() => {
    cy.mockWebSocket();
    cy.visit('/');
  });

  it('displays the main dashboard elements', () => {
    cy.contains('Code Quality Intelligence').should('be.visible');
    cy.contains('AI-powered code analysis').should('be.visible');
    cy.contains('Start New Analysis').should('be.visible');
  });

  it('shows analysis input options', () => {
    cy.contains('Local Path').should('be.visible');
    cy.contains('GitHub Repository').should('be.visible');
    cy.contains('Upload Files').should('be.visible');
  });

  it('allows selecting different input types', () => {
    // Test local path selection
    cy.contains('Local Path').click();
    cy.get('input[placeholder*="path/to/your/code"]').should('be.visible');

    // Test GitHub repository selection
    cy.contains('GitHub Repository').click();
    cy.get('input[placeholder*="github.com"]').should('be.visible');

    // Test file upload selection
    cy.contains('Upload Files').click();
    cy.get('input[type="file"]').should('be.visible');
  });

  it('enables analyze button when path is entered', () => {
    cy.contains('Local Path').click();
    cy.get('input[placeholder*="path/to/your/code"]').type('/test/path');
    cy.contains('Analyze').should('not.be.disabled');
  });

  it('shows recent analyses section', () => {
    cy.contains('Recent Analyses').should('be.visible');
  });
});

describe('Dashboard with Analysis', () => {
  const mockAnalysis = {
    id: 'test-analysis-1',
    path: '/test/sample-code',
    metrics: { overall_score: 85 },
    issues: [
      {
        id: 'issue-1',
        title: 'Test Security Issue',
        category: 'SECURITY',
        severity: 'HIGH',
        description: 'Test description',
        location: { file_path: '/test/file.py', line_start: 10 }
      }
    ],
    timestamp: new Date().toISOString()
  };

  beforeEach(() => {
    cy.mockWebSocket();
    cy.mockAnalysisData(mockAnalysis);
  });

  it('displays analysis results after completion', () => {
    cy.visit('/');
    
    // Simulate analysis completion by directly updating the context
    cy.window().then((win) => {
      // This would normally be handled by WebSocket events
      win.postMessage({
        type: 'ANALYSIS_COMPLETE',
        payload: { result: mockAnalysis }
      }, '*');
    });

    cy.contains('85/100').should('be.visible');
    cy.contains('Overall Quality Score').should('be.visible');
  });
});