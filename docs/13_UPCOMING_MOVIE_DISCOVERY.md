# 13 — Upcoming Movie Discovery

> **Document Status**: Planning / Design
> **Last Updated**: 2025-01-01
> **Related Docs**: [14_AUTOMATED_DATA_INGESTION.md](./14_AUTOMATED_DATA_INGESTION.md) | [06_DATABASE_SCHEMA.md](./06_DATABASE_SCHEMA.md) | [17_SYSTEM_ARCHITECTURE.md](./17_SYSTEM_ARCHITECTURE.md)

---

## Overview

Upcoming Movie Discovery is the first stage of the CineMetrics data pipeline. Before any prediction can be made, the system must know which movies exist, when they are releasing, and have enough metadata to build feature vectors. This document defines the complete strategy for discovering upcoming movies across all supported industries (Bollywood, Tollywood, Kollywood, Mollywood, Hollywood, and other regional Indian cinema), keeping the tracked movie list current, and triggering downstream enrichment jobs.

The discovery system is designed to be:
- **Automated**: runs on schedule without manual intervention for mainstream releases
- **Comprehensive**: captures movies across global and Indian regional markets
- **Idempotent**: re-running discovery never duplicates records
- **Auditable**: every discovery event is logged with source, timestamp, and reason for update

---

## 1. Discovery Sources

### 1.1 Primary Sources

#### 1.1.1 TMDB `/movie/upcoming` Endpoint

The TMDB `/movie/upcoming` endpoint returns movies that are classified as "upcoming" in TMDB's internal system, filtered by region. It is paginated with up to 20 movies per page.

**API Call Pattern:**
```
GET https://api.themoviedb.org/3/movie/upcoming
    ?api_key={TMDB_API_KEY}
    &language=en-US
    &region={REGION_CODE}
    &page={PAGE_NUMBER}
```

**Regions to query (in order):**
| Region Code | Market Coverage |
|-------------|----------------|
| `IN` | India (all languages) |
| `US` | Hollywood, global releases |
| `GB` | UK releases, some international |

**Pagination strategy**: Query page 1, extract `total_pages` from response, then query pages 2 through `total_pages`. Each page contains up to 20 results. For India region, expect 5–15 pages on a typical day.

**Rate limit consideration**: 40 requests per 10 seconds (TMDB free tier). Paginating through all regions at 15 pages each = ~45 requests. Must include a 250ms sleep between requests or use token bucket rate limiting.

**Limitations of this endpoint**:
- Region filtering is imprecise — it shows movies with _any_ release date in that region, not necessarily ones releasing soon
- Some Indian regional language movies are entirely absent
- TMDB's definition of "upcoming" may lag behind official announcements by weeks

#### 1.1.2 TMDB `/discover/movie` with Future Release Date Filter

The `/discover/movie` endpoint is more flexible and allows precise date range filtering. This is used as a secondary primary source to catch movies that the `/movie/upcoming` endpoint missed.

**API Call Pattern:**
```
GET https://api.themoviedb.org/3/discover/movie
    ?api_key={TMDB_API_KEY}
    &primary_release_date.gte={TODAY_ISO}
    &primary_release_date.lte={TODAY_PLUS_365_ISO}
    &sort_by=popularity.desc
    &with_release_type=3|2  -- 2=Limited, 3=Theatrical
    &page={PAGE_NUMBER}
```

**Date range**: TODAY to TODAY+365 days. This gives a full 12-month forward view. The pipeline stores all discovered movies but only actively enriches/predicts movies releasing within 90 days (configurable via `PREDICTION_HORIZON_DAYS` environment variable).

**Sort order**: `popularity.desc` ensures the most commercially significant movies appear in early pages. If the quota runs short, the most important movies are already captured.

**Expected volume**: 500–2000 movies in a 365-day window globally. At 20 per page, this is 25–100 pages. Full scan takes 2–5 minutes at safe rate limits.

---

### 1.2 Indian Cinema Discovery

Indian regional cinema requires dedicated queries because TMDB's global "upcoming" does not reliably surface Telugu, Tamil, Malayalam, Kannada, and Bengali movies.

#### 1.2.1 Language-Filtered Discover Queries

For each Indian language, run a separate discover query:

