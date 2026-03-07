"""
Full SEO Audit Tool
Runs a local-first, one-shot SEO scorecard for a single website URL.
"""

import asyncio
import time
from typing import Any, Dict, List
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from models import ContentQuality, HeadingStructure, KeywordDensity, ReadabilityScore
from utils.accessibility_analyzer import analyze_accessibility
from utils.content_analyzer import (
    analyze_content_quality,
    calculate_content_score,
    calculate_keyword_density,
    calculate_readability,
)
from utils.image_analyzer import analyze_images
from utils.schema_analyzer import (
    detect_page_type_hints,
    extract_schema_types,
    get_missing_recommended_schemas,
)
from utils.security_analyzer import analyze_security_headers
from utils.sitemap_analyzer import (
    analyze_sitemap,
    fetch_robots_txt,
    fetch_sitemap,
    parse_robots_txt,
    parse_sitemap,
)


DEFAULT_WEIGHTS = {
    "technical": 0.30,
    "content": 0.25,
    "performance_local": 0.15,
    "accessibility": 0.15,
    "security": 0.10,
    "internal_linking": 0.05,
}


def _extract_main_content_text(soup: BeautifulSoup) -> str:
    selectors = ["main", "article", "[role=main]", ".content", "#content", ".post"]
    for selector in selectors:
        node = soup.select_one(selector)
        if node:
            return node.get_text(separator=" ", strip=True)

    body = soup.find("body")
    if not body:
        return ""

    for tag in body.find_all(["script", "style", "nav", "header", "footer"]):
        tag.decompose()

    return body.get_text(separator=" ", strip=True)


def calculate_weighted_score(scores: Dict[str, float], weights: Dict[str, float]) -> float:
    return round(sum(scores.get(k, 0) * w for k, w in weights.items()), 2)


def score_to_grade(score: float) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


async def _safe_get(url: str, timeout: int = 20) -> tuple[httpx.Response, bool]:
    """GET with TLS-fallback for environments with custom/intercepting CAs."""
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            return await client.get(url), False
    except httpx.ConnectError as e:
        if "CERTIFICATE_VERIFY_FAILED" not in str(e):
            raise
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, verify=False) as client:
            return await client.get(url), True


async def _check_url_status(url: str) -> Dict[str, Any]:
    try:
        start = time.time()
        resp, used_insecure = await _safe_get(url, timeout=8)
        elapsed = (time.time() - start) * 1000
        out = {
            "url": url,
            "status": resp.status_code,
            "response_time_ms": round(elapsed, 2),
        }
        if used_insecure:
            out["note"] = "TLS verification failed; retried with verify=False"
        return out
    except Exception as e:
        return {
            "url": url,
            "status": 0,
            "response_time_ms": 0,
            "error": str(e),
        }


