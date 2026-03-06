import asyncio
import re
from collections import Counter
from datetime import datetime
from typing import Dict, List, Set
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from celery_app import celery_app
from models import (
    CompetitorOverview,
    DomainKeywords,
    DomainSoV,
    KeywordData,
    KeywordGapResult,
    ShareOfVoiceResult,
)


COMMON_STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "must", "to", "of", "in", "for", "on", "with",
    "at", "by", "from", "as", "into", "through", "during", "before", "after",
    "above", "below", "between", "under", "and", "but", "or", "yet", "so",
    "if", "because", "although", "though", "while", "where", "when", "that",
    "which", "who", "whom", "whose", "what", "this", "these", "those", "it",
    "we", "they", "you", "your", "our", "their", "about", "into", "than",
}


def estimate_ctr(position: int) -> float:
    ctrs = {
        1: 0.28,
        2: 0.15,
        3: 0.09,
        4: 0.06,
        5: 0.04,
        6: 0.03,
        7: 0.03,
        8: 0.02,
        9: 0.02,
        10: 0.02,
    }
    if position <= 10:
        return ctrs.get(position, 0.02)
    elif position <= 20:
        return 0.01
    return 0.005


async def _fetch_html(client: httpx.AsyncClient, url: str) -> str:
    try:
        resp = await client.get(url, timeout=12, follow_redirects=True)
        if resp.status_code >= 400:
            return ""
        return resp.text
    except Exception:
        return ""


async def _discover_pages(domain: str, max_pages: int = 10) -> List[str]:
    if not domain.startswith(("http://", "https://")):
        base_url = f"https://{domain.strip('/')}"
    else:
        base_url = domain.rstrip("/")

    parsed_base = urlparse(base_url)
    netloc = parsed_base.netloc

    candidates: Set[str] = {base_url}

    async with httpx.AsyncClient() as client:
        homepage = await _fetch_html(client, base_url)
        if homepage:
            soup = BeautifulSoup(homepage, "lxml")
            for a in soup.find_all("a", href=True):
                href = a.get("href", "")
                full = urljoin(base_url, href)
                parsed = urlparse(full)
                if parsed.netloc == netloc and parsed.scheme in {"http", "https"}:
                    candidates.add(full.split("#")[0].rstrip("/"))
                if len(candidates) >= max_pages:
                    break

        sitemap_url = f"{base_url}/sitemap.xml"
        sitemap_xml = await _fetch_html(client, sitemap_url)
        if sitemap_xml and "<urlset" in sitemap_xml:
            locs = re.findall(r"<loc>(.*?)</loc>", sitemap_xml)
            for loc in locs[:max_pages]:
                parsed = urlparse(loc)
                if parsed.netloc == netloc:
                    candidates.add(loc.split("#")[0].rstrip("/"))

    ordered = sorted(candidates, key=lambda u: (0 if u == base_url else 1, u))
    return ordered[:max_pages]


def _extract_tokens(html: str) -> Counter:
    if not html:
        return Counter()

    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()

    text = soup.get_text(separator=" ", strip=True).lower()
    words = re.findall(r"\b[a-z][a-z0-9-]{2,}\b", text)
    words = [w for w in words if w not in COMMON_STOPWORDS]
    return Counter(words)


async def fetch_keyword_data(domain: str, max_keywords: int = 100) -> DomainKeywords:
    pages = await _discover_pages(domain, max_pages=10)

    all_counts: Counter = Counter()

    async with httpx.AsyncClient() as client:
        for url in pages:
            html = await _fetch_html(client, url)
            all_counts.update(_extract_tokens(html))

    top = all_counts.most_common(max_keywords)

    keywords: List[KeywordData] = []
    for idx, (kw, count) in enumerate(top, start=1):
        search_volume = max(10, count * 20)
        position = min(50, idx)
        keywords.append(
            KeywordData(
                keyword=kw,
                position=position,
                search_volume=search_volume,
                cpc=round(0.3 + (count % 12) * 0.4, 2),
                competition=round(min(0.95, 0.2 + (count / max(5, top[0][1] if top else 1))), 2),
                url=pages[0] if pages else None,
                estimated_traffic=int(search_volume * estimate_ctr(position)),
            )
        )

    return DomainKeywords(
        domain=domain,
        keywords=keywords,
        total_keywords=len(keywords),
        total_traffic_estimate=sum(k.estimated_traffic or 0 for k in keywords),
        fetched_at=datetime.utcnow(),
    )


