import { useState } from 'react'
import { apiClient } from '../api'
import { Loader2, Play, CheckCircle, AlertTriangle, BookOpen, Type, Image as ImageIcon, Link } from 'lucide-react'

interface ReadabilityScore {
  flesch_reading_ease: number
  flesch_kincaid_grade: number
  word_count: number
  sentence_count: number
  avg_words_per_sentence: number
  reading_time_minutes: number
}

interface Suggestion {
  category: string
  priority: 'high' | 'medium' | 'low'
  issue: string
  recommendation: string
  impact: string
  current_value?: string
  suggested_value?: string
}

export default function ContentOptimizer() {
  const [url, setUrl] = useState('')
  const [targetKeywords, setTargetKeywords] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  const analyzeContent = async () => {
    if (!url) return
    
    setLoading(true)
    setError(null)
    
    try {
      const keywords = targetKeywords.split(',').map(k => k.trim()).filter(Boolean)
      const res = await apiClient.analyzeContentDirect({
        url,
        target_keywords: keywords
      })
      
      setResult(res.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'title': return <Type size={18} />
      case 'meta': return <BookOpen size={18} />
      case 'content': return <BookOpen size={18} />
      case 'headings': return <Type size={18} />
      case 'images': return <ImageIcon size={18} />
      case 'internal_links': return <Link size={18} />
      default: return <CheckCircle size={18} />
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-800'
      case 'medium': return 'bg-yellow-100 text-yellow-800'
      case 'low': return 'bg-blue-100 text-blue-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600'
    if (score >= 60) return 'text-yellow-600'
    return 'text-red-600'
  }

  return (
    <div>
      <h2 className="text-3xl font-bold text-gray-900 mb-2">Content Optimizer</h2>
      <p className="text-gray-500 mb-8">Analyze your content quality and get actionable optimization suggestions</p>
      
      {/* Input Form */}
      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 mb-8">
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">Page URL</label>
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com/blog/post"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </div>
        
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Target Keywords (comma-separated)
          </label>
          <input
            type="text"
            value={targetKeywords}
            onChange={(e) => setTargetKeywords(e.target.value)}
            placeholder="seo tools, content optimization, keyword research"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </div>
        
        <button
          onClick={analyzeContent}
          disabled={loading || !url}
          className="flex items-center gap-2 px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? (
            <>
              <Loader2 className="animate-spin" size={20} />
              Analyzing...
            </>
          ) : (
            <>
              <Play size={20} />
              Analyze Content
            </>
          )}
        </button>
      </div>
      
      {error && (
        <div className="bg-red-50 border border-red-200 p-4 rounded-lg mb-8 flex items-center gap-3">
          <AlertTriangle className="text-red-600" size={20} />
          <p className="text-red-700">{error}</p>
        </div>
      )}
      
      {result && (
        <div className="space-y-6">
          {/* Overall Score */}
          <div className="bg-white p-6 rounded-xl border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500 mb-1">Content Score</p>
                <p className={`text-5xl font-bold ${getScoreColor(result.overall_score)}`}>
                  {result.overall_score}
                </p>
                <p className="text-sm text-gray-400 mt-1">out of 100</p>
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-500 mb-1">Reading Level</p>
                <p className="text-2xl font-semibold text-gray-900">
                  Grade {Math.round(result.readability?.flesch_kincaid_grade || 0)}
                </p>
                <p className="text-sm text-gray-500 mt-1">
                  {result.readability?.word_count || 0} words
                </p>
              </div>
            </div>
          </div>
          
          {/* Readability Stats */}
          <div className="bg-white p-6 rounded-xl border border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Readability Analysis</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-500">Flesch Score</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {result.readability?.flesch_reading_ease?.toFixed(1) || '-'}
                </p>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-500">Sentences</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {result.readability?.sentence_count || '-'}
                </p>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-500">Words/Sentence</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {result.readability?.avg_words_per_sentence?.toFixed(1) || '-'}
                </p>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-500">Reading Time</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {result.readability?.reading_time_minutes?.toFixed(1) || '-'}m
                </p>
              </div>
            </div>
          </div>
          
          {/* Optimization Suggestions */}
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">
                Optimization Suggestions ({result.suggestions?.length || 0})
              </h3>
            </div>
            <div className="divide-y divide-gray-200">
              {result.suggestions?.map((suggestion: Suggestion, idx: number) => (
                <div key={idx} className="p-6 hover:bg-gray-50">
                  <div className="flex items-start gap-4">
                    <div className={`p-2 rounded-lg ${getPriorityColor(suggestion.priority)}`}>
                      {getCategoryIcon(suggestion.category)}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`px-2 py-0.5 rounded text-xs font-medium uppercase ${getPriorityColor(suggestion.priority)}`}>
                          {suggestion.priority}
                        </span>
                        <span className="text-sm text-gray-500 capitalize">
                          {suggestion.category.replace('_', ' ')}
                        </span>
                      </div>
                      <p className="font-medium text-gray-900 mb-1">{suggestion.issue}</p>
                      <p className="text-sm text-gray-600 mb-2">{suggestion.recommendation}</p>
                      {suggestion.current_value && (
                        <div className="flex gap-4 text-sm">
                          <span className="text-red-600 line-through">
                            Current: {suggestion.current_value}
                          </span>
                          {suggestion.suggested_value && (
                            <span className="text-green-600">
                              Suggested: {suggestion.suggested_value}
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
          
          {/* Keyword Optimization */}
          {result.keyword_optimization?.length > 0 && (
            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">Keyword Analysis</h3>
              </div>
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Keyword</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Count</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Density</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Placement</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {result.keyword_optimization.map((kw: any, idx: number) => (
                    <tr key={idx} className="hover:bg-gray-50">
                      <td className="px-6 py-4 text-sm font-medium text-gray-900">{kw.keyword}</td>
                      <td className="px-6 py-4 text-sm text-gray-500">{kw.count}</td>
                      <td className="px-6 py-4 text-sm text-gray-500">{kw.density_percent}%</td>
                      <td className="px-6 py-4 text-sm">
                        <div className="flex gap-2">
                          {kw.in_title && <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs">Title</span>}
                          {kw.in_h1 && <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">H1</span>}
                          {kw.in_meta_description && <span className="px-2 py-1 bg-purple-100 text-purple-800 rounded text-xs">Meta</span>}
                          {kw.in_first_100_words && <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded text-xs">Early</span>}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          
          {/* Priority Actions */}
          <div className="bg-gradient-to-r from-primary-500 to-primary-600 p-6 rounded-xl text-white">
            <h3 className="text-lg font-semibold mb-4">Top Priority Actions</h3>
            <ol className="list-decimal list-inside space-y-2">
              {result.prioritized_actions?.map((action: string, idx: number) => (
                <li key={idx} className="text-primary-50">{action}</li>
              ))}
            </ol>
          </div>
        </div>
      )}
    </div>
  )
}
