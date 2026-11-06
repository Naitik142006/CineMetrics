# 14 — Automated Data Ingestion System

> **Document Status**: Planning / Design
> **Last Updated**: 2025-01-01
> **Related Docs**: [13_UPCOMING_MOVIE_DISCOVERY.md](./13_UPCOMING_MOVIE_DISCOVERY.md) | [17_SYSTEM_ARCHITECTURE.md](./17_SYSTEM_ARCHITECTURE.md) | [18_DATABASE_AND_ER_DIAGRAM.md](./18_DATABASE_AND_ER_DIAGRAM.md)

---

## Overview

The Automated Data Ingestion System is the backbone of CineMetrics' data pipeline. It manages the continuous collection, updating, and quality-checking of all external data: movie metadata, financial figures, trailer statistics, social sentiment, and popularity signals. This document defines the ingestion architecture, all job types, scheduling, rate limit management, database schemas for job management, data freshness policies, change tracking, and admin interface requirements.

The system is designed to be **simple, transparent, and self-healing** — appropriate for a student-scale project that one developer can understand, debug, and maintain without enterprise tooling like Kubernetes, Celery, or Redis.

---

## 1. Ingestion Architecture Overview

### 1.1 Architecture Philosophy

The ingestion system follows a **database-driven job queue** pattern rather than a message broker pattern. This means:

- **No Celery, No Redis, No RabbitMQ**: These are powerful tools but add significant operational complexity. For a project ingesting data for a few hundred movies, a PostgreSQL table as a job queue is more than sufficient.
- **No separate worker processes (initially)**: Jobs run within the same Python process as the FastAPI application, using APScheduler's background thread pool. When the job queue grows and blocks the API, jobs can be extracted to a standalone `scheduler.py` script run as a separate process.
- **Transparency**: Every job, attempt, success, and failure is recorded in the database. The admin can query the state of any job at any time.
- **Simplicity over throughput**: CineMetrics processes hundreds of movies, not millions. Throughput is not a concern — correctness and reliability are.

### 1.2 Scheduler: APScheduler

**Library**: `APScheduler 3.x` (Python)
**Scheduler type**: `BackgroundScheduler` (runs in a background thread, non-blocking)
**Job store**: SQLAlchemy (persists job schedules to PostgreSQL — survives restarts)
**Executor**: `ThreadPoolExecutor` with `max_workers=4` (prevents API starvation)

```python
# backend/jobs/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor

jobstores = {
    'default': SQLAlchemyJobStore(url=settings.DATABASE_URL)
}
executors = {
    'default': ThreadPoolExecutor(max_workers=4)
}
job_defaults = {
    'coalesce': True,     # If multiple runs are due (e.g., after outage), run once
    'max_instances': 1,   # Prevent concurrent runs of the same job
    'misfire_grace_time': 3600  # If a job misses its time by < 1 hour, still run it
}

scheduler = BackgroundScheduler(
    jobstores=jobstores,
    executors=executors,
    job_defaults=job_defaults,
    timezone='Asia/Kolkata'  # IST
)
```

APScheduler is started when FastAPI starts and shut down on application shutdown:

```python
# backend/app/main.py
@app.on_event("startup")
async def startup_event():
    scheduler.start()
    register_all_jobs(scheduler)
    logger.info("APScheduler started with all jobs registered")

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown(wait=False)
```

### 1.3 Job Queue Table (Database-Backed)

The `ingestion_jobs` table serves as both a job queue and an audit log. Jobs are inserted by discovery/scheduler code and consumed by worker functions.

```
State Transitions:
  pending → running → completed
                   → failed → pending (retry)
                            → dead (max retries exceeded)
```

### 1.4 Error Handling Strategy

**Exponential Backoff**: Failed jobs are retried with increasing delays.

```python
RETRY_DELAYS = [
    timedelta(minutes=15),   # 1st retry: 15 minutes after failure
    timedelta(minutes=30),   # 2nd retry: 30 minutes after failure
    timedelta(hours=2),      # 3rd retry: 2 hours after failure
    # After 3 failures: status = "dead"
]

MAX_RETRIES = 3

def handle_job_failure(job: IngestionJob, error: Exception):
    job.attempts += 1
    job.last_error = str(error)[:2000]  # Truncate to fit column
    
    if job.attempts >= MAX_RETRIES:
        job.status = "dead"
        log.error(f"Job {job.job_id} ({job.job_type}) moved to dead letter after "
                  f"{job.attempts} attempts. Last error: {job.last_error}")
    else:
        delay = RETRY_DELAYS[job.attempts - 1]
        job.status = "pending"
        job.scheduled_at = now() + delay
        log.warning(f"Job {job.job_id} failed (attempt {job.attempts}), "
                    f"retrying at {job.scheduled_at}")
    
    db.commit()
```

**Dead Letter Queue**: Jobs with `status = "dead"` are the "dead letter queue" — they appear in the admin interface as failed items requiring manual review. An admin can:
- View the last error message
- Manually retry the job (resets attempts to 0, status to pending)
- Mark as permanently ignored

### 1.5 Monitoring

All job activity is logged to the `ingestion_logs` table. Key metrics that can be queried:

