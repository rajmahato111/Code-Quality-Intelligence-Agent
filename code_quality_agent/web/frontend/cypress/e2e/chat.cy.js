describe('Chat Interface', () => {
  beforeEach(() => {
    cy.mockWebSocket();
    cy.visit('/chat');
  });

  it('displays chat interface elements', () => {
    cy.contains('Code Quality Assistant').should('be.visible');
    cy.contains('Ask questions about your code quality analysis').should('be.visible');
    cy.get('textarea[placeholder*="Ask about your code"]').should('be.visible');
  });

  it('shows empty state when no messages', () => {
    cy.contains('Start a conversation').should('be.visible');
    cy.contains('Ask me anything about your code quality analysis').should('be.visible');
  });

  it('allows typing and sending messages', () => {
    const testMessage = 'What are the security issues?';
    
    cy.get('textarea').type(testMessage);
    cy.get('button[type="submit"], button:contains("Send")').click();
    
    cy.contains(testMessage).should('be.visible');
  });

  it('sends message on Enter key press', () => {
    const testMessage = 'Show me performance issues';
    
    cy.get('textarea').type(testMessage);
    cy.get('textarea').type('{enter}');
    
    cy.contains(testMessage).should('be.visible');
  });

  it('shows suggested questions when no analysis is available', () => {
    cy.contains('What are the main security issues').should('be.visible');
    cy.contains('Which files have the highest complexity').should('be.visible');
    cy.contains('Show me performance bottlenecks').should('be.visible');
  });

  it('allows clicking on suggested questions', () => {
    cy.contains('What are the main security issues').click();
    cy.get('textarea').should('have.value', 'What are the main security issues in my code?');
  });
});

describe('Chat with Analysis Context', () => {
  const mockAnalysis = {
    id: 'test-analysis-1',
    path: '/test/sample-code',
    issues: [
      {
        id: 'issue-1',
        title: 'SQL Injection Vulnerability',
        category: 'SECURITY',
        severity: 'HIGH'
      }
    ]
  };

  beforeEach(() => {
    cy.mockWebSocket();
    
    // Set up analysis context
    cy.window().then((win) => {
      win.localStorage.setItem('currentAnalysis', JSON.stringify(mockAnalysis));
    });
    
    cy.visit('/chat');
  });

  it('shows different placeholder when analysis is available', () => {
    cy.get('textarea').should('have.attr', 'placeholder').and('include', 'Ask about your code analysis');
  });

  it('displays chat response from server', () => {
    const testMessage = 'What security issues were found?';
    const mockResponse = 'I found 1 security issue: SQL Injection Vulnerability in your code.';
    
    cy.get('textarea').type(testMessage);
    cy.get('button:contains("Send")').click();
    
    // Simulate WebSocket response
    cy.window().then((win) => {
      win.dispatchEvent(new CustomEvent('chat_response', {
        detail: {
          response: mockResponse,
          timestamp: new Date().toISOString()
        }
      }));
    });
    
    cy.contains(mockResponse).should('be.visible');
  });

  it('shows typing indicator while waiting for response', () => {
    cy.get('textarea').type('Test message');
    cy.get('button:contains("Send")').click();
    
    cy.contains('Thinking...').should('be.visible');
  });
});