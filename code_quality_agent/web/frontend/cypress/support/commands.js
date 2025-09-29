// ***********************************************
// This example commands.js shows you how to
// create various custom commands and overwrite
// existing commands.
//
// For more comprehensive examples of custom
// commands please read more here:
// https://on.cypress.io/custom-commands
// ***********************************************

// Custom command to mock WebSocket connection
Cypress.Commands.add('mockWebSocket', () => {
  cy.window().then((win) => {
    // Mock socket.io client
    win.io = () => ({
      on: cy.stub(),
      emit: cy.stub(),
      close: cy.stub(),
    });
  });
});

// Custom command to mock analysis data
Cypress.Commands.add('mockAnalysisData', (analysisData) => {
  cy.intercept('GET', '/api/analysis/*', {
    statusCode: 200,
    body: analysisData,
  }).as('getAnalysis');
});

// Custom command to start analysis
Cypress.Commands.add('startAnalysis', (path) => {
  cy.get('[data-testid="path-input"]').type(path);
  cy.get('[data-testid="analyze-button"]').click();
});

// Custom command to wait for analysis completion
Cypress.Commands.add('waitForAnalysisComplete', () => {
  cy.get('[data-testid="progress-tracker"]', { timeout: 10000 }).should('not.exist');
  cy.get('[data-testid="analysis-results"]').should('be.visible');
});