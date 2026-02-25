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
    CrawlResult
)
from config import get_settings

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
    check_cwv: bool = True
) -> tuple[PageData, List[str], List[PageIssue]]:
    """Crawl a single page and return page data, discovered links, and issues."""
    start_time = time.time()
    issues = []
    
    try:
        response = await page.goto(url, wait_until="networkidle", timeout=30000)
        status_code = response.status if response else 0
        
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
        
        # Extract metadata
        title = soup.title.string if soup.title else None
        meta_desc = None
        meta_tag = soup.find("meta", attrs={"name": "description"})
        if meta_tag:
            meta_desc = meta_tag.get("content")
        
        h1 = soup.find("h1")
        h1_text = h1.get_text(strip=True) if h1 else None
        h2s = [h2.get_text(strip=True) for h2 in soup.find_all("h2")]
        
        # Check for missing H1
        if not h1:
            issues.append(PageIssue(
                url=url,
                issue_type="missing_h1",
                severity="error",
                message="Page is missing H1 tag"
            ))
        
        # Check for missing meta description
        if not meta_desc:
            issues.append(PageIssue(
                url=url,
                issue_type="missing_meta_description",
                severity="warning",
                message="Page is missing meta description"
            ))
        
        # Extract and check images
        images = soup.find_all("img")
        images_without_alt = []
        for img in images:
            src = img.get("src", "")
            if not img.get("alt"):
                images_without_alt.append(src)
                issues.append(PageIssue(
                    url=url,
                    issue_type="missing_alt_text",
                    severity="warning",
                    message=f"Image missing alt text: {src[:50]}..."
                ))
        
        # Extract links
        internal_links = []
        external_links = []
        
        for link in soup.find_all("a", href=True):
            href = link["href"]
            full_url = urljoin(url, href)
            full_url, _ = urldefrag(full_url)  # Remove fragment
            
            parsed = urlparse(full_url)
            if parsed.netloc == base_domain:
                internal_links.append(full_url)
            else:
                external_links.append(full_url)
        
        # Get Core Web Vitals if enabled
        cwv = None
        if check_cwv:
            cwv = await get_pagespeed_insights(url)
        
        load_time = (time.time() - start_time) * 1000
        
        page_data = PageData(
            url=url,
            status_code=status_code,
            title=title,
            meta_description=meta_desc,
            h1=h1_text,
            h2s=h2s,
            images_without_alt=images_without_alt,
            internal_links=list(set(internal_links)),
            external_links=list(set(external_links)),
            core_web_vitals=cwv,
            crawl_time=datetime.utcnow(),
            load_time_ms=load_time
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
    """Celery task to crawl a website recursively."""
    task_id = self.request.id
    
    async def _crawl():
        parsed = urlparse(base_url)
        base_domain = parsed.netloc
        
        visited: Set[str] = set()
        to_visit: List[str] = [base_url]
        pages: List[PageData] = []
        all_issues: List[PageIssue] = []
        
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
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow()
        ).dict()
    
    try:
        return asyncio.run(_crawl())
    except Exception as e:
        self.retry(countdown=60, exc=e)