```
GET https://api.themoviedb.org/3/discover/movie
    ?api_key={TMDB_API_KEY}
    &with_original_language={LANG_CODE}
    &primary_release_date.gte={TODAY_ISO}
    &primary_release_date.lte={TODAY_PLUS_365_ISO}
    &sort_by=popularity.desc
    &page={PAGE_NUMBER}
```

**Language codes to query:**

| Language | Code | Industry | Expected Monthly Volume |
|----------|------|----------|------------------------|
| Hindi | `hi` | Bollywood | 80–150 movies |
| Telugu | `te` | Tollywood | 60–120 movies |
| Tamil | `ta` | Kollywood | 50–100 movies |
| Malayalam | `ml` | Mollywood | 40–80 movies |
| Kannada | `kn` | Sandalwood | 20–50 movies |
| Bengali | `bn` | Tollywood (Bengali) | 20–40 movies |
| Punjabi | `pa` | Punjabi Cinema | 10–30 movies |

**Indian Cinema Notes**:
- Telugu and Tamil movies that release pan-India are often also indexed under `hi` language if they have a Hindi dub — the deduplication step (Section 2, Step 4) handles this using `tmdb_id` as the unique key
- Malayalam cinema has strong OTT-first releases; theatrical discovery still matters for prediction but the pipeline should flag OTT-primary movies
- Bhojpuri cinema (`bho`) has poor TMDB coverage and is excluded from initial scope

#### 1.2.2 Pan-India Release Detection

A movie is flagged as `is_pan_india = TRUE` when:
- It appears in both a regional language query AND the global upcoming query
- OR its `production_countries` includes India AND it has a release date in 3+ TMDB regions
- OR it is manually marked as pan-India by an admin

Pan-India movies receive elevated prediction priority because they are commercially significant and have more data available.

---

### 1.3 Supplementary Sources

#### 1.3.1 TMDB Trending + Popularity-Sorted Upcoming

```
GET https://api.themoviedb.org/3/trending/movie/week
    ?api_key={TMDB_API_KEY}
```

The trending endpoint returns movies gaining attention that week. Cross-referenced against the upcoming movie list to:
- Identify upcoming movies with sudden popularity spikes (potential blockbusters)
- Catch movies that may have been missed in discover queries but are going viral

**Schedule**: Run every 6 hours (4× per day). Less comprehensive, more time-sensitive.

#### 1.3.2 Manual Addition via Admin Interface

An admin interface (documented in [14_AUTOMATED_DATA_INGESTION.md](./14_AUTOMATED_DATA_INGESTION.md)) allows manually adding movies that are:
- Not yet indexed on TMDB (too early in production)
- Regional movies with very limited TMDB presence
- Announced via press releases or social media but not yet formally listed

**Manual addition workflow**:
1. Admin provides: title, release_date, language, director (optional), cast (optional), production company (optional)
2. System assigns a synthetic `cinemetrics_id` (UUID) if no TMDB ID
3. Movie is inserted with `status = "manually_added"` and `data_completeness_score` will be low
4. System attempts to find a matching TMDB record and link it
5. Enrichment job is triggered for whatever TMDB data is available
6. If TMDB match found later, records are merged (admin confirmation required for merge)

**Expected use cases**:
- Major South Indian productions announced 12–18 months ahead with limited TMDB data
- Franchise sequels before official TMDB listing
- OTT-exclusive releases that may still have theatrical components

---

## 2. Discovery Algorithm — Step-by-Step

The discovery algorithm runs as a single atomic job: `discover_upcoming_movies`. It is scheduled daily at 2:00am IST (see [14_AUTOMATED_DATA_INGESTION.md](./14_AUTOMATED_DATA_INGESTION.md)).

```
FUNCTION discover_upcoming_movies():
```

### Step 1: Collect Raw Movie Lists from All Sources

