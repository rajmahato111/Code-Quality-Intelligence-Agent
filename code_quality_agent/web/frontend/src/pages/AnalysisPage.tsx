import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import { 
  Search, 
  Settings, 
  Github, 
  GitBranch,
  Filter,
  Play,
  AlertCircle,
  Info
} from 'lucide-react'
import { apiService, RepositoryRequest, AnalysisConfiguration } from '../services/api'

interface AnalysisFormData {
  url: string
  branch: string
  include_patterns: string
  exclude_patterns: string
  analysis_types: string[]
  config: AnalysisConfiguration
}

const AnalysisPage: React.FC = () => {
  const navigate = useNavigate()
  const [showAdvanced, setShowAdvanced] = useState(false)
  
  const { register, handleSubmit, watch, setValue, formState: { errors } } = useForm<AnalysisFormData>({
    defaultValues: {
      url: '',
      branch: 'main',
      include_patterns: '',
      exclude_patterns: '',
      analysis_types: ['all'],
      config: {
        enable_security_analysis: true,
        enable_performance_analysis: true,
        enable_maintainability_analysis: true,
        enable_complexity_analysis: true,
        enable_duplication_analysis: true,
        enable_ai_explanations: true,
        enable_severity_scoring: true,
        severity_threshold: 'LOW',
        max_issues_per_file: 50,
        timeout_seconds: 300,
      }
    }
  })

  const analysisMutation = useMutation({
    mutationFn: (data: RepositoryRequest) => apiService.analyzeRepository(data),
    onSuccess: (result) => {
      toast.success('Analysis started successfully!')
      navigate(`/results/${result.job_id}`)
    },
    onError: (error: any) => {
      console.error('Analysis failed:', error)
      toast.error(error.response?.data?.message || 'Failed to start analysis')
    },
  })

  const onSubmit = (data: AnalysisFormData) => {
    const request: RepositoryRequest = {
      url: data.url,
      branch: data.branch || 'main',
      include_patterns: data.include_patterns ? data.include_patterns.split(',').map(p => p.trim()) : undefined,
      exclude_patterns: data.exclude_patterns ? data.exclude_patterns.split(',').map(p => p.trim()) : undefined,
      analysis_types: data.analysis_types.includes('all') ? undefined : data.analysis_types,
      config: data.config,
    }

    analysisMutation.mutate(request)
  }

  const analysisTypes = [
    { id: 'all', label: 'All Analysis Types', description: 'Run comprehensive analysis' },
    { id: 'security', label: 'Security', description: 'Vulnerability detection' },
    { id: 'performance', label: 'Performance', description: 'Performance bottlenecks' },
    { id: 'complexity', label: 'Complexity', description: 'Code complexity metrics' },
    { id: 'duplication', label: 'Duplication', description: 'Code duplication detection' },
    { id: 'testing', label: 'Testing', description: 'Test coverage analysis' },
    { id: 'documentation', label: 'Documentation', description: 'Documentation quality' },
  ]

  const severityLevels = [
    { value: 'INFO', label: 'Info', description: 'Show all issues including informational' },
    { value: 'LOW', label: 'Low', description: 'Show low severity and above' },
    { value: 'MEDIUM', label: 'Medium', description: 'Show medium severity and above' },
    { value: 'HIGH', label: 'High', description: 'Show high severity and above' },
    { value: 'CRITICAL', label: 'Critical', description: 'Show only critical issues' },
  ]

  const watchedAnalysisTypes = watch('analysis_types')

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Analyze Repository
        </h1>
        <p className="text-gray-600">
          Enter a GitHub repository URL to start comprehensive code quality analysis
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
        {/* Repository URL */}
        <div className="card p-6">
          <div className="flex items-center mb-4">
            <Github className="h-5 w-5 text-gray-400 mr-2" />
            <h2 className="text-lg font-semibold text-gray-900">Repository</h2>
          </div>
          
          <div className="space-y-4">
            <div>
              <label htmlFor="url" className="block text-sm font-medium text-gray-700 mb-2">
                Repository URL *
              </label>
              <input
                {...register('url', { 
                  required: 'Repository URL is required',
                  pattern: {
                    value: /^https:\/\/(github\.com|gitlab\.com|bitbucket\.org)\/.+\/.+$/,
                    message: 'Please enter a valid GitHub, GitLab, or Bitbucket repository URL'
                  }
                })}
                type="url"
                className="input"
                placeholder="https://github.com/owner/repository"
              />
              {errors.url && (
                <p className="mt-1 text-sm text-red-600 flex items-center">
                  <AlertCircle className="h-4 w-4 mr-1" />
                  {errors.url.message}
                </p>
              )}
            </div>

            <div>
              <label htmlFor="branch" className="block text-sm font-medium text-gray-700 mb-2">
                <GitBranch className="inline h-4 w-4 mr-1" />
                Branch
              </label>
              <input
                {...register('branch')}
                type="text"
                className="input"
                placeholder="main"
              />
            </div>
          </div>
        </div>

        {/* Analysis Types */}
        <div className="card p-6">
          <div className="flex items-center mb-4">
            <Search className="h-5 w-5 text-gray-400 mr-2" />
            <h2 className="text-lg font-semibold text-gray-900">Analysis Types</h2>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {analysisTypes.map((type) => (
              <label key={type.id} className="flex items-start space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                <input
                  {...register('analysis_types')}
                  type="checkbox"
                  value={type.id}
                  className="mt-1 h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                  onChange={(e) => {
                    const currentTypes = watchedAnalysisTypes || []
                    if (type.id === 'all') {
                      if (e.target.checked) {
                        setValue('analysis_types', ['all'])
                      } else {
                        setValue('analysis_types', [])
                      }
                    } else {
                      if (e.target.checked) {
                        const newTypes = currentTypes.filter(t => t !== 'all').concat(type.id)
                        setValue('analysis_types', newTypes)
                      } else {
                        const newTypes = currentTypes.filter(t => t !== type.id && t !== 'all')
                        setValue('analysis_types', newTypes)
                      }
                    }
                  }}
                  checked={watchedAnalysisTypes?.includes(type.id) || false}
                />
                <div className="flex-1">
                  <div className="text-sm font-medium text-gray-900">{type.label}</div>
                  <div className="text-xs text-gray-500">{type.description}</div>
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* Advanced Settings */}
        <div className="card p-6">
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="flex items-center w-full text-left mb-4 hover:text-primary-600"
          >
            <Settings className="h-5 w-5 text-gray-400 mr-2" />
            <h2 className="text-lg font-semibold text-gray-900">Advanced Settings</h2>
            <div className={`ml-auto transform transition-transform ${showAdvanced ? 'rotate-180' : ''}`}>
              ▼
            </div>
          </button>

          {showAdvanced && (
            <div className="space-y-6 pt-4 border-t border-gray-200">
              {/* File Patterns */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <Filter className="inline h-4 w-4 mr-1" />
                    Include Patterns
                  </label>
                  <input
                    {...register('include_patterns')}
                    type="text"
                    className="input"
                    placeholder="*.py, *.js, *.ts"
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    Comma-separated file patterns to include
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <Filter className="inline h-4 w-4 mr-1" />
                    Exclude Patterns
                  </label>
                  <input
                    {...register('exclude_patterns')}
                    type="text"
                    className="input"
                    placeholder="node_modules/*, *.min.js"
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    Comma-separated file patterns to exclude
                  </p>
                </div>
              </div>

              {/* Analysis Configuration */}
              <div className="space-y-4">
                <h3 className="text-md font-medium text-gray-900">Analysis Configuration</h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Severity Threshold
                    </label>
                    <select {...register('config.severity_threshold')} className="input">
                      {severityLevels.map((level) => (
                        <option key={level.value} value={level.value}>
                          {level.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Max Issues per File
                    </label>
                    <input
                      {...register('config.max_issues_per_file', { 
                        min: 1, 
                        max: 1000,
                        valueAsNumber: true 
                      })}
                      type="number"
                      className="input"
                      min="1"
                      max="1000"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Timeout (seconds)
                    </label>
                    <input
                      {...register('config.timeout_seconds', { 
                        min: 30, 
                        max: 3600,
                        valueAsNumber: true 
                      })}
                      type="number"
                      className="input"
                      min="30"
                      max="3600"
                    />
                  </div>
                </div>

                {/* Feature toggles */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <label className="flex items-center">
                      <input
                        {...register('config.enable_ai_explanations')}
                        type="checkbox"
                        className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                      />
                      <span className="ml-2 text-sm text-gray-700">Enable AI Explanations</span>
                    </label>
                    <Info className="h-4 w-4 text-gray-400" />
                  </div>

                  <div className="flex items-center justify-between">
                    <label className="flex items-center">
                      <input
                        {...register('config.enable_severity_scoring')}
                        type="checkbox"
                        className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                      />
                      <span className="ml-2 text-sm text-gray-700">Enable Automated Severity Scoring</span>
                    </label>
                    <Info className="h-4 w-4 text-gray-400" />
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Submit Button */}
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={analysisMutation.isPending}
            className="btn btn-primary inline-flex items-center text-lg px-8 py-3 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {analysisMutation.isPending ? (
              <>
                <div className="loading-spinner h-5 w-5 mr-2" />
                Starting Analysis...
              </>
            ) : (
              <>
                <Play className="mr-2 h-5 w-5" />
                Start Analysis
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  )
}

export default AnalysisPage