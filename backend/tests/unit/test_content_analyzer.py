"""
Unit tests for content analyzer utilities
"""
import pytest
from utils.content_analyzer import (
    count_syllables,
    calculate_readability,
    calculate_content_score,
    get_readability_interpretation
)
from models import ReadabilityScore, ContentQuality, KeywordDensity


def estimate_ctr(position: int) -> float:
    """Estimate CTR based on position in SERP (copied from tasks.competitive)."""
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


class TestCountSyllables:
    def test_simple_words(self):
        assert count_syllables("cat") == 1
        assert count_syllables("dog") == 1
        assert count_syllables("the") == 1
    
    def test_multi_syllable_words(self):
        assert count_syllables("hello") == 2
        assert count_syllables("beautiful") == 3
        assert count_syllables("conversation") >= 3
    
    def test_silent_e(self):
        assert count_syllables("cake") == 1
        assert count_syllables("bake") == 1
        assert count_syllables("make") == 1
    
    def test_short_words(self):
        assert count_syllables("a") == 1
        assert count_syllables("I") == 1
        assert count_syllables("to") == 1


class TestCalculateReadability:
    def test_empty_text(self):
        result = calculate_readability("")
        assert result.word_count == 0
        assert result.flesch_reading_ease is None
    
    def test_simple_text(self):
        text = "The cat sat on the mat. It was a sunny day."
        result = calculate_readability(text)
        assert result.word_count == 11
        assert result.sentence_count == 2
        assert result.flesch_reading_ease is not None
    
    def test_longer_text(self):
        text = "The quick brown fox jumps over the lazy dog. " * 10
        result = calculate_readability(text)
        assert result.word_count == 90
        assert result.avg_words_per_sentence == 9.0
        assert result.reading_time_minutes > 0


class TestEstimateCTR:
    def test_position_1(self):
        assert estimate_ctr(1) == 0.28
    
    def test_position_3(self):
        assert estimate_ctr(3) == 0.09
    
    def test_position_10(self):
        assert estimate_ctr(10) == 0.02
    
    def test_position_20(self):
        assert estimate_ctr(20) == 0.01
    
    def test_position_50(self):
        assert estimate_ctr(50) == 0.005


class TestGetReadabilityInterpretation:
    def test_very_easy(self):
        assert "Very Easy" in get_readability_interpretation(95)
    
    def test_standard(self):
        assert "Standard" in get_readability_interpretation(65)
    
    def test_difficult(self):
        assert "Difficult" in get_readability_interpretation(40)
    
    def test_very_difficult(self):
        assert "Very Difficult" in get_readability_interpretation(20)


class TestCalculateContentScore:
    def test_perfect_score(self):
        readability = ReadabilityScore(
            word_count=1500,
            flesch_reading_ease=70
        )
        content_quality = ContentQuality(
            thin_content=False,
            duplicate_content_risk=False,
            keyword_stuffing_detected=False,
            large_paragraphs=[],
            missing_subheadings=False
        )
        score = calculate_content_score(
            readability, content_quality, [],
            "Perfect SEO Title Example Here",
            "This is a perfect meta description that meets all requirements.",
            "Main Heading",
            10, 10, 5, 1500
        )
        assert score >= 80
    
    def test_thin_content_penalty(self):
        readability = ReadabilityScore(word_count=200)
        content_quality = ContentQuality(
            thin_content=True,
            duplicate_content_risk=False,
            keyword_stuffing_detected=False,
            large_paragraphs=[],
            missing_subheadings=False
        )
        score = calculate_content_score(
            readability, content_quality, [],
            "", "", "", 0, 0, 0, 200
        )
        assert score < 70  # Should be penalized
    
    def test_keyword_stuffing_penalty(self):
        readability = ReadabilityScore(word_count=1000)
        content_quality = ContentQuality(
            thin_content=False,
            duplicate_content_risk=False,
            keyword_stuffing_detected=True,
            large_paragraphs=[],
            missing_subheadings=False
        )
        score = calculate_content_score(
            readability, content_quality, [],
            "Title", "Description", "H1", 5, 5, 3, 1000
        )
        # Should be penalized
        assert score < 90