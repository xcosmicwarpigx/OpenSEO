"""
Sitemap and Robots.txt Analysis Module
Validates sitemap structure and robots.txt rules.
"""
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
import httpx

from models import SitemapAnalysis, SitemapUrl, RobotsTxtAnalysis


async def fetch_sitemap(base_url: str) -> Optional[str]:
    """Try to fetch sitemap.xml from the site."""
    sitemap_urls = [
        urljoin(base_url, "sitemap.xml"),
        urljoin(base_url, "sitemap_index.xml"),
        urljoin(base_url, "wp-sitemap.xml"),  # WordPress
    ]
    
    async with httpx.AsyncClient() as client:
        for sitemap_url in sitemap_urls:
            try:
                response = await client.get(sitemap_url, timeout=10)
                if response.status_code == 200:
                    return response.text
            except:
                continue
    
    return None


def parse_sitemap(xml_content: str) -> List[SitemapUrl]:
    """Parse sitemap XML and extract URLs."""
    urls = []
    
    try:
        root = ET.fromstring(xml_content)
        
        # Handle both sitemap and sitemapindex formats
        # Sitemap namespace
        ns = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        
        # Try with namespace
        url_elements = root.findall('.//ns:url', ns) or root.findall('.//url')
        
        for url_elem in url_elements:
            loc_elem = url_elem.find('ns:loc', ns) or url_elem.find('loc')
            lastmod_elem = url_elem.find('ns:lastmod', ns) or url_elem.find('lastmod')
            changefreq_elem = url_elem.find('ns:changefreq', ns) or url_elem.find('changefreq')
            priority_elem = url_elem.find('ns:priority', ns) or url_elem.find('priority')
            
            if loc_elem is not None:
                loc = loc_elem.text
                lastmod = lastmod_elem.text if lastmod_elem is not None else None
                changefreq = changefreq_elem.text if changefreq_elem is not None else None
                priority = None
                
                if priority_elem is not None:
                    try:
                        priority = float(priority_elem.text)
                    except (ValueError, TypeError):
                        pass
                
                urls.append(SitemapUrl(
                    loc=loc,
                    lastmod=lastmod,
                    changefreq=changefreq,
                    priority=priority,
                    in_crawl=False
                ))
    
    except ET.ParseError:
        pass
    
    return urls


def analyze_sitemap(
    sitemap_urls: List[SitemapUrl],
    crawled_urls: List[str]
) -> Optional[SitemapAnalysis]:
    """Analyze sitemap against crawled URLs."""
    if not sitemap_urls:
        return None
    
    crawled_set = set(crawled_urls)
    sitemap_locs = {url.loc for url in sitemap_urls}
    
    # Mark which URLs were in the crawl
    for url in sitemap_urls:
        url.in_crawl = url.loc in crawled_set
    
    # Find URLs in sitemap but not crawled
    not_in_crawl = list(sitemap_locs - crawled_set)
    
    # Check for invalid URLs
    invalid_urls = []
    for url in sitemap_urls:
        parsed = urlparse(url.loc)
        if not parsed.scheme or not parsed.netloc:
            invalid_urls.append(url.loc)
    
    return SitemapAnalysis(
        sitemap_url="sitemap.xml",  # Would be actual URL in production
        urls_found=len(sitemap_urls),
        urls=sitemap_urls,
        urls_not_in_crawl=not_in_crawl,
        invalid_urls=invalid_urls,
        last_modified_fresh=True  # Would check dates in production
    )


async def fetch_robots_txt(base_url: str) -> Optional[str]:
    """Fetch robots.txt from the site."""
    robots_url = urljoin(base_url, "robots.txt")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(robots_url, timeout=10)
            if response.status_code == 200:
                return response.text
        except:
            pass
    
    return None


def parse_robots_txt(content: str, base_url: str) -> RobotsTxtAnalysis:
    """Parse robots.txt and extract rules."""
    if not content:
        return RobotsTxtAnalysis(
            has_robots_txt=False,
            sitemap_reference=None,
            disallowed_paths=[],
            crawl_delay=None,
            issues=["No robots.txt found - search engines can crawl everything"]
        )
    
    disallowed = []
    sitemap_ref = None
    crawl_delay = None
    issues = []
    
    lines = content.split('\n')
    user_agent_relevant = True  # * applies to all
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        if line.lower().startswith('user-agent:'):
            agent = line.split(':', 1)[1].strip().lower()
            user_agent_relevant = (agent == '*' or 'googlebot' in agent)
        
        elif user_agent_relevant and line.lower().startswith('disallow:'):
            path = line.split(':', 1)[1].strip()
            disallowed.append(path)
        
        elif line.lower().startswith('sitemap:'):
            sitemap_ref = line.split(':', 1)[1].strip()
        
        elif user_agent_relevant and line.lower().startswith('crawl-delay:'):
            try:
                crawl_delay = int(line.split(':', 1)[1].strip())
            except ValueError:
                pass
    
    # Check for issues
    if not sitemap_ref:
        issues.append("Sitemap not declared in robots.txt")
    
    if disallowed == ['/']:
        issues.append("All crawling disallowed - site won't be indexed")
    
    return RobotsTxtAnalysis(
        has_robots_txt=True,
        sitemap_reference=sitemap_ref,
        disallowed_paths=disallowed,
        crawl_delay=crawl_delay,
        issues=issues
    )


def generate_sitemap_recommendations(
    sitemap_analysis: Optional[SitemapAnalysis],
    robots_analysis: RobotsTxtAnalysis,
    crawled_urls: List[str]
) -> List[str]:
    """Generate recommendations for sitemap and robots.txt."""
    recommendations = []
    
    if not sitemap_analysis:
        recommendations.append("Create a sitemap.xml to help search engines discover your pages")
    else:
        if sitemap_analysis.urls_not_in_crawl:
            recommendations.append(
                f"{len(sitemap_analysis.urls_not_in_crawl)} URLs in sitemap but not crawled - check for crawl errors"
            )
        
        if sitemap_analysis.invalid_urls:
            recommendations.append(f"Fix {len(sitemap_analysis.invalid_urls)} invalid URLs in sitemap")
    
    if not robots_analysis.has_robots_txt:
        recommendations.append("Create a robots.txt file to guide search engine crawlers")
    else:
        if not robots_analysis.sitemap_reference:
            recommendations.append("Add sitemap reference to robots.txt: Sitemap: https://yoursite.com/sitemap.xml")
        
        if robots_analysis.crawl_delay and robots_analysis.crawl_delay > 10:
            recommendations.append(f"Consider reducing crawl-delay from {robots_analysis.crawl_delay} to improve indexing speed")
    
    # Check for pages not in sitemap
    if sitemap_analysis:
        sitemap_urls = {url.loc for url in sitemap_analysis.urls}
        missing_from_sitemap = [url for url in crawled_urls if url not in sitemap_urls]
        if missing_from_sitemap:
            recommendations.append(
                f"{len(missing_from_sitemap)} crawled pages not in sitemap - add important pages"
            )
    
    return recommendations