```python
raw_results = []

# 1a. TMDB /movie/upcoming — paginate all regions
for region in ["IN", "US", "GB"]:
    page = 1
    while True:
        response = tmdb_client.get("/movie/upcoming", params={
            "region": region,
            "page": page
        })
        raw_results.extend(response["results"])
        if page >= response["total_pages"]:
            break
        page += 1
        rate_limiter.wait()  # token bucket

# 1b. TMDB /discover/movie — global date range
page = 1
while True:
    response = tmdb_client.get("/discover/movie", params={
        "primary_release_date.gte": today_iso(),
        "primary_release_date.lte": today_plus(365),
        "sort_by": "popularity.desc",
        "with_release_type": "3|2",
        "page": page
    })
    raw_results.extend(response["results"])
    if page >= min(response["total_pages"], MAX_DISCOVER_PAGES):  # cap at 100 pages
        break
    page += 1
    rate_limiter.wait()

# 1c. Indian language queries
for lang_code in ["hi", "te", "ta", "ml", "kn", "bn", "pa"]:
    page = 1
    while True:
        response = tmdb_client.get("/discover/movie", params={
            "with_original_language": lang_code,
            "primary_release_date.gte": today_iso(),
            "primary_release_date.lte": today_plus(365),
            "sort_by": "popularity.desc",
            "page": page
        })
        raw_results.extend(response["results"])
        if page >= min(response["total_pages"], 50):  # cap per language
            break
        page += 1
        rate_limiter.wait()
```

### Step 2: Deduplicate by TMDB ID

TMDB IDs are globally unique. The same movie appears in multiple query results (e.g., a Hindi movie appears in region=IN query AND language=hi query). Deduplication is done in memory before any database writes.

```python
seen_tmdb_ids = set()
unique_movies = []
for movie in raw_results:
    if movie["id"] not in seen_tmdb_ids:
        seen_tmdb_ids.add(movie["id"])
        unique_movies.append(movie)

log.info(f"Collected {len(raw_results)} raw results → {len(unique_movies)} unique movies after dedup")
```

### Step 3: Filter Out Clearly Irrelevant Results

Before database lookups, discard movies that are outside scope:

```python
filtered_movies = []
for movie in unique_movies:
    # Must have a release date
    if not movie.get("release_date"):
        continue
    
    # Release date must be in the future (within our horizon)
    release_dt = parse_date(movie["release_date"])
    if release_dt < today():
        continue  # already released — handled by historical collection
    if release_dt > today_plus(365):
        continue  # too far out, skip for now
    
    # Minimum popularity threshold (avoid obscure direct-to-video)
    if movie.get("popularity", 0) < MIN_POPULARITY_THRESHOLD:  # e.g., 1.0
        # Exception: include all Indian language movies regardless of popularity
        if movie.get("original_language") not in INDIAN_LANGUAGES:
            continue
    
    filtered_movies.append(movie)
```

### Step 4: Check Database for Existing Records

For each filtered movie, check if it already exists in the `movies` table using `tmdb_id`:

```python
db_movies = db.query(Movie).filter(
    Movie.tmdb_id.in_([m["id"] for m in filtered_movies])
).all()
existing_tmdb_ids = {m.tmdb_id: m for m in db_movies}
```

### Step 5: Classify Each Movie as New or Existing

```python
new_movies = []
changed_movies = []

for movie in filtered_movies:
    tmdb_id = movie["id"]
    
    if tmdb_id not in existing_tmdb_ids:
        # Truly new — never seen before
        new_movies.append(movie)
    else:
        # Existing — check for meaningful changes
        existing = existing_tmdb_ids[tmdb_id]
        changes = detect_changes(existing, movie)
        if changes:
            changed_movies.append((existing, movie, changes))
```

### Step 6: Insert New Movies

```python
for movie_data in new_movies:
    new_movie = Movie(
        tmdb_id=movie_data["id"],
        title=movie_data["title"],
        original_title=movie_data["original_title"],
        title_normalized=normalize_title(movie_data["title"]),
        release_date=parse_date(movie_data["release_date"]),
        release_year=parse_date(movie_data["release_date"]).year,
        original_language=movie_data["original_language"],
        overview=movie_data.get("overview"),
        poster_tmdb_path=movie_data.get("poster_path"),
        status="newly_discovered",
        market_segment=infer_market_segment(movie_data["original_language"]),
        data_completeness_score=0.15,  # only basic fields populated
        prediction_readiness_score=0,
        created_at=now(),
        updated_at=now()
    )
    db.add(new_movie)
    
    # Schedule enrichment job for this movie
    enqueue_job(
        job_type="enrich_new_movies",
        target_id=str(new_movie.movie_id),
        priority=JOB_PRIORITY_HIGH,
        scheduled_at=now()  # immediate
    )

db.commit()
log.info(f"Inserted {len(new_movies)} new movies")
```

