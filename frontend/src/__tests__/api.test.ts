import { describe, it, expect } from 'vitest'
import apiClient from '../api'

describe('apiClient', () => {
  it('exports all required methods', () => {
    expect(apiClient.startCrawl).toBeDefined()
    expect(apiClient.getCrawlStatus).toBeDefined()
    expect(apiClient.getCrawlResult).toBeDefined()
    expect(apiClient.startKeywordGap).toBeDefined()
    expect(apiClient.getKeywordGapResult).toBeDefined()
    expect(apiClient.startShareOfVoice).toBeDefined()
    expect(apiClient.getShareOfVoiceResult).toBeDefined()
    expect(apiClient.getCompetitorOverview).toBeDefined()
    expect(apiClient.getOverviewResult).toBeDefined()
    expect(apiClient.analyzeContentDirect).toBeDefined()
    expect(apiClient.startContentOptimizer).toBeDefined()
    expect(apiClient.getContentOptimizerResult).toBeDefined()
    expect(apiClient.analyzeBulkDirect).toBeDefined()
    expect(apiClient.startBulkAnalyzer).toBeDefined()
    expect(apiClient.getBulkAnalyzerResult).toBeDefined()
    expect(apiClient.getDashboardStats).toBeDefined()
  })
})