```sql
-- Daily ingestion health check
SELECT 
    job_type,
    COUNT(*) FILTER (WHERE status = 'completed') as completed,
    COUNT(*) FILTER (WHERE status = 'failed') as failed,
    COUNT(*) FILTER (WHERE status = 'dead') as dead,
    AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) as avg_duration_seconds
FROM ingestion_jobs
WHERE scheduled_at >= NOW() - INTERVAL '24 hours'
GROUP BY job_type
ORDER BY job_type;
```

---

## 2. Job Types and Schedules

### 2.1 Complete Job Registry

| Job Name | Schedule (IST) | Priority | Description | Est. Duration | Dependencies |
|----------|---------------|----------|-------------|---------------|--------------|
| `discover_upcoming_movies` | Daily 2:00am | High | Full TMDB upcoming scan across regions and languages | 15–25 min | TMDB API |
| `enrich_new_movies` | Triggered | High | Full metadata fetch for newly discovered movies | 2–8 min/movie | TMDB API, IMDb local |
| `update_popularity_snapshots` | Daily 6:00am | Medium | TMDB popularity scores + Google Trends for all tracked movies | 30–60 min | TMDB API, Trends |
| `update_trailer_stats` | Every 72 hours | Medium | YouTube trailer view counts for upcoming movies | 10–30 min | YouTube Data API |
| `update_sentiment` | Weekly (Sunday 1am) | Low | Reddit, social media sentiment for upcoming movies | 30–60 min | Reddit API, Pushshift |
| `post_release_collection` | Daily 6:30am | High | Box office financial data for recently released movies | 10–20 min | Box Office APIs |
| `model_performance_check` | 1st of month | Low | Evaluate last month's predictions vs actual box office | 5–15 min | Internal DB |
| `update_movie_statuses` | Daily 3:00am | High | Advance movie lifecycle status based on release dates | 1–2 min | Internal DB |
| `batch_predictions` | Daily 4:00am | Medium | Recompute predictions for all upcoming movies | 15–30 min | ML models, DB |
| `cleanup_stale_jobs` | Daily 5:00am | Low | Archive completed jobs older than 30 days | 1–2 min | Internal DB |

### 2.2 Job Detailed Specifications

#### `discover_upcoming_movies`

**Purpose**: Find all upcoming movies from TMDB across global and Indian markets.
**Full specification**: See [13_UPCOMING_MOVIE_DISCOVERY.md](./13_UPCOMING_MOVIE_DISCOVERY.md)
**APScheduler registration**:
```python
scheduler.add_job(
    func=jobs.discover_upcoming_movies,
    trigger='cron',
    hour=2, minute=0,
    id='discover_upcoming_movies',
    name='Discover Upcoming Movies',
    replace_existing=True
)
```

#### `enrich_new_movies`

**Purpose**: Fetch full metadata for newly discovered movies (steps 1–10 from Section 4 of [13_UPCOMING_MOVIE_DISCOVERY.md](./13_UPCOMING_MOVIE_DISCOVERY.md)).
**Triggering**: Triggered immediately after `discover_upcoming_movies` creates new movie records. Each new movie becomes a separate `enrich_new_movies` job in the `ingestion_jobs` table with `target_id = movie_id`.
**Processing**: The scheduler runs a polling function every 5 minutes to check for pending enrichment jobs and processes up to 10 at a time (configurable via `ENRICHMENT_BATCH_SIZE`).

```python
# Poll for pending enrichment jobs
scheduler.add_job(
    func=jobs.process_pending_enrichments,
    trigger='interval',
    minutes=5,
    id='process_pending_enrichments'
)

def process_pending_enrichments():
    pending = db.query(IngestionJob).filter(
        IngestionJob.job_type == "enrich_new_movies",
        IngestionJob.status == "pending",
        IngestionJob.scheduled_at <= now()
    ).order_by(IngestionJob.priority.desc(), IngestionJob.scheduled_at.asc()
    ).limit(settings.ENRICHMENT_BATCH_SIZE).all()
    
    for job in pending:
        movie_id = job.target_id
        enrich_single_movie(movie_id, job)
```

#### `update_popularity_snapshots`

**Purpose**: Track popularity trends over time for all upcoming movies. Popularity changes are a key leading indicator for prediction.

**Data collected per movie**:
1. TMDB `popularity` score (0–1000+)
2. TMDB `vote_average` and `vote_count`
3. Google Trends relative interest score (0–100) for the movie title

**Storage**: Each data point is stored as a row in `popularity_snapshots` with `source`, `snapshot_date`, and `popularity_score`.

**Scope**: Only movies with `status IN ('announced', 'production', 'post_production', 'imminent')`. Historical movies are skipped.

```python
def update_popularity_snapshots():
    upcoming = db.query(Movie).filter(
        Movie.status.in_(["announced", "production", "post_production", "imminent"])
    ).all()
    
    for movie in upcoming:
        # TMDB popularity
        tmdb_data = tmdb_client.get(f"/movie/{movie.tmdb_id}")
        db.add(PopularitySnapshot(
            movie_id=movie.movie_id,
            source="tmdb",
            popularity_score=tmdb_data["popularity"],
            supplemental_data={
                "vote_average": tmdb_data["vote_average"],
                "vote_count": tmdb_data["vote_count"]
            },
            snapshot_date=date.today()
        ))
        rate_limiter.wait()
        
        # Google Trends (once per day, with caching)
        if not has_trends_snapshot_today(movie.movie_id):
            trends_score = google_trends_client.get_interest(
                keyword=movie.title,
                timeframe="today 3-m",
                geo="IN" if movie.market_segment in INDIAN_MARKETS else ""
            )
            db.add(PopularitySnapshot(
                movie_id=movie.movie_id,
                source="google_trends",
                popularity_score=trends_score,
                snapshot_date=date.today()
            ))
            time.sleep(2)  # Google Trends rate limiting
    
    db.commit()
```

