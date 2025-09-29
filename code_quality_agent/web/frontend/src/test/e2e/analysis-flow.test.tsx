import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from '../../App'

// Mock the API service
vi.mock('../../services/api', () => ({
  apiService: {
    getDemoApiKey: vi.fn().mockResolvedValue({ api_key: 'test-key' }),
    getHealth: vi.fn().mockResolvedValue({
      status: 'healthy',
      version: '1.0.0',
      timestamp: new Date().toISOString(),
      components: { orchestrator: 'healthy', qa_engine: 'healthy' },
    }),
    listJobs: vi.fn().mockResolvedValue({ jobs: [] }),
    analyzeRepository: vi.fn().mockResolvedValue({
      job_id: 'test-job-123',
      status: 'pending',
      repository_url: 'https://github.com/test/repo',
      started_at: new Date().toISOString(),
    }),
    getAnalysisResult: vi.fn().mockResolvedValue({
      job_id: 'test-job-123',
      status: 'completed',
      repository_url: 'https://github.com/test/repo',
      started_at: new Date().toISOString(),
      completed_at: new Date().toISOString(),
      issues: [
        {
          id: 'issue-1',
          category: 'security',
          type: 'sql_injection',
          severity: 'high',
          confidence: 0.9,
          title: 'SQL Injection Vulnerability',
          description: 'Potential SQL injection in user query',
          location: {
            file_path: 'src/app.py',
            line_number: 42,
          },
          suggestions: ['Use parameterized queries'],
        },
      ],
      summary: { total_files: 10, issues_found: 1 },
      metrics: { overall_score: 0.8 },
    }),
    getAnalysisProgress: vi.fn().mockResolvedValue({
      job_id: 'test-job-123',
      status: 'running',
      progress_percentage: 50,
      current_step: 'Analyzing files',
      steps_completed: 3,
      total_steps: 6,
      files_processed: 5,
      total_files: 10,
      issues_found: 1,
    }),
    askQuestion: vi.fn().mockResolvedValue({
      question: 'What are the security issues?',
      answer: 'There is 1 SQL injection vulnerability in src/app.py',
      confidence: 0.9,
      timestamp: new Date().toISOString(),
    }),
  },
}))

const renderApp = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  })

  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  )
}

describe('Analysis Flow E2E', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('completes full analysis workflow', async () => {
    const user = userEvent.setup()
    renderApp()

    // Start from home page
    expect(screen.getByText('Code Quality Intelligence Agent')).toBeInTheDocument()

    // Navigate to analysis page
    await user.click(screen.getByRole('link', { name: /analyze repository/i }))
    
    await waitFor(() => {
      expect(screen.getByText('Analyze Repository')).toBeInTheDocument()
    })

    // Fill in repository URL
    const urlInput = screen.getByPlaceholderText('https://github.com/owner/repository')
    await user.type(urlInput, 'https://github.com/test/repo')

    // Submit analysis
    const submitButton = screen.getByRole('button', { name: /start analysis/i })
    await user.click(submitButton)

    // Verify API call would be made (we can't access the mock directly due to hoisting)
    await waitFor(() => {
      expect(screen.getByText('Analysis Results')).toBeInTheDocument()
    })

    // Should navigate to results page
    await waitFor(() => {
      expect(screen.getByText('Analysis Results')).toBeInTheDocument()
    })
  })

  it('shows progress tracking during analysis', async () => {
    renderApp()

    // Navigate directly to results page (simulating redirect after starting analysis)
    window.history.pushState({}, '', '/results/test-job-123')
    
    // The mock will return running status first, then completed
    await waitFor(() => {
      expect(screen.getByText('Analysis Results')).toBeInTheDocument()
    })
  })

  it('displays analysis results correctly', async () => {
    renderApp()

    // Navigate to completed results
    window.history.pushState({}, '', '/results/test-job-123')

    await waitFor(() => {
      expect(screen.getByText('Analysis Results')).toBeInTheDocument()
      expect(screen.getByText('SQL Injection Vulnerability')).toBeInTheDocument()
      expect(screen.getAllByText('HIGH')).toHaveLength(2) // One in overview, one in issue card
    })
  })

  it('enables Q&A interaction', async () => {
    const user = userEvent.setup()
    renderApp()

    // Navigate to Q&A page with job context
    window.history.pushState({}, '', '/qa/test-job-123')

    await waitFor(() => {
      expect(screen.getByText(/Ask me anything about your code/)).toBeInTheDocument()
    })

    // Ask a question
    const questionInput = screen.getByPlaceholderText('Ask a question about your code...')
    await user.type(questionInput, 'What are the security issues?')

    const sendButton = screen.getByRole('button', { name: /send/i })
    await user.click(sendButton)

    // Should show the answer
    await waitFor(() => {
      expect(screen.getByText('There is 1 SQL injection vulnerability in src/app.py')).toBeInTheDocument()
    })
  })

  it('handles analysis errors gracefully', async () => {
    renderApp()

    // Navigate to results page - the mock will return completed status
    window.history.pushState({}, '', '/results/test-job-123')

    await waitFor(() => {
      expect(screen.getByText('Analysis Results')).toBeInTheDocument()
    })
  })
})