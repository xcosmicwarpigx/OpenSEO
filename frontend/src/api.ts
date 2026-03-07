import axios from 'axios'

// Use same-origin by default so Cloudflare/public hostnames work without localhost leakage
const API_URL = import.meta.env.VITE_API_URL || ''

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Single source of truth for frontend -> backend routes
export const ENDPOINTS = {
  crawl: {
    start: '/api/crawl',
    status: (taskId: string) => `/api/crawl/${taskId}`,
    result: (taskId: string) => `/api/crawl/${taskId}/result`,
    deterministic: '/api/deterministic/crawl',
  },
  competitive: {
    keywordGapStart: '/api/competitive/keyword-gap',
    keywordGapStatus: (taskId: string) => `/api/competitive/keyword-gap/${taskId}`,
    keywordGapDeterministic: '/api/deterministic/competitive/keyword-gap',
    sovStart: '/api/competitive/share-of-voice',
    sovStatus: (taskId: string) => `/api/competitive/share-of-voice/${taskId}`,
    sovDeterministic: '/api/deterministic/competitive/share-of-voice',
    overviewStart: (domain: string) => `/api/competitive/overview/${domain}`,
    overviewStatus: (taskId: string) => `/api/competitive/overview/result/${taskId}`,
    overviewDeterministic: (domain: string) => `/api/deterministic/competitive/overview/${domain}`,
  },
  content: {
    analyzeDirect: '/api/tools/content-optimizer/analyze',
    start: '/api/tools/content-optimizer',
    status: (taskId: string) => `/api/tools/content-optimizer/${taskId}`,
  },
  bulk: {
    analyzeDirect: '/api/tools/bulk-url-analyzer/analyze',
    start: '/api/tools/bulk-url-analyzer',
    status: (taskId: string) => `/api/tools/bulk-url-analyzer/${taskId}`,
  },
  audit: {
    full: '/api/audit/full',
  },
  dashboard: {
    stats: '/api/dashboard/stats',
    catalog: '/api/catalog',
  },
} as const

export interface CrawlRequest {
  url: string
  max_pages?: number
  respect_robots_txt?: boolean
  check_core_web_vitals?: boolean
}

export interface KeywordGapRequest {
  domain_a: string
  domain_b: string
  max_keywords?: number
}

export interface ShareOfVoiceRequest {
  domains: string[]
  keywords: string[]
}

export interface ContentOptimizerRequest {
  url: string
  target_keywords?: string[]
  competitor_urls?: string[]
}

export interface BulkUrlRequest {
  urls: string[]
  checks?: string[]
}

export const apiClient = {
  // Crawler
  startCrawl: (data: CrawlRequest) => api.post(ENDPOINTS.crawl.start, data),
  getCrawlStatus: (taskId: string) => api.get(ENDPOINTS.crawl.status(taskId)),
  getCrawlResult: (taskId: string) => api.get(ENDPOINTS.crawl.result(taskId)),
  runCrawlDeterministic: (data: CrawlRequest, timeoutSeconds = 180) =>
    api.post(`${ENDPOINTS.crawl.deterministic}?timeout_seconds=${timeoutSeconds}`, data),

  // Competitive Intelligence
  startKeywordGap: (data: KeywordGapRequest) => api.post(ENDPOINTS.competitive.keywordGapStart, data),
  getKeywordGapResult: (taskId: string) => api.get(ENDPOINTS.competitive.keywordGapStatus(taskId)),
  runKeywordGapDeterministic: (data: KeywordGapRequest, timeoutSeconds = 120) =>
    api.post(`${ENDPOINTS.competitive.keywordGapDeterministic}?timeout_seconds=${timeoutSeconds}`, data),

  startShareOfVoice: (data: ShareOfVoiceRequest) => api.post(ENDPOINTS.competitive.sovStart, data),
  getShareOfVoiceResult: (taskId: string) => api.get(ENDPOINTS.competitive.sovStatus(taskId)),
  runShareOfVoiceDeterministic: (data: ShareOfVoiceRequest, timeoutSeconds = 120) =>
    api.post(`${ENDPOINTS.competitive.sovDeterministic}?timeout_seconds=${timeoutSeconds}`, data),

  getCompetitorOverview: (domain: string) => api.get(ENDPOINTS.competitive.overviewStart(domain)),
  getOverviewResult: (taskId: string) => api.get(ENDPOINTS.competitive.overviewStatus(taskId)),
  getOverviewDeterministic: (domain: string, timeoutSeconds = 120) =>
    api.get(`${ENDPOINTS.competitive.overviewDeterministic(domain)}?timeout_seconds=${timeoutSeconds}`),

  // Content Optimizer
  analyzeContentDirect: (data: ContentOptimizerRequest) => api.post(ENDPOINTS.content.analyzeDirect, data),
  startContentOptimizer: (data: ContentOptimizerRequest) => api.post(ENDPOINTS.content.start, data),
  getContentOptimizerResult: (taskId: string) => api.get(ENDPOINTS.content.status(taskId)),

  // Bulk URL Analyzer
  analyzeBulkDirect: (data: BulkUrlRequest) =>
    api.post(ENDPOINTS.bulk.analyzeDirect, data, {
      headers: { Accept: 'text/csv' },
    }),
  startBulkAnalyzer: (data: BulkUrlRequest) => api.post(ENDPOINTS.bulk.start, data),
  getBulkAnalyzerResult: (taskId: string) => api.get(ENDPOINTS.bulk.status(taskId)),

  // Dashboard + endpoint catalog
  getDashboardStats: () => api.get(ENDPOINTS.dashboard.stats),
  getApiCatalog: () => api.get(ENDPOINTS.dashboard.catalog),

  // Full audit
  runFullAudit: (data: { url: string; max_internal_urls?: number; target_keywords?: string[] }) =>
    api.post(ENDPOINTS.audit.full, data),
}

export default apiClient
