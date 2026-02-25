import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

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

export const apiClient = {
  // Crawler
  startCrawl: (data: CrawlRequest) => api.post('/api/crawl', data),
  getCrawlStatus: (taskId: string) => api.get(`/api/crawl/${taskId}`),
  getCrawlResult: (taskId: string) => api.get(`/api/crawl/${taskId}/result`),
  
  // Competitive Intelligence
  startKeywordGap: (data: KeywordGapRequest) => api.post('/api/competitive/keyword-gap', data),
  getKeywordGapResult: (taskId: string) => api.get(`/api/competitive/keyword-gap/${taskId}`),
  
  startShareOfVoice: (data: ShareOfVoiceRequest) => api.post('/api/competitive/share-of-voice', data),
  getShareOfVoiceResult: (taskId: string) => api.get(`/api/competitive/share-of-voice/${taskId}`),
  
  getCompetitorOverview: (domain: string) => api.get(`/api/competitive/overview/${domain}`),
  getOverviewResult: (taskId: string) => api.get(`/api/competitive/overview/result/${taskId}`),
  
  // Dashboard
  getDashboardStats: () => api.get('/api/dashboard/stats'),
}

export default apiClient
