from fastapi import FastAPI, HTTPException, BackgroundTasks, Response
from fastapi.middleware.cors import CORSMiddleware
from celery.result import AsyncResult
from typing import Optional, List

from models import (
    CrawlRequest, CrawlResult, KeywordGapRequest, KeywordGapResult,
    ShareOfVoiceRequest, ShareOfVoiceResult, CompetitorOverview, CrawlStatus,
    ContentOptimizerRequest, ContentOptimizerResult,
    BulkUrlRequest, BulkUrlResult
)
from tasks.crawler import crawl_website
from tasks.competitive import analyze_keyword_gap, calculate_share_of_voice, get_competitor_overview
from celery_app import celery_app
from tools.content_optimizer import optimize_content
from tools.bulk_url_analyzer import analyze_urls_bulk

app = FastAPI(
    title="OpenSEO API",
    description="Open source SEO analysis platform with advanced content optimization",
    version="1.1.0"
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
    return {"message": "OpenSEO API", "version": "1.1.0", "features": ["crawler", "competitive_intelligence", "content_optimizer", "bulk_analyzer"]}


@app.get("/health")
async def health():
    return {"status": "healthy"}


# ==================== CRAWLER ENDPOINTS ====================

@app.post("/api/crawl", response_model=dict)
async def start_crawl(request: CrawlRequest, background_tasks: BackgroundTasks):
    """Start a new website crawl with comprehensive analysis."""
    task = crawl_website.delay(
        str(request.url),
        request.max_pages,
        request.check_core_web_vitals
    )
    return {
        "task_id": task.id,
        "status": "pending",
        "message": "Crawl started successfully",
        "features_enabled": ["content_analysis", "security_headers", "accessibility", "internal_linking", "sitemap_analysis"]
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


# ==================== CONTENT OPTIMIZER TOOL ====================

@app.post("/api/tools/content-optimizer", response_model=dict)
async def start_content_optimizer(request: ContentOptimizerRequest):
    """
    Analyze content and generate optimization suggestions.
    
    Analyzes:
    - Readability (Flesch Reading Ease, Flesch-Kincaid Grade)
    - Keyword density and placement
    - Content quality (thin content, large paragraphs)
    - Title/meta optimization
    - Heading structure
    - Image optimization
    - Internal linking
    
    Returns actionable suggestions prioritized by impact.
    """
    task = celery_app.send_task(
        'tools.content_optimizer.optimize_content_task',
        args=[request.dict()]
    )
    return {
        "task_id": task.id,
        "status": "pending",
        "message": "Content optimization analysis started"
    }


@app.get("/api/tools/content-optimizer/{task_id}")
async def get_content_optimizer_result(task_id: str):
    """Get content optimizer results."""
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


# Direct endpoint for immediate content optimization (no Celery)
@app.post("/api/tools/content-optimizer/analyze", response_model=ContentOptimizerResult)
async def analyze_content_direct(request: ContentOptimizerRequest):
    """Analyze content immediately (for quick analysis of single pages)."""
    try:
        result = await optimize_content(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== BULK URL ANALYZER ====================

@app.post("/api/tools/bulk-url-analyzer", response_model=dict)
async def start_bulk_url_analyzer(request: BulkUrlRequest):
    """
    Analyze multiple URLs in parallel for common SEO issues.
    
    Checks:
    - HTTP status codes
    - Redirect chains
    - Title/Meta/H1 presence
    - Indexability (robots meta, X-Robots-Tag)
    - Response times
    
    Returns summary statistics and CSV export.
    """
    if len(request.urls) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 URLs per request")
    
    task = celery_app.send_task(
        'tools.bulk_url_analyzer.analyze_bulk_task',
        args=[request.dict()]
    )
    return {
        "task_id": task.id,
        "status": "pending",
        "message": f"Analyzing {len(request.urls)} URLs",
        "url_count": len(request.urls)
    }


@app.get("/api/tools/bulk-url-analyzer/{task_id}")
async def get_bulk_analyzer_result(task_id: str):
    """Get bulk URL analyzer results."""
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


@app.post("/api/tools/bulk-url-analyzer/analyze")
async def analyze_bulk_direct(request: BulkUrlRequest, response: Response):
    """Analyze URLs immediately and return CSV download."""
    if len(request.urls) > 50:  # Lower limit for direct endpoint
        raise HTTPException(status_code=400, detail="Maximum 50 URLs for direct analysis. Use /start for larger batches.")
    
    try:
        result = await analyze_urls_bulk(request)
        
        # Return CSV as downloadable file
        response.headers["Content-Disposition"] = "attachment; filename=url-analysis.csv"
        response.headers["Content-Type"] = "text/csv"
        return result.export_csv
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== DASHBOARD ENDPOINTS ====================

@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """Get overall dashboard statistics."""
    return {
        "total_crawls": 0,
        "active_tasks": 0,
        "tools_available": [
            {
                "id": "crawler",
                "name": "Site Crawler",
                "description": "Comprehensive site audit with content, security, and accessibility analysis"
            },
            {
                "id": "keyword_gap",
                "name": "Keyword Gap Analysis",
                "description": "Compare keyword rankings between domains"
            },
            {
                "id": "sov",
                "name": "Share of Voice",
                "description": "Calculate visibility scores across keyword sets"
            },
            {
                "id": "content_optimizer",
                "name": "Content Optimizer",
                "description": "Analyze content quality and get optimization suggestions"
            },
            {
                "id": "bulk_analyzer",
                "name": "Bulk URL Analyzer",
                "description": "Quickly check multiple URLs for common SEO issues"
            }
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)