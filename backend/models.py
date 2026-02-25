from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class CrawlStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class CrawlRequest(BaseModel):
    url: HttpUrl
    max_pages: int = 100
    respect_robots_txt: bool = True
    check_core_web_vitals: bool = True


class PageIssue(BaseModel):
    url: str
    issue_type: str  # 'broken_link', 'missing_h1', 'duplicate_meta', 'missing_alt', 'redirect_chain'
    severity: str  # 'error', 'warning', 'info'
    message: str
    details: Optional[Dict[str, Any]] = None


class CoreWebVitals(BaseModel):
    lcp: Optional[float] = None  # Largest Contentful Paint
    cls: Optional[float] = None  # Cumulative Layout Shift
    fid: Optional[float] = None  # First Input Delay (deprecated, keeping for compatibility)
    inp: Optional[float] = None  # Interaction to Next Paint
    ttfb: Optional[float] = None  # Time to First Byte
    score: Optional[int] = None  # Overall performance score (0-100)


class PageData(BaseModel):
    url: str
    status_code: int
    title: Optional[str] = None
    meta_description: Optional[str] = None
    h1: Optional[str] = None
    h2s: List[str] = []
    images_without_alt: List[str] = []
    internal_links: List[str] = []
    external_links: List[str] = []
    core_web_vitals: Optional[CoreWebVitals] = None
    crawl_time: datetime
    page_size_kb: Optional[float] = None
    load_time_ms: Optional[float] = None


class CrawlResult(BaseModel):
    task_id: str
    status: CrawlStatus
    base_url: str
    pages_crawled: int
    max_pages: int
    pages: List[PageData]
    issues: List[PageIssue]
    start_time: datetime
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None


class KeywordData(BaseModel):
    keyword: str
    position: int
    search_volume: Optional[int] = None
    cpc: Optional[float] = None  # Cost per click
    competition: Optional[float] = None  # 0-1 scale
    url: Optional[str] = None
    estimated_traffic: Optional[int] = None


class DomainKeywords(BaseModel):
    domain: str
    keywords: List[KeywordData]
    total_keywords: int
    total_traffic_estimate: int
    fetched_at: datetime


class KeywordGapRequest(BaseModel):
    domain_a: str
    domain_b: str
    max_keywords: int = 100


class KeywordGapResult(BaseModel):
    domain_a: str
    domain_b: str
    keywords_only_in_a: List[KeywordData]  # A \ B
    keywords_only_in_b: List[KeywordData]  # B \ A
    common_keywords: List[KeywordData]  # A ∩ B
    gap_opportunities: List[KeywordData]  # High value keywords in B not in A


class ShareOfVoiceRequest(BaseModel):
    domains: List[str]
    keywords: List[str]


class DomainSoV(BaseModel):
    domain: str
    visibility_score: float
    estimated_ctr: float
    total_search_volume: int
    weighted_position: float


class ShareOfVoiceResult(BaseModel):
    request_date: datetime
    domains: List[DomainSoV]
    market_total_volume: int


class CompetitorOverview(BaseModel):
    domain: str
    authority_score: Optional[int] = None
    organic_traffic: Optional[int] = None
    paid_traffic: Optional[int] = None
    backlink_count: Optional[int] = None
    referring_domains: Optional[int] = None
    top_keywords: List[KeywordData] = []
    traffic_trend: List[Dict[str, Any]] = []  # date, traffic pairs
