"""
Content Optimizer Tool
Comprehensive content analysis with competitor comparison.
"""
import asyncio
from typing import List, Dict, Any, Optional
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

from models import ContentOptimizerRequest, ContentOptimizerResult, ContentOptimizationSuggestion
from utils.content_analyzer import (
    calculate_readability, calculate_keyword_density, analyze_content_quality,
    extract_top_keywords, generate_content_suggestions, calculate_content_score
)


async def fetch_page_content(url: str) -> Dict[str, Any]:
    """Fetch and parse page content using Playwright."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            html = await page.content()
            soup = BeautifulSoup(html, 'lxml')
            
            # Extract content
            title = soup.title.string if soup.title else ""
            meta_desc = ""
            meta_tag = soup.find("meta", attrs={"name": "description"})
            if meta_tag:
                meta_desc = meta_tag.get("content", "")
            
            h1 = soup.find("h1")
            h1_text = h1.get_text(strip=True) if h1 else ""
            
            # Get main content text
            # Try to find main content area
            content_selectors = ['main', 'article', '[role="main"]', '.content', '#content', '.post']
            content_text = ""
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content_text = content_elem.get_text(separator=' ', strip=True)
                    break
            
            # Fallback to body if no content area found
            if not content_text:
                body = soup.find('body')
                if body:
                    # Remove script and style elements
                    for script in body.find_all(['script', 'style', 'nav', 'header', 'footer']):
                        script.decompose()
                    content_text = body.get_text(separator=' ', strip=True)
            
            # Extract headings
            headings = []
            for i in range(1, 7):
                for h in soup.find_all(f'h{i}'):
                    headings.append({
                        'level': i,
                        'text': h.get_text(strip=True),
                        'word_count': len(h.get_text(strip=True).split())
                    })
            
            # Count images
            images = soup.find_all('img')
            images_without_alt = [img.get('src', '') for img in images if not img.get('alt')]
            
            # Count internal links
            internal_links = []
            base_domain = url.split('/')[2]
            for link in soup.find_all('a', href=True):
                href = link['href']
                if base_domain in href or href.startswith('/'):
                    internal_links.append(href)
            
            await browser.close()
            
            return {
                'title': title,
                'meta_description': meta_desc,
                'h1': h1_text,
                'content_text': content_text,
                'headings': headings,
                'images_count': len(images),
                'images_without_alt': len(images_without_alt),
                'internal_links': len(internal_links),
                'html': html
            }
            
        except Exception as e:
            await browser.close()
            raise e


async def optimize_content(request: ContentOptimizerRequest) -> ContentOptimizerResult:
    """Analyze content and generate optimization suggestions."""
    # Fetch main page
    page_data = await fetch_page_content(request.url)
    
    # Calculate readability
    readability = calculate_readability(page_data['content_text'])
    
    # Calculate keyword density for target keywords
    keyword_density = calculate_keyword_density(
        page_data['content_text'],
        page_data['title'],
        page_data['h1'],
        page_data['meta_description'],
        request.target_keywords
    )
    
    # If no target keywords provided, extract top keywords
    if not keyword_density:
        top_keywords = extract_top_keywords(page_data['content_text'], top_n=5)
        keyword_density = [
            type('KeywordDensity', (), {
                'keyword': kw['keyword'],
                'count': kw['count'],
                'density_percent': kw['density_percent'],
                'in_title': kw['keyword'] in page_data['title'].lower(),
                'in_h1': kw['keyword'] in page_data['h1'].lower(),
                'in_meta_description': kw['keyword'] in page_data['meta_description'].lower(),
                'in_first_100_words': False
            })()
            for kw in top_keywords
        ]
    
    # Analyze content quality
    content_quality = analyze_content_quality(
        page_data['content_text'],
        page_data['headings'],
        keyword_density
    )
    
    # Generate suggestions
    suggestions = generate_content_suggestions(
        page_data['title'],
        page_data['meta_description'],
        page_data['h1'],
        page_data['headings'],
        readability,
        content_quality,
        keyword_density,
        page_data['images_without_alt'],
        page_data['internal_links'],
        readability.word_count
    )
    
    # Calculate overall score
    overall_score = calculate_content_score(
        readability,
        content_quality,
        keyword_density,
        page_data['title'],
        page_data['meta_description'],
        page_data['h1'],
        page_data['images_count'],
        page_data['images_count'] - page_data['images_without_alt'],
        page_data['internal_links'],
        readability.word_count
    )
    
    # Get prioritized actions
    prioritized = [s.recommendation for s in suggestions[:5]]
    
    return ContentOptimizerResult(
        url=request.url,
        overall_score=overall_score,
        readability=readability,
        suggestions=suggestions,
        keyword_optimization=keyword_density,
        competitor_comparison=None,  # Would need competitor analysis
        content_quality=content_quality,
        prioritized_actions=prioritized
    )


async def compare_with_competitors(
    your_url: str,
    competitor_urls: List[str]
) -> Dict[str, Any]:
    """Compare your content with competitors."""
    # Fetch all pages
    your_data = await fetch_page_content(your_url)
    competitor_data = {}
    
    for url in competitor_urls[:3]:  # Limit to 3 competitors
        try:
            competitor_data[url] = await fetch_page_content(url)
        except:
            continue
    
    # Calculate metrics for comparison
    your_metrics = {
        'word_count': len(your_data['content_text'].split()),
        'title_length': len(your_data['title']),
        'meta_length': len(your_data['meta_description']),
        'h1_count': 1 if your_data['h1'] else 0,
        'heading_count': len(your_data['headings']),
        'image_count': your_data['images_count']
    }
    
    competitor_metrics = {}
    for url, data in competitor_data.items():
        competitor_metrics[url] = {
            'word_count': len(data['content_text'].split()),
            'title_length': len(data['title']),
            'meta_length': len(data['meta_description']),
            'h1_count': 1 if data['h1'] else 0,
            'heading_count': len(data['headings']),
            'image_count': data['images_count']
        }
    
    # Identify gaps
    gaps = []
    opportunities = []
    
    avg_competitor_words = sum(m['word_count'] for m in competitor_metrics.values()) / len(competitor_metrics) if competitor_metrics else 0
    
    if your_metrics['word_count'] < avg_competitor_words * 0.8:
        gaps.append(f"Your content is shorter than competitors (avg: {int(avg_competitor_words)} words)")
        opportunities.append("Expand content to match or exceed competitor word counts")
    
    max_competitor_images = max(m['image_count'] for m in competitor_metrics.values()) if competitor_metrics else 0
    if your_metrics['image_count'] < max_competitor_images:
        gaps.append(f"Competitors use more images (max: {max_competitor_images})")
        opportunities.append("Add more relevant images to your content")
    
    return {
        'your_metrics': your_metrics,
        'competitor_metrics': competitor_metrics,
        'gaps': gaps,
        'opportunities': opportunities
    }