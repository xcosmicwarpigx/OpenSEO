"""
Content Analysis Module
Analyzes readability, keyword density, content quality, and provides optimization suggestions.
"""
import re
import math
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from models import (
    ReadabilityScore, KeywordDensity, ContentQuality, ContentOptimizationSuggestion,
    HeadingStructure
)


# Syllable counting for readability
def count_syllables(word: str) -> int:
    """Count syllables in a word using vowel group counting."""
    word = word.lower()
    if len(word) <= 3:
        return 1
    
    # Remove trailing e
    if word.endswith('e'):
        word = word[:-1]
    
    # Count vowel groups
    vowels = "aeiouy"
    syllables = 0
    prev_was_vowel = False
    
    for char in word:
        is_vowel = char in vowels
        if is_vowel and not prev_was_vowel:
            syllables += 1
        prev_was_vowel = is_vowel
    
    return max(1, syllables)


def calculate_readability(text: str, title: str = "", h1: str = "") -> ReadabilityScore:
    """Calculate Flesch Reading Ease and Flesch-Kincaid Grade Level."""
    if not text:
        return ReadabilityScore()
    
    # Clean text
    text = re.sub(r'<[^>]+>', '', text)
    
    # Count sentences (approximate by punctuation)
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    sentence_count = len(sentences)
    
    # Count words
    words = re.findall(r'\b\w+\b', text.lower())
    word_count = len(words)
    
    if sentence_count == 0 or word_count == 0:
        return ReadabilityScore(word_count=word_count)
    
    # Count syllables
    syllable_count = sum(count_syllables(w) for w in words)
    complex_words = sum(1 for w in words if count_syllables(w) >= 3)
    
    # Calculate metrics
    avg_words_per_sentence = word_count / sentence_count
    avg_syllables_per_word = syllable_count / word_count
    
    # Flesch Reading Ease (higher = easier)
    flesch_reading_ease = 206.835 - (1.015 * avg_words_per_sentence) - (84.6 * avg_syllables_per_word)
    
    # Flesch-Kincaid Grade Level
    flesch_kincaid_grade = (0.39 * avg_words_per_sentence) + (11.8 * avg_syllables_per_word) - 15.59
    
    # Reading time (avg 200 wpm)
    reading_time = word_count / 200
    
    return ReadabilityScore(
        flesch_reading_ease=round(flesch_reading_ease, 1),
        flesch_kincaid_grade=round(flesch_kincaid_grade, 1),
        word_count=word_count,
        sentence_count=sentence_count,
        avg_words_per_sentence=round(avg_words_per_sentence, 1),
        complex_words_count=complex_words,
        reading_time_minutes=round(reading_time, 1)
    )


def get_readability_interpretation(score: float) -> str:
    """Get interpretation of Flesch Reading Ease score."""
    if score >= 90:
        return "Very Easy (5th grade)"
    elif score >= 80:
        return "Easy (6th grade)"
    elif score >= 70:
        return "Fairly Easy (7th grade)"
    elif score >= 60:
        return "Standard (8th-9th grade)"
    elif score >= 50:
        return "Fairly Difficult (10th-12th grade)"
    elif score >= 30:
        return "Difficult (College)"
    else:
        return "Very Difficult (College Graduate)"


def calculate_keyword_density(
    text: str,
    title: str = "",
    h1: str = "",
    meta_description: str = "",
    target_keywords: List[str] = []
) -> List[KeywordDensity]:
    """Calculate keyword density and placement for target keywords."""
    if not text or not target_keywords:
        return []
    
    # Clean and tokenize
    clean_text = re.sub(r'<[^>]+>', ' ', text).lower()
    words = re.findall(r'\b\w+\b', clean_text)
    total_words = len(words)
    
    if total_words == 0:
        return []
    
    # Get first 100 words
    first_100 = ' '.join(words[:100])
    
    results = []
    for keyword in target_keywords:
        keyword_lower = keyword.lower()
        
        # Count occurrences
        # Check for exact match and word variations
        pattern = r'\b' + re.escape(keyword_lower) + r'\b'
        matches = len(re.findall(pattern, clean_text))
        
        # Calculate density
        density = (matches / total_words) * 100 if total_words > 0 else 0
        
        results.append(KeywordDensity(
            keyword=keyword,
            count=matches,
            density_percent=round(density, 2),
            in_title=keyword_lower in title.lower(),
            in_h1=keyword_lower in h1.lower(),
            in_meta_description=keyword_lower in meta_description.lower(),
            in_first_100_words=keyword_lower in first_100
        ))
    
    return results


