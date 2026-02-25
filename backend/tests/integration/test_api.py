"""
Integration tests for FastAPI endpoints
"""
import pytest
from fastapi.testclient import TestClient
from main import app


client = TestClient(app)


class TestHealthEndpoints:
    def test_root_endpoint(self):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "OpenSEO" in data["message"]
        assert "version" in data
    
    def test_health_endpoint(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestDashboardEndpoints:
    def test_dashboard_stats(self):
        response = client.get("/api/dashboard/stats")
        assert response.status_code == 200
        data = response.json()
        assert "tools_available" in data
        assert len(data["tools_available"]) > 0


class TestCrawlerEndpoints:
    def test_start_crawl_invalid_url(self):
        response = client.post("/api/crawl", json={
            "url": "not-a-valid-url",
            "max_pages": 10
        })
        assert response.status_code == 422  # Validation error
    
    def test_start_crawl_valid_url(self):
        # Note: This would actually trigger a crawl in real scenario
        # For integration tests, we'd mock the celery task
        response = client.post("/api/crawl", json={
            "url": "https://example.com",
            "max_pages": 5
        })
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert data["status"] == "pending"
    
    def test_get_crawl_status_invalid_task(self):
        response = client.get("/api/crawl/invalid-task-id")
        assert response.status_code == 200
        # Should return status even for invalid task


class TestCompetitiveEndpoints:
    def test_keyword_gap_invalid_domains(self):
        response = client.post("/api/competitive/keyword-gap", json={
            "domain_a": "",
            "domain_b": "competitor.com"
        })
        assert response.status_code == 422
    
    def test_keyword_gap_valid_domains(self):
        response = client.post("/api/competitive/keyword-gap", json={
            "domain_a": "example.com",
            "domain_b": "competitor.com",
            "max_keywords": 50
        })
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
    
    def test_share_of_voice(self):
        response = client.post("/api/competitive/share-of-voice", json={
            "domains": ["example.com", "competitor.com"],
            "keywords": ["seo tools", "keyword research"]
        })
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
    
    def test_competitor_overview(self):
        response = client.get("/api/competitive/overview/example.com")
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data


class TestContentOptimizerEndpoints:
    def test_content_optimizer_invalid_url(self):
        response = client.post("/api/tools/content-optimizer/analyze", json={
            "url": "not-valid",
            "target_keywords": ["seo"]
        })
        assert response.status_code == 422
    
    def test_content_optimizer_no_url(self):
        response = client.post("/api/tools/content-optimizer/analyze", json={{
            "target_keywords": ["seo"]
        }})
        assert response.status_code == 422


class TestBulkAnalyzerEndpoints:
    def test_bulk_analyzer_too_many_urls(self):
        urls = [f"https://example.com/page{i}" for i in range(60)]
        response = client.post("/api/tools/bulk-url-analyzer/analyze", json={
            "urls": urls
        })
        assert response.status_code == 400
    
    def test_bulk_analyzer_empty_urls(self):
        response = client.post("/api/tools/bulk-url-analyzer/analyze", json={
            "urls": []
        })
        # Should handle gracefully
        assert response.status_code in [200, 422]
    
    def test_start_bulk_analyzer(self):
        response = client.post("/api/tools/bulk-url-analyzer", json={
            "urls": [
                "https://example.com/page1",
                "https://example.com/page2"
            ],
            "checks": ["status", "meta"]
        })
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert data["url_count"] == 2