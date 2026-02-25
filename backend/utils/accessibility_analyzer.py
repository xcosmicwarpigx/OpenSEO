"""
Accessibility Analysis Module
Basic WCAG 2.1 compliance checks.
"""
import re
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup, Tag
from models import AccessibilityIssue, AccessibilityScore


def analyze_accessibility(soup: BeautifulSoup, url: str) -> AccessibilityScore:
    """Analyze page for accessibility issues."""
    issues = []
    passed = []
    
    # Check images for alt text (WCAG 1.1.1)
    images = soup.find_all("img")
    for img in images:
        if not img.get("alt") and not img.get("aria-label") and not img.get("aria-labelledby"):
            issues.append(AccessibilityIssue(
                wcag_guideline="1.1.1",
                severity="critical",
                element="img",
                message=f"Image missing alt text: {img.get('src', 'unknown')[:50]}",
                recommendation="Add descriptive alt text or mark as decorative with alt=''"
            ))
    
    if not any(not img.get("alt") for img in images):
        passed.append("All images have alt text (1.1.1)")
    
    # Check form labels (WCAG 1.3.1, 3.3.2)
    inputs = soup.find_all(["input", "select", "textarea"])
    for inp in inputs:
        input_id = inp.get("id")
        aria_label = inp.get("aria-label")
        aria_labelledby = inp.get("aria-labelledby")
        placeholder = inp.get("placeholder")
        
        # Check for associated label
        has_label = False
        if input_id:
            label = soup.find("label", attrs={"for": input_id})
            if label:
                has_label = True
        
        # Check for implicit label
        if inp.parent and inp.parent.name == "label":
            has_label = True
        
        if not has_label and not aria_label and not aria_labelledby and not placeholder:
            input_type = inp.get("type", "text")
            if input_type not in ["hidden", "submit", "button", "image", "reset"]:
                issues.append(AccessibilityIssue(
                    wcag_guideline="1.3.1",
                    severity="serious",
                    element=f"input[type={input_type}]",
                    message="Form input missing label",
                    recommendation="Add a label element or aria-label attribute"
                ))
    
    # Check link text (WCAG 2.4.4)
    bad_link_texts = ["click here", "read more", "learn more", "here", "link", "more"]
    links = soup.find_all("a")
    for link in links:
        text = link.get_text(strip=True).lower()
        href = link.get("href", "")
        
        # Skip anchor links and empty links
        if not href or href.startswith("#") or href.startswith("javascript:"):
            continue
        
        if any(bad in text for bad in bad_link_texts) and len(text) < 20:
            issues.append(AccessibilityIssue(
                wcag_guideline="2.4.4",
                severity="moderate",
                element="a",
                message=f"Non-descriptive link text: '{link.get_text(strip=True)}'",
                recommendation="Use descriptive link text that makes sense out of context"
            ))
    
    # Check for language attribute (WCAG 3.1.1)
    html_tag = soup.find("html")
    if html_tag and not html_tag.get("lang"):
        issues.append(AccessibilityIssue(
            wcag_guideline="3.1.1",
            severity="serious",
            element="html",
            message="Page language not specified",
            recommendation="Add lang attribute to html element (e.g., lang='en')"
        ))
    else:
        passed.append("Page language specified (3.1.1)")
    
    # Check page title (WCAG 2.4.2)
    title = soup.find("title")
    if not title or not title.get_text(strip=True):
        issues.append(AccessibilityIssue(
            wcag_guideline="2.4.2",
            severity="serious",
            element="title",
            message="Page missing title",
            recommendation="Add a descriptive title element"
        ))
    else:
        passed.append("Page has title (2.4.2)")
    
    # Check heading hierarchy (WCAG 1.3.1)
    headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
    prev_level = 0
    for h in headings:
        level = int(h.name[1])
        if prev_level > 0 and level > prev_level + 1:
            issues.append(AccessibilityIssue(
                wcag_guideline="1.3.1",
                severity="moderate",
                element=h.name,
                message=f"Skipped heading level: h{prev_level} to h{level}",
                recommendation="Maintain proper heading hierarchy without skipping levels"
            ))
        prev_level = level
    
    if headings:
        passed.append("Headings present (1.3.1)")
    
    # Check for duplicate H1 (WCAG 1.3.1)
    h1s = soup.find_all("h1")
    if len(h1s) > 1:
        issues.append(AccessibilityIssue(
            wcag_guideline="1.3.1",
            severity="moderate",
            element="h1",
            message=f"Multiple H1 elements found ({len(h1s)})",
            recommendation="Use only one H1 per page"
        ))
    
    # Check for bypass blocks (WCAG 2.4.1)
    skip_links = soup.find_all("a", href=re.compile(r"^#main|^#content", re.I))
    landmarks = soup.find_all(["main", "nav", "aside", "header", "footer"])
    if not skip_links and not landmarks:
        issues.append(AccessibilityIssue(
            wcag_guideline="2.4.1",
            severity="moderate",
            element="body",
            message="No skip link or ARIA landmarks found",
            recommendation="Add skip navigation link or use ARIA landmark regions"
        ))
    else:
        passed.append("Skip links or landmarks present (2.4.1)")
    
    # Check for contrast issues (basic check - real contrast requires rendering)
    # This is a placeholder - would need actual color values
    style_tags = soup.find_all("style")
    inline_styles = [tag.get("style", "") for tag in soup.find_all()]
    
    # Check for small text (potential contrast issue)
    small_text_pattern = r'font-size\s*:\s*(\d+)px'
    for style in inline_styles:
        match = re.search(small_text_pattern, style)
        if match:
            size = int(match.group(1))
            if size < 12:
                issues.append(AccessibilityIssue(
                    wcag_guideline="1.4.3",
                    severity="minor",
                    element="text",
                    message=f"Very small text detected ({size}px)",
                    recommendation="Ensure text is at least 12px and has sufficient contrast"
                ))
                break
    
    # Calculate score
    critical = sum(1 for i in issues if i.severity == "critical")
    serious = sum(1 for i in issues if i.severity == "serious")
    moderate = sum(1 for i in issues if i.severity == "moderate")
    minor = sum(1 for i in issues if i.severity == "minor")
    
    # Score calculation (100 - penalties)
    score = 100 - (critical * 15) - (serious * 10) - (moderate * 5) - (minor * 2)
    score = max(0, score)
    
    return AccessibilityScore(
        score=score,
        issues=issues,
        passed_checks=passed,
        critical_issues=critical,
        serious_issues=serious
    )


