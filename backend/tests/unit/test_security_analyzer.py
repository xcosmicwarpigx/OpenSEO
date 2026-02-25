"""
Unit tests for security header analyzer
"""
import pytest
from utils.security_analyzer import (
    analyze_security_headers,
    get_security_grade,
    generate_security_report
)


class TestAnalyzeSecurityHeaders:
    def test_perfect_security_headers(self):
        headers = {
            "content-security-policy": "default-src 'self'",
            "strict-transport-security": "max-age=31536000; includeSubDomains",
            "x-content-type-options": "nosniff",
            "x-frame-options": "DENY",
            "referrer-policy": "strict-origin-when-cross-origin",
            "permissions-policy": "camera=(), microphone=()"
        }
        result = analyze_security_headers(headers)
        assert result.score == 100
        assert len(result.missing_headers) == 0
    
    def test_missing_all_headers(self):
        headers = {}
        result = analyze_security_headers(headers)
        assert result.score == 0
        assert len(result.missing_headers) == 6
    
    def test_partial_headers(self):
        headers = {
            "x-frame-options": "SAMEORIGIN",
            "x-content-type-options": "nosniff"
        }
        result = analyze_security_headers(headers)
        assert 0 < result.score < 100
        assert "Content-Security-Policy" in result.missing_headers
    
    def test_case_insensitive_headers(self):
        headers = {
            "X-Frame-Options": "DENY",
            "CONTENT-SECURITY-POLICY": "default-src 'self'"
        }
        result = analyze_security_headers(headers)
        assert result.x_frame_options == "DENY"
        assert result.content_security_policy == "default-src 'self'"


class TestGetSecurityGrade:
    def test_grade_a(self):
        assert get_security_grade(95) == "A"
        assert get_security_grade(90) == "A"
    
    def test_grade_b(self):
        assert get_security_grade(85) == "B"
        assert get_security_grade(80) == "B"
    
    def test_grade_c(self):
        assert get_security_grade(75) == "C"
        assert get_security_grade(70) == "C"
    
    def test_grade_f(self):
        assert get_security_grade(50) == "F"
        assert get_security_grade(0) == "F"


class TestGenerateSecurityReport:
    def test_secure_report(self):
        headers = {
            "content-security-policy": "default-src 'self'",
            "strict-transport-security": "max-age=31536000",
            "x-content-type-options": "nosniff",
            "x-frame-options": "DENY",
            "referrer-policy": "strict-origin",
            "permissions-policy": "camera=()"
        }
        analysis = analyze_security_headers(headers)
        report = generate_security_report(analysis)
        
        assert report["score"] == 100
        assert report["grade"] == "A"
        assert report["status"] == "secure"
        assert len(report["missing_headers"]) == 0
    
    def test_vulnerable_report(self):
        headers = {}
        analysis = analyze_security_headers(headers)
        report = generate_security_report(analysis)
        
        assert report["grade"] == "F"
        assert report["status"] == "vulnerable"
        assert len(report["recommendations"]) > 0