"""
Integration tests for models
"""
import pytest
from pydantic import ValidationError
from datetime import datetime, timezone
from models import (
    CrawlRequest, CrawlResult, PageData, PageIssue,
    KeywordGapRequest, ShareOfVoiceRequest,
    ContentOptimizerRequest, BulkUrlRequest
)


class TestCrawlRequest:
    def test_valid_crawl_request(self):
        request = CrawlRequest(
            url="https://example.com",
            max_pages=100,
            respect_robots_txt=True
        )
        assert request.max_pages == 100
        assert str(request.url) == "https://example.com/"
    
    def test_default_max_pages(self):
        request = CrawlRequest(url="https://example.com")
        assert request.max_pages == 100
    
    def test_invalid_url(self):
        with pytest.raises(ValidationError):
            CrawlRequest(url="not-a-url")


class TestPageData:
    def test_minimal_page_data(self):
        page = PageData(
            url="https://example.com",
            status_code=200,
            crawl_time=datetime.now(timezone.utc)
        )
        assert page.url == "https://example.com"
        assert page.status_code == 200

    def test_page_with_metadata(self):
        page = PageData(
            url="https://example.com",
            status_code=200,
            title="Test Page",
            meta_description="A test description",
            h1="Main Heading",
            crawl_time=datetime.now(timezone.utc)
        )
        assert page.title == "Test Page"
        assert page.h1 == "Main Heading"


class TestKeywordGapRequest:
    def test_valid_request(self):
        request = KeywordGapRequest(
            domain_a="example.com",
            domain_b="competitor.com",
            max_keywords=50
        )
        assert request.max_keywords == 50
    
    def test_default_max_keywords(self):
        request = KeywordGapRequest(
            domain_a="example.com",
            domain_b="competitor.com"
        )
        assert request.max_keywords == 100


class TestShareOfVoiceRequest:
    def test_valid_request(self):
        request = ShareOfVoiceRequest(
            domains=["example.com", "competitor.com"],
            keywords=["seo", "marketing"]
        )
        assert len(request.domains) == 2
        assert len(request.keywords) == 2


class TestContentOptimizerRequest:
    def test_valid_request(self):
        request = ContentOptimizerRequest(
            url="https://example.com/blog/post",
            target_keywords=["seo tools", "content optimization"]
        )
        assert len(request.target_keywords) == 2
    
    def test_empty_keywords(self):
        request = ContentOptimizerRequest(url="https://example.com")
        assert request.target_keywords == []


class TestBulkUrlRequest:
    def test_valid_request(self):
        request = BulkUrlRequest(
            urls=[
                "https://example.com/page1",
                "https://example.com/page2"
            ],
            checks=["status", "meta"]
        )
        assert len(request.urls) == 2
        assert "status" in request.checks
    
    def test_default_checks(self):
        request = BulkUrlRequest(urls=["https://example.com"])
        assert request.checks == ["status", "meta", "headers", "performance"]