# OpenSEO

An open-source SEO analysis platform built with FastAPI, React, and Playwright.

## Features

### 1. Technical Crawler (Site Auditor)
- **Recursive crawling** using Playwright for JavaScript-rendered pages
- **HTTP status code monitoring** - flags 404s, 500s, redirects
- **Metadata validation** - missing H1s, duplicate meta descriptions, missing alt text
- **Core Web Vitals** integration with Google PageSpeed Insights API
- **Performance metrics** - page load times, page sizes

### 2. Competitive Intelligence
- **Keyword Gap Analysis** - symmetric difference between two domains' keyword rankings
- **Share of Voice (SoV)** - weighted visibility score calculation:
  ```
  SoV = Σ(Estimated CTR × Search Volume) / Total Market Volume
  ```
- **Competitor Overview** - authority scores, backlink counts, traffic estimates

## Architecture

```
OpenSEO/
├── backend/          # FastAPI + Celery + Redis
│   ├── main.py       # API routes
│   ├── tasks/        # Celery tasks
│   │   ├── crawler.py     # Site crawling logic
│   │   └── competitive.py # Competitive analysis
│   └── models.py     # Pydantic models
├── frontend/         # React + Vite + Tailwind + Recharts
│   ├── src/
│   │   ├── pages/    # Dashboard, Crawler, Competitive
│   │   └── components/ # Layout, Sidebar
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
cd OpenSEO

# Create .env file (optional - for PageSpeed API)
echo "GOOGLE_PAGESPEED_API_KEY=your_api_key" > .env

# Start all services
docker-compose up --build

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

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/crawl` | POST | Start website crawl |
| `/api/crawl/{task_id}` | GET | Get crawl status/result |
| `/api/competitive/keyword-gap` | POST | Start keyword gap analysis |
| `/api/competitive/share-of-voice` | POST | Calculate Share of Voice |
| `/api/competitive/overview/{domain}` | GET | Get domain overview |

## Keyword Data Sources

The competitive intelligence features currently use **simulated data** for demonstration purposes. To use real data, integrate with:

- **SEMrush API** - Most comprehensive ($200+/month)
- **Ahrefs API** - Great backlink data
- **Serpstat API** - Budget-friendly option
- **DataForSEO** - Pay-as-you-go model

Update `backend/tasks/competitive.py` to call your preferred API instead of `fetch_keyword_data()`.

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_PAGESPEED_API_KEY` | For Core Web Vitals API | (empty) |
| `REDIS_URL` | Redis connection | `redis://localhost:6379` |
| `CELERY_BROKER_URL` | Celery broker | `redis://localhost:6379/0` |
| `CELERY_RESULT_BACKEND` | Celery results | `redis://localhost:6379/0` |

## License

MIT License - feel free to use for personal or commercial projects.
