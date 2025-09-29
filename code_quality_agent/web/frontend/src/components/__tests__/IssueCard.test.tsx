import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import IssueCard from '../IssueCard'
import { Issue } from '../../services/api'

describe('IssueCard', () => {
  const mockIssue: Issue = {
    id: 'test-issue-1',
    category: 'security',
    type: 'sql_injection',
    severity: 'high',
    confidence: 0.85,
    title: 'Potential SQL Injection Vulnerability',
    description: 'User input is directly concatenated into SQL query without proper sanitization.',
    explanation: 'This code is vulnerable to SQL injection attacks because user input is not properly escaped.',
    location: {
      file_path: 'src/database/queries.py',
      line_number: 42,
      function_name: 'get_user_data',
    },
    code_snippet: 'query = "SELECT * FROM users WHERE id = " + user_id',
    suggestions: [
      'Use parameterized queries or prepared statements',
      'Validate and sanitize user input',
    ],
    business_impact: 0.9,
    priority_score: 0.8,
    tags: ['owasp-top-10', 'database'],
  }

  it('renders issue information correctly', () => {
    render(<IssueCard issue={mockIssue} />)

    expect(screen.getByText('Potential SQL Injection Vulnerability')).toBeInTheDocument()
    expect(screen.getByText(/User input is directly concatenated/)).toBeInTheDocument()
    expect(screen.getByText('HIGH')).toBeInTheDocument()
    expect(screen.getByText('security')).toBeInTheDocument()
  })

  it('displays location information', () => {
    render(<IssueCard issue={mockIssue} />)

    expect(screen.getByText('queries.py')).toBeInTheDocument()
    expect(screen.getByText(':42')).toBeInTheDocument()
    expect(screen.getByText('get_user_data')).toBeInTheDocument()
  })

  it('shows confidence percentage', () => {
    render(<IssueCard issue={mockIssue} />)

    expect(screen.getByText('85%')).toBeInTheDocument()
  })

  it('displays tags', () => {
    render(<IssueCard issue={mockIssue} />)

    expect(screen.getByText('owasp-top-10')).toBeInTheDocument()
    expect(screen.getByText('database')).toBeInTheDocument()
  })

  it('shows business impact and priority scores', () => {
    render(<IssueCard issue={mockIssue} />)

    expect(screen.getByText('Business Impact: 90%')).toBeInTheDocument()
    expect(screen.getByText('Priority: 80%')).toBeInTheDocument()
  })

  it('displays quick fix suggestion', () => {
    render(<IssueCard issue={mockIssue} />)

    expect(screen.getByText('Quick Fix:')).toBeInTheDocument()
    expect(screen.getByText('Use parameterized queries or prepared statements')).toBeInTheDocument()
    expect(screen.getByText('+1 more suggestions')).toBeInTheDocument()
  })

  it('calls onClick when clicked', () => {
    const handleClick = vi.fn()
    render(<IssueCard issue={mockIssue} onClick={handleClick} />)

    const card = screen.getByText('Potential SQL Injection Vulnerability').closest('.card')
    fireEvent.click(card!)
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('shows selected state', () => {
    render(<IssueCard issue={mockIssue} isSelected={true} />)

    // Find the outermost card div
    const card = screen.getByText('Potential SQL Injection Vulnerability').closest('.card')
    expect(card).toHaveClass('ring-2', 'ring-primary-500')
  })

  it('handles different severity levels', () => {
    const criticalIssue = { ...mockIssue, severity: 'critical' as const }
    render(<IssueCard issue={criticalIssue} />)

    expect(screen.getByText('CRITICAL')).toBeInTheDocument()
  })

  it('handles different categories', () => {
    const performanceIssue = { ...mockIssue, category: 'performance' }
    render(<IssueCard issue={performanceIssue} />)

    expect(screen.getByText('performance')).toBeInTheDocument()
  })
})