def extract_top_keywords(text: str, exclude_common: bool = True, top_n: int = 10) -> List[Dict[str, Any]]:
    """Extract top keywords by frequency from text."""
    from collections import Counter
    
    # Common words to exclude
    stopwords = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare',
        'ought', 'used', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by',
        'from', 'as', 'into', 'through', 'during', 'before', 'after', 'above',
        'below', 'between', 'under', 'and', 'but', 'or', 'yet', 'so', 'if',
        'because', 'although', 'though', 'while', 'where', 'when', 'that',
        'which', 'who', 'whom', 'whose', 'what', 'this', 'these', 'those',
        'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her',
        'us', 'them', 'my', 'your', 'his', 'its', 'our', 'their', 'mine',
        'yours', 'hers', 'ours', 'theirs', 'myself', 'yourself', 'himself',
        'herself', 'itself', 'ourselves', 'yourselves', 'themselves'
    }
    
    # Clean and tokenize
    clean_text = re.sub(r'<[^>]+>', ' ', text).lower()
    words = re.findall(r'\b[a-z]+\b', clean_text)
    
    if exclude_common:
        words = [w for w in words if w not in stopwords and len(w) > 2]
    
    # Count word frequencies
    word_counts = Counter(words)
    total_words = sum(word_counts.values())
    
    # Get top N
    top_keywords = []
    for word, count in word_counts.most_common(top_n):
        density = (count / total_words) * 100 if total_words > 0 else 0
        top_keywords.append({
            'keyword': word,
            'count': count,
            'density_percent': round(density, 2)
        })
    
    return top_keywords


def analyze_content_quality(
    text: str,
    headings: List[HeadingStructure] = [],
    existing_keywords: List[KeywordDensity] = []
) -> ContentQuality:
    """Analyze content for quality issues."""
    clean_text = re.sub(r'<[^>]+>', ' ', text)
    words = clean_text.split()
    word_count = len(words)
    
    # Check for thin content
    thin_content = word_count < 300
    
    # Check for large paragraphs (>150 words)
    paragraphs = [p.strip() for p in clean_text.split('\n\n') if p.strip()]
    large_paragraphs = [p for p in paragraphs if len(p.split()) > 150]
    
    # Check for missing subheadings
    h2_count = sum(1 for h in headings if h.level == 2)
    missing_subheadings = word_count > 300 and h2_count == 0
    
    # Check for keyword stuffing (>5% density for any keyword)
    keyword_stuffing = any(kw.density_percent > 5 for kw in existing_keywords)
    
    # Check for duplicate content risk (simplified - would need external comparison)
    duplicate_content_risk = False  # Placeholder
    
    return ContentQuality(
        thin_content=thin_content,
        duplicate_content_risk=duplicate_content_risk,
        keyword_stuffing_detected=keyword_stuffing,
        large_paragraphs=[p[:100] + "..." for p in large_paragraphs[:3]],  # First 3 large paragraphs
        missing_subheadings=missing_subheadings
    )


