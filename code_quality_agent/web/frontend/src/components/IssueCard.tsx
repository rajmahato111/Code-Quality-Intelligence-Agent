import React from 'react'
import { 
  Shield, 
  Zap, 
  BarChart3, 
  FileText, 
  Code, 
  MapPin,
  TrendingUp,
  Eye
} from 'lucide-react'
import { Issue } from '../services/api'

interface IssueCardProps {
  issue: Issue
  onClick?: () => void
  isSelected?: boolean
}

const IssueCard: React.FC<IssueCardProps> = ({ issue, onClick, isSelected }) => {
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'text-severity-critical bg-red-50 border-red-200'
      case 'high': return 'text-severity-high bg-orange-50 border-orange-200'
      case 'medium': return 'text-severity-medium bg-yellow-50 border-yellow-200'
      case 'low': return 'text-severity-low bg-green-50 border-green-200'
      case 'info': return 'text-severity-info bg-blue-50 border-blue-200'
      default: return 'text-gray-600 bg-gray-50 border-gray-200'
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

  const getCategoryColor = (category: string) => {
    switch (category.toLowerCase()) {
      case 'security': return 'text-red-600 bg-red-100'
      case 'performance': return 'text-yellow-600 bg-yellow-100'
      case 'complexity': return 'text-blue-600 bg-blue-100'
      case 'documentation': return 'text-green-600 bg-green-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  const Icon = getCategoryIcon(issue.category)

  return (
    <div 
      className={`card p-6 cursor-pointer transition-all hover:shadow-md ${
        isSelected ? 'ring-2 ring-primary-500 border-primary-200' : ''
      }`}
      onClick={onClick}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-start space-x-3">
          <div className={`p-2 rounded-lg ${getCategoryColor(issue.category)}`}>
            <Icon className="h-5 w-5" />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900 mb-1">
              {issue.title}
            </h3>
            <p className="text-gray-600 text-sm line-clamp-2">
              {issue.description}
            </p>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <span className={`px-3 py-1 rounded-full text-xs font-medium ${getSeverityColor(issue.severity)}`}>
            {issue.severity.toUpperCase()}
          </span>
          {onClick && (
            <button className="p-1 text-gray-400 hover:text-gray-600">
              <Eye className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>

      {/* Location and metadata */}
      <div className="flex items-center justify-between text-sm text-gray-500">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-1">
            <MapPin className="h-4 w-4" />
            <span>{issue.location.file_path.split('/').pop()}</span>
            {issue.location.line_number && (
              <span>:{issue.location.line_number}</span>
            )}
          </div>
          
          {issue.location.function_name && (
            <div className="flex items-center space-x-1">
              <Code className="h-4 w-4" />
              <span>{issue.location.function_name}</span>
            </div>
          )}
        </div>

        <div className="flex items-center space-x-3">
          {issue.confidence && (
            <div className="flex items-center space-x-1">
              <TrendingUp className="h-4 w-4" />
              <span>{Math.round(issue.confidence * 100)}%</span>
            </div>
          )}
          
          <span className={`px-2 py-1 rounded text-xs ${getCategoryColor(issue.category)}`}>
            {issue.category}
          </span>
        </div>
      </div>

      {/* Tags */}
      {issue.tags && issue.tags.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1">
          {issue.tags.map((tag, index) => (
            <span
              key={index}
              className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full"
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      {/* Priority indicators */}
      {(issue.business_impact || issue.priority_score) && (
        <div className="mt-3 flex items-center space-x-4 text-xs text-gray-500">
          {issue.business_impact && (
            <div>
              Business Impact: {Math.round(issue.business_impact * 100)}%
            </div>
          )}
          {issue.priority_score && (
            <div>
              Priority: {Math.round(issue.priority_score * 100)}%
            </div>
          )}
        </div>
      )}

      {/* Quick preview of suggestions */}
      {issue.suggestions && issue.suggestions.length > 0 && (
        <div className="mt-3 p-3 bg-gray-50 rounded-lg">
          <div className="text-xs font-medium text-gray-700 mb-1">
            Quick Fix:
          </div>
          <div className="text-xs text-gray-600 line-clamp-2">
            {issue.suggestions[0]}
          </div>
          {issue.suggestions.length > 1 && (
            <div className="text-xs text-gray-500 mt-1">
              +{issue.suggestions.length - 1} more suggestions
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default IssueCard