"""
Celery task wrapper for Content Optimizer
"""
from celery_app import celery_app
from tools.content_optimizer import optimize_content, compare_with_competitors
from models import ContentOptimizerRequest


@celery_app.task(bind=True)
def optimize_content_task(self, request_dict: dict) -> dict:
    """Celery task wrapper for content optimization."""
    import asyncio
    
    request = ContentOptimizerRequest(**request_dict)
    result = asyncio.run(optimize_content(request))
    
    return result.dict()


@celery_app.task(bind=True)
def compare_competitors_task(self, your_url: str, competitor_urls: list) -> dict:
    """Celery task wrapper for competitor comparison."""
    import asyncio
    
    result = asyncio.run(compare_with_competitors(your_url, competitor_urls))
    return result