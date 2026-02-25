"""
Schema / Structured Data Analysis Module
Validates JSON-LD structured data and checks for recommended schema types.
"""
import json
import re
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from models import StructuredData, SchemaAnalysis, SchemaType


# Required and recommended fields by schema type
SCHEMA_REQUIREMENTS = {
    "Article": {
        "required": ["headline", "author"],
        "recommended": ["datePublished", "dateModified", "image", "publisher"]
    },
    "Product": {
        "required": ["name", "offers"],
        "recommended": ["image", "description", "sku", "brand", "aggregateRating", "review"]
    },
    "Organization": {
        "required": ["name"],
        "recommended": ["url", "logo", "sameAs", "contactPoint"]
    },
    "WebSite": {
        "required": ["url", "name"],
        "recommended": ["potentialAction", "description"]
    },
    "LocalBusiness": {
        "required": ["name", "address"],
        "recommended": ["telephone", "url", "openingHours", "geo", "image"]
    },
    "BreadcrumbList": {
        "required": ["itemListElement"],
        "recommended": []
    },
    "FAQPage": {
        "required": ["mainEntity"],
        "recommended": []
    },
    "HowTo": {
        "required": ["name", "step"],
        "recommended": ["image", "totalTime", "estimatedCost"]
    }
}


def extract_schema_types(soup: BeautifulSoup) -> List[StructuredData]:
    """Extract and parse all JSON-LD structured data from a page."""
    schemas = []
    
    # Find all JSON-LD scripts
    jsonld_scripts = soup.find_all("script", type="application/ld+json")
    
    for script in jsonld_scripts:
        try:
            data = json.loads(script.string)
            
            # Handle both single objects and arrays
            if isinstance(data, list):
                for item in data:
                    schema = parse_schema(item)
                    if schema:
                        schemas.append(schema)
            else:
                schema = parse_schema(data)
                if schema:
                    schemas.append(schema)
                    
        except (json.JSONDecodeError, AttributeError):
            continue
    
    return schemas


def parse_schema(data: Dict[str, Any]) -> Optional[StructuredData]:
    """Parse a single schema object and validate it."""
    schema_type_str = data.get("@type", "Other")
    
    # Map to SchemaType enum
    try:
        schema_type = SchemaType(schema_type_str)
    except ValueError:
        schema_type = SchemaType.OTHER
    
    # Validate schema
    validation_errors = []
    recommended_missing = []
    
    type_key = schema_type_str if schema_type_str in SCHEMA_REQUIREMENTS else None
    
    if type_key:
        requirements = SCHEMA_REQUIREMENTS[type_key]
        
        # Check required fields
        for field in requirements["required"]:
            if field not in data or not data[field]:
                validation_errors.append(f"Missing required field: {field}")
        
        # Check recommended fields
        for field in requirements["recommended"]:
            if field not in data or not data[field]:
                recommended_missing.append(field)
    
    return StructuredData(
        schema_type=schema_type,
        raw_json=data,
        valid=len(validation_errors) == 0,
        validation_errors=validation_errors,
        recommended_fields_missing=recommended_missing
    )


def get_missing_recommended_schemas(
    found_schemas: List[StructuredData],
    page_type_hints: Dict[str, Any]
) -> List[SchemaType]:
    """Determine which recommended schemas are missing based on page content."""
    found_types = {s.schema_type for s in found_schemas}
    missing = []
    
    # Check for Organization/Website on homepage
    if page_type_hints.get("is_homepage", False):
        if SchemaType.ORGANIZATION not in found_types:
            missing.append(SchemaType.ORGANIZATION)
        if SchemaType.WEBSITE not in found_types:
            missing.append(SchemaType.WEBSITE)
    
    # Check for Article/BlogPosting on article pages
    if page_type_hints.get("has_article_markup", False):
        if SchemaType.ARTICLE not in found_types:
            missing.append(SchemaType.ARTICLE)
    
    # Check for Product on product pages
    if page_type_hints.get("has_product_info", False):
        if SchemaType.PRODUCT not in found_types:
            missing.append(SchemaType.PRODUCT)
    
    # Check for BreadcrumbList (recommended on most pages)
    if SchemaType.BREADCRUMB not in found_types:
        breadcrumbs = page_type_hints.get("breadcrumbs", [])
        if len(breadcrumbs) > 1:
            missing.append(SchemaType.BREADCRUMB)
    
    # Check for FAQPage if FAQ content detected
    if page_type_hints.get("has_faq_content", False):
        if SchemaType.FAQ not in found_types:
            missing.append(SchemaType.FAQ)
    
    # Check for LocalBusiness
    if page_type_hints.get("has_local_info", False):
        if SchemaType.LOCAL_BUSINESS not in found_types:
            missing.append(SchemaType.LOCAL_BUSINESS)
    
    return missing


