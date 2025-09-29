import React from 'react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { Copy, Check } from 'lucide-react'

interface CodeSnippetProps {
  code: string
  language?: string
  showLineNumbers?: boolean
  highlightLines?: number[]
}

const CodeSnippet: React.FC<CodeSnippetProps> = ({ 
  code, 
  language = 'javascript', 
  showLineNumbers = true,
  highlightLines = []
}) => {
  const [copied, setCopied] = React.useState(false)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy code:', err)
    }
  }

  const getLanguageFromExtension = (lang: string) => {
    const languageMap: Record<string, string> = {
      'py': 'python',
      'js': 'javascript',
      'ts': 'typescript',
      'jsx': 'jsx',
      'tsx': 'tsx',
      'java': 'java',
      'cpp': 'cpp',
      'c': 'c',
      'cs': 'csharp',
      'php': 'php',
      'rb': 'ruby',
      'go': 'go',
      'rs': 'rust',
      'sh': 'bash',
      'sql': 'sql',
      'json': 'json',
      'yaml': 'yaml',
      'yml': 'yaml',
      'xml': 'xml',
      'html': 'html',
      'css': 'css',
      'scss': 'scss',
      'md': 'markdown',
    }
    
    return languageMap[lang.toLowerCase()] || lang
  }

  const detectedLanguage = getLanguageFromExtension(language)

  return (
    <div className="relative group">
      {/* Header with language and copy button */}
      <div className="flex items-center justify-between bg-gray-800 text-gray-300 px-4 py-2 text-sm rounded-t-lg">
        <span className="font-medium capitalize">
          {detectedLanguage}
        </span>
        <button
          onClick={handleCopy}
          className="flex items-center space-x-1 px-2 py-1 rounded hover:bg-gray-700 transition-colors"
          title="Copy code"
        >
          {copied ? (
            <>
              <Check className="h-4 w-4" />
              <span>Copied!</span>
            </>
          ) : (
            <>
              <Copy className="h-4 w-4" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>

      {/* Code content */}
      <div className="rounded-b-lg overflow-hidden">
        <SyntaxHighlighter
          language={detectedLanguage}
          style={vscDarkPlus}
          showLineNumbers={showLineNumbers}
          wrapLines={true}
          lineProps={(lineNumber) => {
            const isHighlighted = highlightLines.includes(lineNumber)
            return {
              style: {
                backgroundColor: isHighlighted ? 'rgba(255, 255, 0, 0.1)' : 'transparent',
                display: 'block',
                width: '100%',
              }
            }
          }}
          customStyle={{
            margin: 0,
            borderRadius: 0,
            fontSize: '14px',
            lineHeight: '1.5',
          }}
        >
          {code}
        </SyntaxHighlighter>
      </div>
    </div>
  )
}

export default CodeSnippet