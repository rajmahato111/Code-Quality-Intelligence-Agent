import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Layout from '../Layout'

// Mock the API service
vi.mock('../../services/api', () => ({
  apiService: {
    getDemoApiKey: vi.fn().mockResolvedValue({ api_key: 'test-key' }),
    getHealth: vi.fn().mockResolvedValue({
      status: 'healthy',
      version: '1.0.0',
      timestamp: new Date().toISOString(),
      components: {
        orchestrator: 'healthy',
        qa_engine: 'healthy',
      },
    }),
  },
}))

const renderWithProviders = (children: React.ReactNode) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  })

  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </QueryClientProvider>
  )
}

describe('Layout', () => {
  it('renders the main navigation', () => {
    renderWithProviders(
      <Layout>
        <div>Test content</div>
      </Layout>
    )

    expect(screen.getByText('CodeQuality')).toBeInTheDocument()
    expect(screen.getByText('Home')).toBeInTheDocument()
    expect(screen.getByText('Analyze')).toBeInTheDocument()
    expect(screen.getByText('Q&A')).toBeInTheDocument()
  })

  it('renders children content', () => {
    renderWithProviders(
      <Layout>
        <div>Test content</div>
      </Layout>
    )

    expect(screen.getByText('Test content')).toBeInTheDocument()
  })

  it('displays AI-powered tagline', () => {
    renderWithProviders(
      <Layout>
        <div>Test content</div>
      </Layout>
    )

    expect(screen.getByText('AI-Powered Code Analysis')).toBeInTheDocument()
  })
})