"""
Internal Linking Analysis Module
Analyzes internal link structure, identifies orphan pages, and calculates link depth.
"""
from typing import List, Dict, Any, Set, Optional
from urllib.parse import urlparse
from collections import defaultdict
from models import InternalLinkingStats, LinkAnalysis


def analyze_internal_linking(
    pages_data: List[Dict[str, Any]],
    base_url: str
) -> InternalLinkingStats:
    """
    Analyze internal linking structure across all crawled pages.
    
    Args:
        pages_data: List of page data dicts with 'url' and 'internal_links' keys
        base_url: The starting/base URL of the crawl
    """
    # Build link graph
    url_to_links = {}  # URL -> set of URLs it links to
    url_to_incoming = defaultdict(set)  # URL -> set of URLs linking to it
    
    all_urls = set()
    
    for page in pages_data:
        url = page.get("url", "")
        internal_links = page.get("internal_links", [])
        
        all_urls.add(url)
        url_to_links[url] = set(internal_links)
        
        for link in internal_links:
            url_to_incoming[link].add(url)
            all_urls.add(link)
    
    # Calculate click depth from homepage using BFS
    click_depths = calculate_click_depths(base_url, url_to_links, all_urls)
    
    # Find orphan pages (no incoming internal links)
    orphan_pages = [
        url for url in all_urls 
        if url in url_to_links and len(url_to_incoming[url]) == 0 and url != base_url
    ]
    
    # Find pages with few links
    pages_with_few_links = []
    for url, links in url_to_links.items():
        if len(links) < 3:
            pages_with_few_links.append({
                "url": url,
                "link_count": len(links),
                "suggestion": "Add more internal links to related content"
            })
    
    # Find most linked pages
    incoming_counts = [(url, len(sources)) for url, sources in url_to_incoming.items()]
    incoming_counts.sort(key=lambda x: x[1], reverse=True)
    most_linked = [
        {"url": url, "incoming_links": count}
        for url, count in incoming_counts[:10]
    ]
    
    # Calculate stats
    total_internal = sum(len(links) for links in url_to_links.values())
    unique_internal = len(set(
        link for links in url_to_links.values() for link in links
    ))
    
    avg_links = total_internal / len(url_to_links) if url_to_links else 0
    max_depth = max(click_depths.values()) if click_depths else 0
    
    return InternalLinkingStats(
        total_internal_links=total_internal,
        unique_internal_links=unique_internal,
        orphan_pages=orphan_pages,
        pages_with_few_links=pages_with_few_links[:10],
        most_linked_pages=most_linked,
        avg_links_per_page=round(avg_links, 1),
        max_click_depth=max_depth
    )


def calculate_click_depths(
    base_url: str,
    url_to_links: Dict[str, Set[str]],
    all_urls: Set[str]
) -> Dict[str, int]:
    """Calculate click depth from homepage using BFS."""
    depths = {base_url: 0}
    queue = [base_url]
    visited = {base_url}
    
    while queue:
        current = queue.pop(0)
        current_depth = depths[current]
        
        # Get all outgoing links from this page
        outgoing = url_to_links.get(current, set())
        
        for url in outgoing:
            if url not in visited and url in all_urls:
                visited.add(url)
                depths[url] = current_depth + 1
                queue.append(url)
    
    # Set depth to -1 for unreachable pages
    for url in all_urls:
        if url not in depths:
            depths[url] = -1
    
    return depths


def find_broken_internal_links(pages_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Find internal links that point to pages not in the crawl (potential 404s)."""
    all_crawled_urls = {p.get("url", "") for p in pages_data}
    broken_links = []
    
    for page in pages_data:
        source_url = page.get("url", "")
        for link in page.get("internal_links", []):
            # Check if link is to a page that wasn't crawled
            # This could mean 404, redirect, or blocked by robots
            if link not in all_crawled_urls:
                # Skip if it's clearly a different path pattern (e.g., /blog/ vs /product/)
                # This is a heuristic - in production you'd want to actually check the URL
                broken_links.append({
                    "source": source_url,
                    "target": link,
                    "issue": "Page not found in crawl (potential 404 or redirect)"
                })
    
    return broken_links


def analyze_anchor_text_distribution(pages_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze the distribution of anchor text used in internal links."""
    anchor_texts = defaultdict(int)
    url_anchor_map = defaultdict(list)  # Target URL -> list of anchor texts
    
    # This would need the actual anchor text from the crawl
    # For now, return a structure for future implementation
    
    return {
        "total_unique_anchor_texts": len(anchor_texts),
        "most_common_anchors": [],
        "generic_anchors": [],  # "click here", "read more", etc.
        "recommendations": [
            "Use descriptive anchor text that includes target keywords",
            "Avoid generic text like 'click here' or 'read more'",
            "Ensure anchor text varies across different links to the same page"
        ]
    }


def generate_internal_linking_recommendations(stats: InternalLinkingStats) -> List[str]:
    """Generate recommendations based on internal linking analysis."""
    recommendations = []
    
    if stats.orphan_pages:
        recommendations.append(
            f"Fix {len(stats.orphan_pages)} orphan pages by adding internal links from relevant content"
        )
    
    if stats.pages_with_few_links:
        recommendations.append(
            f"Improve {len(stats.pages_with_few_links)} pages with few internal links - aim for 3-5 per page"
        )
    
    if stats.max_click_depth > 4:
        recommendations.append(
            f"Reduce click depth - some pages are {stats.max_click_depth} clicks from homepage. Aim for max 3-4."
        )
    
    if stats.avg_links_per_page < 2:
        recommendations.append(
            f"Increase internal linking - current average is {stats.avg_links_per_page} links per page"
        )
    
    # Check for excessive links
    if stats.avg_links_per_page > 100:
        recommendations.append(
            "Some pages have excessive internal links - consider limiting to under 100 per page"
        )
    
    return recommendations


def calculate_internal_linking_health_score(stats: InternalLinkingStats) -> int:
    """Calculate a health score for internal linking (0-100)."""
    score = 70  # Base score
    
    # Penalties
    score -= len(stats.orphan_pages) * 5  # -5 per orphan page
    score -= len(stats.pages_with_few_links) * 2  # -2 per page with few links
    score -= max(0, stats.max_click_depth - 3) * 5  # -5 per level over 3
    
    # Bonuses
    if stats.avg_links_per_page >= 3:
        score += 10
    if stats.avg_links_per_page >= 5:
        score += 10
    if not stats.orphan_pages:
        score += 10
    if stats.max_click_depth <= 3:
        score += 10
    
    return max(0, min(100, score))