"""
Unit tests for accessibility analyzer
"""
import pytest
from bs4 import BeautifulSoup
from utils.accessibility_analyzer import (
    analyze_accessibility,
    get_accessibility_grade,
    generate_accessibility_report
)


class TestAnalyzeAccessibility:
    def test_perfect_accessibility(self):
        html = """
        <html lang="en">
        <head><title>Test Page</title></head>
        <body>
            <main>
                <h1>Main Heading</h1>
                <img src="test.jpg" alt="Test image description">
                <a href="/page">Descriptive link text</a>
                <form>
                    <label for="name">Name:</label>
                    <input type="text" id="name">
                </form>
            </main>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'lxml')
        result = analyze_accessibility(soup, "http://test.com")
        
        assert result.score >= 90
        assert result.critical_issues == 0
        assert len(result.passed_checks) >= 3
    
    def test_missing_alt_text(self):
        html = """
        <html lang="en">
        <head><title>Test</title></head>
        <body>
            <img src="test.jpg">
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'lxml')
        result = analyze_accessibility(soup, "http://test.com")
        
        assert result.critical_issues >= 1
        assert any("alt text" in issue.message.lower() for issue in result.issues)
    
    def test_missing_title(self):
        html = """
        <html lang="en">
        <head></head>
        <body>
            <h1>Heading</h1>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'lxml')
        result = analyze_accessibility(soup, "http://test.com")
        
        assert any("missing title" in issue.message.lower() for issue in result.issues)
    
    def test_missing_language(self):
        html = """
        <html>
        <head><title>Test</title></head>
        <body></body>
        </html>
        """
        soup = BeautifulSoup(html, 'lxml')
        result = analyze_accessibility(soup, "http://test.com")
        
        assert any("language" in issue.message.lower() for issue in result.issues)
    
    def test_multiple_h1(self):
        html = """
        <html lang="en">
        <head><title>Test</title></head>
        <body>
            <h1>First Heading</h1>
            <h1>Second Heading</h1>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'lxml')
        result = analyze_accessibility(soup, "http://test.com")
        
        assert any("multiple h1" in issue.message.lower() for issue in result.issues)
    
    def test_skipped_heading_levels(self):
        html = """
        <html lang="en">
        <head><title>Test</title></head>
        <body>
            <h1>Main</h1>
            <h3>Skipped H2</h3>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'lxml')
        result = analyze_accessibility(soup, "http://test.com")
        
        assert any("skipped" in issue.message.lower() for issue in result.issues)
    
    def test_non_descriptive_links(self):
        html = """
        <html lang="en">
        <head><title>Test</title></head>
        <body>
            <a href="/page">click here</a>
            <a href="/other">read more</a>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'lxml')
        result = analyze_accessibility(soup, "http://test.com")
        
        link_issues = [i for i in result.issues if i.element == "a"]
        assert len(link_issues) >= 1


class TestGetAccessibilityGrade:
    def test_grade_a(self):
        assert get_accessibility_grade(95) == "A"
        assert get_accessibility_grade(100) == "A"
    
    def test_grade_b(self):
        assert get_accessibility_grade(90) == "B"
        assert get_accessibility_grade(85) == "B"
    
    def test_grade_f(self):
        assert get_accessibility_grade(50) == "F"
        assert get_accessibility_grade(0) == "F"


class TestGenerateAccessibilityReport:
    def test_report_structure(self):
        html = """
        <html lang="en">
        <head><title>Test</title></head>
        <body>
            <h1>Heading</h1>
            <img src="test.jpg">
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'lxml')
        score = analyze_accessibility(soup, "http://test.com")
        report = generate_accessibility_report(score)
        
        assert "score" in report
        assert "grade" in report
        assert "compliance_level" in report
        assert "issues_by_severity" in report
        assert "top_issues" in report
        assert "improvement_priority" in report