#### `update_trailer_stats`

**Purpose**: Track YouTube trailer view counts over time. Trailer views are a strong pre-release demand signal.

**YouTube API usage**: The YouTube Data API v3 provides video statistics (view count, like count, comment count) via the `videos.list` endpoint. Each call uses 1 API quota unit and can fetch up to 50 videos per request.

**Strategy**:
- Batch movie trailers into groups of 50 to minimize API quota usage
- Only fetch stats for movies releasing within the next 90 days
- One snapshot per movie per 3 days

```python
def update_trailer_stats():
    # Get all trailers for upcoming movies (releasing within 90 days)
    trailers = db.query(MovieTrailer).join(Movie).filter(
        Movie.release_date.between(date.today(), date.today() + timedelta(days=90)),
        Movie.status.in_(["post_production", "imminent"]),
        MovieTrailer.is_primary == True
    ).all()
    
    # Batch into groups of 50
    for batch in chunked(trailers, 50):
        video_ids = [t.youtube_id for t in batch]
        response = youtube_client.videos().list(
            part="statistics",
            id=",".join(video_ids)
        ).execute()
        
        for item in response.get("items", []):
            trailer = find_trailer_by_youtube_id(batch, item["id"])
            stats = item["statistics"]
            trailer.view_count_at_snapshot = int(stats.get("viewCount", 0))
            trailer.like_count_at_snapshot = int(stats.get("likeCount", 0))
            trailer.last_stats_updated = now()
        
        youtube_quota_tracker.increment(len(batch) * 1)  # 1 unit per video
    
    db.commit()
```

**YouTube quota management**: 10,000 units/day free. At 1 unit per video, this allows up to 10,000 video stat fetches per day. CineMetrics will rarely track more than 100–200 trailers concurrently, so quota is not a concern in normal operation. If quota approaches limit, fetch stats for only imminent (releasing within 30 days) movies first.

#### `update_sentiment`

**Purpose**: Collect social media sentiment about upcoming movies as a demand signal.

**Sources**:
- **Reddit**: Subreddits `/r/bollywood`, `/r/tollywood`, `/r/kollywood`, `/r/MalayalamMovies`, `/r/movies`, `/r/india`
- **Search**: Reddit search API for movie title within relevant subreddits
- **Data collected**: Post count, comment count, average upvote ratio, sentiment classification (positive/negative/neutral using a pre-trained model)

**Sentiment model**: HuggingFace `cardiffnlp/twitter-roberta-base-sentiment-latest` (runs locally, no API cost). For student project, can also use VADER as a simpler alternative.

```python
from transformers import pipeline

sentiment_pipeline = pipeline(
    "sentiment-analysis",
    model="cardiffnlp/twitter-roberta-base-sentiment-latest",
    device=-1  # CPU; use 0 for GPU if available
)

def analyze_reddit_sentiment(movie: Movie) -> SentimentObservation:
    posts = reddit_client.search(
        query=movie.title,
        subreddits=RELEVANT_SUBREDDITS[movie.market_segment],
        time_filter="week",
        limit=100
    )
    
    texts = [f"{p.title} {p.selftext[:200]}" for p in posts]
    if not texts:
        return None
    
    results = sentiment_pipeline(texts, truncation=True, max_length=512)
    
    positive_count = sum(1 for r in results if r["label"] == "positive")
    negative_count = sum(1 for r in results if r["label"] == "negative")
    neutral_count = len(results) - positive_count - negative_count
    
    return SentimentObservation(
        movie_id=movie.movie_id,
        source="reddit",
        observation_date=date.today(),
        post_count=len(posts),
        positive_ratio=positive_count / len(results),
        negative_ratio=negative_count / len(results),
        neutral_ratio=neutral_count / len(results),
        composite_sentiment_score=(positive_count - negative_count) / len(results),
        raw_data={"subreddits_queried": RELEVANT_SUBREDDITS[movie.market_segment]}
    )
```

#### `post_release_collection`

**Purpose**: Collect actual box office financial data for movies that have been released. This data is used to evaluate prediction accuracy and train future models.

**Sources** (in preference order):
1. **Sacnilk** (Indian box office): India net collections by day, week; nett vs gross distinction. **[REQUIRES VERIFICATION: scraping terms of service]**
2. **Box Office Mojo**: Worldwide and domestic gross for Hollywood and wide-release films. **[REQUIRES VERIFICATION]**
3. **TMDB `/movie/{id}`**: `revenue` field — often incorrect/outdated but useful as fallback
4. **Manual entry**: Admin can enter verified figures from credible sources

**Collection timeline**:
- Day 1–7 after release: Run daily (opening week is most volatile and important)
- Day 8–30: Every 3 days
- Day 31–90: Weekly
- Day 90+: Monthly until figures stabilize

