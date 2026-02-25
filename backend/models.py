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


# ==================== CONTENT ANALYSIS ====================

class ReadabilityScore(BaseModel):
    flesch_reading_ease: Optional[float] = None
    flesch_kincaid_grade: Optional[float] = None
    word_count: int = 0
    sentence_count: int = 0
    avg_words_per_sentence: float = 0
    complex_words_count: int = 0
    reading_time_minutes: float = 0


class KeywordDensity(BaseModel):
    keyword: str
    count: int
    density_percent: float
    in_title: bool
    in_h1: bool
    in_meta_description: bool
    in_first_100_words: bool


class HeadingStructure(BaseModel):
    level: int  # 1-6
    text: str
    word_count: int


class ContentQuality(BaseModel):
    thin_content: bool  # < 300 words
    duplicate_content_risk: bool
    keyword_stuffing_detected: bool
    large_paragraphs: List[str]  # Paragraphs > 150 words
    missing_subheadings: bool


# ==================== IMAGE ANALYSIS ====================

class ImageAnalysis(BaseModel):
    url: str
    alt_text: Optional[str] = None
    dimensions: Optional[Dict[str, int]] = None  # width, height
    file_size_kb: Optional[float] = None
    format: Optional[str] = None  # jpeg, png, webp, avif, etc.
    is_lazy_loaded: bool = False
    has_modern_format: bool = False  # webp, avif
    oversized: bool = False  # > 200KB without good reason
    responsive_srcset: bool = False


# ==================== INTERNAL LINKING ====================

class LinkAnalysis(BaseModel):
    url: str
    link_text: str
    is_nofollow: bool
    is_external: bool
    click_depth: int  # How many clicks from homepage


class InternalLinkingStats(BaseModel):
    total_internal_links: int
    unique_internal_links: int
    orphan_pages: List[str]  # Pages with 0 internal links
    pages_with_few_links: List[Dict[str, Any]]  # Pages with < 3 internal links
    most_linked_pages: List[Dict[str, Any]]  # Top 10 by link count
    avg_links_per_page: float
    max_click_depth: int


# ==================== SCHEMA / STRUCTURED DATA ====================

class SchemaType(str, Enum):
    ARTICLE = "Article"
    PRODUCT = "Product"
    ORGANIZATION = "Organization"
    WEBSITE = "WebSite"
    BREADCRUMB = "BreadcrumbList"
    FAQ = "FAQPage"
    HOWTO = "HowTo"
    REVIEW = "Review"
    AGGREGATE_RATING = "AggregateRating"
    LOCAL_BUSINESS = "LocalBusiness"
    EVENT = "Event"
    VIDEO = "VideoObject"
    OTHER = "Other"


class StructuredData(BaseModel):
    schema_type: SchemaType
    raw_json: Dict[str, Any]
    valid: bool
    validation_errors: List[str] = []
    recommended_fields_missing: List[str] = []


class SchemaAnalysis(BaseModel):
    schemas_found: List[StructuredData]
    missing_recommended: List[SchemaType]  # Schemas that should be present but aren't
    total_schemas: int
    valid_schemas: int


# ==================== SECURITY HEADERS ====================

class SecurityHeaders(BaseModel):
    content_security_policy: Optional[str] = None
    strict_transport_security: Optional[str] = None
    x_content_type_options: Optional[str] = None
    x_frame_options: Optional[str] = None
    referrer_policy: Optional[str] = None
    permissions_policy: Optional[str] = None
    score: int  # 0-100
    missing_headers: List[str]
    recommendations: List[str]


# ==================== PERFORMANCE BUDGET ====================

class ResourceBreakdown(BaseModel):
    html_size_kb: float
    css_size_kb: float
    js_size_kb: float
    images_size_kb: float
    fonts_size_kb: float
    other_size_kb: float
    total_size_kb: float


class PerformanceBudget(BaseModel):
    resource_breakdown: ResourceBreakdown
    request_count: int
    exceeds_budget: bool
    budget_violations: List[str]  # What exceeded limits
    recommendations: List[str]


# ==================== SITEMAP & ROBOTS ====================

class SitemapUrl(BaseModel):
    loc: str
    lastmod: Optional[str] = None
    changefreq: Optional[str] = None
    priority: Optional[float] = None
    in_crawl: bool = False  # Was this URL found in the crawl?


class SitemapAnalysis(BaseModel):
    sitemap_url: str
    urls_found: int
    urls: List[SitemapUrl]
    urls_not_in_crawl: List[str]  # In sitemap but not crawled
    invalid_urls: List[str]
    last_modified_fresh: bool


class RobotsTxtAnalysis(BaseModel):
    has_robots_txt: bool
    sitemap_reference: Optional[str] = None
    disallowed_paths: List[str]
    crawl_delay: Optional[int] = None
    issues: List[str]


# ==================== ACCESSIBILITY ====================

class AccessibilityIssue(BaseModel):
    wcag_guideline: str  # e.g., "1.1.1", "2.4.4"
    severity: str  # critical, serious, moderate, minor
    element: str
    message: str
    recommendation: str


class AccessibilityScore(BaseModel):
    score: int  # 0-100
    issues: List[AccessibilityIssue]
    passed_checks: List[str]
    critical_issues: int
    serious_issues: int


# ==================== CANONICAL & REDIRECTS ====================