def detect_page_type_hints(soup: BeautifulSoup, url: str) -> Dict[str, Any]:
    """Detect hints about page type from content."""
    hints = {
        "is_homepage": False,
        "has_article_markup": False,
        "has_product_info": False,
        "has_faq_content": False,
        "has_local_info": False,
        "breadcrumbs": []
    }
    
    # Check for homepage
    parsed = re.findall(r'https?://[^/]+/?$', url)
    hints["is_homepage"] = len(parsed) > 0
    
    # Check for article indicators
    article_tags = soup.find_all('article')
    hints["has_article_markup"] = len(article_tags) > 0
    
    # Check for product indicators
    product_selectors = ['.product', '[data-product]', '.woocommerce-product']
    for selector in product_selectors:
        if soup.select(selector):
            hints["has_product_info"] = True
            break
    
    # Check for FAQ indicators
    faq_patterns = [
        r'\bFAQ\b', r'\bFrequently Asked Questions\b',
        r'\bQ[:\.]?\s*', r'\bQuestion[:\.]?\s*'
    ]
    text_content = soup.get_text()
    for pattern in faq_patterns:
        if re.search(pattern, text_content, re.IGNORECASE):
            hints["has_faq_content"] = True
            break
    
    # Check for local business indicators
    local_patterns = [
        r'\bAddress\b', r'\bPhone\b', r'\bHours\b',
        r'\d{3}-\d{3}-\d{4}',  # Phone number
        r'\d+\s+[\w\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd)'
    ]
    for pattern in local_patterns:
        if re.search(pattern, text_content, re.IGNORECASE):
            hints["has_local_info"] = True
            break
    
    # Extract breadcrumbs
    breadcrumb_selectors = [
        '.breadcrumb', '.breadcrumbs', '[typeof="BreadcrumbList"]',
        '.yoast-breadcrumbs', '.rank-math-breadcrumb'
    ]
    for selector in breadcrumb_selectors:
        breadcrumbs = soup.select(selector)
        if breadcrumbs:
            links = breadcrumbs[0].find_all('a')
            hints["breadcrumbs"] = [a.get_text(strip=True) for a in links]
            break
    
    return hints


def generate_schema_recommendations(analysis: SchemaAnalysis) -> List[str]:
    """Generate recommendations based on schema analysis."""
    recommendations = []
    
    # General recommendations
    if analysis.total_schemas == 0:
        recommendations.append("No structured data found. Consider adding JSON-LD schemas for better rich snippet eligibility.")
    
    # Check for validation errors
    for schema in analysis.schemas_found:
        if schema.validation_errors:
            recommendations.append(
                f"Fix validation errors in {schema.schema_type.value} schema: {', '.join(schema.validation_errors[:2])}"
            )
        
        if schema.recommended_fields_missing:
            recommendations.append(
                f"Add recommended fields to {schema.schema_type.value}: {', '.join(schema.recommended_fields_missing[:3])}"
            )
    
    # Recommend missing schemas
    for missing in analysis.missing_recommended:
        recommendations.append(f"Consider adding {missing.value} structured data")
    
    return recommendations