```python
def post_release_collection():
    recently_released = db.query(Movie).filter(
        Movie.status == "released",
        Movie.release_date >= date.today() - timedelta(days=90)
    ).all()
    
    for movie in recently_released:
        days_since_release = (date.today() - movie.release_date).days
        
        # Determine if we should collect today based on days_since_release
        if not should_collect_today(days_since_release):
            continue
        
        # Attempt collection from each source
        collection_success = False
        for source in ["sacnilk", "bom", "tmdb"]:
            try:
                financial_data = financial_collectors[source].fetch(movie)
                if financial_data:
                    update_movie_financials(movie, financial_data, source)
                    collection_success = True
                    break  # Use first successful source
            except CollectionError as e:
                log_collection_failure(movie, source, e)
        
        if not collection_success:
            log.warning(f"All sources failed for {movie.title} financial collection")
```

#### `model_performance_check`

**Purpose**: Monthly evaluation of prediction quality. Compares predictions made before release against actual box office results.

**Metrics computed**:
- Mean Absolute Percentage Error (MAPE) across all predictions
- MAPE segmented by: industry, budget tier, prediction stage (pre-production vs imminent)
- Hit rate: % of movies where predicted tier (flop/average/hit/blockbuster) matched actual tier
- Calibration: whether confidence intervals captured actual values at stated frequency

Results stored in `model_evaluations` table. Alert is logged if MAPE exceeds 35% (threshold indicates model drift).

---

## 3. Rate Limit Management

### 3.1 TMDB Rate Limiting

TMDB free tier allows 40 requests per 10 seconds (4 req/sec sustained). Exceeding this returns HTTP 429.

**Token Bucket Implementation**:

```python
import time
import threading

class TokenBucketRateLimiter:
    """
    Token bucket rate limiter for TMDB API.
    Allows up to `rate` requests per `per` seconds.
    """
    def __init__(self, rate: int = 38, per: float = 10.0):
        # Use 38 instead of 40 to have safety margin
        self.rate = rate
        self.per = per
        self.tokens = rate
        self.last_refill = time.monotonic()
        self._lock = threading.Lock()
    
    def wait(self):
        with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            
            # Refill tokens based on elapsed time
            self.tokens = min(
                self.rate,
                self.tokens + elapsed * (self.rate / self.per)
            )
            self.last_refill = now
            
            if self.tokens >= 1:
                self.tokens -= 1
                return  # Token available, proceed immediately
            else:
                # Wait for a token to become available
                wait_time = (1 - self.tokens) * (self.per / self.rate)
                time.sleep(wait_time)
                self.tokens = 0
                self.last_refill = time.monotonic()

tmdb_rate_limiter = TokenBucketRateLimiter(rate=38, per=10.0)
```

**HTTP client wrapper**:
```python
class TMDBClient:
    BASE_URL = "https://api.themoviedb.org/3"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = httpx.Client(timeout=30.0)
        self.rate_limiter = TokenBucketRateLimiter(rate=38, per=10.0)
    
    def get(self, endpoint: str, params: dict = None) -> dict:
        self.rate_limiter.wait()
        url = f"{self.BASE_URL}{endpoint}"
        response = self.session.get(url, params={
            "api_key": self.api_key,
            **(params or {})
        })
        response.raise_for_status()  # Raises on 4xx/5xx
        return response.json()
```

### 3.2 YouTube Data API v3 Rate Limiting

**Quota**: 10,000 units/day (resets midnight Pacific Time)
**Cost per operation**:
- `videos.list` (statistics part): 1 unit per request (up to 50 videos per request)
- `search.list`: 100 units per request (expensive — avoid if possible)

**Quota tracking**:
```sql
CREATE TABLE youtube_quota_usage (
    usage_date DATE PRIMARY KEY,
    units_used INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT NOW()
);
```

```python
class YouTubeQuotaTracker:
    DAILY_LIMIT = 10000
    SAFETY_THRESHOLD = 9500  # Stop at 95% to avoid edge cases
    
    def increment(self, units: int):
        db.execute("""
            INSERT INTO youtube_quota_usage (usage_date, units_used)
            VALUES (CURRENT_DATE, :units)
            ON CONFLICT (usage_date)
            DO UPDATE SET units_used = youtube_quota_usage.units_used + :units,
                          last_updated = NOW()
        """, {"units": units})
        db.commit()
    
    def can_use(self, units: int) -> bool:
        today_usage = db.scalar(
            "SELECT units_used FROM youtube_quota_usage WHERE usage_date = CURRENT_DATE"
        ) or 0
        return (today_usage + units) <= self.SAFETY_THRESHOLD
    
    def get_remaining(self) -> int:
        today_usage = db.scalar(
            "SELECT units_used FROM youtube_quota_usage WHERE usage_date = CURRENT_DATE"
        ) or 0
        return max(0, self.SAFETY_THRESHOLD - today_usage)
```

**Priority queue for YouTube quota**:
When quota is running low, only fetch stats for high-priority movies:
1. Movies releasing in next 7 days (highest priority)
2. Movies releasing in next 30 days
3. Movies releasing in next 90 days
4. All other upcoming movies (skip if quota low)

### 3.3 Google Trends Rate Limiting

Google Trends has no official API and no documented rate limits. The unofficial `pytrends` library is commonly used but can be blocked.

**Strategy**:
- Maximum 1 Trends request per movie per day
- Minimum 2 seconds between any two Trends requests
- If HTTP 429 received: back off for 15 minutes, then retry
- Results cached in `popularity_snapshots` — never re-fetch on same day
- If blocked for > 24 hours: log warning but do not fail other jobs

