import asyncio
import random
from typing import List, Dict, Set
from datetime import datetime
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from celery_app import celery_app
from models import (
    KeywordData, DomainKeywords, KeywordGapResult,
    ShareOfVoiceResult, DomainSoV, CompetitorOverview
)


# Simulated keyword data source - In production, integrate with:
# - SEMrush API
# - Ahrefs API  
# - Serpstat API
# - DataForSEO
# Or scrape from search engines with proper rate limiting


async def fetch_keyword_data(domain: str, max_keywords: int = 100) -> DomainKeywords:
    """
    Fetch ranking keywords for a domain.
    
    NOTE: This is a mock implementation. In production, integrate with:
    - SEMrush API ($200+/month)
    - Ahrefs API
    - Serpstat API
    - Or build a scraper with proper proxies and rate limiting
    """
    
    # For demo purposes, generate simulated data based on domain
    # In production, replace with actual API calls
    
    keywords = []
    base_traffic = hash(domain) % 50000 + 10000
    
    sample_keywords = [
        "seo tools", "keyword research", "backlink analysis", "site audit",
        "rank tracking", "competitor analysis", "content optimization",
        "technical seo", "local seo", "link building", "on-page seo",
        "seo dashboard", "serp tracking", "domain authority", "page speed",
        "mobile seo", "schema markup", "canonical tags", "meta tags",
        "xml sitemap", "robots.txt", "google analytics", "search console"
    ]
    
    for i, kw in enumerate(sample_keywords[:max_keywords]):
        position = random.randint(1, 50)
        volume = random.randint(100, 50000)
        
        # Simulate domain-specific variations
        if domain in kw or any(c in domain for c in ["seo", "tool", "rank"]):
            position = max(1, position - 10)
        
        # Calculate estimated traffic
        ctr = estimate_ctr(position)
        est_traffic = int(volume * ctr)
        
        keywords.append(KeywordData(
            keyword=kw,
            position=position,
            search_volume=volume,
            cpc=round(random.uniform(0.5, 15.0), 2),
            competition=round(random.uniform(0.1, 0.9), 2),
            url=f"https://{domain}/{kw.replace(' ', '-')}",
            estimated_traffic=est_traffic
        ))
    
    # Sort by position (best rankings first)
    keywords.sort(key=lambda k: k.position)
    
    return DomainKeywords(
        domain=domain,
        keywords=keywords,
        total_keywords=len(keywords),
        total_traffic_estimate=sum(k.estimated_traffic or 0 for k in keywords),
        fetched_at=datetime.utcnow()
    )


def estimate_ctr(position: int) -> float:
    """Estimate CTR based on position in SERP."""
    ctrs = {
        1: 0.28, 2: 0.15, 3: 0.09, 4: 0.06, 5: 0.04,
        6: 0.03, 7: 0.03, 8: 0.02, 9: 0.02, 10: 0.02
    }
    if position <= 10:
        return ctrs.get(position, 0.02)
    elif position <= 20:
        return 0.01
    else:
        return 0.005


@celery_app.task(bind=True)
def analyze_keyword_gap(
    self,
    domain_a: str,
    domain_b: str,
    max_keywords: int = 100
) -> dict:
    """
    Perform keyword gap analysis between two domains.
    
    Returns:
        - Keywords only in A (A \ B)
        - Keywords only in B (B \ A)  
        - Common keywords (A ∩ B)
        - Gap opportunities (high-value keywords B has that A doesn't)
    """
    
    async def _analyze():
        # Fetch data for both domains
        domain_a_data = await fetch_keyword_data(domain_a, max_keywords)
        domain_b_data = await fetch_keyword_data(domain_b, max_keywords)
        
        # Build keyword sets
        keywords_a = {k.keyword: k for k in domain_a_data.keywords}
        keywords_b = {k.keyword: k for k in domain_b_data.keywords}
        
        set_a = set(keywords_a.keys())
        set_b = set(keywords_b.keys())
        
        # Calculate gaps
        only_in_a = set_a - set_b
        only_in_b = set_b - set_a
        common = set_a & set_b
        
        # Gap opportunities: keywords B ranks well for that A doesn't have
        gap_opportunities = [
            keywords_b[kw] for kw in only_in_b
            if keywords_b[kw].position <= 10 and keywords_b[kw].search_volume and keywords_b[kw].search_volume > 1000
        ]
        gap_opportunities.sort(key=lambda k: (k.position, -(k.search_volume or 0)))
        
        return KeywordGapResult(
            domain_a=domain_a,
            domain_b=domain_b,
            keywords_only_in_a=[keywords_a[kw] for kw in only_in_a],
            keywords_only_in_b=[keywords_b[kw] for kw in only_in_b],
            common_keywords=[keywords_a[kw] for kw in common],
            gap_opportunities=gap_opportunities[:20]  # Top 20 opportunities
        ).dict()
    
    return asyncio.run(_analyze())