@celery_app.task(bind=True)
def analyze_keyword_gap(self, domain_a: str, domain_b: str, max_keywords: int = 100) -> dict:
    async def _analyze():
        domain_a_data = await fetch_keyword_data(domain_a, max_keywords)
        domain_b_data = await fetch_keyword_data(domain_b, max_keywords)

        keywords_a = {k.keyword: k for k in domain_a_data.keywords}
        keywords_b = {k.keyword: k for k in domain_b_data.keywords}

        set_a = set(keywords_a.keys())
        set_b = set(keywords_b.keys())

        only_in_a = sorted(set_a - set_b)
        only_in_b = sorted(set_b - set_a)
        common = sorted(set_a & set_b)

        gap_opportunities = [
            keywords_b[kw]
            for kw in only_in_b
            if (keywords_b[kw].search_volume or 0) >= 100 and keywords_b[kw].position <= 20
        ]
        gap_opportunities.sort(key=lambda k: (k.position, -(k.search_volume or 0)))

        return KeywordGapResult(
            domain_a=domain_a,
            domain_b=domain_b,
            keywords_only_in_a=[keywords_a[kw] for kw in only_in_a],
            keywords_only_in_b=[keywords_b[kw] for kw in only_in_b],
            common_keywords=[keywords_a[kw] for kw in common],
            gap_opportunities=gap_opportunities[:20],
        ).dict()

    return asyncio.run(_analyze())


@celery_app.task(bind=True)
def calculate_share_of_voice(self, domains: List[str], keywords: List[str]) -> dict:
    async def _calculate():
        domain_data: Dict[str, DomainKeywords] = {}
        for domain in domains:
            domain_data[domain] = await fetch_keyword_data(domain, 300)

        keyword_set = {k.lower().strip() for k in keywords if k.strip()}
        if not keyword_set:
            for data in domain_data.values():
                keyword_set.update(k.keyword for k in data.keywords)

        keyword_volume_map: Dict[str, int] = {}
        for data in domain_data.values():
            for kw in data.keywords:
                if kw.keyword in keyword_set and kw.search_volume:
                    keyword_volume_map[kw.keyword] = max(keyword_volume_map.get(kw.keyword, 0), kw.search_volume)

        total_volume = sum(keyword_volume_map.values()) or 1
        domain_sovs: List[DomainSoV] = []

        for domain, data in domain_data.items():
            domain_keywords = {k.keyword: k for k in data.keywords if k.keyword in keyword_set}
            weighted_visibility = 0.0
            ctr_values: List[float] = []
            weighted_position_sum = 0.0

            for kw_name, kw_data in domain_keywords.items():
                volume = keyword_volume_map.get(kw_name, kw_data.search_volume or 10)
                ctr = estimate_ctr(kw_data.position)
                weighted_visibility += ctr * volume
                ctr_values.append(ctr)
                weighted_position_sum += kw_data.position * volume

            sov_score = (weighted_visibility / total_volume) * 100
            avg_position = weighted_position_sum / total_volume if total_volume else 0

            domain_sovs.append(
                DomainSoV(
                    domain=domain,
                    visibility_score=round(sov_score, 2),
                    estimated_ctr=round(sum(ctr_values) / len(ctr_values), 4) if ctr_values else 0.0,
                    total_search_volume=sum(k.search_volume or 0 for k in domain_keywords.values()),
                    weighted_position=round(avg_position, 2),
                )
            )

        domain_sovs.sort(key=lambda x: x.visibility_score, reverse=True)

        return ShareOfVoiceResult(
            request_date=datetime.utcnow(),
            domains=domain_sovs,
            market_total_volume=total_volume,
        ).dict()

    return asyncio.run(_calculate())


@celery_app.task(bind=True)
def get_competitor_overview(self, domain: str) -> dict:
    async def _overview():
        keyword_data = await fetch_keyword_data(domain, 250)
        top_keywords = sorted(
            keyword_data.keywords,
            key=lambda k: (k.estimated_traffic or 0),
            reverse=True,
        )[:10]

        authority_seed = min(100, 20 + len(keyword_data.keywords) // 2)
        backlinks_seed = 100 + keyword_data.total_keywords * 15

        traffic_trend = []
        base_traffic = max(100, keyword_data.total_traffic_estimate)
        for month in range(1, 13):
            month_traffic = int(base_traffic * (0.85 + ((month % 5) * 0.04)))
            traffic_trend.append({"month": f"2026-{month:02d}", "traffic": month_traffic})

        return CompetitorOverview(
            domain=domain,
            authority_score=authority_seed,
            organic_traffic=keyword_data.total_traffic_estimate,
            paid_traffic=int(keyword_data.total_traffic_estimate * 0.08),
            backlink_count=backlinks_seed,
            referring_domains=max(20, backlinks_seed // 10),
            top_keywords=top_keywords,
            traffic_trend=traffic_trend,
        ).dict()

    return asyncio.run(_overview())
