import { useState } from 'react'
import { apiClient } from '../api'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { Search, Target, TrendingUp, Globe, Loader2, Play } from 'lucide-react'

const COLORS = ['#0ea5e9', '#22c55e', '#f59e0b', '#ef4444']

export default function Competitive() {
  const [activeTab, setActiveTab] = useState<'gap' | 'sov' | 'overview'>('gap')
  
  // Keyword Gap State
  const [domainA, setDomainA] = useState('')
  const [domainB, setDomainB] = useState('')
  
  // SoV State
  const [sovDomains, setSovDomains] = useState('')
  const [sovKeywords, setSovKeywords] = useState('')
  
  // Overview State
  const [overviewDomain, setOverviewDomain] = useState('')
  
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)

  const analyzeKeywordGap = async () => {
    if (!domainA || !domainB) return
    
    setLoading(true)
    try {
      const res = await apiClient.startKeywordGap({
        domain_a: domainA,
        domain_b: domainB
      })
      
      // Poll for result
      const interval = setInterval(async () => {
        const statusRes = await apiClient.getKeywordGapResult(res.data.task_id)
        if (statusRes.data.status === 'SUCCESS') {
          clearInterval(interval)
          setResult({ type: 'gap', data: statusRes.data.result })
          setLoading(false)
        }
      }, 2000)
    } catch (err) {
      setLoading(false)
    }
  }

  const calculateSoV = async () => {
    if (!sovDomains) return
    
    setLoading(true)
    try {
      const domains = sovDomains.split(',').map(d => d.trim())
      const keywords = sovKeywords.split(',').map(k => k.trim()).filter(Boolean)
      
      const res = await apiClient.startShareOfVoice({ domains, keywords })
      
      const interval = setInterval(async () => {
        const statusRes = await apiClient.getShareOfVoiceResult(res.data.task_id)
        if (statusRes.data.status === 'SUCCESS') {
          clearInterval(interval)
          setResult({ type: 'sov', data: statusRes.data.result })
          setLoading(false)
        }
      }, 2000)
    } catch (err) {
      setLoading(false)
    }
  }

  const getOverview = async () => {
    if (!overviewDomain) return
    
    setLoading(true)
    try {
      const res = await apiClient.getCompetitorOverview(overviewDomain)
      
      const interval = setInterval(async () => {
        const statusRes = await apiClient.getOverviewResult(res.data.task_id)
        if (statusRes.data.status === 'SUCCESS') {
          clearInterval(interval)
          setResult({ type: 'overview', data: statusRes.data.result })
          setLoading(false)
        }
      }, 2000)
    } catch (err) {
      setLoading(false)
    }
  }

  return (
    <div>
      <h2 className="text-3xl font-bold text-gray-900 mb-8">Competitive Intelligence</h2>
      
      {/* Tabs */}
      <div className="flex gap-4 mb-8">
        <button
          onClick={() => setActiveTab('gap')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium ${
            activeTab === 'gap' 
              ? 'bg-primary-100 text-primary-700' 
              : 'bg-white text-gray-600 hover:bg-gray-50'
          }`}
        >
          <Target size={18} />
          Keyword Gap
        </button>
        <button
          onClick={() => setActiveTab('sov')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium ${
            activeTab === 'sov' 
              ? 'bg-primary-100 text-primary-700' 
              : 'bg-white text-gray-600 hover:bg-gray-50'
          }`}
        >
          <TrendingUp size={18} />
          Share of Voice
        </button>
        <button
          onClick={() => setActiveTab('overview')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium ${
            activeTab === 'overview' 
              ? 'bg-primary-100 text-primary-700' 
              : 'bg-white text-gray-600 hover:bg-gray-50'
          }`}
        >
          <Globe size={18} />
          Competitor Overview
        </button>
      </div>

      {/* Keyword Gap Analysis */}
      {activeTab === 'gap' && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Compare Two Domains</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Your Domain</label>
                <input
                  type="text"
                  value={domainA}
                  onChange={(e) => setDomainA(e.target.value)}
                  placeholder="example.com"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Competitor Domain</label>
                <input
                  type="text"
                  value={domainB}
                  onChange={(e) => setDomainB(e.target.value)}
                  placeholder="competitor.com"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                />
              </div>
            </div>
            <button
              onClick={analyzeKeywordGap}
              disabled={loading || !domainA || !domainB}
              className="flex items-center gap-2 px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
            >
              {loading ? <Loader2 className="animate-spin" size={20} /> : <Play size={20} />}
              Analyze Gap
            </button>
          </div>

          {result?.type === 'gap' && (
            <>
              {/* Gap Summary */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-white p-6 rounded-xl border border-gray-200">
                  <p className="text-sm text-gray-500 mb-1">Unique to {result.data.domain_a}</p>
                  <p className="text-3xl font-bold text-primary-600">{result.data.keywords_only_in_a?.length}</p>
                </div>
                <div className="bg-white p-6 rounded-xl border border-gray-200">
                  <p className="text-sm text-gray-500 mb-1">Common Keywords</p>
                  <p className="text-3xl font-bold text-green-600">{result.data.common_keywords?.length}</p>
                </div>
                <div className="bg-white p-6 rounded-xl border border-gray-200">
                  <p className="text-sm text-gray-500 mb-1">Opportunities (in {result.data.domain_b} only)</p>
                  <p className="text-3xl font-bold text-amber-600">{result.data.keywords_only_in_b?.length}</p>
                </div>
              </div>

              {/* Gap Opportunities */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900">Top Opportunities</h3>
                  <p className="text-sm text-gray-500">High-value keywords your competitor ranks for</p>
                </div>
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Keyword</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Position</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Volume</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">CPC</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {result.data.gap_opportunities?.slice(0, 10).map((kw: any, idx: number) => (
                      <tr key={idx} className="hover:bg-gray-50">
                        <td className="px-6 py-4 text-sm font-medium text-gray-900">{kw.keyword}</td>
                        <td className="px-6 py-4 text-sm text-gray-500">#{kw.position}</td>
                        <td className="px-6 py-4 text-sm text-gray-500">{kw.search_volume?.toLocaleString()}</td>
                        <td className="px-6 py-4 text-sm text-gray-500">${kw.cpc}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      )}

      {/* Share of Voice */}
      {activeTab === 'sov' && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Calculate Share of Voice</h3>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">Domains (comma-separated)</label>
              <input
                type="text"
                value={sovDomains}
                onChange={(e) => setSovDomains(e.target.value)}
                placeholder="example.com, competitor1.com, competitor2.com"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">Keywords (comma-separated, optional)</label>
              <input
                type="text"
                value={sovKeywords}
                onChange={(e) => setSovKeywords(e.target.value)}
                placeholder="seo tools, keyword research, rank tracking..."
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <button
              onClick={calculateSoV}
              disabled={loading || !sovDomains}
              className="flex items-center gap-2 px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
            >
              {loading ? <Loader2 className="animate-spin" size={20} /> : <Play size={20} />}
              Calculate SoV
            </button>
          </div>

          {result?.type === 'sov' && (
            <>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                  <h3 className="text-lg font-semibold text-gray-900 mb-6">Visibility Distribution</h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={result.data.domains}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ domain, visibility_score }) => `${domain}: ${visibility_score}%`}
                        outerRadius={80}
                        dataKey="visibility_score"
                      >
                        {result.data.domains?.map((_: any, idx: number) => (
                          <Cell key={`cell-${idx}`} fill={COLORS[idx % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>

                <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                  <h3 className="text-lg font-semibold text-gray-900 mb-6">Domain Comparison</h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={result.data.domains}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis dataKey="domain" stroke="#6b7280" />
                      <YAxis stroke="#6b7280" />
                      <Tooltip />
                      <Bar dataKey="visibility_score" fill="#0ea5e9" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Domain</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Visibility Score</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Avg Position</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Est. CTR</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {result.data.domains?.map((d: any, idx: number) => (
                      <tr key={idx} className="hover:bg-gray-50">
                        <td className="px-6 py-4 text-sm font-medium text-gray-900">{d.domain}</td>
                        <td className="px-6 py-4 text-sm text-gray-900">{d.visibility_score}%</td>
                        <td className="px-6 py-4 text-sm text-gray-500">{d.weighted_position}</td>
                        <td className="px-6 py-4 text-sm text-gray-500">{(d.estimated_ctr * 100).toFixed(1)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      )}

      {/* Competitor Overview */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Domain Overview</h3>
            <div className="flex gap-4 mb-4">
              <input
                type="text"
                value={overviewDomain}
                onChange={(e) => setOverviewDomain(e.target.value)}
                placeholder="Enter domain (e.g., example.com)"
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              />
              <button
                onClick={getOverview}
                disabled={loading || !overviewDomain}
                className="flex items-center gap-2 px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
              >
                {loading ? <Loader2 className="animate-spin" size={20} /> : <Search size={20} />}
                Analyze
              </button>
            </div>
          </div>

          {result?.type === 'overview' && (
            <>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-white p-6 rounded-xl border border-gray-200">
                  <p className="text-sm text-gray-500 mb-1">Authority Score</p>
                  <p className="text-3xl font-bold text-primary-600">{result.data.authority_score}</p>
                </div>
                <div className="bg-white p-6 rounded-xl border border-gray-200">
                  <p className="text-sm text-gray-500 mb-1">Organic Traffic</p>
                  <p className="text-3xl font-bold text-green-600">{result.data.organic_traffic?.toLocaleString()}</p>
                </div>
                <div className="bg-white p-6 rounded-xl border border-gray-200">
                  <p className="text-sm text-gray-500 mb-1">Backlinks</p>
                  <p className="text-3xl font-bold text-amber-600">{result.data.backlink_count?.toLocaleString()}</p>
                </div>
                <div className="bg-white p-6 rounded-xl border border-gray-200">
                  <p className="text-sm text-gray-500 mb-1">Referring Domains</p>
                  <p className="text-3xl font-bold text-purple-600">{result.data.referring_domains?.toLocaleString()}</p>
                </div>
              </div>

              {/* Traffic Trend */}
              <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                <h3 className="text-lg font-semibold text-gray-900 mb-6">Traffic Trend</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={result.data.traffic_trend}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="month" stroke="#6b7280" />
                    <YAxis stroke="#6b7280" />
                    <Tooltip />
                    <Bar dataKey="traffic" fill="#0ea5e9" />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Top Keywords */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900">Top Keywords</h3>
                </div>
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Keyword</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Position</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Volume</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Est. Traffic</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {result.data.top_keywords?.map((kw: any, idx: number) => (
                      <tr key={idx} className="hover:bg-gray-50">
                        <td className="px-6 py-4 text-sm font-medium text-gray-900">{kw.keyword}</td>
                        <td className="px-6 py-4 text-sm text-gray-500">#{kw.position}</td>
                        <td className="px-6 py-4 text-sm text-gray-500">{kw.search_volume?.toLocaleString()}</td>
                        <td className="px-6 py-4 text-sm text-gray-500">{kw.estimated_traffic?.toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  )
}
