import React, { useState, useRef, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { 
  ArrowLeft, 
  Send, 
  MessageSquare, 
  Bot, 
  User, 
  Lightbulb,
  FileText,
  Code,
  AlertCircle,
  Loader
} from 'lucide-react'
import { apiService, QuestionRequest, Answer } from '../services/api'
import CodeSnippet from '../components/CodeSnippet'

interface ChatMessage {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: Date
  answer?: Answer
}

const QAPage: React.FC = () => {
  const { jobId } = useParams<{ jobId?: string }>()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputValue, setInputValue] = useState('')
  const [selectedFile, setSelectedFile] = useState<string>('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Fetch analysis result if jobId is provided
  const { data: analysisResult } = useQuery({
    queryKey: ['analysis', jobId],
    queryFn: () => apiService.getAnalysisResult(jobId!),
    enabled: !!jobId,
  })

  // Question mutation
  const questionMutation = useMutation({
    mutationFn: (request: QuestionRequest) => apiService.askQuestion(request),
    onSuccess: (answer, variables) => {
      const assistantMessage: ChatMessage = {
        id: Date.now().toString() + '_assistant',
        type: 'assistant',
        content: answer.answer,
        timestamp: new Date(),
        answer,
      }
      setMessages(prev => [...prev, assistantMessage])
    },
    onError: (error: any) => {
      const errorMessage: ChatMessage = {
        id: Date.now().toString() + '_error',
        type: 'assistant',
        content: `Sorry, I encountered an error: ${error.response?.data?.message || 'Please try again.'}`,
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, errorMessage])
    },
  })

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!inputValue.trim() || questionMutation.isPending) return

    // Add user message
    const userMessage: ChatMessage = {
      id: Date.now().toString() + '_user',
      type: 'user',
      content: inputValue.trim(),
      timestamp: new Date(),
    }
    setMessages(prev => [...prev, userMessage])

    // Prepare question request
    const request: QuestionRequest = {
      question: inputValue.trim(),
      job_id: jobId,
      file_path: selectedFile || undefined,
    }

    // Send question
    questionMutation.mutate(request)
    setInputValue('')
  }

  const suggestedQuestions = [
    "What are the most critical security issues in this codebase?",
    "Which files have the highest complexity?",
    "Are there any performance bottlenecks I should address?",
    "What's the overall code quality score?",
    "Which areas need better test coverage?",
    "Are there any code duplication issues?",
    "What documentation improvements are needed?",
    "How can I improve the maintainability of this code?",
  ]

  const handleSuggestedQuestion = (question: string) => {
    setInputValue(question)
    inputRef.current?.focus()
  }

  const formatTimestamp = (date: Date) => {
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit' 
    })
  }

  const getUniqueFiles = () => {
    if (!analysisResult?.issues) return []
    const files = [...new Set(analysisResult.issues.map(issue => issue.location.file_path))]
    return files.sort()
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 h-screen flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-4">
          <Link to={jobId ? `/results/${jobId}` : '/'} className="btn btn-secondary">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center">
              <MessageSquare className="h-6 w-6 mr-2" />
              Code Q&A
            </h1>
            {analysisResult?.repository_url && (
              <p className="text-gray-600">
                Ask questions about {analysisResult.repository_url.split('/').slice(-2).join('/')}
              </p>
            )}
          </div>
        </div>

        {/* File selector */}
        {getUniqueFiles().length > 0 && (
          <div className="flex items-center space-x-2">
            <label className="text-sm font-medium text-gray-700">Focus on file:</label>
            <select
              value={selectedFile}
              onChange={(e) => setSelectedFile(e.target.value)}
              className="input w-64"
            >
              <option value="">All files</option>
              {getUniqueFiles().map((file) => (
                <option key={file} value={file}>
                  {file.split('/').pop()}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Chat Container */}
      <div className="flex-1 flex flex-col bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.length === 0 ? (
            <div className="text-center py-12">
              <Bot className="h-16 w-16 mx-auto mb-4 text-gray-300" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Ask me anything about your code
              </h3>
              <p className="text-gray-600 mb-8">
                I can help you understand code quality issues, suggest improvements, 
                and answer questions about your analysis results.
              </p>

              {/* Suggested Questions */}
              <div className="max-w-2xl mx-auto">
                <h4 className="text-sm font-medium text-gray-700 mb-4 flex items-center justify-center">
                  <Lightbulb className="h-4 w-4 mr-2" />
                  Suggested Questions
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {suggestedQuestions.slice(0, 6).map((question, index) => (
                    <button
                      key={index}
                      onClick={() => handleSuggestedQuestion(question)}
                      className="text-left p-3 bg-gray-50 hover:bg-gray-100 rounded-lg text-sm text-gray-700 transition-colors"
                    >
                      {question}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <>
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`flex max-w-3xl ${message.type === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                    {/* Avatar */}
                    <div className={`flex-shrink-0 ${message.type === 'user' ? 'ml-3' : 'mr-3'}`}>
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                        message.type === 'user' 
                          ? 'bg-primary-600 text-white' 
                          : 'bg-gray-200 text-gray-600'
                      }`}>
                        {message.type === 'user' ? (
                          <User className="h-4 w-4" />
                        ) : (
                          <Bot className="h-4 w-4" />
                        )}
                      </div>
                    </div>

                    {/* Message Content */}
                    <div className={`flex-1 ${message.type === 'user' ? 'text-right' : 'text-left'}`}>
                      <div className={`inline-block p-4 rounded-lg ${
                        message.type === 'user'
                          ? 'bg-primary-600 text-white'
                          : 'bg-gray-100 text-gray-900'
                      }`}>
                        <div className="whitespace-pre-wrap">{message.content}</div>
                        
                        {/* Answer metadata */}
                        {message.answer && (
                          <div className="mt-3 pt-3 border-t border-gray-300 text-xs opacity-75">
                            <div className="flex items-center justify-between">
                              <span>Confidence: {Math.round(message.answer.confidence * 100)}%</span>
                              {message.answer.sources && message.answer.sources.length > 0 && (
                                <span>Sources: {message.answer.sources.join(', ')}</span>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                      
                      <div className={`text-xs text-gray-500 mt-1 ${
                        message.type === 'user' ? 'text-right' : 'text-left'
                      }`}>
                        {formatTimestamp(message.timestamp)}
                      </div>

                      {/* Related issues */}
                      {message.answer?.related_issues && message.answer.related_issues.length > 0 && (
                        <div className="mt-2">
                          <div className="text-xs text-gray-600 mb-1">Related Issues:</div>
                          <div className="flex flex-wrap gap-1">
                            {message.answer.related_issues.map((issueId, index) => (
                              <span
                                key={index}
                                className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full"
                              >
                                {issueId}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Suggestions */}
                      {message.answer?.suggestions && message.answer.suggestions.length > 0 && (
                        <div className="mt-2">
                          <div className="text-xs text-gray-600 mb-1">Suggestions:</div>
                          <ul className="text-sm text-gray-700 list-disc list-inside space-y-1">
                            {message.answer.suggestions.map((suggestion, index) => (
                              <li key={index}>{suggestion}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}

              {/* Loading indicator */}
              {questionMutation.isPending && (
                <div className="flex justify-start">
                  <div className="flex">
                    <div className="flex-shrink-0 mr-3">
                      <div className="w-8 h-8 rounded-full bg-gray-200 text-gray-600 flex items-center justify-center">
                        <Bot className="h-4 w-4" />
                      </div>
                    </div>
                    <div className="bg-gray-100 text-gray-900 p-4 rounded-lg">
                      <div className="flex items-center space-x-2">
                        <Loader className="h-4 w-4 animate-spin" />
                        <span>Thinking...</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Form */}
        <div className="border-t border-gray-200 p-4">
          <form onSubmit={handleSubmit} className="flex space-x-4">
            <div className="flex-1">
              <input
                ref={inputRef}
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="Ask a question about your code..."
                className="input"
                disabled={questionMutation.isPending}
              />
            </div>
            <button
              type="submit"
              disabled={!inputValue.trim() || questionMutation.isPending}
              className="btn btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send className="h-4 w-4" />
            </button>
          </form>
          
          {!jobId && (
            <div className="mt-2 flex items-center text-sm text-amber-600 bg-amber-50 p-2 rounded">
              <AlertCircle className="h-4 w-4 mr-2" />
              No analysis context available. Questions will be answered based on general knowledge.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default QAPage