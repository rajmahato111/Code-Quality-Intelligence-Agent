/// <reference types="vite/client" />
import axios, { AxiosResponse } from 'axios'
import toast from 'react-hot-toast'

// Types matching the backend models
export type AnalysisStatus = 'pending' | 'running' | 'completed' | 'failed'

export type SeverityLevel = 'critical' | 'high' | 'medium' | 'low' | 'info'

export interface AnalysisConfiguration {
  enable_security_analysis?: boolean
  enable_performance_analysis?: boolean
  enable_maintainability_analysis?: boolean
  enable_complexity_analysis?: boolean
  enable_duplication_analysis?: boolean
  enable_ai_explanations?: boolean
  enable_severity_scoring?: boolean
  severity_threshold?: SeverityLevel
  max_issues_per_file?: number
  timeout_seconds?: number
}

export interface RepositoryRequest {
  url: string
  branch?: string
  include_patterns?: string[]
  exclude_patterns?: string[]
  analysis_types?: string[]
  config?: AnalysisConfiguration
}

export interface IssueLocation {
  file_path: string
  line_number?: number
  column_number?: number
  function_name?: string
  class_name?: string
}

export interface Issue {
  id: string
  category: string
  type: string
  severity: SeverityLevel
  confidence: number
  title: string
  description: string
  explanation?: string
  location: IssueLocation
  code_snippet?: string
  suggestions?: string[]
  business_impact?: number
  priority_score?: number
  tags?: string[]
}

export interface AnalysisResult {
  job_id: string
  status: AnalysisStatus
  repository_url?: string
  branch?: string
  commit_hash?: string
  started_at: string
  completed_at?: string
  duration_seconds?: number
  issues: Issue[]
  summary: Record<string, any>
  metrics: Record<string, any>
  quality_score?: number  // Add quality_score field from API response
  error_message?: string
  error_details?: Record<string, any>
}

export interface AnalysisProgress {
  job_id: string
  status: AnalysisStatus
  progress_percentage: number
  current_step: string
  steps_completed: number
  total_steps: number
  files_processed: number
  total_files: number
  issues_found: number
  estimated_time_remaining?: number
  message?: string
}

export interface QuestionRequest {
  question: string
  job_id?: string
  file_path?: string
  issue_id?: string
  context?: Record<string, any>
}

export interface Answer {
  question: string
  answer: string
  confidence?: number | null
  sources?: string[]
  related_issues?: string[]
  suggestions?: string[]
  timestamp: string
}

export interface HealthCheck {
  status: string
  version: string
  timestamp: string
  components: Record<string, string>
}

// API client configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for auth
apiClient.interceptors.request.use((config) => {
  const apiKey = localStorage.getItem('api_key')
  if (apiKey) {
    config.headers.Authorization = `Bearer ${apiKey}`
  }
  return config
})

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('api_key')
      toast.error('Authentication failed. Please refresh and try again.')
    } else if (error.response?.status >= 500) {
      toast.error('Server error. Please try again later.')
    } else if (error.code === 'ECONNABORTED') {
      toast.error('Request timeout. Please try again.')
    }
    return Promise.reject(error)
  }
)

// API service functions
export const apiService = {
  // Health check
  async getHealth(): Promise<HealthCheck> {
    const response: AxiosResponse<HealthCheck> = await apiClient.get('/health')
    return response.data
  },

  // Authentication
  async createApiKey(userId?: string): Promise<{ api_key: string; user_id: string }> {
    const response = await apiClient.post('/auth/api-key', { user_id: userId })
    return response.data
  },

  async getDemoApiKey(): Promise<{ api_key: string; message: string }> {
    const response = await apiClient.get('/demo/api-key')
    return response.data
  },

  // Analysis
  async analyzeRepository(request: RepositoryRequest): Promise<AnalysisResult> {
    const response: AxiosResponse<AnalysisResult> = await apiClient.post('/analyze/repository', request)
    return response.data
  },

  async getAnalysisResult(jobId: string): Promise<AnalysisResult> {
    const response: AxiosResponse<AnalysisResult> = await apiClient.get(`/analyze/${jobId}`)
    return response.data
  },

  async getAnalysisProgress(jobId: string): Promise<AnalysisProgress> {
    const response: AxiosResponse<AnalysisProgress> = await apiClient.get(`/analyze/${jobId}/progress`)
    return response.data
  },

  // Q&A
  async askQuestion(request: QuestionRequest): Promise<Answer> {
    const response: AxiosResponse<Answer> = await apiClient.post('/qa/ask', request)
    return response.data
  },

  // Jobs management
  async listJobs(): Promise<{ jobs: Array<{ job_id: string; status: AnalysisStatus; started_at: string; repository_url?: string }> }> {
    const response = await apiClient.get('/jobs')
    return response.data
  },

  async cancelJob(jobId: string): Promise<{ message: string }> {
    const response = await apiClient.delete(`/jobs/${jobId}`)
    return response.data
  },

  // Test endpoints
  async testComponents(): Promise<{ components: Record<string, string>; overall_status: string }> {
    const response = await apiClient.get('/test/components')
    return response.data
  },
}

export default apiService