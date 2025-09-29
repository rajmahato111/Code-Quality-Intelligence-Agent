import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import '@testing-library/jest-dom';
import Header from '../Header';

const renderWithRouter = (component) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('Header Component', () => {
  test('renders header with logo and navigation', () => {
    renderWithRouter(<Header />);
    
    expect(screen.getByText('Code Quality Intelligence')).toBeInTheDocument();
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Chat')).toBeInTheDocument();
  });
  
  test('logo links to home page', () => {
    renderWithRouter(<Header />);
    
    const logoLink = screen.getByText('Code Quality Intelligence').closest('a');
    expect(logoLink).toHaveAttribute('href', '/');
  });
  
  test('navigation links have correct hrefs', () => {
    renderWithRouter(<Header />);
    
    const dashboardLink = screen.getByText('Dashboard').closest('a');
    const chatLink = screen.getByText('Chat').closest('a');
    
    expect(dashboardLink).toHaveAttribute('href', '/');
    expect(chatLink).toHaveAttribute('href', '/chat');
  });
});