### Step 7: Update Changed Existing Movies

```python
for existing_movie, new_data, changes in changed_movies:
    # Record each changed field in movie_history
    for field_name, (old_value, new_value) in changes.items():
        history_entry = MovieHistory(
            movie_id=existing_movie.movie_id,
            field_name=field_name,
            old_value=str(old_value),
            new_value=str(new_value),
            changed_at=now(),
            source="tmdb_discovery",
            retrieval_timestamp=now(),
            data_quality="verified"
        )
        db.add(history_entry)
    
    # Apply changes to main record
    for field_name, (old_value, new_value) in changes.items():
        setattr(existing_movie, field_name, new_value)
    existing_movie.updated_at = now()
    
    # If release date changed: re-enrich and re-predict
    if "release_date" in changes:
        enqueue_job(
            job_type="enrich_new_movies",
            target_id=str(existing_movie.movie_id),
            priority=JOB_PRIORITY_MEDIUM
        )

db.commit()
log.info(f"Updated {len(changed_movies)} existing movies")
```

### Step 8: Check for Release Date Crossings

Movies that had a future release date but whose `release_date` is now TODAY or in the past have "crossed" into released territory. These need post-release collection triggered.

```python
just_released = db.query(Movie).filter(
    Movie.release_date <= today(),
    Movie.status.in_(["newly_discovered", "imminent", "announced", "post_production"])
).all()

for movie in just_released:
    movie.status = "released"
    enqueue_job(
        job_type="post_release_collection",
        target_id=str(movie.movie_id),
        priority=JOB_PRIORITY_HIGH,
        scheduled_at=now()
    )

db.commit()
log.info(f"Transitioned {len(just_released)} movies to released status")
```

### Step 9: Log Discovery Run Summary

```python
log_ingestion_summary(
    job_type="discover_upcoming_movies",
    new_movies_found=len(new_movies),
    movies_updated=len(changed_movies),
    movies_released=len(just_released),
    total_api_calls=rate_limiter.total_calls,
    duration_seconds=elapsed()
)
```

---

## 3. Movie Status Lifecycle

Each movie in the database has a `status` field that tracks where it is in its production and release lifecycle. Status transitions are driven by both automated checks and manual admin updates.

```
                    ┌─────────────────────────────────────────────────────────────────┐
                    │                    MOVIE STATUS LIFECYCLE                       │
                    └─────────────────────────────────────────────────────────────────┘

   [Admin / TMDB]         [Auto / Time]       [Auto / Time]      [Date Crossing]
         │                      │                   │                   │
         ▼                      ▼                   ▼                   ▼
   ┌──────────┐         ┌──────────────┐    ┌──────────────┐    ┌──────────┐    ┌────────────┐
   │announced │ ──────► │ production   │──► │post_production│──► │ imminent │──► │  released  │──► historical
   └──────────┘         └──────────────┘    └──────────────┘    └──────────┘    └────────────┘
         ▲                                                              ▲
         │                                                              │
   [Manual Add]                                              [30 days before release]
```

### Status Definitions

| Status | Meaning | Prediction Active? | Data Sources |
|--------|---------|-------------------|--------------|
| `announced` | Movie announced, no confirmed release date | No | TMDB basic metadata only |
| `production` | Confirmed in production, release date > 90 days away | No | TMDB, cast/crew, Wikipedia |
| `post_production` | Release date 30–90 days away; active promotions starting | Yes (early) | TMDB, trailers, social media |
| `imminent` | Release date within 30 days | Yes (full) | All sources, daily updates |
| `released` | Past release date; box office data being collected | Yes (actuals) | Financial APIs, news |
| `historical` | Released > 6 months ago, data fully settled | Archive only | IMDb, Box Office Mojo |
| `newly_discovered` | Just inserted, enrichment not yet complete | No | Discovery payload only |
| `manually_added` | Added by admin, may not have TMDB record | Conditional | Admin-provided data |
| `excluded` | Explicitly excluded from predictions | No | — |

### Automatic Status Transitions

The discovery job and a separate `update_movie_statuses` cron job handle transitions:

