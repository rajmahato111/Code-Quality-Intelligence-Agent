import React from 'react'
import { Link } from 'react-router-dom'
import { Home, Search, MessageSquare } from 'lucide-react'

const NotFoundPage: React.FC = () => {
  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="max-w-md w-full text-center">
        <div className="mb-8">
          <div className="text-6xl font-bold text-gray-300 mb-4">404</div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Page Not Found
          </h1>
          <p className="text-gray-600">
            The page you're looking for doesn't exist or has been moved.
          </p>
        </div>

        <div className="space-y-4">
          <Link
            to="/"
            className="btn btn-primary w-full inline-flex items-center justify-center"
          >
            <Home className="mr-2 h-4 w-4" />
            Go Home
          </Link>
          
          <div className="flex space-x-4">
            <Link
              to="/analyze"
              className="btn btn-secondary flex-1 inline-flex items-center justify-center"
            >
              <Search className="mr-2 h-4 w-4" />
              Analyze Code
            </Link>
            
            <Link
              to="/qa"
              className="btn btn-secondary flex-1 inline-flex items-center justify-center"
            >
              <MessageSquare className="mr-2 h-4 w-4" />
              Ask Questions
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}

export default NotFoundPage