```python
class GoogleTrendsClient:
    def __init__(self):
        self.pytrends = TrendReq(hl='en-US', tz=330)  # IST offset
        self._last_request = 0
        self._min_interval = 2.0  # seconds
    
    def get_interest(self, keyword: str, timeframe: str, geo: str) -> Optional[int]:
        # Rate limiting
        elapsed = time.time() - self._last_request
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        
        try:
            self.pytrends.build_payload([keyword], timeframe=timeframe, geo=geo)
            data = self.pytrends.interest_over_time()
            self._last_request = time.time()
            
            if data.empty:
                return None
            
            # Return most recent week's interest score (0–100)
            return int(data[keyword].iloc[-1])
        
        except ResponseError as e:
            if e.response.status_code == 429:
                log.warning(f"Google Trends rate limited. Backing off 15 minutes.")
                time.sleep(900)
                return None
            raise
```

### 3.4 Reddit API Rate Limiting

Reddit API (OAuth): 100 requests per minute per OAuth client.

```python
import praw

reddit = praw.Reddit(
    client_id=settings.REDDIT_CLIENT_ID,
    client_secret=settings.REDDIT_CLIENT_SECRET,
    user_agent="CineMetrics/1.0 by u/cinemetrics_bot"
)
# PRAW handles rate limiting automatically with built-in backoff
```

---

## 4. Ingestion Job Database Schema

### 4.1 `ingestion_jobs` Table (Complete DDL)

```sql
CREATE TABLE ingestion_jobs (
    -- Identity
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_type VARCHAR(100) NOT NULL,
    -- e.g., discover_upcoming_movies, enrich_new_movies, update_trailer_stats
    
    -- Targeting
    target_id VARCHAR(100) NULL,
    -- movie_id (UUID as string) for movie-specific jobs; NULL for global jobs
    target_type VARCHAR(50) NULL,
    -- 'movie', 'person', 'global', etc.
    
    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    -- pending | running | completed | failed | dead | cancelled
    
    -- Priority (lower number = higher priority, processed first)
    priority INTEGER NOT NULL DEFAULT 50,
    -- 10=Critical, 20=High, 50=Medium, 80=Low
    
    -- Timing
    scheduled_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE NULL,
    completed_at TIMESTAMP WITH TIME ZONE NULL,
    
    -- Retry tracking
    attempts INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 3,
    last_error TEXT NULL,  -- Last failure error message (truncated to 2000 chars)
    next_retry_at TIMESTAMP WITH TIME ZONE NULL,
    
    -- Result
    result_summary JSONB NULL,
    -- Flexible result storage: {"movies_found": 23, "movies_inserted": 5, "movies_updated": 2}
    
    -- Deduplication
    idempotency_key VARCHAR(255) UNIQUE NULL,
    -- Prevents duplicate jobs: e.g., "enrich:movie_id:date" ensures one enrichment per day
    
    -- Audit
    created_by VARCHAR(100) NOT NULL DEFAULT 'scheduler',
    -- 'scheduler', 'admin:username', 'api:request_id'
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes for job queue processing
CREATE INDEX idx_ingestion_jobs_status_scheduled 
    ON ingestion_jobs(status, scheduled_at) 
    WHERE status IN ('pending', 'failed');
-- Used by job processor to find work: WHERE status='pending' AND scheduled_at <= NOW()

CREATE INDEX idx_ingestion_jobs_job_type_status 
    ON ingestion_jobs(job_type, status);
-- Used by admin to view status of a specific job type

CREATE INDEX idx_ingestion_jobs_target_id 
    ON ingestion_jobs(target_id) 
    WHERE target_id IS NOT NULL;
-- Used to find all jobs for a specific movie

CREATE INDEX idx_ingestion_jobs_created_at 
    ON ingestion_jobs(created_at);
-- Used by cleanup job to archive old records
```

### 4.2 `ingestion_logs` Table (Complete DDL)

```sql
CREATE TABLE ingestion_logs (
    -- Identity
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES ingestion_jobs(job_id) ON DELETE CASCADE NULL,
    -- NULL for system-level log entries not tied to a specific job
    
    -- Classification
    log_level VARCHAR(10) NOT NULL,
    -- DEBUG | INFO | WARNING | ERROR | CRITICAL
    log_category VARCHAR(50) NULL,
    -- rate_limit | api_error | data_quality | db_write | enrichment | prediction
    
    -- Content
    message TEXT NOT NULL,
    extra_data JSONB NULL,
    -- Structured extra context: {"movie_id": "...", "tmdb_id": 12345, "api_response_code": 429}
    
    -- Source
    logger_name VARCHAR(200) NULL,  -- Python logger name, e.g., "jobs.enrichment"
    
    -- Timing
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_ingestion_logs_job_id ON ingestion_logs(job_id);
CREATE INDEX idx_ingestion_logs_log_level ON ingestion_logs(log_level, created_at DESC);
CREATE INDEX idx_ingestion_logs_created_at ON ingestion_logs(created_at DESC);
-- Note: Logs older than 90 days should be archived/deleted by cleanup job
```

### 4.3 Enqueuing Jobs

