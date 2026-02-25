# OpenSEO

An open-source SEO analysis platform built with FastAPI, React, Playwright, and Celery.

## Features

### 1. Technical Crawler (Site Auditor)
Comprehensive site crawling with Playwright for JavaScript-rendered pages:

**SEO Analysis:**
- HTTP status code monitoring (404s, 500s, redirects)
- Metadata validation (missing/duplicate H1s, meta descriptions)
- Title optimization (length checks)
- Image analysis (alt text, lazy loading, modern formats)
- Internal/external link extraction
- Canonical URL detection
- Redirect chain detection

**Content Analysis:**
- **Readability scoring** (Flesch Reading Ease, Flesch-Kincaid Grade)
- Word count and reading time estimation
- Content quality checks (thin content detection)
- Heading structure validation
- Large paragraph detection

**Technical Analysis:**
- **Structured data validation** (JSON-LD schema detection)
- **Security headers analysis** (CSP, HSTS, X-Frame-Options, etc.)
- **Accessibility checks** (WCAG 2.1 compliance)
  - Alt text validation
  - Form labels
  - Link text quality
  - Heading hierarchy
  - Language specification
- **Core Web Vitals** integration (Google PageSpeed Insights API)
- **Internal linking analysis** (orphan pages, click depth, link distribution)
- **Sitemap & robots.txt validation**

### 2. Competitive Intelligence
- **Keyword Gap Analysis** - symmetric difference between two domains
- **Share of Voice (SoV)** - weighted visibility calculation
- **Competitor Overview** - authority scores, traffic estimates, backlink data

### 3. Content Optimizer Tool
Detailed single-page content analysis:

- **Readability Analysis:**
  - Flesch Reading Ease score
  - Flesch-Kincaid Grade Level
  - Word count, sentence count
  - Average words per sentence
  - Reading time estimation

- **Keyword Optimization:**
  - Keyword density calculation
  - Placement checking (title, H1, meta, first 100 words)
  - Keyword stuffing detection
  - Top keyword extraction

- **Content Quality Checks:**
  - Thin content detection (< 300 words)
  - Missing subheadings
  - Large paragraphs (> 150 words)
  - Keyword stuffing alerts

- **Prioritized Suggestions:**
  - Title optimization
  - Meta description improvements
  - Heading structure fixes
  - Content readability improvements
  - Image alt text
  - Internal linking opportunities

### 4. Bulk URL Analyzer
Quickly analyze up to 100 URLs in parallel:

- HTTP status codes
- Redirect detection
- Title/Meta/H1 presence
- Indexability checks (robots meta, X-Robots-Tag)
- Response time tracking
- CSV export for further analysis

## Architecture

```
OpenSEO/
├── backend/                 # FastAPI + Celery + Redis
│   ├── main.py             # API routes
│   ├── tasks/              # Celery background tasks
│   │   ├── crawler.py      # Site crawling with comprehensive analysis
│   │   └── competitive.py  # Competitive intelligence
│   ├── tools/              # Standalone analysis tools
│   │   ├── content_optimizer.py    # Content optimization engine
│   │   └── bulk_url_analyzer.py    # Bulk URL analysis
│   ├── utils/              # Analysis utilities
│   │   ├── content_analyzer.py     # Readability & keyword analysis
│   │   ├── schema_analyzer.py      # Structured data validation
│   │   ├── security_analyzer.py    # Security headers
│   │   ├── image_analyzer.py       # Image optimization
│   │   ├── accessibility_analyzer.py # WCAG compliance
│   │   ├── internal_linking_analyzer.py # Link structure
│   │   └── sitemap_analyzer.py     # Sitemap/robots.txt
│   └── models.py           # Pydantic data models
├── frontend/               # React + Vite + Tailwind + Recharts
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Crawler.tsx
│   │   │   ├── Competitive.tsx
│   │   │   ├── ContentOptimizer.tsx
│   │   │   └── BulkAnalyzer.tsx
│   │   └── components/
│   │       ├── Layout.tsx
│   │       └── Sidebar.tsx
│   └── package.json
└── docker-compose.yml
```

## Quick Start

### Prerequisites
- Docker & Docker Compose
- (Optional) Google PageSpeed Insights API key for Core Web Vitals

### Run with Docker