async def run_full_audit(url: str, max_internal_urls: int = 25, target_keywords: List[str] | None = None) -> Dict[str, Any]:
    parsed_input = urlparse(url)
    if not parsed_input.scheme:
        url = f"https://{url}"
    parsed = urlparse(url)
    base_domain = parsed.netloc
    target_keywords = target_keywords or []

    start = time.time()
    response, used_insecure_tls = await _safe_get(url, timeout=20)
    response_time_ms = (time.time() - start) * 1000
    html = response.text
    page_size_kb = len(response.content) / 1024

    soup = BeautifulSoup(html, "lxml")

    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    meta_tag = soup.find("meta", attrs={"name": "description"})
    meta_description = meta_tag.get("content", "").strip() if meta_tag else ""
    h1 = soup.find("h1")
    h1_text = h1.get_text(strip=True) if h1 else ""
    h1_count = len(soup.find_all("h1"))

    canonical_tag = soup.find("link", attrs={"rel": lambda v: v and "canonical" in str(v).lower()})
    canonical_url = canonical_tag.get("href") if canonical_tag else None

    robots_meta = soup.find("meta", attrs={"name": "robots"})
    robots_meta_value = robots_meta.get("content", "") if robots_meta else ""

    headings: List[HeadingStructure] = []
    for i in range(1, 7):
        for heading in soup.find_all(f"h{i}"):
            text = heading.get_text(strip=True)
            headings.append(HeadingStructure(level=i, text=text, word_count=len(text.split())))

    content_text = _extract_main_content_text(soup)
    readability: ReadabilityScore = calculate_readability(content_text, title, h1_text)

    images = analyze_images(soup, url)
    images_without_alt = [img.url for img in images if not img.alt_text]

    keyword_density: List[KeywordDensity] = calculate_keyword_density(
        content_text,
        title,
        h1_text,
        meta_description,
        target_keywords,
    )
    content_quality: ContentQuality = analyze_content_quality(content_text, headings, keyword_density)

    security_headers = analyze_security_headers(dict(response.headers))

    schemas = extract_schema_types(soup)
    page_hints = detect_page_type_hints(soup, url)
    missing_schemas = get_missing_recommended_schemas(schemas, page_hints)

    accessibility = analyze_accessibility(soup, url)

    internal_links = []
    for a in soup.find_all("a", href=True):
        full = urljoin(url, a["href"]).split("#")[0]
        parsed_link = urlparse(full)
        if parsed_link.netloc == base_domain:
            internal_links.append(full.rstrip("/"))

    unique_internal_links = sorted(set(internal_links))
    sampled_internal = unique_internal_links[:max_internal_urls]
    status_results = await asyncio.gather(*[_check_url_status(u) for u in sampled_internal]) if sampled_internal else []

    checked_count = len(status_results)
    status_200_count = sum(1 for r in status_results if r.get("status") == 200)
    broken_count = sum(1 for r in status_results if r.get("status", 0) >= 400 or r.get("status", 0) == 0)

    sitemap_content = await fetch_sitemap(url)
    robots_content = await fetch_robots_txt(url)

    sitemap_analysis = None
    if sitemap_content:
        sitemap_urls = parse_sitemap(sitemap_content)
        sitemap_analysis = analyze_sitemap(sitemap_urls, [url] + sampled_internal)

    robots_analysis = parse_robots_txt(robots_content or "", url)

    content_score = calculate_content_score(
        readability=readability,
        content_quality=content_quality,
        keyword_density=keyword_density,
        title=title,
        meta_description=meta_description,
        h1=h1_text,
        images_count=len(images),
        images_with_alt=max(0, len(images) - len(images_without_alt)),
        internal_links=len(unique_internal_links),
        word_count=readability.word_count,
    )

    # Performance score (local approximation, no external API)
    perf_score = 100
    if response_time_ms > 3000:
        perf_score -= 35
    elif response_time_ms > 1500:
        perf_score -= 20
    elif response_time_ms > 800:
        perf_score -= 10

    if page_size_kb > 3000:
        perf_score -= 35
    elif page_size_kb > 1500:
        perf_score -= 20
    elif page_size_kb > 800:
        perf_score -= 10

    perf_score = max(0, min(100, perf_score))

    technical_score = 100
    if not title:
        technical_score -= 15
    if not meta_description:
        technical_score -= 10
    if not h1_text:
        technical_score -= 15
    if h1_count > 1:
        technical_score -= 10
    if not canonical_url:
        technical_score -= 8
    if "noindex" in robots_meta_value.lower():
        technical_score -= 20
    if broken_count > 0 and checked_count > 0:
        technical_score -= min(25, int((broken_count / checked_count) * 30))
    if not robots_analysis.has_robots_txt:
        technical_score -= 5
    if not sitemap_analysis:
        technical_score -= 5
    technical_score = max(0, min(100, technical_score))

    internal_linking_score = 100
    if len(unique_internal_links) < 3:
        internal_linking_score -= 35
    elif len(unique_internal_links) < 10:
        internal_linking_score -= 15

    if checked_count > 0:
        good_ratio = status_200_count / checked_count
        if good_ratio < 0.7:
            internal_linking_score -= 30
        elif good_ratio < 0.9:
            internal_linking_score -= 15

    internal_linking_score = max(0, min(100, internal_linking_score))

    score_components = {
        "technical": technical_score,
        "content": content_score,
        "performance_local": perf_score,
        "accessibility": accessibility.score,
        "security": security_headers.score,
        "internal_linking": internal_linking_score,
    }
    overall_score = calculate_weighted_score(score_components, DEFAULT_WEIGHTS)
    grade = score_to_grade(overall_score)

    keyword_presence_summary = []
    for kw in keyword_density:
        keyword_presence_summary.append(
            {
                "keyword": kw.keyword,
                "density_percent": kw.density_percent,
                "in_title": kw.in_title,
                "in_h1": kw.in_h1,
                "in_meta_description": kw.in_meta_description,
                "in_first_100_words": kw.in_first_100_words,
            }
        )

    recommendations: List[str] = []
    if not title:
        recommendations.append("Add a descriptive title tag (target 50-60 characters).")
    if not meta_description:
        recommendations.append("Add a meta description (target 120-160 characters).")
    if not h1_text:
        recommendations.append("Add exactly one H1 heading on the page.")
    if len(images_without_alt) > 0:
        recommendations.append(f"Add alt text to {len(images_without_alt)} images.")
    if broken_count > 0:
        recommendations.append(f"Fix {broken_count} broken/internal unreachable links from sampled pages.")
    if security_headers.score < 70:
        recommendations.append("Improve missing security headers (CSP, HSTS, X-Frame-Options, etc.).")
    if accessibility.critical_issues > 0:
        recommendations.append("Resolve critical accessibility issues first (WCAG critical findings).")
    if missing_schemas:
        recommendations.append("Add recommended structured data types for this page intent.")

    if keyword_density:
        for kw in keyword_density:
            if not kw.in_title:
                recommendations.append(f"Include target keyword '{kw.keyword}' in the title naturally.")
            if not kw.in_h1:
                recommendations.append(f"Include target keyword '{kw.keyword}' in the H1 naturally.")
            if kw.density_percent < 0.5:
                recommendations.append(f"Increase natural usage of '{kw.keyword}' in body copy (currently {kw.density_percent}%).")
            if kw.density_percent > 3.0:
                recommendations.append(f"Reduce repetition of '{kw.keyword}' to avoid over-optimization ({kw.density_percent}%).")

    return {
        "url": url,
        "overall_score": overall_score,
        "grade": grade,
        "scores": score_components,
        "weights": DEFAULT_WEIGHTS,
        "highlights": {
            "status_code": response.status_code,
            "response_time_ms": round(response_time_ms, 2),
            "page_size_kb": round(page_size_kb, 2),
            "title_length": len(title),
            "meta_description_length": len(meta_description),
            "word_count": readability.word_count,
            "internal_links_found": len(unique_internal_links),
            "internal_links_checked": checked_count,
            "internal_links_ok": status_200_count,
            "internal_links_broken": broken_count,
            "schemas_found": len(schemas),
            "missing_recommended_schemas": [s.value for s in missing_schemas],
            "images_total": len(images),
            "images_missing_alt": len(images_without_alt),
            "target_keywords_checked": len(keyword_density),
            "tls_retry_insecure": used_insecure_tls,
        },
        "components": {
            "readability": readability.dict(),
            "content_quality": content_quality.dict(),
            "keyword_density": keyword_presence_summary,
            "security_headers": security_headers.dict(),
            "accessibility": accessibility.dict(),
            "robots_txt": robots_analysis.dict(),
            "sitemap": sitemap_analysis.dict() if sitemap_analysis else None,
        },
        "recommendations": recommendations[:15],
        "mode": "local-first",
    }
