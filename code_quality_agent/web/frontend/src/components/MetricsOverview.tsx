import React from 'react'
import { 
  BarChart3, 
  Shield, 
  Zap, 
  FileText, 
  AlertTriangle, 
  CheckCircle,
  Clock,
  GitCommit
} from 'lucide-react'
import { AnalysisResult } from '../services/api'

interface MetricsOverviewProps {
  result: AnalysisResult
}

const MetricsOverview: React.FC<MetricsOverviewProps> = ({ result }) => {
  // Calculate issue counts by severity
  const severityCounts = result.issues.reduce((acc, issue) => {
    acc[issue.severity] = (acc[issue.severity] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  // Calculate issue counts by category
  const categoryCounts = result.issues.reduce((acc, issue) => {
    acc[issue.category] = (acc[issue.category] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  const formatDuration = (seconds?: number) => {
    if (!seconds) return 'Unknown'
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = Math.floor(seconds % 60)
    return minutes > 0 ? `${minutes}m ${remainingSeconds}s` : `${remainingSeconds}s`
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

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
      default: return AlertTriangle
    }
  }

  const getOverallScore = () => {
    if (result.metrics?.overall_score) {
      return Math.round(result.metrics.overall_score * 100)
    }
    // Calculate a simple score based on issue severity
    const totalIssues = result.issues.length
    if (totalIssues === 0) return 100
    
    const criticalWeight = (severityCounts.critical || 0) * 4
    const highWeight = (severityCounts.high || 0) * 3
    const mediumWeight = (severityCounts.medium || 0) * 2
    const lowWeight = (severityCounts.low || 0) * 1
    
    const weightedScore = criticalWeight + highWeight + mediumWeight + lowWeight
    const maxPossibleScore = totalIssues * 4
    
    return Math.max(0, Math.round(100 - (weightedScore / maxPossibleScore) * 100))
  }

  const overallScore = getOverallScore()
  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600'
    if (score >= 60) return 'text-yellow-600'
    if (score >= 40) return 'text-orange-600'
    return 'text-red-600'
  }

  return (
    <div className="space-y-6">
      {/* Header with overall metrics */}
      <div className="card p-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {/* Overall Score */}
          <div className="text-center">
            <div className={`text-4xl font-bold ${getScoreColor(overallScore)} mb-2`}>
              {overallScore}
            </div>
            <div className="text-sm text-gray-600">Overall Score</div>
            <div className="mt-2">
              {overallScore >= 80 ? (
                <CheckCircle className="h-5 w-5 text-green-500 mx-auto" />
              ) : (
                <AlertTriangle className="h-5 w-5 text-yellow-500 mx-auto" />
              )}
            </div>
          </div>

          {/* Total Issues */}
          <div className="text-center">
            <div className="text-4xl font-bold text-gray-900 mb-2">
              {result.issues.length}
            </div>
            <div className="text-sm text-gray-600">Total Issues</div>
            <div className="text-xs text-gray-500 mt-1">
              Found in analysis
            </div>
          </div>

          {/* Files Analyzed */}
          <div className="text-center">
            <div className="text-4xl font-bold text-gray-900 mb-2">
              {result.summary?.total_files || result.summary?.files_analyzed || 0}
            </div>
            <div className="text-sm text-gray-600">Files Analyzed</div>
            <div className="text-xs text-gray-500 mt-1">
              In repository
            </div>
          </div>

          {/* Analysis Time */}
          <div className="text-center">
            <div className="text-4xl font-bold text-gray-900 mb-2">
              {formatDuration(result.duration_seconds)}
            </div>
            <div className="text-sm text-gray-600">Analysis Time</div>
            <div className="text-xs text-gray-500 mt-1">
              <Clock className="h-3 w-3 inline mr-1" />
              {formatDate(result.started_at)}
            </div>
          </div>
        </div>
      </div>

      {/* Issue breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Severity Breakdown */}
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <AlertTriangle className="h-5 w-5 mr-2" />
            Issues by Severity
          </h3>
          
          <div className="space-y-3">
            {['critical', 'high', 'medium', 'low', 'info'].map((severity) => {
              const count = severityCounts[severity] || 0
              const percentage = result.issues.length > 0 ? (count / result.issues.length) * 100 : 0
              
              return (
                <div key={severity} className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSeverityColor(severity)}`}>
                      {severity.toUpperCase()}
                    </span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="w-24 bg-gray-200 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${getSeverityColor(severity).split(' ')[1]}`}
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                    <span className="text-sm font-medium text-gray-900 w-8 text-right">
                      {count}
                    </span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Category Breakdown */}
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <BarChart3 className="h-5 w-5 mr-2" />
            Issues by Category
          </h3>
          
          <div className="space-y-3">
            {Object.entries(categoryCounts)
              .sort(([,a], [,b]) => b - a)
              .map(([category, count]) => {
                const percentage = result.issues.length > 0 ? (count / result.issues.length) * 100 : 0
                const Icon = getCategoryIcon(category)
                
                return (
                  <div key={category} className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Icon className="h-4 w-4 text-gray-500" />
                      <span className="text-sm font-medium text-gray-700 capitalize">
                        {category}
                      </span>
                    </div>
                    <div className="flex items-center space-x-3">
                      <div className="w-24 bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-primary-600 h-2 rounded-full"
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                      <span className="text-sm font-medium text-gray-900 w-8 text-right">
                        {count}
                      </span>
                    </div>
                  </div>
                )
              })}
          </div>
        </div>
      </div>

      {/* Repository Information */}
      {result.summary?.repository_info && (
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <GitCommit className="h-5 w-5 mr-2" />
            Repository Information
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <div className="font-medium text-gray-700">Repository</div>
              <div className="text-gray-600">
                {result.summary.repository_info.owner}/{result.summary.repository_info.name}
              </div>
            </div>
            
            {result.summary.repository_info.commit_hash && (
              <div>
                <div className="font-medium text-gray-700">Commit</div>
                <div className="text-gray-600 font-mono">
                  {result.summary.repository_info.commit_hash.slice(0, 8)}
                </div>
              </div>
            )}
            
            {result.summary.repository_info.author && (
              <div>
                <div className="font-medium text-gray-700">Author</div>
                <div className="text-gray-600">
                  {result.summary.repository_info.author}
                </div>
              </div>
            )}
          </div>
          
          {result.summary.repository_info.commit_message && (
            <div className="mt-4 p-3 bg-gray-50 rounded-lg">
              <div className="font-medium text-gray-700 text-sm mb-1">Latest Commit</div>
              <div className="text-gray-600 text-sm">
                {result.summary.repository_info.commit_message}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default MetricsOverview