import { useState } from 'react'
import { apiClient } from '../api'
import { Play, Loader2, CheckCircle, AlertCircle, Globe, Clock, FileText } from 'lucide-react'

export default function Crawler() {
  const [url, setUrl] = useState('')
  const [maxPages, setMaxPages] = useState(50)
  const [checkCWV, setCheckCWV] = useState(true)
  const [loading, setLoading] = useState(false)
  const [taskId, setTaskId] = useState<string | null>(null)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  const startCrawl = async () => {
    if (!url) return
    
    setLoading(true)
    setError(null)
    
    try {
      const res = await apiClient.startCrawl({
        url,
        max_pages: maxPages,
        check_core_web_vitals: checkCWV
      })
      
      setTaskId(res.data.task_id)
      pollStatus(res.data.task_id)
    } catch (err: any) {
      setError(err.message)
      setLoading(false)
    }
  }

  const pollStatus = async (id: string) => {
    const interval = setInterval(async () => {
      try {
        const res = await apiClient.getCrawlStatus(id)
        
        if (res.data.status === 'SUCCESS') {
          clearInterval(interval)
          setResult(res.data.result)
          setLoading(false)
        } else if (res.data.status === 'FAILURE') {
          clearInterval(interval)
          setError(res.data.error || 'Crawl failed')
          setLoading(false)
        }
      } catch (err) {
        clearInterval(interval)
        setError('Failed to check status')
        setLoading(false)
      }
    }, 2000)
  }

  return (
    <div>
      <h2 className="text-3xl font-bold text-gray-900 mb-8">Site Crawler</h2>
      
      {/* Input Form */}
      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 mb-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="md:col-span-2">
            <label htmlFor="url-input" className="block text-sm font-medium text-gray-700 mb-2">
              Website URL
            </label>
            <input
              id="url-input"
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
          
          <div>
            <label htmlFor="max-pages-input" className="block text-sm font-medium text-gray-700 mb-2">
              Max Pages
            </label>
            <input
              id="max-pages-input"
              type="number"
              value={maxPages}
              onChange={(e) => setMaxPages(Number(e.target.value))}
              min={1}
              max={1000}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
        </div>
        
        <div className="flex items-center gap-4 mb-6">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={checkCWV}
              onChange={(e) => setCheckCWV(e.target.checked)}
              className="w-4 h-4 text-primary-600 rounded"
            />
            <span className="text-sm text-gray-700">Check Core Web Vitals (requires API key)</span>
          </label>
        </div>
        
        <button
          onClick={startCrawl}
          disabled={loading || !url}
          className="flex items-center gap-2 px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? (
            <>
              <Loader2 className="animate-spin" size={20} />
              Crawling...
            </>
          ) : (
            <>
              <Play size={20} />
              Start Crawl
            </>
          )}
        </button>
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
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white p-4 rounded-lg border border-gray-200">
              <div className="flex items-center gap-2 text-gray-500 mb-1">
                <Globe size={16} />
                <span className="text-sm">Pages Crawled</span>
              </div>
              <p className="text-2xl font-bold text-gray-900">{result.pages_crawled}</p>
            </div>
            
            <div className="bg-white p-4 rounded-lg border border-gray-200">
              <div className="flex items-center gap-2 text-gray-500 mb-1">
                <AlertCircle size={16} />
                <span className="text-sm">Issues Found</span>
              </div>
              <p className="text-2xl font-bold text-red-600">{result.issues?.length || 0}</p>
            </div>
            
            <div className="bg-white p-4 rounded-lg border border-gray-200">
              <div className="flex items-center gap-2 text-gray-500 mb-1">
                <Clock size={16} />
                <span className="text-sm">Avg Load Time</span>
              </div>
              <p className="text-2xl font-bold text-gray-900">
                {result.pages?.length > 0 
                  ? Math.round(result.pages.reduce((acc: number, p: any) => acc + (p.load_time_ms || 0), 0) / result.pages.length)
                  : 0}ms
              </p>
            </div>
            
            <div className="bg-white p-4 rounded-lg border border-gray-200">
              <div className="flex items-center gap-2 text-gray-500 mb-1">
                <FileText size={16} />
                <span className="text-sm">Total Size</span>
              </div>
              <p className="text-2xl font-bold text-gray-900">
                {result.pages?.length > 0 
                  ? (result.pages.reduce((acc: number, p: any) => acc + (p.page_size_kb || 0), 0) / 1024).toFixed(1)
                  : 0}MB
              </p>
            </div>
          </div>
          
          {/* Pages Table */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Crawled Pages</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">URL</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Title</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Load Time</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {result.pages?.map((page: any, idx: number) => (
                    <tr key={idx} className="hover:bg-gray-50">
                      <td className="px-6 py-4 text-sm text-gray-900 truncate max-w-xs">{page.url}</td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          page.status_code === 200 
                            ? 'bg-green-100 text-green-800' 
                            : page.status_code >= 400 
                              ? 'bg-red-100 text-red-800' 
                              : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {page.status_code}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500 truncate max-w-xs">{page.title || '-'}</td>
                      <td className="px-6 py-4 text-sm text-gray-500">{page.load_time_ms ? `${Math.round(page.load_time_ms)}ms` : '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          
          {/* Issues Table */}
          {result.issues?.length > 0 && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">Issues Found</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">URL</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Issue Type</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Severity</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Message</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {result.issues.map((issue: any, idx: number) => (
                      <tr key={idx} className="hover:bg-gray-50">
                        <td className="px-6 py-4 text-sm text-gray-900 truncate max-w-xs">{issue.url}</td>
                        <td className="px-6 py-4 text-sm text-gray-500">{issue.issue_type}</td>
                        <td className="px-6 py-4">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            issue.severity === 'error' 
                              ? 'bg-red-100 text-red-800' 
                              : issue.severity === 'warning' 
                                ? 'bg-yellow-100 text-yellow-800' 
                                : 'bg-blue-100 text-blue-800'
                          }`}>
                            {issue.severity}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-500">{issue.message}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
