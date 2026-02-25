"""
Celery task wrapper for Bulk URL Analyzer
"""
from celery_app import celery_app
from tools.bulk_url_analyzer import analyze_urls_bulk
from models import BulkUrlRequest


@celery_app.task(bind=True)
def analyze_bulk_task(self, request_dict: dict) -> dict:
    """Celery task wrapper for bulk URL analysis."""
    import asyncio
    
    request = BulkUrlRequest(**request_dict)
    result = asyncio.run(analyze_urls_bulk(request))
    
    return result.dict()