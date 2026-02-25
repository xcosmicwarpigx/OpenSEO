"""
Image Optimization Analysis Module
Analyzes images for optimization opportunities.
"""
import re
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup, Tag
from models import ImageAnalysis


def analyze_images(soup: BeautifulSoup, base_url: str, page_headers: Optional[Dict] = None) -> List[ImageAnalysis]:
    """Analyze all images on a page for optimization opportunities."""
    images = []
    img_tags = soup.find_all("img")
    
    for img in img_tags:
        analysis = analyze_single_image(img, base_url)
        if analysis:
            images.append(analysis)
    
    return images


def analyze_single_image(img_tag: Tag, base_url: str) -> Optional[ImageAnalysis]:
    """Analyze a single image tag."""
    src = img_tag.get("src", "")
    if not src:
        return None
    
    # Handle data URIs
    if src.startswith("data:"):
        return None
    
    # Build full URL
    if src.startswith("//"):
        full_url = "https:" + src
    elif src.startswith("http"):
        full_url = src
    else:
        full_url = urljoin(base_url, src)
    
    # Get alt text
    alt_text = img_tag.get("alt")
    
    # Check lazy loading
    is_lazy = (
        img_tag.get("loading") == "lazy" or
        "lazyload" in img_tag.get("class", []) or
        img_tag.get("data-src") is not None
    )
    
    # Check srcset for responsive images
    has_srcset = img_tag.get("srcset") is not None
    
    # Try to determine format from URL
    format_match = re.search(r'\.(\w+)(?:\?|$)', full_url.lower())
    img_format = format_match.group(1) if format_match else None
    
    # Check for modern format
    modern_formats = ["webp", "avif"]
    has_modern_format = img_format in modern_formats
    
    # Check dimensions from attributes
    width = img_tag.get("width")
    height = img_tag.get("height")
    dimensions = None
    if width and height:
        try:
            dimensions = {"width": int(width), "height": int(height)}
        except ValueError:
            pass
    
    return ImageAnalysis(
        url=full_url,
        alt_text=alt_text,
        dimensions=dimensions,
        file_size_kb=None,  # Would need to fetch the image
        format=img_format,
        is_lazy_loaded=is_lazy,
        has_modern_format=has_modern_format,
        oversized=False,  # Would need file size
        responsive_srcset=has_srcset
    )


def generate_image_recommendations(images: List[ImageAnalysis]) -> List[str]:
    """Generate optimization recommendations based on image analysis."""
    recommendations = []
    
    if not images:
        return recommendations
    
    # Count issues
    without_alt = sum(1 for img in images if not img.alt_text)
    not_lazy = sum(1 for img in images if not img.is_lazy_loaded)
    not_modern = sum(1 for img in images if not img.has_modern_format)
    not_responsive = sum(1 for img in images if not img.responsive_srcset)
    
    # Alt text recommendations
    if without_alt > 0:
        recommendations.append(
            f"{without_alt} images missing alt text - add descriptive alt text for accessibility and SEO"
        )
    
    # Lazy loading recommendations
    if not_lazy > len(images) * 0.5:  # More than 50% not lazy loaded
        recommendations.append(
            f"Consider lazy loading {not_lazy} images below the fold to improve page speed"
        )
    
    # Modern format recommendations
    if not_modern > len(images) * 0.3:  # More than 30% not modern
        recommendations.append(
            f"Convert {not_modern} images to WebP or AVIF format for better compression"
        )
    
    # Responsive images
    if not_responsive > len(images) * 0.5:
        recommendations.append(
            f"Add srcset attributes to {not_responsive} images for responsive serving"
        )
    
    # Check for missing dimensions
    without_dims = sum(1 for img in images if not img.dimensions)
    if without_dims > 0:
        recommendations.append(
            f"Add width and height attributes to {without_dims} images to prevent layout shift"
        )
    
    return recommendations


def estimate_image_optimization_impact(images: List[ImageAnalysis]) -> Dict[str, Any]:
    """Estimate the potential impact of image optimizations."""
    if not images:
        return {"potential_savings_kb": 0, "estimated_improvement": "N/A"}
    
    # Conservative estimates for potential savings
    modern_format_savings = sum(1 for img in images if not img.has_modern_format) * 50  # ~50KB per image
    lazy_load_improvement = sum(1 for img in images if not img.is_lazy_loaded) * 0.1  # ~0.1s per image
    
    return {
        "images_analyzed": len(images),
        "without_alt_text": sum(1 for img in images if not img.alt_text),
        "not_lazy_loaded": sum(1 for img in images if not img.is_lazy_loaded),
        "not_modern_format": sum(1 for img in images if not img.has_modern_format),
        "estimated_size_savings_kb": modern_format_savings,
        "estimated_load_time_improvement_sec": round(lazy_load_improvement, 1)
    }