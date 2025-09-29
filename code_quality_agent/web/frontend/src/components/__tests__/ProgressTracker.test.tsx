import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import ProgressTracker from '../ProgressTracker'
import { AnalysisProgress } from '../../services/api'

describe('ProgressTracker', () => {
  const mockProgress: AnalysisProgress = {
    job_id: 'test-job',
    status: 'running',
    progress_percentage: 45.5,
    current_step: 'Analyzing security issues',
    steps_completed: 3,
    total_steps: 7,
    files_processed: 15,
    total_files: 30,
    issues_found: 8,
    estimated_time_remaining: 120,
    message: 'Processing Python files...',
  }

  it('renders progress information correctly', () => {
    render(<ProgressTracker progress={mockProgress} />)

    expect(screen.getByText('Analysis Progress')).toBeInTheDocument()
    expect(screen.getByText('Analyzing security issues')).toBeInTheDocument()
    expect(screen.getByText('46%')).toBeInTheDocument() // Rounded percentage
  })

  it('displays step progress', () => {
    render(<ProgressTracker progress={mockProgress} />)

    expect(screen.getByText('3/7')).toBeInTheDocument()
    expect(screen.getByText('Steps')).toBeInTheDocument()
  })

  it('displays file progress', () => {
    render(<ProgressTracker progress={mockProgress} />)

    expect(screen.getByText('15/30')).toBeInTheDocument()
    expect(screen.getByText('Files')).toBeInTheDocument()
  })

  it('displays issues found', () => {
    render(<ProgressTracker progress={mockProgress} />)

    expect(screen.getByText('8')).toBeInTheDocument()
    expect(screen.getByText('Issues Found')).toBeInTheDocument()
  })

  it('displays estimated time remaining', () => {
    render(<ProgressTracker progress={mockProgress} />)

    expect(screen.getByText('2m 0s')).toBeInTheDocument()
    expect(screen.getByText('Remaining')).toBeInTheDocument()
  })

  it('displays status message', () => {
    render(<ProgressTracker progress={mockProgress} />)

    expect(screen.getByText('Processing Python files...')).toBeInTheDocument()
  })

  it('shows completed status correctly', () => {
    const completedProgress: AnalysisProgress = {
      ...mockProgress,
      status: 'completed',
      progress_percentage: 100,
      current_step: 'Analysis complete',
    }

    render(<ProgressTracker progress={completedProgress} />)

    expect(screen.getByText('100%')).toBeInTheDocument()
    expect(screen.getByText('Analysis complete')).toBeInTheDocument()
  })

  it('shows failed status correctly', () => {
    const failedProgress: AnalysisProgress = {
      ...mockProgress,
      status: 'failed',
      current_step: 'Analysis failed',
    }

    render(<ProgressTracker progress={failedProgress} />)

    expect(screen.getByText('Analysis failed')).toBeInTheDocument()
  })
})