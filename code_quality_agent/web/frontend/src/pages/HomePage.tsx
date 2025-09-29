import React from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { 
  Search, 
  MessageSquare, 
  Shield, 
  Zap, 
  BarChart3,
  Clock,
  CheckCircle,
  AlertTriangle,
  ArrowRight
} from 'lucide-react'
import { apiService } from '../services/api'

const HomePage: React.FC = () => {
  // Fetch recent jobs
  const { data: jobsData } = useQuery({
    queryKey: ['jobs'],
    queryFn: apiService.listJobs,
  })

  // Fetch health status
  const { data: healthData } = useQuery({
    queryKey: ['health'],
    queryFn: apiService.getHealth,
  })

  const features = [
    {
      icon: Shield,
      title: 'Security Analysis',
      description: 'Detect vulnerabilities, insecure patterns, and OWASP Top 10 issues',
      color: 'text-red-600 bg-red-100',
    },
    {
      icon: Zap,
      title: 'Performance Insights',
      description: 'Identify bottlenecks, memory leaks, and optimization opportunities',
      color: 'text-yellow-600 bg-yellow-100',
    },
    {
      icon: BarChart3,
      title: 'Code Metrics',
      description: 'Complexity analysis, maintainability scores, and quality trends',
      color: 'text-blue-600 bg-blue-100',
    },
    {
      icon: MessageSquare,
      title: 'AI Q&A',
      description: 'Ask questions about your code and get intelligent answers',
      color: 'text-green-600 bg-green-100',
    },
  ]

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'running':
        return <Clock className="h-5 w-5 text-blue-500 animate-spin" />
      case 'failed':
        return <AlertTriangle className="h-5 w-5 text-red-500" />
      default:
        return <Clock className="h-5 w-5 text-gray-500" />
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Hero section */}
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Code Quality Intelligence Agent
        </h1>
        <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
          AI-powered code analysis that goes beyond simple linting. Get actionable insights, 
          security recommendations, and performance optimizations for your codebase.
        </p>
        
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            to="/analyze"
            className="btn btn-primary inline-flex items-center text-lg px-8 py-3"
          >
            <Search className="mr-2 h-5 w-5" />
            Analyze Repository
          </Link>
          <Link
            to="/qa"
            className="btn btn-secondary inline-flex items-center text-lg px-8 py-3"
          >
            <MessageSquare className="mr-2 h-5 w-5" />
            Ask Questions
          </Link>
        </div>
      </div>

      {/* Features grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
        {features.map((feature, index) => {
          const Icon = feature.icon
          return (
            <div key={index} className="card p-6 text-center hover:shadow-md transition-shadow">
              <div className={`inline-flex p-3 rounded-full ${feature.color} mb-4`}>
                <Icon className="h-6 w-6" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                {feature.title}
              </h3>
              <p className="text-gray-600 text-sm">
                {feature.description}
              </p>
            </div>
          )
        })}
      </div>

      {/* Dashboard sections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Recent analyses */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Recent Analyses</h2>
            <Link 
              to="/analyze" 
              className="text-primary-600 hover:text-primary-700 text-sm font-medium inline-flex items-center"
            >
              View all
              <ArrowRight className="ml-1 h-4 w-4" />
            </Link>
          </div>
          
          {jobsData?.jobs && jobsData.jobs.length > 0 ? (
            <div className="space-y-3">
              {jobsData.jobs.slice(0, 5).map((job) => (
                <div key={job.job_id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    {getStatusIcon(job.status)}
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        {job.repository_url ? 
                          job.repository_url.split('/').slice(-2).join('/') : 
                          `Job ${job.job_id.slice(0, 8)}`
                        }
                      </div>
                      <div className="text-xs text-gray-500">
                        {formatDate(job.started_at)}
                      </div>
                    </div>
                  </div>
                  <Link
                    to={`/results/${job.job_id}`}
                    className="text-primary-600 hover:text-primary-700 text-sm font-medium"
                  >
                    View
                  </Link>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <Search className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p>No analyses yet</p>
              <p className="text-sm">Start by analyzing a repository</p>
            </div>
          )}
        </div>

        {/* System status */}
        <div className="card p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">System Status</h2>
          
          {healthData ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">Overall Status</span>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  healthData.status === 'healthy' 
                    ? 'bg-green-100 text-green-800'
                    : healthData.status === 'degraded'
                    ? 'bg-yellow-100 text-yellow-800'
                    : 'bg-red-100 text-red-800'
                }`}>
                  {healthData.status}
                </span>
              </div>
              
              <div className="space-y-2">
                {Object.entries(healthData.components).map(([component, status]) => (
                  <div key={component} className="flex items-center justify-between text-sm">
                    <span className="text-gray-600 capitalize">
                      {component.replace('_', ' ')}
                    </span>
                    <span className={`px-2 py-1 rounded text-xs ${
                      status === 'healthy' 
                        ? 'bg-green-100 text-green-700'
                        : status === 'unavailable'
                        ? 'bg-gray-100 text-gray-700'
                        : 'bg-red-100 text-red-700'
                    }`}>
                      {status}
                    </span>
                  </div>
                ))}
              </div>
              
              <div className="pt-4 border-t border-gray-200">
                <div className="text-xs text-gray-500">
                  Version {healthData.version} • Last updated {formatDate(healthData.timestamp)}
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-4 text-gray-500">
              <div className="loading-spinner h-8 w-8 mx-auto mb-2" />
              <p className="text-sm">Loading system status...</p>
            </div>
          )}
        </div>
      </div>

      {/* Quick start guide */}
      <div className="mt-12 card p-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">
          Quick Start Guide
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="text-center">
            <div className="bg-primary-100 text-primary-600 rounded-full w-12 h-12 flex items-center justify-center mx-auto mb-4">
              <span className="text-xl font-bold">1</span>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Analyze Repository
            </h3>
            <p className="text-gray-600 text-sm">
              Enter a GitHub repository URL and start comprehensive code analysis
            </p>
          </div>
          
          <div className="text-center">
            <div className="bg-primary-100 text-primary-600 rounded-full w-12 h-12 flex items-center justify-center mx-auto mb-4">
              <span className="text-xl font-bold">2</span>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Review Results
            </h3>
            <p className="text-gray-600 text-sm">
              Get detailed insights on security, performance, and code quality issues
            </p>
          </div>
          
          <div className="text-center">
            <div className="bg-primary-100 text-primary-600 rounded-full w-12 h-12 flex items-center justify-center mx-auto mb-4">
              <span className="text-xl font-bold">3</span>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Ask Questions
            </h3>
            <p className="text-gray-600 text-sm">
              Use the AI Q&A feature to get specific insights about your codebase
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default HomePage