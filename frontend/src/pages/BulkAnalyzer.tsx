import { useState } from 'react'
import { apiClient } from '../api'
import { Loader2, Play, Download, CheckCircle, AlertCircle, XCircle } from 'lucide-react'

interface UrlResult {
  url: string
  status_code: number
  redirect_url?: string
  title?: string
  meta_description?: string
  h1?: string
  indexable: boolean
  issues: string[]
  response_time_ms: number
}

export default function BulkAnalyzer() {
  const [urls, setUrls] = useState('')
  const [checks, setChecks] = useState({
    status: true,
    meta: true,
    headers: true,
    performance: true
  })
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  const analyzeUrls = async () => {
    const urlList = urls.split('\n').map(u => u.trim()).filter(Boolean)
    if (urlList.length === 0) return
    
    setLoading(true)
    setError(null)
    
    try {
      const activeChecks = Object.entries(checks)
        .filter(([_, v]) => v)
        .map(([k, _]) => k)
      
      const res = await apiClient.analyzeBulkDirect({
        urls: urlList,
        checks: activeChecks
      })
      
      setResult(res.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  const downloadCSV = () => {
    if (!result?.export_csv) return
    
    const blob = new Blob([result.export_csv], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'url-analysis.csv'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
  }

  const getStatusIcon = (statusCode: number) => {
    if (statusCode === 200) return <CheckCircle className="text-green-600" size={20} />
    if (statusCode >= 300 && statusCode < 400) return <AlertCircle className="text-yellow-600" size={20} />
    return <XCircle className="text-red-600" size={20} />
  }

  return (
    <div>
      <h2 className="text-3xl font-bold text-gray-900 mb-2">Bulk URL Analyzer</h2>
      <p className="text-gray-500 mb-8">Analyze multiple URLs for common SEO issues in seconds</p>
      
      {/* Input Form */}
      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 mb-8">
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            URLs (one per line, max 50)
          </label>
          <textarea
            value={urls}
            onChange={(e) => setUrls(e.target.value)}
            placeholder="https://example.com/page1&#10;https://example.com/page2&#10;https://example.com/page3"
            rows={8}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent font-mono text-sm"
          />
        </div>
        
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">Checks to Run</label>
          <div className="flex gap-4">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={checks.status}
                onChange={(e) => setChecks({...checks, status: e.target.checked})}
                className="w-4 h-4 text-primary-600 rounded"
              />
              <span className="text-sm text-gray-700">Status Codes</span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={checks.meta}
                onChange={(e) => setChecks({...checks, meta: e.target.checked})}
                className="w-4 h-4 text-primary-600 rounded"
              />
              <span className="text-sm text-gray-700">Meta Data</span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={checks.headers}
                onChange={(e) => setChecks({...checks, headers: e.target.checked})}
                className="w-4 h-4 text-primary-600 rounded"
              />
              <span className="text-sm text-gray-700">Indexability</span>
            </label>
          </div>
        </div>
        
        <div className="flex gap-4">
          <button
            onClick={analyzeUrls}
            disabled={loading || !urls.trim()}
            className="flex items-center gap-2 px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <Loader2 className="animate-spin" size={20} />
                Analyzing {urls.split('\n').filter(Boolean).length} URLs...
              </>
            ) : (
              <>
                <Play size={20} />
                Analyze URLs
              </>
            )}
          </button>
          
          {result && (
            <button
              onClick={downloadCSV}
              className="flex items-center gap-2 px-6 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
            >
              <Download size={20} />
              Download CSV
            </button>
          )}
        </div>
      </div>
      
      {error && (
        <div className="bg-red-50 border border-red-200 p-4 rounded-lg mb-8 flex items-center gap-3">
          <AlertCircle className="text-red-600" size={20} />
          <p className="text-red-700">{error}</p>
        </div>
      )}
      
      {result && (
        <div className="space-y-6">
          {/* Summary Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white p-4 rounded-lg border border-gray-200">
              <p className="text-sm text-gray-500">Total URLs</p>
              <p className="text-2xl font-bold text-gray-900">{result.summary?.total_urls}</p>
            </div>
            <div className="bg-white p-4 rounded-lg border border-gray-200">
              <p className="text-sm text-gray-500">200 OK</p>
              <p className="text-2xl font-bold text-green-600">{result.summary?.status_200}</p>
            </div>
            <div className="bg-white p-4 rounded-lg border border-gray-200">
              <p className="text-sm text-gray-500">Redirects</p>
              <p className="text-2xl font-bold text-yellow-600">{result.summary?.redirects}</p>
            </div>
            <div className="bg-white p-4 rounded-lg border border-gray-200">
              <p className="text-sm text-gray-500">Errors</p>
              <p className="text-2xl font-bold text-red-600">
                {result.summary?.errors + result.summary?.timeouts}
              </p>
            </div>
          </div>
          
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-white p-4 rounded-lg border border-gray-200">
              <p className="text-sm text-gray-500">Missing Titles</p>
              <p className="text-2xl font-bold text-red-600">{result.summary?.missing_titles}</p>
            </div>
            <div className="bg-white p-4 rounded-lg border border-gray-200">
              <p className="text-sm text-gray-500">Missing Meta</p>
              <p className="text-2xl font-bold text-red-600">{result.summary?.missing_meta}</p>
            </div>
            <div className="bg-white p-4 rounded-lg border border-gray-200">
              <p className="text-sm text-gray-500">Missing H1</p>
              <p className="text-2xl font-bold text-red-600">{result.summary?.missing_h1}</p>
            </div>
          </div>
          
          {/* Results Table */}
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
              <h3 className="text-lg font-semibold text-gray-900">Results</h3>
              <p className="text-sm text-gray-500">
                Avg Response: {result.summary?.avg_response_time_ms}ms
              </p>
            </div>
            <div className="overflow-x-auto max-h-96 overflow-y-auto">
              <table className="w-full">
                <thead className="bg-gray-50 sticky top-0">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">URL</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Title</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">H1</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Issues</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {result.results?.map((r: UrlResult, idx: number) => (
                    <tr key={idx} className="hover:bg-gray-50">
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          {getStatusIcon(r.status_code)}
                          <span className="text-sm font-medium">{r.status_code}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900 truncate max-w-xs" title={r.url}>
                        {r.url}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-500 truncate max-w-xs">
                        {r.title || '-'}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-500 truncate max-w-xs">
                        {r.h1 || '-'}
                      </td>
                      <td className="px-4 py-3">
                        {r.issues.length > 0 ? (
                          <span className="text-xs text-red-600">
                            {r.issues.join(', ')}
                          </span>
                        ) : (
                          <CheckCircle className="text-green-600" size={16} />
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
