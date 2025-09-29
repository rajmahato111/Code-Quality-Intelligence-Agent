import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import styled from 'styled-components';
import { Activity, MessageSquare, BarChart3 } from 'lucide-react';

const HeaderContainer = styled.header`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid #e2e8f0;
  padding: 0 2rem;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: space-between;
`;

const Logo = styled(Link)`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  text-decoration: none;
  color: #1e293b;
  font-weight: 700;
  font-size: 1.25rem;
  
  &:hover {
    color: #667eea;
  }
`;

const Nav = styled.nav`
  display: flex;
  gap: 2rem;
`;

const NavLink = styled(Link)`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  text-decoration: none;
  color: #64748b;
  font-weight: 500;
  transition: all 0.2s ease;
  
  ${props => props.$active && `
    background: #667eea;
    color: white;
  `}
  
  &:hover {
    background: ${props => props.$active ? '#5a67d8' : '#f1f5f9'};
    color: ${props => props.$active ? 'white' : '#1e293b'};
  }
`;

const Header = () => {
  const location = useLocation();
  
  return (
    <HeaderContainer>
      <Logo to="/">
        <Activity size={28} />
        Code Quality Intelligence
      </Logo>
      
      <Nav>
        <NavLink 
          to="/" 
          $active={location.pathname === '/'}
        >
          <BarChart3 size={18} />
          Dashboard
        </NavLink>
        
        <NavLink 
          to="/chat" 
          $active={location.pathname === '/chat'}
        >
          <MessageSquare size={18} />
          Chat
        </NavLink>
      </Nav>
    </HeaderContainer>
  );
};

export default Header;