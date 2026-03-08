import { FormEvent, useMemo, useState } from 'react'
import { apiClient } from '../api'
import { Download, Loader2, Sparkles, Target, Wrench, Zap } from 'lucide-react'

type ScoreMap = {
  technical: number
  content: number
  performance_local: number
  accessibility: number
  security: number
  internal_linking: number
  mobile_seo: number
}

type RecommendationItem = {
  text: string
  priority: 'high' | 'medium' | 'low'
  effort: 'low' | 'medium' | 'high'
  impact: 'high' | 'medium' | 'low'
}

type AuditResult = {
  url: string
  overall_score: number
  grade: string
  scores: ScoreMap
  highlights?: Record<string, unknown>
  recommendations: string[]
  mode: string
}

function getGradeColor(grade: string): string {
  if (grade === 'A') return 'text-green-600'
  if (grade === 'B') return 'text-lime-600'
  if (grade === 'C') return 'text-yellow-600'
  if (grade === 'D') return 'text-orange-600'
  return 'text-red-600'
}

function scoreBarColor(score: number): string {
  if (score >= 85) return 'bg-green-500'
  if (score >= 70) return 'bg-yellow-500'
  if (score >= 55) return 'bg-orange-500'
  return 'bg-red-500'
}

function classifyRecommendation(text: string): RecommendationItem {
  const lower = text.toLowerCase()

  let priority: RecommendationItem['priority'] = 'low'
  let effort: RecommendationItem['effort'] = 'medium'
  let impact: RecommendationItem['impact'] = 'medium'

  if (
    lower.includes('critical') ||
    lower.includes('broken') ||
    lower.includes('noindex') ||
    lower.includes('missing title') ||
    lower.includes('missing meta') ||
    lower.includes('h1')
  ) {
    priority = 'high'
    impact = 'high'
  } else if (
    lower.includes('security') ||
    lower.includes('accessibility') ||
    lower.includes('schema')
  ) {
    priority = 'medium'
    impact = 'high'
  }

  if (lower.includes('add ') || lower.includes('fix ') || lower.includes('include ')) {
    effort = 'low'
  }
  if (lower.includes('restructure') || lower.includes('migrate') || lower.includes('refactor')) {
    effort = 'high'
  }

  return { text, priority, effort, impact }
}

function toLabel(value: string): string {
  return value.charAt(0).toUpperCase() + value.slice(1)
}