```python
def enqueue_job(
    job_type: str,
    target_id: Optional[str] = None,
    target_type: Optional[str] = None,
    priority: int = JOB_PRIORITY_MEDIUM,
    scheduled_at: Optional[datetime] = None,
    created_by: str = "scheduler",
    idempotency_key: Optional[str] = None
) -> Optional[IngestionJob]:
    """
    Insert a job into the queue. Returns None if idempotency_key already exists (deduplicated).
    """
    if idempotency_key:
        existing = db.query(IngestionJob).filter(
            IngestionJob.idempotency_key == idempotency_key,
            IngestionJob.status.in_(["pending", "running", "completed"])
        ).first()
        if existing:
            log.debug(f"Job deduplicated by idempotency_key: {idempotency_key}")
            return None
    
    job = IngestionJob(
        job_type=job_type,
        target_id=target_id,
        target_type=target_type,
        priority=priority,
        scheduled_at=scheduled_at or now(),
        created_by=created_by,
        idempotency_key=idempotency_key
    )
    db.add(job)
    db.commit()
    return job
```

---

## 5. Data Freshness Policy

Data freshness defines when a piece of data is considered "stale" and should be re-fetched. The ingestion system uses these thresholds to decide whether to skip a re-fetch (data is fresh) or proceed (data is stale).

### 5.1 Freshness Thresholds by Data Type

| Data Type | Stale After | Rationale | Priority Queue |
|-----------|-------------|-----------|----------------|
| Movie core metadata (title, cast, runtime) | 7 days | Changes infrequently; major changes are detected via TMDB discovery | Medium |
| TMDB popularity score | 24 hours | Daily snapshot required for trend tracking | Medium |
| TMDB vote average/count | 48 hours | Meaningful change takes days | Low |
| Trailer stats (YouTube views) | 72 hours | Specified schedule: every 3 days | Medium |
| Financial data (released, within 30 days) | 24 hours | Box office updated daily for recent releases | High |
| Financial data (released, 30–90 days old) | 72 hours | Collections stabilize over time | Medium |
| Financial data (historical, > 90 days) | 7 days | Rarely changes; minor adjustments possible | Low |
| Google Trends score | 24 hours | 1 request per movie per day limit | Low |
| Reddit sentiment | 48 hours | Weekly job runs every 7 days; 48h is the check threshold | Low |
| Competition data (release week analysis) | 24 hours | Competitors may be added/removed | Medium |
| Feature snapshot | At each prediction event | Always recomputed before prediction | High |
| IMDb rating (from dataset file) | 7 days (file update) | IMDb dataset files are updated weekly | Low |

### 5.2 Freshness Check Implementation

```python
def is_stale(data_type: str, last_updated: Optional[datetime], movie: Movie) -> bool:
    """
    Check if data of a given type for a movie is stale and should be refreshed.
    Returns True if data needs refreshing.
    """
    if last_updated is None:
        return True  # Never fetched — always stale
    
    thresholds = {
        "movie_metadata": timedelta(days=7),
        "tmdb_popularity": timedelta(hours=24),
        "tmdb_ratings": timedelta(hours=48),
        "trailer_stats": timedelta(hours=72),
        "financial_data": get_financial_staleness(movie),
        "google_trends": timedelta(hours=24),
        "sentiment": timedelta(hours=48),
        "competition": timedelta(hours=24),
    }
    
    threshold = thresholds.get(data_type, timedelta(days=7))
    return (now() - last_updated) > threshold

def get_financial_staleness(movie: Movie) -> timedelta:
    if not movie.release_date:
        return timedelta(days=7)
    days_since_release = (date.today() - movie.release_date).days
    if days_since_release <= 30:
        return timedelta(hours=24)
    elif days_since_release <= 90:
        return timedelta(hours=72)
    else:
        return timedelta(days=7)
```

---

## 6. Historical Change Tracking Schema

Every meaningful change to movie data is recorded in `movie_history`. This serves multiple purposes:
1. **Audit trail**: Know what changed, when, and from what source
2. **Model training data**: Track how metadata evolves as release approaches
3. **Debugging**: Diagnose why a prediction changed between runs
4. **Data quality**: Identify sources that frequently provide incorrect data

### 6.1 `movie_history` Table (Complete DDL)

```sql
CREATE TABLE movie_history (
    -- Identity
    history_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    movie_id UUID NOT NULL REFERENCES movies(movie_id) ON DELETE CASCADE,
    
    -- What changed
    field_name VARCHAR(100) NOT NULL,
    -- Examples: 'release_date', 'title', 'budget', 'tmdb_popularity', 'status'
    
    old_value TEXT NULL,
    -- Previous value as string; NULL if first time this field was set
    
    new_value TEXT NULL,
    -- New value as string; NULL if field was cleared
    
    value_type VARCHAR(20) NOT NULL DEFAULT 'string',
    -- 'string' | 'integer' | 'float' | 'date' | 'boolean' | 'json'
    -- Helps downstream code parse old_value/new_value correctly
    
    -- When and from where
    changed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    source VARCHAR(100) NOT NULL,
    -- 'tmdb_discovery' | 'tmdb_enrichment' | 'youtube_stats' | 'admin:username'
    -- | 'financial_collection:sacnilk' | 'sentiment_analysis'
    
    retrieval_timestamp TIMESTAMP WITH TIME ZONE NULL,
    -- When the data was retrieved from the external source (may differ from changed_at)
    
    -- Data quality classification
    data_quality VARCHAR(20) NOT NULL DEFAULT 'unconfirmed',
    -- 'verified' | 'estimated' | 'unconfirmed' | 'manual'
    -- 'verified': from official/reliable source
    -- 'estimated': computed or approximated
    -- 'unconfirmed': from TMDB/fan sources, not cross-verified
    -- 'manual': entered by admin
    
    -- Change significance
    change_significance VARCHAR(20) NULL,
    -- 'critical' (release_date, title) | 'important' (cast, budget) | 'minor' (popularity)
    
    -- Optional job reference
    ingestion_job_id UUID REFERENCES ingestion_jobs(job_id) ON DELETE SET NULL NULL,
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_movie_history_movie_id ON movie_history(movie_id, changed_at DESC);
CREATE INDEX idx_movie_history_field_name ON movie_history(movie_id, field_name, changed_at DESC);
CREATE INDEX idx_movie_history_changed_at ON movie_history(changed_at DESC);
CREATE INDEX idx_movie_history_source ON movie_history(source, changed_at DESC);
```

