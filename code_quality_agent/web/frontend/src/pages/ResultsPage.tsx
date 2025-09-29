import React, { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { 
  ArrowLeft, 
  Download, 
  MessageSquare, 
  AlertTriangle, 
  CheckCircle, 
  Clock,
  FileText,
  BarChart3,
  Shield,
  Zap,
  Code,
  Eye,
  Filter,
  Search
} from 'lucide-react'
import { apiService, Issue, AnalysisResult } from '../services/api'
import ProgressTracker from '../components/ProgressTracker'
import IssueCard from '../components/IssueCard'
import MetricsOverview from '../components/MetricsOverview'
import CodeSnippet from '../components/CodeSnippet'

const ResultsPage: React.FC = () => {
  const { jobId } = useParams<{ jobId: string }>()
  const [selectedSeverity, setSelectedSeverity] = useState<string>('all')
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedIssue, setSelectedIssue] = useState<Issue | null>(null)

  // Fetch analysis result with polling for incomplete jobs
  const { data: result, isLoading, error } = useQuery({
    queryKey: ['analysis', jobId],
    queryFn: () => apiService.getAnalysisResult(jobId!),
    enabled: !!jobId,
    refetchInterval: (data) => {
      // Poll every 2 seconds if analysis is still running
      return data?.status === 'running' || data?.status === 'pending' ? 2000 : false
    },
  })

  // Fetch progress for running analyses
  const { data: progress } = useQuery({
    queryKey: ['progress', jobId],
    queryFn: () => apiService.getAnalysisProgress(jobId!),
    enabled: !!jobId && (result?.status === 'running' || result?.status === 'pending'),
    refetchInterval: 1000, // Poll every second for progress
  })

  const isAnalysisComplete = result?.status === 'completed'
  const isAnalysisFailed = result?.status === 'failed'
  const isAnalysisRunning = result?.status === 'running' || result?.status === 'pending'

  // Filter issues based on selected filters
  const filteredIssues = result?.issues?.filter((issue) => {
    const matchesSeverity = selectedSeverity === 'all' || issue.severity === selectedSeverity
    const matchesCategory = selectedCategory === 'all' || issue.category === selectedCategory
    const matchesSearch = searchTerm === '' || 
      issue.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      issue.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      issue.location.file_path.toLowerCase().includes(searchTerm.toLowerCase())
    
    return matchesSeverity && matchesCategory && matchesSearch
  }) || []

  // Get unique categories and severities for filters
  const categories = [...new Set(result?.issues?.map(issue => issue.category) || [])]
  const severities = [...new Set(result?.issues?.map(issue => issue.severity) || [])]

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'text-red-600 bg-red-100'
      case 'high': return 'text-orange-600 bg-orange-100'
      case 'medium': return 'text-yellow-600 bg-yellow-100'
      case 'low': return 'text-green-600 bg-green-100'
      case 'info': return 'text-blue-600 bg-blue-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  const getCategoryIcon = (category: string) => {
    switch (category.toLowerCase()) {
      case 'security': return Shield
      case 'performance': return Zap
      case 'complexity': return BarChart3
      case 'documentation': return FileText
      default: return Code
    }
  }

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center">
          <div className="loading-spinner h-12 w-12 mx-auto mb-4" />
          <p className="text-gray-600">Loading analysis results...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center">
          <AlertTriangle className="h-12 w-12 mx-auto mb-4 text-red-500" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Error Loading Results</h2>
          <p className="text-gray-600 mb-4">Failed to load analysis results</p>
          <Link to="/" className="btn btn-primary">
            Back to Home
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center space-x-4">
          <Link to="/" className="btn btn-secondary">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Analysis Results
            </h1>
            {result?.repository_url && (
              <p className="text-gray-600">
                {result.repository_url.split('/').slice(-2).join('/')}
                {result.branch && ` (${result.branch})`}
              </p>
            )}
          </div>
        </div>

        {isAnalysisComplete && (
          <div className="flex items-center space-x-2">
            <Link
              to={`/qa/${jobId}`}
              className="btn btn-secondary inline-flex items-center"
            >
              <MessageSquare className="h-4 w-4 mr-2" />
              Ask Questions
            </Link>
            <button className="btn btn-primary inline-flex items-center">
              <Download className="h-4 w-4 mr-2" />
              Export
            </button>
          </div>
        )}
      </div>

      {/* Progress Tracker for Running Analysis */}
      {isAnalysisRunning && progress && (
        <div className="mb-8">
          <ProgressTracker progress={progress} />
        </div>
      )}

      {/* Failed Analysis */}
      {isAnalysisFailed && (
        <div className="card p-8 text-center mb-8">
          <AlertTriangle className="h-16 w-16 mx-auto mb-4 text-red-500" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Analysis Failed</h2>
          <p className="text-gray-600 mb-4">
            {result?.error_message || 'The analysis could not be completed'}
          </p>
          <Link to="/analyze" className="btn btn-primary">
            Try Again
          </Link>
        </div>
      )}

      {/* Completed Analysis Results */}
      {isAnalysisComplete && (
        <>
          {/* Metrics Overview */}
          <div className="mb-8">
            <MetricsOverview result={result} />
          </div>

          {/* Issues Section */}
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
            {/* Filters Sidebar */}
            <div className="lg:col-span-1">
              <div className="card p-6 sticky top-24">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Filters</h3>
                
                {/* Search */}
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Search Issues
                  </label>
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <input
                      type="text"
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="input pl-10"
                      placeholder="Search..."
                    />
                  </div>
                </div>

                {/* Severity Filter */}
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Severity
                  </label>
                  <select
                    value={selectedSeverity}
                    onChange={(e) => setSelectedSeverity(e.target.value)}
                    className="input"
                  >
                    <option value="all">All Severities</option>
                    {severities.map((severity) => (
                      <option key={severity} value={severity}>
                        {severity.charAt(0).toUpperCase() + severity.slice(1)}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Category Filter */}
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Category
                  </label>
                  <select
                    value={selectedCategory}
                    onChange={(e) => setSelectedCategory(e.target.value)}
                    className="input"
                  >
                    <option value="all">All Categories</option>
                    {categories.map((category) => (
                      <option key={category} value={category}>
                        {category.charAt(0).toUpperCase() + category.slice(1)}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Results Count */}
                <div className="text-sm text-gray-600">
                  Showing {filteredIssues.length} of {result?.issues?.length || 0} issues
                </div>
              </div>
            </div>

            {/* Issues List */}
            <div className="lg:col-span-3">
              {filteredIssues.length > 0 ? (
                <div className="space-y-4">
                  {filteredIssues.map((issue) => (
                    <IssueCard
                      key={issue.id}
                      issue={issue}
                      onClick={() => setSelectedIssue(issue)}
                      isSelected={selectedIssue?.id === issue.id}
                    />
                  ))}
                </div>
              ) : (
                <div className="card p-8 text-center">
                  <Filter className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    No Issues Found
                  </h3>
                  <p className="text-gray-600">
                    {result?.issues?.length === 0 
                      ? 'Great! No code quality issues were detected.'
                      : 'No issues match your current filters. Try adjusting the filters above.'
                    }
                  </p>
                </div>
              )}
            </div>
          </div>
        </>
      )}

      {/* Issue Detail Modal */}
      {selectedIssue && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
            <div 
              className="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75"
              onClick={() => setSelectedIssue(null)}
            />
            
            <div className="inline-block w-full max-w-4xl p-6 my-8 overflow-hidden text-left align-middle transition-all transform bg-white shadow-xl rounded-lg">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-start space-x-3">
                  <div className={`p-2 rounded-lg ${getSeverityColor(selectedIssue.severity)}`}>
                    {React.createElement(getCategoryIcon(selectedIssue.category), { className: 'h-5 w-5' })}
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">
                      {selectedIssue.title}
                    </h3>
                    <div className="flex items-center space-x-2 text-sm text-gray-500">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSeverityColor(selectedIssue.severity)}`}>
                        {selectedIssue.severity}
                      </span>
                      <span>•</span>
                      <span>{selectedIssue.category}</span>
                      <span>•</span>
                      <span>Confidence: {Math.round(selectedIssue.confidence * 100)}%</span>
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => setSelectedIssue(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Description</h4>
                  <p className="text-gray-700">{selectedIssue.description}</p>
                </div>

                {selectedIssue.explanation && (
                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">AI Explanation</h4>
                    <p className="text-gray-700">{selectedIssue.explanation}</p>
                  </div>
                )}

                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Location</h4>
                  <div className="bg-gray-50 p-3 rounded-lg">
                    <div className="text-sm">
                      <div><strong>File:</strong> {selectedIssue.location.file_path}</div>
                      {selectedIssue.location.line_number && (
                        <div><strong>Line:</strong> {selectedIssue.location.line_number}</div>
                      )}
                      {selectedIssue.location.function_name && (
                        <div><strong>Function:</strong> {selectedIssue.location.function_name}</div>
                      )}
                    </div>
                  </div>
                </div>

                {selectedIssue.code_snippet && (
                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">Code Snippet</h4>
                    <CodeSnippet 
                      code={selectedIssue.code_snippet}
                      language="python" // Would be detected from file extension
                    />
                  </div>
                )}

                {selectedIssue.suggestions && selectedIssue.suggestions.length > 0 && (
                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">Suggestions</h4>
                    <ul className="list-disc list-inside space-y-1 text-gray-700">
                      {selectedIssue.suggestions.map((suggestion, index) => (
                        <li key={index}>{suggestion}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ResultsPage