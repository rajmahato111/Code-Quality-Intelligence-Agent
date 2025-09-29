import React, { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { 
  Search, 
  BarChart3, 
  MessageSquare, 
  Settings, 
  Menu, 
  X,
  Github,
  Shield,
  Zap
} from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { apiService } from '../services/api'
import toast from 'react-hot-toast'

interface LayoutProps {
  children: React.ReactNode
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [apiKeyInitialized, setApiKeyInitialized] = useState(false)
  const location = useLocation()

  // Initialize API key on first load
  useEffect(() => {
    const initializeApiKey = async () => {
      const existingKey = localStorage.getItem('api_key')
      if (!existingKey) {
        try {
          const { api_key } = await apiService.getDemoApiKey()
          localStorage.setItem('api_key', api_key)
          setApiKeyInitialized(true)
        } catch (error) {
          console.error('Failed to initialize API key:', error)
          toast.error('Failed to initialize API connection')
        }
      } else {
        setApiKeyInitialized(true)
      }
    }

    initializeApiKey()
  }, [])

  // Health check query
  const { data: healthData } = useQuery({
    queryKey: ['health'],
    queryFn: apiService.getHealth,
    refetchInterval: 30000, // Check every 30 seconds
    enabled: apiKeyInitialized,
  })

  const navigation = [
    { name: 'Home', href: '/', icon: BarChart3 },
    { name: 'Analyze', href: '/analyze', icon: Search },
    { name: 'Q&A', href: '/qa', icon: MessageSquare },
  ]

  const isCurrentPath = (path: string) => {
    if (path === '/') {
      return location.pathname === '/'
    }
    return location.pathname.startsWith(path)
  }

  const getHealthStatus = () => {
    if (!healthData) return { color: 'gray', text: 'Unknown' }
    
    switch (healthData.status) {
      case 'healthy':
        return { color: 'green', text: 'Healthy' }
      case 'degraded':
        return { color: 'yellow', text: 'Degraded' }
      default:
        return { color: 'red', text: 'Unhealthy' }
    }
  }

  const healthStatus = getHealthStatus()

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 z-40 bg-gray-600 bg-opacity-75 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={`
        fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center justify-between h-16 px-6 border-b border-gray-200">
            <div className="flex items-center space-x-2">
              <Shield className="h-8 w-8 text-primary-600" />
              <span className="text-xl font-bold text-gray-900">CodeQuality</span>
            </div>
            <button
              onClick={() => setSidebarOpen(false)}
              className="lg:hidden p-1 rounded-md hover:bg-gray-100"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-2">
            {navigation.map((item) => {
              const Icon = item.icon
              const current = isCurrentPath(item.href)
              
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`
                    flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors
                    ${current 
                      ? 'bg-primary-100 text-primary-700 border-r-2 border-primary-600' 
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                    }
                  `}
                  onClick={() => setSidebarOpen(false)}
                >
                  <Icon className="mr-3 h-5 w-5" />
                  {item.name}
                </Link>
              )
            })}
          </nav>

          {/* Status indicator */}
          <div className="px-4 py-4 border-t border-gray-200">
            <div className="flex items-center space-x-2 text-sm">
              <div className={`h-2 w-2 rounded-full bg-${healthStatus.color}-500`} />
              <span className="text-gray-600">Status: {healthStatus.text}</span>
            </div>
            {healthData && (
              <div className="mt-2 text-xs text-gray-500">
                v{healthData.version}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Top bar */}
        <div className="sticky top-0 z-40 bg-white shadow-sm border-b border-gray-200">
          <div className="flex items-center justify-between h-16 px-4 sm:px-6 lg:px-8">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100"
            >
              <Menu className="h-6 w-6" />
            </button>

            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 text-sm text-gray-500">
                <Zap className="h-4 w-4" />
                <span>AI-Powered Code Analysis</span>
              </div>
              
              <a
                href="https://github.com/your-repo/code-quality-agent"
                target="_blank"
                rel="noopener noreferrer"
                className="p-2 text-gray-400 hover:text-gray-500"
              >
                <Github className="h-5 w-5" />
              </a>
            </div>
          </div>
        </div>

        {/* Page content */}
        <main className="flex-1">
          {children}
        </main>
      </div>
    </div>
  )
}

export default Layout