```python
# Runs daily as part of discover_upcoming_movies Step 8 and a separate cleanup job

def update_movie_statuses():
    today = date.today()
    
    # newly_discovered → announced (after enrichment completes)
    db.query(Movie).filter(
        Movie.status == "newly_discovered",
        Movie.data_completeness_score >= 0.4
    ).update({"status": "announced"})
    
    # announced/production → post_production (90 days before release)
    db.query(Movie).filter(
        Movie.status.in_(["announced", "production"]),
        Movie.release_date.between(today + timedelta(days=30), today + timedelta(days=90))
    ).update({"status": "post_production"})
    
    # post_production → imminent (30 days before release)
    db.query(Movie).filter(
        Movie.status == "post_production",
        Movie.release_date.between(today, today + timedelta(days=30))
    ).update({"status": "imminent"})
    
    # imminent/post_production → released (release date passed)
    db.query(Movie).filter(
        Movie.status.in_(["imminent", "post_production", "announced", "production"]),
        Movie.release_date < today
    ).update({"status": "released"})
    
    # released → historical (6 months after release)
    db.query(Movie).filter(
        Movie.status == "released",
        Movie.release_date < today - timedelta(days=180)
    ).update({"status": "historical"})
    
    db.commit()
```

---

## 4. Enrichment Pipeline for Each Discovered Movie

After a new movie is inserted with basic TMDB discovery data, the enrichment pipeline fetches complete metadata. Enrichment runs as a separate job (`enrich_new_movies`) triggered by the discovery job.

### Enrichment Steps (Ordered by Priority)

Each step calls a TMDB endpoint and stores results in the database. Steps are executed sequentially for reliability. If a step fails, it logs the error and continues with remaining steps. The `data_completeness_score` is updated after each successful step.

#### Step 1: Full Movie Metadata — `GET /movie/{tmdb_id}`

```python
response = tmdb_client.get(f"/movie/{tmdb_id}")
# Updates: title, original_title, overview, tagline, runtime_minutes,
#          budget, revenue, status, release_date, production_countries,
#          spoken_languages, homepage, adult flag
# Sets: data_completeness += 0.15
```

Stores `budget` and `revenue` in `movie_financials` with:
- `source = "tmdb"`
- `data_quality = "unconfirmed"` (TMDB financial data is often wrong)
- `currency = "USD"` (TMDB always reports in USD)

#### Step 2: Cast and Crew — `GET /movie/{tmdb_id}/credits`

```python
response = tmdb_client.get(f"/movie/{tmdb_id}/credits")
# cast: list of {id, name, character, order, known_for_department}
# crew: list of {id, name, job, department, known_for_department}

# Store each cast member in `persons` (upsert by tmdb_person_id)
# Store each crew member (filter: Director, Producer, Writer, Cinematographer)
# Create movie_cast junction records with billing_order
# Sets: data_completeness += 0.15
```

**Crew jobs to capture**:
- `Director` → `role_type = "director"`
- `Producer`, `Executive Producer` → `role_type = "producer"`
- `Screenplay`, `Writer`, `Story` → `role_type = "writer"`
- `Director of Photography` → `role_type = "cinematographer"`
- `Music` → `role_type = "music_director"`

#### Step 3: Regional Release Dates — `GET /movie/{tmdb_id}/release_dates`

```python
response = tmdb_client.get(f"/movie/{tmdb_id}/release_dates")
# Returns: list of {iso_3166_1 (country code), release_dates: [{release_date, type, note}]}
# type: 1=Premiere, 2=Limited, 3=Theatrical, 4=Digital, 5=Physical, 6=TV

# Store IN (India) release date separately for pan-India logic
# Sets: data_completeness += 0.05
```

If the India release date differs from the global `release_date`, update `release_date` to the India date for Indian-language movies.

#### Step 4: Trailers — `GET /movie/{tmdb_id}/videos`

```python
response = tmdb_client.get(f"/movie/{tmdb_id}/videos")
# Returns: list of {id, key (YouTube ID), name, type, official, published_at, site}

# Filter: type="Trailer", site="YouTube", official=True (prefer official)
# If no official trailer: take first trailer regardless of official flag
# Store in movie_trailers: youtube_id = key

# Sets: data_completeness += 0.10 (trailer is a key signal)
```

