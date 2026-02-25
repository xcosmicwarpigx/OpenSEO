import asyncio
import time
from typing import Set, Dict, List, Optional
from urllib.parse import urljoin, urlparse, urldefrag
from datetime import datetime

from playwright.async_api import async_playwright, Page
from bs4 import BeautifulSoup
import httpx

from celery_app import celery_app
from models import (
    PageData, PageIssue, CoreWebVitals, CrawlStatus,
    CrawlResult, HeadingStructure, ImageAnalysis,
    InternalLinkingStats, SitemapAnalysis, RobotsTxtAnalysis,
    AccessibilityScore
)
from config import get_settings

# Import new analyzers
from utils.content_analyzer import calculate_readability, calculate_keyword_density, analyze_content_quality
from utils.schema_analyzer import extract_schema_types, detect_page_type_hints, get_missing_recommended_schemas
from utils.security_analyzer import analyze_security_headers
from utils.image_analyzer import analyze_images, generate_image_recommendations
from utils.accessibility_analyzer import analyze_accessibility
from utils.internal_linking_analyzer import analyze_internal_linking
from utils.sitemap_analyzer import fetch_sitemap, parse_sitemap, analyze_sitemap, fetch_robots_txt, parse_robots_txt

settings = get_settings()


async def get_pagespeed_insights(url: str) -> Optional[CoreWebVitals]:
    """Fetch Core Web Vitals from Google PageSpeed Insights API."""
    if not settings.google_pagespeed_api_key:
        return None
    
    api_url = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    params = {
        "url": url,
        "key": settings.google_pagespeed_api_key,
        "category": "PERFORMANCE"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(api_url, params=params, timeout=60)
            data = response.json()
            
            lighthouse = data.get("lighthouseResult", {})
            audits = lighthouse.get("audits", {})
            categories = lighthouse.get("categories", {})
            
            return CoreWebVitals(
                lcp=_extract_metric(audits, "largest-contentful-paint"),
                cls=_extract_metric(audits, "cumulative-layout-shift"),
                inp=_extract_metric(audits, "interaction-to-next-paint"),
                ttfb=_extract_metric(audits, "server-response-time"),
                score=categories.get("performance", {}).get("score", 0) * 100
            )
    except Exception as e:
        print(f"PageSpeed API error for {url}: {e}")
        return None


def _extract_metric(audits: dict, key: str) -> Optional[float]:
    metric = audits.get(key, {})
    numeric = metric.get("numericValue")
    return float(numeric) if numeric else None


async def crawl_page(
    page: Page,
    url: str,
    base_domain: str,
    check_cwv: bool = True,
    response_headers: Optional[Dict] = None
) -> tuple[PageData, List[str], List[PageIssue]]:
    """Crawl a single page with comprehensive analysis."""
    start_time = time.time()
    issues = []
    
    try:
        response = await page.goto(url, wait_until="networkidle", timeout=30000)
        status_code = response.status if response else 0
        
        # Get response headers for security analysis
        headers = {}
        try:
            if response:
                headers = await response.all_headers()
        except:
            pass
        
        # Check for HTTP errors
        if status_code >= 400:
            issues.append(PageIssue(
                url=url,
                issue_type="http_error",
                severity="error",
                message=f"HTTP {status_code} error"
            ))
        
        html = await page.content()
        soup = BeautifulSoup(html, 'lxml')
        
        # Extract content for analysis
        content_selectors = ['main', 'article', '[role="main"]', '.content', '#content', '.post']
        content_text = ""
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                content_text = content_elem.get_text(separator=' ', strip=True)
                break
        if not content_text:
            body = soup.find('body')
            if body:
                for script in body.find_all(['script', 'style', 'nav', 'header', 'footer']):
                    script.decompose()
                content_text = body.get_text(separator=' ', strip=True)
        
        # Extract metadata
        title = soup.title.string if soup.title else None
        meta_desc = None
        meta_tag = soup.find("meta", attrs={"name": "description"})
        if meta_tag:
            meta_desc = meta_tag.get("content")
        
        h1 = soup.find("h1")
        h1_text = h1.get_text(strip=True) if h1 else None
        h1_count = len(soup.find_all("h1"))
        
        h2s = [h2.get_text(strip=True) for h2 in soup.find_all("h2")]
        h3s = [h3.get_text(strip=True) for h3 in soup.find_all("h3")]
        h4s = [h4.get_text(strip=True) for h4 in soup.find_all("h4")]
        
        # Build heading structure
        heading_structure = []
        for i in range(1, 7):
            for h in soup.find_all(f'h{i}'):
                heading_structure.append(HeadingStructure(
                    level=i,
                    text=h.get_text(strip=True),
                    word_count=len(h.get_text(strip=True).split())
                ))
        
        # Check for missing H1
        if not h1:
            issues.append(PageIssue(
                url=url,
                issue_type="missing_h1",
                severity="error",
                message="Page is missing H1 tag"
            ))
        elif h1_count > 1:
            issues.append(PageIssue(
                url=url,
                issue_type="multiple_h1",
                severity="warning",
                message=f"Page has {h1_count} H1 tags (should be 1)"
            ))
        
        # Check for missing meta description
        if not meta_desc:
            issues.append(PageIssue(
                url=url,
                issue_type="missing_meta_description",
                severity="warning",
                message="Page is missing meta description"
            ))
        elif len(meta_desc) > 160:
            issues.append(PageIssue(
                url=url,
                issue_type="meta_description_too_long",
                severity="info",
                message=f"Meta description is {len(meta_desc)} chars (recommended < 160)"
            ))
        
        # Check title length
        if title:
            if len(title) < 30:
                issues.append(PageIssue(
                    url=url,
                    issue_type="title_too_short",
                    severity="info",
                    message=f"Title is {len(title)} chars (recommended 50-60)"
                ))
            elif len(title) > 60:
                issues.append(PageIssue(
                    url=url,
                    issue_type="title_too_long",
                    severity="info",
                    message=f"Title is {len(title)} chars (may be truncated in SERP)"
                ))
        
        # Analyze images
        images = analyze_images(soup, url)
        images_without_alt = [img.url for img in images if not img.alt_text]
        
        for img in images_without_alt[:3]:  # Limit issues reported
            issues.append(PageIssue(
                url=url,
                issue_type="missing_alt_text",
                severity="warning",
                message=f"Image missing alt text: {img[:50]}..."
            ))
        
        # Check for modern image formats
        non_modern_images = [img for img in images if not img.has_modern_format]
        if len(non_modern_images) > len(images) * 0.5:
            issues.append(PageIssue(
                url=url,
                issue_type="non_optimized_images",
                severity="info",
                message=f"{len(non_modern_images)} images not using modern formats (WebP/AVIF)"
            ))
        
        # Extract links
        internal_links = []
        external_links = []
        external_nofollow = []
        
        for link in soup.find_all("a", href=True):
            href = link["href"]
            full_url = urljoin(url, href)
            full_url, _ = urldefrag(full_url)
            
            is_nofollow = 'nofollow' in link.get('rel', [])
            parsed = urlparse(full_url)
            
            if parsed.netloc == base_domain or not parsed.netloc:
                internal_links.append(full_url)
            else:
                external_links.append(full_url)
                if is_nofollow:
                    external_nofollow.append(full_url)
        
        # Get Core Web Vitals if enabled
        cwv = None
        if check_cwv:
            cwv = await get_pagespeed_insights(url)
        
        # Calculate readability
        readability = calculate_readability(content_text, title or "", h1_text or "")
        
        # Analyze content quality
        content_quality = analyze_content_quality(content_text, heading_structure, [])
        
        if content_quality.thin_content:
            issues.append(PageIssue(
                url=url,
                issue_type="thin_content",
                severity="warning",
                message=f"Content may be too short ({readability.word_count} words)"
            ))
        
        if content_quality.missing_subheadings and readability.word_count > 500:
            issues.append(PageIssue(
                url=url,
                issue_type="missing_subheadings",
                severity="info",
                message="Long content without H2 subheadings"
            ))
        
        # Analyze structured data
        schemas = extract_schema_types(soup)
        page_hints = detect_page_type_hints(soup, url)
        missing_schemas = get_missing_recommended_schemas(schemas, page_hints)
        
        from models import SchemaAnalysis
        schema_analysis = SchemaAnalysis(
            schemas_found=schemas,
            missing_recommended=missing_schemas,
            total_schemas=len(schemas),
            valid_schemas=sum(1 for s in schemas if s.valid)
        )
        
        if missing_schemas:
            issues.append(PageIssue(
                url=url,
                issue_type="missing_structured_data",
                severity="info",
                message=f"Consider adding: {', '.join(s.value for s in missing_schemas[:2])}"
            ))
        
        # Analyze security headers
        security_headers = analyze_security_headers(headers)
        
        if security_headers.score < 50:
            issues.append(PageIssue(
                url=url,
                issue_type="security_headers",
                severity="warning",
                message=f"Security headers score: {security_headers.score}/100",
                details={"missing": security_headers.missing_headers}
            ))
        
        # Analyze accessibility
        accessibility = analyze_accessibility(soup, url)
        
        if accessibility.critical_issues > 0:
            issues.append(PageIssue(
                url=url,
                issue_type="accessibility_critical",
                severity="error",
                message=f"{accessibility.critical_issues} critical accessibility issues"
            ))
        
        if accessibility.serious_issues > 0:
            issues.append(PageIssue(
                url=url,
                issue_type="accessibility_serious",
                severity="warning",
                message=f"{accessibility.serious_issues} serious accessibility issues"
            ))
        
        load_time = (time.time() - start_time) * 1000
        
        page_data = PageData(
            url=url,
            status_code=status_code,
            title=title,
            title_length=len(title) if title else 0,
            meta_description=meta_desc,
            meta_description_length=len(meta_desc) if meta_desc else 0,
            h1=h1_text,
            h1_count=h1_count,
            h2s=h2s,
            h3s=h3s,
            h4s=h4s,
            heading_structure=heading_structure,
            images=images,
            images_without_alt=images_without_alt,
            internal_links=list(set(internal_links)),
            external_links=list(set(external_links)),
            external_links_nofollow=list(set(external_nofollow)),
            core_web_vitals=cwv,
            crawl_time=datetime.utcnow(),
            load_time_ms=load_time,
            word_count=readability.word_count,
            readability=readability,
            content_quality=content_quality,
            keyword_density=[],
            structured_data=schema_analysis,
            security_headers=security_headers,
            mobile_optimization=None,  # Would need viewport/device testing
            canonical_analysis=None,
            redirect_chain=None
        )
        
        return page_data, list(set(internal_links)), issues
        
    except Exception as e:
        issues.append(PageIssue(
            url=url,
            issue_type="crawl_error",
            severity="error",
            message=str(e)
        ))
        return PageData(
            url=url,
            status_code=0,
            crawl_time=datetime.utcnow()
        ), [], issues


@celery_app.task(bind=True, max_retries=3)
def crawl_website(self, base_url: str, max_pages: int = 100, check_cwv: bool = True) -> dict:
    """Celery task to crawl a website with comprehensive analysis."""
    task_id = self.request.id
    
    async def _crawl():
        parsed = urlparse(base_url)
        base_domain = parsed.netloc
        
        visited: Set[str] = set()
        to_visit: List[str] = [base_url]
        pages: List[PageData] = []
        all_issues: List[PageIssue] = []
        
        # Fetch sitemap and robots.txt first
        sitemap_content = await fetch_sitemap(base_url)
        robots_content = await fetch_robots_txt(base_url)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                while to_visit and len(visited) < max_pages:
                    current_url = to_visit.pop(0)
                    if current_url in visited:
                        continue
                    
                    visited.add(current_url)
                    
                    # Update progress
                    self.update_state(
                        state='PROGRESS',
                        meta={
                            'current': len(visited),
                            'total': max_pages,
                            'current_url': current_url
                        }
                    )
                    
                    page_data, new_links, issues = await crawl_page(
                        page, current_url, base_domain, check_cwv
                    )
                    
                    pages.append(page_data)
                    all_issues.extend(issues)
                    
                    # Add new internal links to queue
                    for link in new_links:
                        if link not in visited and link not in to_visit:
                            to_visit.append(link)
                
                await browser.close()
                
                # Analyze internal linking structure
                pages_dict = [p.dict() for p in pages]
                internal_linking_stats = analyze_internal_linking(pages_dict, base_url)
                
                # Analyze sitemap
                sitemap_analysis = None
                if sitemap_content:
                    sitemap_urls = parse_sitemap(sitemap_content)
                    crawled_urls = [p.url for p in pages]
                    sitemap_analysis = analyze_sitemap(sitemap_urls, crawled_urls)
                
                # Parse robots.txt
                robots_analysis = parse_robots_txt(robots_content or "", base_url)
                
                # Generate accessibility summary
                accessibility_summary = {
                    "avg_score": sum(p.readability.flesch_reading_ease or 0 for p in pages if p.readability) / len([p for p in pages if p.readability]) if pages else 0,
                    "total_issues": sum(1 for i in all_issues if i.issue_type.startswith("accessibility_")),
                    "pages_with_critical": len(set(i.url for i in all_issues if i.severity == "error" and i.issue_type.startswith("accessibility_")))
                }
                
            except Exception as e:
                await browser.close()
                raise e
        
        return CrawlResult(
            task_id=task_id,
            status=CrawlStatus.COMPLETED,
            base_url=base_url,
            pages_crawled=len(pages),
            max_pages=max_pages,
            pages=pages,
            issues=all_issues,
            internal_linking_stats=internal_linking_stats,
            sitemap_analysis=sitemap_analysis,
            robots_txt_analysis=robots_analysis,
            accessibility_summary=accessibility_summary,
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow()
        ).dict()
    
    try:
        return asyncio.run(_crawl())
    except Exception as e:
        self.retry(countdown=60, exc=e)