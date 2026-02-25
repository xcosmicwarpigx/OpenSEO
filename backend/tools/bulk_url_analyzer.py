"""
Bulk URL Analyzer Tool
Quickly analyze multiple URLs for common SEO issues.
"""
import asyncio
from typing import List, Dict, Any
import httpx
from urllib.parse import urlparse

from models import BulkUrlRequest, BulkUrlResult, UrlCheckResult


async def analyze_single_url(url: str, checks: List[str]) -> UrlCheckResult:
    """Analyze a single URL quickly."""
    issues = []
    redirect_url = None
    
    async with httpx.AsyncClient(follow_redirects=False, timeout=10) as client:
        start_time = asyncio.get_event_loop().time()
        
        try:
            response = await client.get(url)
            response_time = (asyncio.get_event_loop().time() - start_time) * 1000
            status_code = response.status_code
            
            # Check for redirects
            if 300 <= status_code < 400:
                redirect_url = response.headers.get('location')
                issues.append(f"Redirect to {redirect_url}")
            
            # Check for errors
            if status_code >= 400:
                issues.append(f"HTTP {status_code} error")
            
            # Extract meta data if requested
            title = None
            meta_description = None
            h1 = None
            
            if 'meta' in checks and status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'lxml')
                
                title = soup.title.string if soup.title else None
                meta_tag = soup.find('meta', attrs={'name': 'description'})
                if meta_tag:
                    meta_description = meta_tag.get('content')
                h1_tag = soup.find('h1')
                if h1_tag:
                    h1 = h1_tag.get_text(strip=True)
                
                # Check for missing elements
                if not title:
                    issues.append('Missing title tag')
                if not meta_description:
                    issues.append('Missing meta description')
                if not h1:
                    issues.append('Missing H1 tag')
            
            # Check indexability
            indexable = True
            if 'headers' in checks:
                x_robots = response.headers.get('x-robots-tag', '')
                if 'noindex' in x_robots.lower():
                    indexable = False
                    issues.append('X-Robots-Tag: noindex')
                
                if 'meta' in checks and status_code == 200:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(response.text, 'lxml')
                    robots_meta = soup.find('meta', attrs={'name': 'robots'})
                    if robots_meta and 'noindex' in robots_meta.get('content', '').lower():
                        indexable = False
                        issues.append('Meta robots: noindex')
            
            return UrlCheckResult(
                url=url,
                status_code=status_code,
                redirect_url=redirect_url,
                title=title,
                meta_description=meta_description,
                h1=h1,
                indexable=indexable,
                issues=issues,
                response_time_ms=round(response_time, 2)
            )
            
        except httpx.TimeoutException:
            return UrlCheckResult(
                url=url,
                status_code=0,
                redirect_url=None,
                title=None,
                meta_description=None,
                h1=None,
                indexable=False,
                issues=['Request timeout'],
                response_time_ms=0
            )
        except Exception as e:
            return UrlCheckResult(
                url=url,
                status_code=0,
                redirect_url=None,
                title=None,
                meta_description=None,
                h1=None,
                indexable=False,
                issues=[str(e)],
                response_time_ms=0
            )


async def analyze_urls_bulk(request: BulkUrlRequest) -> BulkUrlResult:
    """Analyze multiple URLs in parallel."""
    # Limit to 100 URLs per request
    urls = request.urls[:100]
    
    # Analyze all URLs concurrently
    tasks = [analyze_single_url(url, request.checks) for url in urls]
    results = await asyncio.gather(*tasks)
    
    # Generate summary
    total = len(results)
    status_200 = sum(1 for r in results if r.status_code == 200)
    redirects = sum(1 for r in results if 300 <= r.status_code < 400)
    errors = sum(1 for r in results if r.status_code >= 400)
    timeouts = sum(1 for r in results if r.status_code == 0)
    not_indexable = sum(1 for r in results if not r.indexable)
    
    missing_titles = sum(1 for r in results if r.title is None and r.status_code == 200)
    missing_meta = sum(1 for r in results if r.meta_description is None and r.status_code == 200)
    missing_h1 = sum(1 for r in results if r.h1 is None and r.status_code == 200)
    
    summary = {
        'total_urls': total,
        'status_200': status_200,
        'redirects': redirects,
        'errors': errors,
        'timeouts': timeouts,
        'not_indexable': not_indexable,
        'missing_titles': missing_titles,
        'missing_meta': missing_meta,
        'missing_h1': missing_h1,
        'avg_response_time_ms': round(
            sum(r.response_time_ms for r in results if r.response_time_ms > 0) / 
            max(1, sum(1 for r in results if r.response_time_ms > 0)), 
            2
        )
    }
    
    # Generate CSV export
    csv_lines = ['URL,Status,Title,Meta Description,H1,Indexable,Issues,Response Time (ms)']
    for r in results:
        csv_lines.append(
            f'"{r.url}",{r.status_code},"{r.title or ""}","{r.meta_description or ""}",'
            f'"{r.h1 or ""}",{r.indexable},"{"; ".join(r.issues)}",{r.response_time_ms}'
        )
    
    return BulkUrlResult(
        results=list(results),
        summary=summary,
        export_csv='\n'.join(csv_lines)
    )