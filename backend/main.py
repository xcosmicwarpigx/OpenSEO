from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from celery.result import AsyncResult
from typing import Optional

from models import (
    CrawlRequest, CrawlResult, KeywordGapRequest, KeywordGapResult,
    ShareOfVoiceRequest, ShareOfVoiceResult, CompetitorOverview, CrawlStatus
)
from tasks.crawler import crawl_website
from tasks.competitive import analyze_keyword_gap, calculate_share_of_voice, get_competitor_overview
from celery_app import celery_app

app = FastAPI(
    title="OpenSEO API",
    description="Open source SEO analysis platform",
    version="1.0.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://frontend:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "OpenSEO API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


# ==================== CRAWLER ENDPOINTS ====================

@app.post("/api/crawl", response_model=dict)
async def start_crawl(request: CrawlRequest, background_tasks: BackgroundTasks):
    """Start a new website crawl."""
    task = crawl_website.delay(
        str(request.url),
        request.max_pages,
        request.check_core_web_vitals
    )
    return {
        "task_id": task.id,
        "status": "pending",
        "message": "Crawl started successfully"
    }


@app.get("/api/crawl/{task_id}")
async def get_crawl_status(task_id: str):
    """Get crawl task status and results."""
    task_result = AsyncResult(task_id, app=celery_app)
    
    response = {
        "task_id": task_id,
        "status": task_result.status,
        "result": None
    }
    
    if task_result.status == "SUCCESS":
        response["result"] = task_result.result
    elif task_result.status == "FAILURE":
        response["error"] = str(task_result.result)
    elif task_result.status == "PROGRESS":
        response["meta"] = task_result.info
    
    return response


@app.get("/api/crawl/{task_id}/result", response_model=CrawlResult)
async def get_crawl_result(task_id: str):
    """Get complete crawl results."""
    task_result = AsyncResult(task_id, app=celery_app)
    
    if task_result.status != "SUCCESS":
        raise HTTPException(status_code=400, detail="Crawl not completed yet")
    
    return task_result.result


# ==================== COMPETITIVE INTELLIGENCE ====================

@app.post("/api/competitive/keyword-gap", response_model=dict)
async def start_keyword_gap_analysis(request: KeywordGapRequest):
    """Start keyword gap analysis between two domains."""
    task = analyze_keyword_gap.delay(
        request.domain_a,
        request.domain_b,
        request.max_keywords
    )
    return {
        "task_id": task.id,
        "status": "pending",
        "message": "Keyword gap analysis started"
    }


@app.get("/api/competitive/keyword-gap/{task_id}")
async def get_keyword_gap_result(task_id: str):
    """Get keyword gap analysis results."""
    task_result = AsyncResult(task_id, app=celery_app)
    
    response = {
        "task_id": task_id,
        "status": task_result.status,
        "result": None
    }
    
    if task_result.status == "SUCCESS":
        response["result"] = task_result.result
    elif task_result.status == "FAILURE":
        response["error"] = str(task_result.result)
    
    return response


@app.post("/api/competitive/share-of-voice", response_model=dict)
async def start_share_of_voice(request: ShareOfVoiceRequest):
    """Calculate Share of Voice for multiple domains."""
    task = calculate_share_of_voice.delay(
        request.domains,
        request.keywords
    )
    return {
        "task_id": task.id,
        "status": "pending",
        "message": "Share of Voice calculation started"
    }


@app.get("/api/competitive/share-of-voice/{task_id}")
async def get_share_of_voice_result(task_id: str):
    """Get Share of Voice results."""
    task_result = AsyncResult(task_id, app=celery_app)
    
    response = {
        "task_id": task_id,
        "status": task_result.status,
        "result": None
    }
    
    if task_result.status == "SUCCESS":
        response["result"] = task_result.result
    elif task_result.status == "FAILURE":
        response["error"] = str(task_result.result)
    
    return response


@app.get("/api/competitive/overview/{domain}", response_model=dict)
async def get_domain_overview(domain: str):
    """Get competitive overview for a domain."""
    task = get_competitor_overview.delay(domain)
    return {
        "task_id": task.id,
        "status": "pending",
        "message": "Competitor overview started"
    }


@app.get("/api/competitive/overview/result/{task_id}")
async def get_overview_result(task_id: str):
    """Get competitor overview results."""
    task_result = AsyncResult(task_id, app=celery_app)
    
    response = {
        "task_id": task_id,
        "status": task_result.status,
        "result": None
    }
    
    if task_result.status == "SUCCESS":
        response["result"] = task_result.result
    elif task_result.status == "FAILURE":
        response["error"] = str(task_result.result)
    
    return response


# ==================== DASHBOARD ENDPOINTS ====================

@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """Get overall dashboard statistics."""
    # This would aggregate data from various sources
    return {
        "total_crawls": 0,
        "active_tasks": 0,
        "avg_core_web_vitals": None,
        "last_updated": None
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