Trailer data at discovery time only captures the YouTube ID. The `update_trailer_stats` job (see Section 5 of [14_AUTOMATED_DATA_INGESTION.md](./14_AUTOMATED_DATA_INGESTION.md)) subsequently fetches view counts via the YouTube Data API.

**Trailer type priority** (which trailer to designate as "primary"):
1. `type = "Trailer"` + `official = True` + most recent `published_at`
2. `type = "Trailer"` + oldest `published_at` (first trailer = most impact)
3. `type = "Teaser"` + `official = True`
4. Any video with "trailer" in the name (case-insensitive)

#### Step 5: Keywords — `GET /movie/{tmdb_id}/keywords`

```python
response = tmdb_client.get(f"/movie/{tmdb_id}/keywords")
# Returns: {keywords: [{id, name}]}
# Store in movie_keywords junction table
# Sets: data_completeness += 0.05
```

Keywords are used as categorical features in ML. Thematic keywords like "based on comic", "superhero", "revenge", "family drama" carry predictive signal.

#### Step 6: External IDs — `GET /movie/{tmdb_id}/external_ids`

```python
response = tmdb_client.get(f"/movie/{tmdb_id}/external_ids")
# Returns: {imdb_id: "tt...", wikidata_id, facebook_id, instagram_id, twitter_id}

# Update movies.imdb_id with the tconst (tt...)
# Store social media handles for future sentiment analysis
# Sets: data_completeness += 0.05
```

The IMDb `tconst` (e.g., `tt12345678`) is critical for joining with IMDb datasets. Without it, the movie cannot benefit from IMDb rating data or historical comparison.

#### Step 7: IMDb Cross-Reference (if IMDb tconst available)

```python
if movie.imdb_id:
    # Look up in locally downloaded IMDb title.basics.tsv.gz (from datasets.imdbws.com)
    imdb_record = imdb_local_db.lookup(movie.imdb_id)
    if imdb_record:
        # Update: genres (from IMDb), runtime (more reliable than TMDB),
        #         title_type (movie/tvMovie/short), startYear
        # Sets: data_completeness += 0.05
```

> [!NOTE]
> IMDb datasets are downloaded weekly as part of the historical data pipeline (see [04_DATA_SOURCES.md](./04_DATA_SOURCES.md)). The enrichment step does a local lookup — no IMDb API call is made (IMDb has no public API).

#### Step 8: Historical Performance Lookup — Lead Actor and Director

For each movie, compute career performance metrics for the top-billed cast member and the director. These are **model features**, not raw data storage.

```python
def compute_person_performance_metrics(person_id: UUID, as_of_date: date) -> dict:
    """
    Returns career statistics for a person as of a specific date.
    Only uses movies released BEFORE as_of_date to prevent leakage.
    """
    past_movies = db.query(Movie).join(MovieCast).filter(
        MovieCast.person_id == person_id,
        Movie.release_date < as_of_date,
        Movie.status.in_(["released", "historical"])
    ).all()
    
    return {
        "movie_count": len(past_movies),
        "avg_worldwide_gross": safe_avg([m.financials.worldwide_gross for m in past_movies]),
        "hit_rate": count_hits(past_movies) / max(len(past_movies), 1),
        "last_3_movies_avg_gross": avg_last_n(past_movies, 3),
        "highest_gross": max_or_zero([m.financials.worldwide_gross for m in past_movies]),
        "franchise_movie_count": count_franchise(past_movies),
    }
```

Metrics stored in `feature_snapshots`, not as a separate column in `persons`.

#### Step 9: Competition Analysis — Same-Week Releases

Identify other movies releasing in the same calendar week (Saturday–Friday box office week):

```python
release_week_start = movie.release_date - timedelta(days=movie.release_date.weekday())  # Monday
release_week_end = release_week_start + timedelta(days=6)

competitors = db.query(Movie).filter(
    Movie.release_date.between(release_week_start, release_week_end),
    Movie.movie_id != movie.movie_id,
    Movie.status.in_(["imminent", "post_production", "released"])
).all()

competition_data = {
    "competitor_count": len(competitors),
    "max_competitor_predicted_revenue": max([c.latest_prediction.predicted_worldwide_gross 
                                              for c in competitors if c.latest_prediction], default=0),
    "total_competition_index": compute_competition_index(competitors, movie)
}
```