### 6.2 Change Tracking for Financial Data

Financial data changes are tracked separately at a finer granularity because they involve multiple currencies, sources, and reliability levels:

```sql
CREATE TABLE financial_history (
    history_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    movie_id UUID NOT NULL REFERENCES movies(movie_id) ON DELETE CASCADE,
    
    collection_date DATE NOT NULL,  -- Date the collection was performed
    days_since_release INTEGER,
    
    -- Collected values (all amounts in INR crore OR USD million, specified per field)
    india_nett_gross NUMERIC(12, 2) NULL,     -- INR crore
    india_gross NUMERIC(12, 2) NULL,           -- INR crore (before tax = nett / 0.82 approx)
    worldwide_gross_usd NUMERIC(14, 2) NULL,   -- USD million
    
    -- Source and quality
    source VARCHAR(100) NOT NULL,
    data_quality VARCHAR(20) NOT NULL DEFAULT 'unconfirmed',
    source_url TEXT NULL,
    notes TEXT NULL,
    
    -- Context
    ingestion_job_id UUID REFERENCES ingestion_jobs(job_id) ON DELETE SET NULL NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_financial_history_movie_id ON financial_history(movie_id, collection_date DESC);
```

---

## 7. Admin Interface Requirements

The admin interface is a set of protected API endpoints and a minimal frontend panel that allows a CineMetrics administrator to manage data quality, override automated decisions, and monitor system health.

> [!IMPORTANT]
> The admin interface is NOT part of the public-facing frontend. It is accessible only to authenticated admin users. For MVP, authentication can be a simple bearer token in `settings.ADMIN_TOKEN`.

### 7.1 Movie Management

#### 7.1.1 Manually Add a Movie

**Use case**: A major South Indian movie is announced but not yet on TMDB.

**Admin action**:
1. Navigate to Admin → Movies → Add Movie
2. Fill in: Title, Original Title, Release Date, Language, Director, Lead Cast (optional), Production Company (optional), Budget (optional), Notes
3. Click Save → Movie inserted with `status = "manually_added"`, `data_completeness_score = 0.0`
4. System attempts TMDB title search to find a matching record and proposes a link
5. Admin approves or rejects the TMDB link

**API endpoint**: `POST /api/v1/admin/movies`

**Required fields**: `title`, `release_date`, `original_language`
**Optional fields**: All other movie fields

#### 7.1.2 Correct a Movie Field

**Use case**: TMDB has wrong budget or the release date was postponed and not yet updated in TMDB.

**Admin action**: Navigate to movie → Edit Fields → Change field value → Select data_quality ("verified" if from official source, "estimated" if approximated) → Save

**Effect**: 
- Updates `movies` table field
- Inserts a `movie_history` record with `source = "admin:{username}"`, `data_quality = "verified"`
- If `release_date` changed: re-enqueues enrichment and prediction jobs

**API endpoint**: `PATCH /api/v1/admin/movies/{movie_id}`

#### 7.1.3 Merge Duplicate Records

**Use case**: The same movie was added to TMDB twice (e.g., once as a Telugu entry, once as a Hindi dub), resulting in two records in CineMetrics.

**Admin action**:
1. Admin → Movies → Find Duplicates (shows candidate pairs by similarity)
2. Select canonical record (keep this one)
3. Select duplicate record (this will be merged into canonical)
4. Review what will be merged: cast, financials, predictions, history
5. Confirm merge

**Merge logic**:
- All foreign key references (cast, predictions, history, etc.) are updated to point to canonical `movie_id`
- Duplicate record is soft-deleted (`status = "merged"`, `merged_into = canonical_movie_id`)
- All history records from duplicate are preserved with a `source` annotation `"merged_from:{duplicate_id}"`

**API endpoint**: `POST /api/v1/admin/movies/merge`

#### 7.1.4 Exclude a Movie from Predictions

**Use case**: An adult film or non-theatrical release was incorrectly included.

**Admin action**: Movie → Set Status → "excluded" → Reason (dropdown: adult_content / ott_only / data_quality_too_low / duplicate / other)

**Effect**: `status = "excluded"`, excluded from all upcoming dashboards, no predictions generated.

**API endpoint**: `PATCH /api/v1/admin/movies/{movie_id}/status`

#### 7.1.5 Mark Financial Value as Verified/Unverified

**Use case**: Admin has cross-checked the box office collection from an authoritative source (trade magazine, Bollywood Hungama official tweet).

**Admin action**: Movie → Financials → Click field → Mark as Verified → Source URL → Save

