import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import HomePage from '../HomePage'

// Mock the API service
vi.mock('../../services/api', () => ({
  apiService: {
    listJobs: vi.fn().mockResolvedValue({
      jobs: [
        {
          job_id: 'job-1',
          status: 'completed',
          started_at: new Date().toISOString(),
          repository_url: 'https://github.com/test/repo',
        },
        {
          job_id: 'job-2',
          status: 'running',
          started_at: new Date().toISOString(),
          repository_url: 'https://github.com/test/another-repo',
        },
      ],
    }),
    getHealth: vi.fn().mockResolvedValue({
      status: 'healthy',
      version: '1.0.0',
      timestamp: new Date().toISOString(),
      components: {
        orchestrator: 'healthy',
        qa_engine: 'healthy',
        scoring_engine: 'healthy',
      },
    }),
  },
}))

const renderWithProviders = (component: React.ReactNode) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  })

  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {component}
      </BrowserRouter>
    </QueryClientProvider>
  )
}

describe('HomePage', () => {
  it('renders the main heading', () => {
    renderWithProviders(<HomePage />)

    expect(screen.getByText('Code Quality Intelligence Agent')).toBeInTheDocument()
  })

  it('displays feature cards', () => {
    renderWithProviders(<HomePage />)

    expect(screen.getByText('Security Analysis')).toBeInTheDocument()
    expect(screen.getByText('Performance Insights')).toBeInTheDocument()
    expect(screen.getByText('Code Metrics')).toBeInTheDocument()
    expect(screen.getByText('AI Q&A')).toBeInTheDocument()
  })

  it('shows analyze and Q&A buttons', () => {
    renderWithProviders(<HomePage />)

    expect(screen.getByRole('link', { name: /analyze repository/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /ask questions/i })).toBeInTheDocument()
  })

  it('displays recent analyses section', () => {
    renderWithProviders(<HomePage />)

    expect(screen.getByText('Recent Analyses')).toBeInTheDocument()
  })

  it('displays system status section', () => {
    renderWithProviders(<HomePage />)

    expect(screen.getByText('System Status')).toBeInTheDocument()
  })

  it('shows quick start guide', () => {
    renderWithProviders(<HomePage />)

    expect(screen.getByText('Quick Start Guide')).toBeInTheDocument()
    expect(screen.getAllByText('Analyze Repository')).toHaveLength(2) // Button and guide step
    expect(screen.getByText('Review Results')).toBeInTheDocument()
    expect(screen.getAllByText('Ask Questions')).toHaveLength(2) // Button and guide step
  })
})