@celery_app.task(bind=True)
def calculate_share_of_voice(
    self,
    domains: List[str],
    keywords: List[str]
) -> dict:
    """
    Calculate Share of Voice for domains across keyword set.
    
    Formula: SoV = Σ(Estimated CTR × Search Volume) / Total Market Volume
    """
    
    async def _calculate():
        # Fetch keyword data for all domains
        domain_data = {}
        for domain in domains:
            domain_data[domain] = await fetch_keyword_data(domain, 500)
        
        # Build keyword universe from provided keywords
        keyword_set = set(keywords) if keywords else set()
        
        # If no keywords provided, use union of all domain keywords
        if not keyword_set:
            for data in domain_data.values():
                keyword_set.update(k.keyword for k in data.keywords)
        
        # Calculate market total volume
        market_volume = 0
        keyword_volume_map = {}
        
        for domain, data in domain_data.items():
            for kw in data.keywords:
                if kw.keyword in keyword_set:
                    if kw.search_volume:
                        market_volume = max(market_volume, kw.search_volume)
                        keyword_volume_map[kw.keyword] = kw.search_volume
        
        # Calculate SoV for each domain
        domain_sovs = []
        
        for domain, data in domain_data.items():
            domain_keywords = {k.keyword: k for k in data.keywords if k.keyword in keyword_set}
            
            total_weighted_visibility = 0
            total_estimated_ctr = 0
            weighted_position = 0
            
            for kw_name, kw_data in domain_keywords.items():
                volume = keyword_volume_map.get(kw_name, 1000)
                ctr = estimate_ctr(kw_data.position)
                
                total_weighted_visibility += ctr * volume
                total_estimated_ctr += ctr
                weighted_position += kw_data.position * volume
            
            total_volume = sum(keyword_volume_map.values()) or 1
            
            sov_score = (total_weighted_visibility / total_volume) * 100
            avg_position = weighted_position / total_volume if total_volume > 0 else 0
            
            domain_sovs.append(DomainSoV(
                domain=domain,
                visibility_score=round(sov_score, 2),
                estimated_ctr=round(total_estimated_ctr / len(domain_keywords) if domain_keywords else 0, 4),
                total_search_volume=sum(k.search_volume or 0 for k in domain_keywords.values()),
                weighted_position=round(avg_position, 2)
            ))
        
        # Sort by visibility score descending
        domain_sovs.sort(key=lambda x: x.visibility_score, reverse=True)
        
        return ShareOfVoiceResult(
            request_date=datetime.utcnow(),
            domains=domain_sovs,
            market_total_volume=total_volume
        ).dict()
    
    return asyncio.run(_calculate())


@celery_app.task(bind=True)
def get_competitor_overview(self, domain: str) -> dict:
    """Get competitive overview for a domain."""
    
    async def _overview():
        keyword_data = await fetch_keyword_data(domain, 1000)
        
        # Calculate some basic metrics
        top_keywords = sorted(
            keyword_data.keywords,
            key=lambda k: (k.estimated_traffic or 0),
            reverse=True
        )[:10]
        
        # Generate traffic trend (mock data for demo)
        import random
        traffic_trend = []
        base_traffic = keyword_data.total_traffic_estimate
        
        for i in range(12):
            month_traffic = int(base_traffic * (0.8 + random.random() * 0.4))
            traffic_trend.append({
                "month": f"2024-{i+1:02d}",
                "traffic": month_traffic
            })
        
        # Mock authority metrics
        domain_hash = hash(domain) % 100
        
        return CompetitorOverview(
            domain=domain,
            authority_score=30 + domain_hash,
            organic_traffic=keyword_data.total_traffic_estimate,
            paid_traffic=int(keyword_data.total_traffic_estimate * 0.1),
            backlink_count=10000 + domain_hash * 500,
            referring_domains=500 + domain_hash * 50,
            top_keywords=top_keywords,
            traffic_trend=traffic_trend
        ).dict()
    
    return asyncio.run(_overview())
