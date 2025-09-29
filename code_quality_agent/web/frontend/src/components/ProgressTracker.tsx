import React from 'react'
import { Clock, CheckCircle, FileText, Search, AlertTriangle } from 'lucide-react'
import { AnalysisProgress } from '../services/api'

interface ProgressTrackerProps {
  progress: AnalysisProgress
}

const ProgressTracker: React.FC<ProgressTrackerProps> = ({ progress }) => {
  const getStatusIcon = () => {
    switch (progress.status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'failed':
        return <AlertTriangle className="h-5 w-5 text-red-500" />
      case 'running':
        return <div className="loading-spinner h-5 w-5" />
      default:
        return <Clock className="h-5 w-5 text-gray-500" />
    }
  }

  const getStatusColor = () => {
    switch (progress.status) {
      case 'completed':
        return 'text-green-600 bg-green-50 border-green-200'
      case 'failed':
        return 'text-red-600 bg-red-50 border-red-200'
      case 'running':
        return 'text-blue-600 bg-blue-50 border-blue-200'
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  const formatTime = (seconds?: number) => {
    if (!seconds) return 'Unknown'
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = Math.floor(seconds % 60)
    return minutes > 0 ? `${minutes}m ${remainingSeconds}s` : `${remainingSeconds}s`
  }

  return (
    <div className={`card p-6 border-2 ${getStatusColor()}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          {getStatusIcon()}
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              Analysis Progress
            </h3>
            <p className="text-sm text-gray-600">
              {progress.current_step}
            </p>
          </div>
        </div>
        
        <div className="text-right">
          <div className="text-2xl font-bold text-gray-900">
            {Math.round(progress.progress_percentage)}%
          </div>
          <div className="text-sm text-gray-600">
            Complete
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-4">
        <div className="progress-bar">
          <div 
            className="progress-fill"
            style={{ width: `${progress.progress_percentage}%` }}
          />
        </div>
      </div>

      {/* Progress Details */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
        <div className="flex items-center space-x-2">
          <CheckCircle className="h-4 w-4 text-gray-400" />
          <div>
            <div className="font-medium text-gray-900">
              {progress.steps_completed}/{progress.total_steps}
            </div>
            <div className="text-gray-600">Steps</div>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <FileText className="h-4 w-4 text-gray-400" />
          <div>
            <div className="font-medium text-gray-900">
              {progress.files_processed}/{progress.total_files}
            </div>
            <div className="text-gray-600">Files</div>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <Search className="h-4 w-4 text-gray-400" />
          <div>
            <div className="font-medium text-gray-900">
              {progress.issues_found}
            </div>
            <div className="text-gray-600">Issues Found</div>
          </div>
        </div>

        {progress.estimated_time_remaining && (
          <div className="flex items-center space-x-2">
            <Clock className="h-4 w-4 text-gray-400" />
            <div>
              <div className="font-medium text-gray-900">
                {formatTime(progress.estimated_time_remaining)}
              </div>
              <div className="text-gray-600">Remaining</div>
            </div>
          </div>
        )}
      </div>

      {/* Status Message */}
      {progress.message && (
        <div className="mt-4 p-3 bg-gray-50 rounded-lg">
          <p className="text-sm text-gray-700">{progress.message}</p>
        </div>
      )}

      {/* Real-time updates indicator */}
      <div className="mt-4 flex items-center justify-center text-xs text-gray-500">
        <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse mr-2" />
        Live updates
      </div>
    </div>
  )
}

export default ProgressTracker