def generate_content_suggestions(
    title: str,
    meta_description: str,
    h1: str,
    headings: List[HeadingStructure],
    readability: ReadabilityScore,
    content_quality: ContentQuality,
    keyword_density: List[KeywordDensity],
    images_without_alt: int,
    internal_links: int,
    word_count: int
) -> List[ContentOptimizationSuggestion]:
    """Generate prioritized content optimization suggestions."""
    suggestions = []
    
    # Title suggestions
    if not title:
        suggestions.append(ContentOptimizationSuggestion(
            category="title",
            priority="high",
            issue="Missing title tag",
            recommendation="Add a descriptive title tag (50-60 characters)",
            impact="Critical for SEO and click-through rates"
        ))
    elif len(title) < 30:
        suggestions.append(ContentOptimizationSuggestion(
            category="title",
            priority="medium",
            current_value=title,
            issue="Title too short",
            recommendation=f"Expand title to 50-60 characters (currently {len(title)})",
            impact="Better keyword targeting and CTR"
        ))
    elif len(title) > 60:
        suggestions.append(ContentOptimizationSuggestion(
            category="title",
            priority="low",
            current_value=title,
            issue="Title may be truncated in SERP",
            recommendation=f"Shorten title to under 60 characters (currently {len(title)})",
            impact="Full title visible in search results"
        ))
    
    # Meta description suggestions
    if not meta_description:
        suggestions.append(ContentOptimizationSuggestion(
            category="meta",
            priority="medium",
            issue="Missing meta description",
            recommendation="Add a compelling meta description (150-160 characters)",
            impact="Improves click-through rate from search results"
        ))
    elif len(meta_description) < 120:
        suggestions.append(ContentOptimizationSuggestion(
            category="meta",
            priority="low",
            current_value=meta_description[:50] + "...",
            issue="Meta description could be more descriptive",
            recommendation=f"Expand to 150-160 characters (currently {len(meta_description)})",
            impact="More context for users in search results"
        ))
    
    # H1 suggestions
    if not h1:
        suggestions.append(ContentOptimizationSuggestion(
            category="headings",
            priority="high",
            issue="Missing H1 heading",
            recommendation="Add one H1 heading that describes the main topic",
            impact="Critical for SEO and content structure"
        ))
    
    # Content length suggestions
    if content_quality.thin_content:
        suggestions.append(ContentOptimizationSuggestion(
            category="content",
            priority="high",
            issue="Thin content detected",
            recommendation=f"Expand content to at least 300 words (currently {word_count})",
            impact="Better rankings and user engagement"
        ))
    
    # Subheading suggestions
    if content_quality.missing_subheadings:
        suggestions.append(ContentOptimizationSuggestion(
            category="headings",
            priority="medium",
            issue="Long content without subheadings",
            recommendation="Add H2 subheadings every 300 words to improve readability",
            impact="Better user experience and SEO structure"
        ))
    
    # Large paragraph suggestions
    if content_quality.large_paragraphs:
        suggestions.append(ContentOptimizationSuggestion(
            category="content",
            priority="medium",
            issue=f"{len(content_quality.large_paragraphs)} large paragraphs detected",
            recommendation="Break paragraphs into 2-4 sentences for better readability",
            impact="Improved readability and engagement"
        ))
    
    # Readability suggestions
    if readability.flesch_reading_ease and readability.flesch_reading_ease < 50:
        suggestions.append(ContentOptimizationSuggestion(
            category="content",
            priority="medium",
            issue="Content may be too difficult to read",
            recommendation="Simplify language, use shorter sentences, avoid jargon",
            impact="Better engagement and broader audience reach"
        ))
    
    # Keyword suggestions
    for kw in keyword_density:
        if kw.density_percent > 5:
            suggestions.append(ContentOptimizationSuggestion(
                category="content",
                priority="high",
                issue=f"Possible keyword stuffing: '{kw.keyword}'",
                recommendation=f"Reduce keyword usage from {kw.density_percent}% to under 2%",
                impact="Avoid search engine penalties"
            ))
        elif kw.density_percent < 0.5 and kw.in_title:
            suggestions.append(ContentOptimizationSuggestion(
                category="content",
                priority="medium",
                issue=f"Target keyword '{kw.keyword}' underused in content",
                recommendation="Include keyword naturally in first 100 words and throughout content",
                impact="Better keyword relevance signals"
            ))
        
        if not kw.in_first_100_words and kw.in_title:
            suggestions.append(ContentOptimizationSuggestion(
                category="content",
                priority="medium",
                issue=f"Keyword '{kw.keyword}' not in first 100 words",
                recommendation="Include the keyword early in the content",
                impact="Stronger topical relevance signal"
            ))
    
    # Image suggestions
    if images_without_alt > 0:
        suggestions.append(ContentOptimizationSuggestion(
            category="images",
            priority="medium",
            issue=f"{images_without_alt} images missing alt text",
            recommendation="Add descriptive alt text to all images",
            impact="Better accessibility and image SEO"
        ))
    
    # Internal linking suggestions
    if internal_links < 3 and word_count > 500:
        suggestions.append(ContentOptimizationSuggestion(
            category="internal_links",
            priority="medium",
            issue="Low internal linking",
            recommendation="Add 3-5 relevant internal links to related content",
            impact="Better site structure and PageRank distribution"
        ))
    
    # Sort by priority
    priority_order = {"high": 0, "medium": 1, "low": 2}
    suggestions.sort(key=lambda x: priority_order.get(x.priority, 3))
    
    return suggestions


def calculate_content_score(
    readability: ReadabilityScore,
    content_quality: ContentQuality,
    keyword_density: List[KeywordDensity],
    title: str,
    meta_description: str,
    h1: str,
    images_count: int,
    images_with_alt: int,
    internal_links: int,
    word_count: int
) -> int:
    """Calculate an overall content optimization score (0-100)."""
    score = 50  # Base score
    
    # Content length (up to 15 points)
    if word_count >= 1000:
        score += 15
    elif word_count >= 500:
        score += 10
    elif word_count >= 300:
        score += 5
    
    # Title optimization (up to 10 points)
    if title and 30 <= len(title) <= 60:
        score += 10
    elif title:
        score += 5
    
    # Meta description (up to 5 points)
    if meta_description and 120 <= len(meta_description) <= 160:
        score += 5
    
    # H1 present (up to 10 points)
    if h1:
        score += 10
    
    # Readability (up to 10 points)
    if readability.flesch_reading_ease:
        if readability.flesch_reading_ease >= 60:
            score += 10
        elif readability.flesch_reading_ease >= 40:
            score += 5
    
    # Images with alt text (up to 5 points)
    if images_count > 0:
        alt_ratio = images_with_alt / images_count
        score += int(5 * alt_ratio)
    else:
        score += 5  # No images to worry about
    
    # Internal linking (up to 5 points)
    if internal_links >= 3:
        score += 5
    elif internal_links >= 1:
        score += 2
    
    # Keyword optimization (up to 10 points)
    good_keywords = sum(1 for kw in keyword_density if 0.5 <= kw.density_percent <= 2.5)
    stuffed_keywords = sum(1 for kw in keyword_density if kw.density_percent > 5)
    score += min(10, good_keywords * 2)
    score -= stuffed_keywords * 5
    
    # Penalties
    if content_quality.thin_content:
        score -= 15
    if content_quality.keyword_stuffing_detected:
        score -= 10
    if content_quality.missing_subheadings and word_count > 500:
        score -= 5
    
    return max(0, min(100, score))