#### Step 10: Initial Feature Snapshot

After enrichment steps 1–9, create an initial `feature_snapshot` record:

```python
feature_vector = feature_engineer.compute_snapshot(
    movie=movie,
    snapshot_stage="enrichment_complete",
    snapshot_date=date.today()
)

snapshot = FeatureSnapshot(
    movie_id=movie.movie_id,
    snapshot_date=date.today(),
    snapshot_stage="enrichment_complete",
    features=feature_vector,  # JSONB
    data_completeness_at_snapshot=movie.data_completeness_score,
    prediction_stage="pre_release"
)
db.add(snapshot)

# Trigger initial prediction if data_completeness >= threshold
if movie.data_completeness_score >= 0.60:
    enqueue_job(
        job_type="predict_movie",
        target_id=str(movie.movie_id),
        priority=JOB_PRIORITY_MEDIUM
    )
```

---

## 5. Indian Cinema Discovery Challenges and Mitigations

### 5.1 Late Addition to TMDB

**Problem**: Many Indian movies, especially from smaller regional markets, are not added to TMDB until weeks or months after announcement. High-profile Telugu and Tamil movies are sometimes added only 2–4 weeks before release.

**Mitigation**:
- Run language-specific queries more aggressively (paginate further, lower popularity threshold)
- Admin interface to manually add movies by title + expected release date
- Weekly check of Bollywood Hungama, Sacnilk, and similar sites' scheduled releases (via web scraping — documented separately, **REQUIRES VERIFICATION** on legal terms)
- Community-sourced admin updates for major South Indian releases

### 5.2 Incomplete Metadata for Regional Movies

**Problem**: Telugu, Tamil, and Malayalam movies often have minimal English metadata on TMDB — missing overviews, sparse cast details, no trailers linked, wrong budget/revenue.

**Mitigation**:
- Accept lower `data_completeness_score` threshold for regional movies before enrichment is marked complete
- Adjust prediction confidence intervals for data-sparse movies
- In the UI, display "Limited data available" badge for movies with `data_completeness_score < 0.50`
- Enrich from regional sources where available (Sacnilk for South Indian releases) — **REQUIRES VERIFICATION**

### 5.3 Multiple Release Versions

**Problem**: Pan-India movies release in multiple languages (e.g., RRR released in Telugu, Hindi, Tamil, Malayalam, Kannada). TMDB sometimes lists them as separate entries or merges them.

**Mitigation**:
- Use `imdb_id` as the canonical deduplication key when available
- Flag movies with `is_pan_india = TRUE` and store language variants in a `movie_language_variants` table (future enhancement)
- For prediction: use the aggregate gross across all languages, stored as `worldwide_gross`

### 5.4 OTT vs Theatrical Classification

**Problem**: Indian OTT-first releases (Amazon Prime, Netflix originals) may be listed as upcoming movies on TMDB but have no theatrical release. Including them in theatrical prediction would be incorrect.

**Mitigation**:
- Check `release_dates` endpoint for type=4 (Digital) vs type=3 (Theatrical)
- If only Digital release date found and no Theatrical: set `is_ott_only = TRUE`
- Exclude `is_ott_only = TRUE` movies from box office predictions
- Keep in database for content discovery and future OTT prediction features

### 5.5 Admin-Managed Supplementary List

For the 20–30 highest-profile South Indian releases per year, maintain an admin-curated list:

```sql
CREATE TABLE admin_movie_list (
    list_entry_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    movie_id UUID REFERENCES movies(movie_id),
    added_by VARCHAR(100),
    added_at TIMESTAMP DEFAULT NOW(),
    reason TEXT,
    priority_tier INTEGER,  -- 1=Must predict, 2=Important, 3=Nice to have
    notes TEXT
);
```

Admins can add movies to this list from the admin interface. Movies on this list receive:
- Priority enrichment (retried more aggressively)
- More frequent popularity snapshot updates
- Manual metadata correction support
- Featured placement in the upcoming dashboard

---

## 6. Discovery Scheduling

### Schedule Summary

