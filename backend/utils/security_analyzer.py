"""
Security Headers Analysis Module
Checks for security best practices in HTTP response headers.
"""
from typing import Dict, List, Any, Optional
from models import SecurityHeaders


# Security headers to check
SECURITY_HEADERS = {
    "Content-Security-Policy": {
        "description": "Prevents XSS and data injection attacks",
        "severity": "high",
        "recommendation": "Implement a CSP policy: default-src 'self'"
    },
    "Strict-Transport-Security": {
        "description": "Forces HTTPS connections",
        "severity": "high", 
        "recommendation": "Add: max-age=31536000; includeSubDomains"
    },
    "X-Content-Type-Options": {
        "description": "Prevents MIME type sniffing",
        "severity": "medium",
        "recommendation": "Set to: nosniff"
    },
    "X-Frame-Options": {
        "description": "Prevents clickjacking attacks",
        "severity": "high",
        "recommendation": "Set to: DENY or SAMEORIGIN"
    },
    "Referrer-Policy": {
        "description": "Controls referrer information",
        "severity": "medium",
        "recommendation": "Set to: strict-origin-when-cross-origin"
    },
    "Permissions-Policy": {
        "description": "Controls browser features/APIs",
        "severity": "low",
        "recommendation": "Disable unused features like camera, microphone"
    }
}


def analyze_security_headers(headers: Dict[str, str]) -> SecurityHeaders:
    """Analyze security headers from HTTP response."""
    # Normalize header keys to lowercase for comparison
    normalized = {k.lower(): v for k, v in headers.items()}
    
    csp = normalized.get('content-security-policy')
    hsts = normalized.get('strict-transport-security')
    x_content_type = normalized.get('x-content-type-options')
    x_frame = normalized.get('x-frame-options')
    referrer = normalized.get('referrer-policy')
    permissions = normalized.get('permissions-policy') or normalized.get('feature-policy')
    
    # Calculate score
    score = 0
    missing = []
    recommendations = []
    
    if csp:
        score += 20
        # Check if CSP is too permissive
        if "'unsafe-inline'" in csp and "'unsafe-eval'" in csp:
            recommendations.append("CSP allows unsafe-inline and unsafe-eval - consider stricter policy")
    else:
        missing.append("Content-Security-Policy")
        recommendations.append(SECURITY_HEADERS["Content-Security-Policy"]["recommendation"])
    
    if hsts:
        score += 20
        # Check max-age
        if "max-age" in hsts:
            try:
                max_age = int(hsts.split("max-age=")[1].split(";")[0])
                if max_age < 31536000:  # Less than 1 year
                    recommendations.append("Consider increasing HSTS max-age to at least 1 year (31536000)")
            except (IndexError, ValueError):
                pass
    else:
        missing.append("Strict-Transport-Security")
        recommendations.append(SECURITY_HEADERS["Strict-Transport-Security"]["recommendation"])
    
    if x_content_type and x_content_type.lower() == "nosniff":
        score += 15
    else:
        missing.append("X-Content-Type-Options")
        recommendations.append(SECURITY_HEADERS["X-Content-Type-Options"]["recommendation"])
    
    if x_frame and x_frame.upper() in ["DENY", "SAMEORIGIN"]:
        score += 20
    else:
        missing.append("X-Frame-Options")
        recommendations.append(SECURITY_HEADERS["X-Frame-Options"]["recommendation"])
    
    if referrer:
        score += 10
        good_policies = ["no-referrer", "strict-origin", "strict-origin-when-cross-origin"]
        if not any(policy in referrer.lower() for policy in good_policies):
            recommendations.append("Consider stricter Referrer-Policy")
    else:
        missing.append("Referrer-Policy")
        recommendations.append(SECURITY_HEADERS["Referrer-Policy"]["recommendation"])
    
    if permissions:
        score += 15
    else:
        missing.append("Permissions-Policy")
        recommendations.append(SECURITY_HEADERS["Permissions-Policy"]["recommendation"])
    
    return SecurityHeaders(
        content_security_policy=csp,
        strict_transport_security=hsts,
        x_content_type_options=x_content_type,
        x_frame_options=x_frame,
        referrer_policy=referrer,
        permissions_policy=permissions,
        score=score,
        missing_headers=missing,
        recommendations=recommendations
    )


def get_security_grade(score: int) -> str:
    """Get letter grade for security score."""
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"


def generate_security_report(analysis: SecurityHeaders) -> Dict[str, Any]:
    """Generate a detailed security report."""
    return {
        "score": analysis.score,
        "grade": get_security_grade(analysis.score),
        "status": "secure" if analysis.score >= 80 else "needs_improvement" if analysis.score >= 50 else "vulnerable",
        "missing_headers": analysis.missing_headers,
        "recommendations": analysis.recommendations,
        "header_values": {
            "content_security_policy": analysis.content_security_policy,
            "strict_transport_security": analysis.strict_transport_security,
            "x_content_type_options": analysis.x_content_type_options,
            "x_frame_options": analysis.x_frame_options,
            "referrer_policy": analysis.referrer_policy,
            "permissions_policy": analysis.permissions_policy
        }
    }