**Effect**: Updates `movie_financials.data_quality` and `movie_financials.source_url`, inserts history record.

**API endpoint**: `PATCH /api/v1/admin/movies/{movie_id}/financials`

#### 7.1.6 Trigger Manual Enrichment

**Use case**: TMDB just updated metadata for a movie (new trailer added, cast confirmed) and admin wants to fetch it immediately.

**Admin action**: Movie → Actions → Re-enrich → Confirm

**Effect**: Inserts a high-priority `enrich_new_movies` job with `created_by = "admin:username"`.

**API endpoint**: `POST /api/v1/admin/movies/{movie_id}/enrich`

### 7.2 Ingestion Monitoring

#### 7.2.1 View Ingestion Logs

**Display**: Paginated log viewer filtered by:
- Log level (DEBUG/INFO/WARNING/ERROR)
- Job type
- Date range
- Movie ID (to see all events for a specific movie)

**API endpoint**: `GET /api/v1/admin/ingestion/logs?level=ERROR&job_type=enrich_new_movies&from=2025-01-01`

#### 7.2.2 View Failed Jobs (Dead Letter Queue)

**Display**: Table of all `status = "dead"` jobs with:
- Job type, target movie, failure date, number of attempts, last error message
- Action buttons: Retry (reset attempts, set to pending) | Ignore (mark as permanently ignored)

**API endpoint**: `GET /api/v1/admin/ingestion/jobs?status=dead`

#### 7.2.3 View All Ingestion Jobs

**Display**: Dashboard showing:
- Jobs by status (pending/running/completed/failed/dead) — today and rolling 7 days
- Last run time and result for each scheduled job type
- Upcoming scheduled job times

**API endpoint**: `GET /api/v1/admin/ingestion/status`

#### 7.2.4 Pause/Resume Specific Job Types

**Use case**: Admin wants to pause trailer stat collection while YouTube quota is manually being conserved for a special event.

**Admin action**: Admin → Scheduler → `update_trailer_stats` → Pause

**Effect**: The APScheduler job is paused via `scheduler.pause_job(job_id)`. All currently-enqueued jobs of that type remain in the queue but the scheduler stops creating new ones.

**API endpoint**: 
- `POST /api/v1/admin/ingestion/pause/{job_type}`
- `POST /api/v1/admin/ingestion/resume/{job_type}`

#### 7.2.5 Trigger Manual Job Run

**Use case**: Admin wants to run the upcoming movie discovery scan immediately (without waiting for 2am).

**Admin action**: Admin → Scheduler → `discover_upcoming_movies` → Run Now

**Effect**: Inserts a high-priority one-off job into the queue.

**API endpoint**: `POST /api/v1/admin/ingestion/trigger/{job_type}`

### 7.3 Admin Authentication

For MVP, admin endpoints are protected by a single shared admin token in environment variables:

```python
# backend/app/api/admin.py
from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

def require_admin(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.credentials != settings.ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid admin token")
    return True
```

> [!CAUTION]
> The `ADMIN_TOKEN` must be a long, random string stored only in `.env` (never committed to git). Generate with: `python -c "import secrets; print(secrets.token_hex(32))"`

For production: replace with proper user authentication (FastAPI Users or similar).

---

## 8. Ingestion System Startup and Shutdown

### 8.1 Startup Sequence

When the application starts, the ingestion system initializes in order:

1. **Database connection**: Verify PostgreSQL is reachable
2. **Migration check**: Ensure Alembic migrations are current (`alembic check`)
3. **Rate limiter initialization**: Create shared rate limiter instances
4. **API client initialization**: TMDB, YouTube, Reddit clients with credentials from env
5. **APScheduler startup**: Load persisted job schedules from database
6. **Job registration**: Register all cron jobs (using `replace_existing=True` to handle restarts)
7. **Stale job cleanup**: Any jobs stuck in `status = "running"` from a previous crash are reset to `status = "failed"` with error `"Process restart — job interrupted"`

### 8.2 Shutdown Sequence

```python
@app.on_event("shutdown")
async def shutdown_event():
    # 1. Pause scheduler — stop accepting new jobs
    scheduler.pause()
    
    # 2. Mark any currently-running jobs as interrupted
    db.query(IngestionJob).filter(
        IngestionJob.status == "running"
    ).update({
        "status": "failed",
        "last_error": "Application shutdown while job was running",
        "completed_at": now()
    })
    db.commit()
    
    # 3. Shutdown scheduler (don't wait for running jobs — already marked failed)
    scheduler.shutdown(wait=False)
    
    log.info("Ingestion system shut down cleanly")
```

---

## 9. Environment Variables Reference

All ingestion configuration is in `.env` (never committed to git):

```bash
# TMDB
TMDB_API_KEY=your_tmdb_api_key_here
TMDB_RATE_LIMIT_PER_10S=38  # Conservative rate limit

# YouTube
YOUTUBE_API_KEY=your_youtube_data_api_v3_key

# Reddit
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=CineMetrics/1.0

# Ingestion settings
ENRICHMENT_BATCH_SIZE=10  # Movies to enrich per 5-minute cycle
PREDICTION_HORIZON_DAYS=365  # Days ahead to discover movies
MIN_POPULARITY_THRESHOLD=1.0  # TMDB popularity floor

# Admin
ADMIN_TOKEN=generate_a_long_random_string_here
```