```bash
# Clone and navigate
git clone https://github.com/xcosmicwarpigx/OpenSEO.git
cd OpenSEO

# Create .env file (optional - for PageSpeed API)
echo "GOOGLE_PAGESPEED_API_KEY=your_api_key" > .env

# Start all services
docker-compose up --build -d

# Or use Makefile
make up-build

# Access:
# - Frontend: http://localhost:5173
# - API Docs: http://localhost:8000/docs
# - Backend: http://localhost:8000
```

### Development (without Docker)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
uvicorn main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

### Crawler
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/crawl` | POST | Start comprehensive site crawl |
| `/api/crawl/{task_id}` | GET | Get crawl status |
| `/api/crawl/{task_id}/result` | GET | Get full crawl results |

### Competitive Intelligence
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/competitive/keyword-gap` | POST | Start keyword gap analysis |
| `/api/competitive/share-of-voice` | POST | Calculate Share of Voice |
| `/api/competitive/overview/{domain}` | GET | Get domain overview |

### Content Optimizer
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/tools/content-optimizer/analyze` | POST | Analyze single page immediately |
| `/api/tools/content-optimizer` | POST | Start async content analysis |
| `/api/tools/content-optimizer/{task_id}` | GET | Get results |

### Bulk URL Analyzer
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/tools/bulk-url-analyzer/analyze` | POST | Analyze up to 50 URLs (direct) |
| `/api/tools/bulk-url-analyzer` | POST | Start async bulk analysis (up to 100) |
| `/api/tools/bulk-url-analyzer/{task_id}` | GET | Get results |

## Content Optimizer - Analysis Details

### Readability Scores

**Flesch Reading Ease:**
- 90-100: Very Easy (5th grade)
- 80-89: Easy (6th grade)
- 70-79: Fairly Easy (7th grade)
- 60-69: Standard (8th-9th grade)
- 50-59: Fairly Difficult (10th-12th grade)
- 30-49: Difficult (College)
- 0-29: Very Difficult (College Graduate)

**Flesch-Kincaid Grade Level:**
- Estimates the US school grade level needed to understand the text
- Aim for 8-12 for general web content

### Content Score Factors

The content optimizer calculates a score (0-100) based on:

- **Content Length** (+15 points for 1000+ words)
- **Title Optimization** (+10 points for 30-60 chars)
- **Meta Description** (+5 points for 120-160 chars)
- **H1 Present** (+10 points)
- **Readability** (+10 points for score 60+)
- **Images with Alt Text** (+5 points)
- **Internal Linking** (+5 points for 3+ links)
- **Keyword Optimization** (variable)

**Penalties:**
- Thin content (-15)
- Keyword stuffing (-10)
- Missing subheadings (-5)

## Accessibility Checks

The crawler checks for WCAG 2.1 compliance:

- **1.1.1** - Non-text content (alt text)
- **1.3.1** - Info and relationships (labels, headings)
- **2.4.1** - Bypass blocks (skip links)
- **2.4.2** - Page titled
- **2.4.4** - Link purpose (descriptive text)
- **3.1.1** - Language of page

## Keyword Data Sources

Competitive intelligence features use **simulated data** for demonstration. To use real data, integrate with:

- **SEMrush API** - Most comprehensive ($200+/month)
- **Ahrefs API** - Great backlink data
- **Serpstat API** - Budget-friendly option
- **DataForSEO** - Pay-as-you-go model

Update `backend/tasks/competitive.py` to call your preferred API.

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_PAGESPEED_API_KEY` | PageSpeed Insights API key | (empty) |
| `REDIS_URL` | Redis connection | `redis://localhost:6379` |
| `CELERY_BROKER_URL` | Celery broker | `redis://localhost:6379/0` |
| `CELERY_RESULT_BACKEND` | Celery results | `redis://localhost:6379/0` |

## Makefile Commands

```bash
make up          # Start all services
make up-build    # Build and start
make down        # Stop services
make logs        # View logs
make dev-backend # Run backend locally
make dev-frontend # Run frontend locally
make clean       # Clean up Docker
```

## License

MIT License - feel free to use for personal or commercial projects.

## Contributing

Contributions welcome! Areas for improvement:

- Real keyword data API integrations
- Additional schema types
- More accessibility checks
- Performance budget tracking
- Export to PDF/Excel
- Scheduled audits