| Job | Cron (IST) | Description | Estimated Duration |
|-----|-----------|-------------|-------------------|
| `discover_upcoming_movies` | Daily 2:00am | Full TMDB upcoming scan + status transitions | 10–20 minutes |
| `update_trending` | Every 6 hours | TMDB trending endpoint, cross-reference | 2–5 minutes |
| `enrich_new_movies` | Triggered after discovery | Full enrichment for newly discovered movies | 2–5 min per movie |
| `update_movie_statuses` | Daily 3:00am | Auto-advance status lifecycle states | 1–2 minutes |
| `check_release_crossings` | Daily 6:00am | Identify movies that released overnight | 1 minute |

### IST Timing Rationale

- **2:00am IST**: Low traffic on external APIs, TMDB servers less loaded. Indian movie industry announcements typically happen during business hours (9am–9pm IST), so running at 2am captures the previous day's announcements.
- **6:00am IST**: Financial websites update box office data for the previous day by ~5–6am IST for Indian releases. Running release crossing check at 6am captures this.
- **Every 6 hours**: Trending data has a short half-life; 4× per day provides reasonable timeliness.

### Discovery Failure Handling

If the discovery job fails midway:
- Database writes are transactional — partial discoveries are rolled back
- The job is re-attempted after exponential backoff: 15min → 30min → 60min → dead letter
- Failed jobs are visible in the admin interface
- If discovery fails for > 24 hours, an alert is logged prominently in ingestion logs

---

## 7. Change Detection Logic

The `detect_changes` function used in Step 7 of the algorithm compares a TMDB discovery response against the stored database record:

```python
TRACKABLE_FIELDS = {
    "title": ("title", str),
    "release_date": ("release_date", date_parse),
    "overview": ("overview", str),
    "poster_path": ("poster_tmdb_path", str),
    "popularity": None,  # tracked via popularity_snapshots, not movie record
    "vote_average": None,  # tracked via movie_ratings
    "vote_count": None,  # tracked via movie_ratings
    "status": ("status", str),  # TMDB status (Rumored/Planned/In Production/etc.)
}

def detect_changes(existing_movie: Movie, new_tmdb_data: dict) -> dict:
    changes = {}
    for tmdb_field, mapping in TRACKABLE_FIELDS.items():
        if mapping is None:
            continue
        db_field, transform = mapping
        new_value = transform(new_tmdb_data.get(tmdb_field))
        old_value = getattr(existing_movie, db_field)
        
        if new_value and new_value != old_value:
            # Special case: release_date change is high-importance
            if db_field == "release_date":
                log.warning(f"Release date changed for {existing_movie.title}: "
                           f"{old_value} → {new_value}")
            changes[db_field] = (old_value, new_value)
    
    return changes
```

All detected changes are recorded in `movie_history` with the source `"tmdb_discovery"` and timestamp.

---

## 8. Data Quality Flags

Each discovered movie receives automated quality flags during discovery and enrichment:

| Flag | Meaning | UI Representation |
|------|---------|-------------------|
| `has_imdb_id` | IMDb tconst successfully linked | Green check |
| `has_trailer` | At least one YouTube trailer found | Green check |
| `has_cast_data` | > 3 cast members stored | Green check |
| `has_financial_estimate` | Budget or revenue available | Yellow (estimate) |
| `release_date_confirmed` | Release date from official/theatrical source | Green check |
| `is_ott_only` | No confirmed theatrical release | Orange badge |
| `is_manually_added` | Added by admin, not from TMDB | Blue badge |
| `data_completeness_score` | 0–100% completeness across all data types | Progress bar |
| `prediction_readiness_score` | 0–100 score indicating if ML prediction is reliable | Readiness badge |

The `prediction_readiness_score` is computed at enrichment completion:

```python
def compute_prediction_readiness(movie: Movie) -> int:
    score = 0
    if movie.release_date: score += 15
    if movie.has_director: score += 20
    if movie.has_lead_cast: score += 15
    if movie.has_trailer: score += 15
    if movie.has_production_company: score += 10
    if movie.genre_count >= 1: score += 10
    if movie.has_imdb_id: score += 5
    if movie.has_budget_estimate: score += 5
    if movie.has_competition_data: score += 5
    return min(score, 100)
```

Movies with `prediction_readiness_score < 40` are flagged as "Insufficient Data" in prediction outputs and their predictions are marked with low confidence.