class RedirectChain(BaseModel):
    start_url: str
    final_url: str
    hops: List[str]
    hop_count: int
    has_loop: bool


class CanonicalAnalysis(BaseModel):
    url: str
    canonical_url: Optional[str] = None
    self_canonical: bool  # Points to itself
    canonicalized_to_other: bool  # Points to different URL
    missing_canonical: bool
    issues: List[str]


# ==================== MOBILE OPTIMIZATION ====================

class MobileOptimization(BaseModel):
    has_viewport_meta: bool
    viewport_content: Optional[str] = None
    touch_target_issues: List[Dict[str, Any]]  # Elements too small for touch
    font_size_issues: List[str]  # Text too small
    uses_responsive_images: bool
    mobile_score: int  # 0-100
    recommendations: List[str]


# ==================== UPDATED PAGE DATA ====================

class PageIssue(BaseModel):
    url: str
    issue_type: str
    severity: str  # 'error', 'warning', 'info'
    message: str
    details: Optional[Dict[str, Any]] = None


class CoreWebVitals(BaseModel):
    lcp: Optional[float] = None
    cls: Optional[float] = None
    fid: Optional[float] = None
    inp: Optional[float] = None
    ttfb: Optional[float] = None
    score: Optional[int] = None


class PageData(BaseModel):
    url: str
    status_code: int
    title: Optional[str] = None
    title_length: int = 0
    meta_description: Optional[str] = None
    meta_description_length: int = 0
    h1: Optional[str] = None
    h1_count: int = 0
    h2s: List[str] = []
    h3s: List[str] = []
    h4s: List[str] = []
    heading_structure: List[HeadingStructure] = []
    images: List[ImageAnalysis] = []
    images_without_alt: List[str] = []
    internal_links: List[str] = []
    external_links: List[str] = []
    external_links_nofollow: List[str] = []
    core_web_vitals: Optional[CoreWebVitals] = None
    crawl_time: datetime
    page_size_kb: Optional[float] = None
    load_time_ms: Optional[float] = None
    word_count: int = 0
    readability: Optional[ReadabilityScore] = None
    content_quality: Optional[ContentQuality] = None
    keyword_density: List[KeywordDensity] = []
    structured_data: Optional[SchemaAnalysis] = None
    security_headers: Optional[SecurityHeaders] = None
    performance_budget: Optional[PerformanceBudget] = None
    mobile_optimization: Optional[MobileOptimization] = None
    canonical_analysis: Optional[CanonicalAnalysis] = None
    redirect_chain: Optional[RedirectChain] = None


class CrawlResult(BaseModel):
    task_id: str
    status: CrawlStatus
    base_url: str
    pages_crawled: int
    max_pages: int
    pages: List[PageData]
    issues: List[PageIssue]
    internal_linking_stats: Optional[InternalLinkingStats] = None
    sitemap_analysis: Optional[SitemapAnalysis] = None
    robots_txt_analysis: Optional[RobotsTxtAnalysis] = None
    accessibility_summary: Optional[Dict[str, Any]] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None


# ==================== COMPETITIVE INTELLIGENCE ====================

class KeywordData(BaseModel):
    keyword: str
    position: int
    search_volume: Optional[int] = None
    cpc: Optional[float] = None
    competition: Optional[float] = None
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
    keywords_only_in_a: List[KeywordData]
    keywords_only_in_b: List[KeywordData]
    common_keywords: List[KeywordData]
    gap_opportunities: List[KeywordData]


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
    traffic_trend: List[Dict[str, Any]] = []


# ==================== CONTENT OPTIMIZER TOOL ====================

class ContentOptimizerRequest(BaseModel):
    url: str
    target_keywords: List[str] = []
    competitor_urls: List[str] = []


class ContentOptimizationSuggestion(BaseModel):
    category: str  # title, meta, headings, content, images, internal_links
    priority: str  # high, medium, low
    current_value: Optional[str] = None
    suggested_value: Optional[str] = None
    issue: str
    recommendation: str
    impact: str  # description of expected impact


class CompetitorContentComparison(BaseModel):
    your_metrics: Dict[str, Any]
    competitor_metrics: Dict[str, Dict[str, Any]]
    gaps: List[str]  # What competitors have that you don't
    opportunities: List[str]


class ContentOptimizerResult(BaseModel):
    url: str
    overall_score: int  # 0-100
    readability: ReadabilityScore
    suggestions: List[ContentOptimizationSuggestion]
    keyword_optimization: List[KeywordDensity]
    competitor_comparison: Optional[CompetitorContentComparison] = None
    content_quality: ContentQuality
    prioritized_actions: List[str]  # Top 5 actions to take


# ==================== BULK URL ANALYZER ====================

class BulkUrlRequest(BaseModel):
    urls: List[str]
    checks: List[str] = ["status", "meta", "headers", "performance"]


class UrlCheckResult(BaseModel):
    url: str
    status_code: int
    redirect_url: Optional[str] = None
    title: Optional[str] = None
    meta_description: Optional[str] = None
    h1: Optional[str] = None
    indexable: bool
    issues: List[str]
    response_time_ms: float


class BulkUrlResult(BaseModel):
    results: List[UrlCheckResult]
    summary: Dict[str, Any]
    export_csv: str  # CSV content for download