def get_accessibility_grade(score: int) -> str:
    """Get accessibility grade."""
    if score >= 95:
        return "A"
    elif score >= 85:
        return "B"
    elif score >= 75:
        return "C"
    elif score >= 65:
        return "D"
    else:
        return "F"


def generate_accessibility_report(score: AccessibilityScore) -> Dict[str, Any]:
    """Generate a comprehensive accessibility report."""
    return {
        "score": score.score,
        "grade": get_accessibility_grade(score.score),
        "compliance_level": "AAA" if score.score >= 95 else "AA" if score.score >= 80 else "A" if score.score >= 60 else "Non-compliant",
        "issues_by_severity": {
            "critical": score.critical_issues,
            "serious": score.serious_issues,
            "moderate": sum(1 for i in score.issues if i.severity == "moderate"),
            "minor": sum(1 for i in score.issues if i.severity == "minor")
        },
        "total_issues": len(score.issues),
        "passed_checks": score.passed_checks,
        "top_issues": [{
            "guideline": i.wcag_guideline,
            "severity": i.severity,
            "message": i.message,
            "recommendation": i.recommendation
        } for i in score.issues[:5]],  # Top 5 issues
        "improvement_priority": [
            i.recommendation for i in score.issues 
            if i.severity in ["critical", "serious"]
        ][:3]  # Top 3 priority fixes
    }