function downloadFile(filename: string, content: string, mimeType: string): void {
  const blob = new Blob([content], { type: mimeType })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

export default function Dashboard() {
  const [url, setUrl] = useState('')
  const [keywords, setKeywords] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [audit, setAudit] = useState<AuditResult | null>(null)

  const enrichedRecommendations = useMemo(() => {
    if (!audit) return []
    return audit.recommendations.map(classifyRecommendation)
  }, [audit])

  const quickWins = useMemo(
    () => enrichedRecommendations.filter((r) => r.effort === 'low').slice(0, 6),
    [enrichedRecommendations],
  )

  const biggerProjects = useMemo(
    () => enrichedRecommendations.filter((r) => r.effort !== 'low').slice(0, 6),
    [enrichedRecommendations],
  )

  async function runAudit(e: FormEvent<HTMLFormElement>): Promise<void> {
    e.preventDefault()
    setError(null)
    setAudit(null)
    setIsLoading(true)

    try {
      const targetKeywords = keywords
        .split(',')
        .map((k) => k.trim())
        .filter(Boolean)

      const response = await apiClient.runFullAudit({
        url,
        target_keywords: targetKeywords,
      })

      setAudit(response.data as AuditResult)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to run full audit.'
      setError(message)
    } finally {
      setIsLoading(false)
    }
  }

  function exportJson(): void {
    if (!audit) return
    const safeHost = audit.url.replace(/https?:\/\//, '').replace(/[^a-z0-9.-]/gi, '_')
    downloadFile(`${safeHost}-audit.json`, JSON.stringify(audit, null, 2), 'application/json')
  }

  function exportHtml(): void {
    if (!audit) return

    const scoreRows = Object.entries(audit.scores)
      .map(([k, v]) => `<tr><td>${k}</td><td>${v}</td></tr>`)
      .join('')

    const recRows = enrichedRecommendations
      .map(
        (r) =>
          `<tr><td>${r.text}</td><td>${r.priority}</td><td>${r.impact}</td><td>${r.effort}</td></tr>`,
      )
      .join('')

    const html = `<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>OpenSEO Report - ${audit.url}</title>
  <style>
    body { font-family: Inter, Arial, sans-serif; margin: 32px; color: #111827; }
    h1,h2 { margin: 0 0 12px; }
    .meta { margin-bottom: 24px; color: #4b5563; }
    table { border-collapse: collapse; width: 100%; margin: 16px 0 28px; }
    th, td { border: 1px solid #e5e7eb; padding: 10px; text-align: left; }
    th { background: #f9fafb; }
  </style>
</head>
<body>
  <h1>OpenSEO One-Stop Audit Report</h1>
  <p class="meta"><strong>URL:</strong> ${audit.url}<br/><strong>Overall Score:</strong> ${audit.overall_score} (${audit.grade})<br/><strong>Mode:</strong> ${audit.mode}</p>

  <h2>Category Scores</h2>
  <table>
    <thead><tr><th>Category</th><th>Score</th></tr></thead>
    <tbody>${scoreRows}</tbody>
  </table>

  <h2>Prioritized Recommendations</h2>
  <table>
    <thead><tr><th>Recommendation</th><th>Priority</th><th>Impact</th><th>Effort</th></tr></thead>
    <tbody>${recRows}</tbody>
  </table>
</body>
</html>`

    const safeHost = audit.url.replace(/https?:\/\//, '').replace(/[^a-z0-9.-]/gi, '_')
    downloadFile(`${safeHost}-audit.html`, html, 'text/html')
  }

  return (
    <div>
      <div className="mb-6 sm:mb-8">
        <h2 className="text-2xl sm:text-3xl font-bold text-gray-900">SEO Command Center</h2>
        <p className="text-gray-600 mt-2">
          Enter one URL and get a full SEO scorecard, prioritized fixes, and exportable reports.
        </p>
      </div>

      <form onSubmit={runAudit} className="bg-white border border-gray-100 rounded-xl p-4 sm:p-6 shadow-sm mb-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="lg:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-2">Website URL</label>
            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Target Keywords (optional)</label>
            <input
              type="text"
              value={keywords}
              onChange={(e) => setKeywords(e.target.value)}
              placeholder="seo audit, technical seo"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
        </div>

        <div className="mt-5 flex flex-wrap items-center gap-3">
          <button
            type="submit"
            disabled={isLoading}
            className="inline-flex items-center gap-2 bg-primary-600 text-white px-5 py-3 rounded-lg hover:bg-primary-700 disabled:opacity-60"
          >
            {isLoading ? <Loader2 size={18} className="animate-spin" /> : <Sparkles size={18} />}
            {isLoading ? 'Running Full Audit...' : 'Run One-Stop Audit'}
          </button>

          {audit && (
            <>
              <button
                type="button"
                onClick={exportJson}
                className="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                <Download size={16} /> JSON
              </button>
              <button
                type="button"
                onClick={exportHtml}
                className="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                <Download size={16} /> HTML Report
              </button>
            </>
          )}
        </div>

        {error && <p className="mt-4 text-sm text-red-600">{error}</p>}
      </form>

      {audit && (
        <div className="space-y-8">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
            <div className="bg-white p-4 sm:p-6 rounded-xl border border-gray-100 shadow-sm">
              <p className="text-sm text-gray-500">Overall Score</p>
              <p className="text-3xl sm:text-4xl font-bold text-gray-900 mt-2">{audit.overall_score}</p>
            </div>
            <div className="bg-white p-4 sm:p-6 rounded-xl border border-gray-100 shadow-sm">
              <p className="text-sm text-gray-500">Letter Grade</p>
              <p className={`text-3xl sm:text-4xl font-bold mt-2 ${getGradeColor(audit.grade)}`}>{audit.grade}</p>
            </div>
            <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm">
              <p className="text-sm text-gray-500">Mode</p>
              <p className="text-xl font-semibold text-gray-900 mt-2">{audit.mode}</p>
            </div>
          </div>

          <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Category Breakdown</h3>
            <div className="space-y-4">
              {Object.entries(audit.scores).map(([key, value]) => (
                <div key={key}>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm text-gray-700">{key.replace('_', ' ')}</span>
                    <span className="text-sm font-medium text-gray-900">{value}</span>
                  </div>
                  <div className="w-full h-2 bg-gray-100 rounded-full">
                    <div
                      className={`h-2 rounded-full ${scoreBarColor(value)}`}
                      style={{ width: `${Math.max(2, Math.min(100, value))}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Zap size={18} className="text-green-600" /> Quick Wins
              </h3>
              <ul className="space-y-3">
                {quickWins.length === 0 && <li className="text-sm text-gray-500">No quick wins found.</li>}
                {quickWins.map((r, idx) => (
                  <li key={`${r.text}-${idx}`} className="text-sm text-gray-700 border-b border-gray-100 pb-2">
                    <p>{r.text}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      Priority: {toLabel(r.priority)} · Impact: {toLabel(r.impact)} · Effort: {toLabel(r.effort)}
                    </p>
                  </li>
                ))}
              </ul>
            </div>

            <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Wrench size={18} className="text-orange-600" /> Bigger Projects
              </h3>
              <ul className="space-y-3">
                {biggerProjects.length === 0 && (
                  <li className="text-sm text-gray-500">No medium/high effort projects flagged.</li>
                )}
                {biggerProjects.map((r, idx) => (
                  <li key={`${r.text}-${idx}`} className="text-sm text-gray-700 border-b border-gray-100 pb-2">
                    <p>{r.text}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      Priority: {toLabel(r.priority)} · Impact: {toLabel(r.impact)} · Effort: {toLabel(r.effort)}
                    </p>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="bg-white p-4 sm:p-6 rounded-xl border border-gray-100 shadow-sm">
            <h3 className="text-base sm:text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Target size={18} className="text-primary-600" /> All Recommendations
            </h3>
            <div className="overflow-x-auto">
              <table className="min-w-[700px] w-full text-sm">
                <thead>
                  <tr className="text-left text-gray-500 border-b border-gray-100">
                    <th className="pb-2 pr-4">Recommendation</th>
                    <th className="pb-2 pr-4">Priority</th>
                    <th className="pb-2 pr-4">Impact</th>
                    <th className="pb-2">Effort</th>
                  </tr>
                </thead>
                <tbody>
                  {enrichedRecommendations.map((r, idx) => (
                    <tr key={`${r.text}-${idx}`} className="border-b border-gray-50">
                      <td className="py-2 pr-4 text-gray-800">{r.text}</td>
                      <td className="py-2 pr-4 text-gray-600">{toLabel(r.priority)}</td>
                      <td className="py-2 pr-4 text-gray-600">{toLabel(r.impact)}</td>
                      <td className="py-2 text-gray-600">{toLabel(r.effort)}</td>
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
