"""
CineMetrics — Automated Movie Discovery & Ingestion Job
Continuously discovers upcoming theatrical releases from TMDB (Global & Indian Regional),
deduplicates candidates, tracks release date shifts, enriches credits/trailers,
and materializes the live upcoming releases radar catalog.
"""

import os
import json
import time
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler

from backend.app.services.tmdb_client import ProductionTMDBClient
from backend.app.services.enrichment_service import EnrichmentService

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("DiscoveryJob")

PROCESSED_DATA_DIR = Path("data") / "processed"
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
CATALOG_FILE = PROCESSED_DATA_DIR / "upcoming_discovery_catalog.parquet"
AUDIT_LOG_FILE = PROCESSED_DATA_DIR / "discovery_audit_log.jsonl"
REPORT_FILE = Path("backend") / "jobs" / "DISCOVERY_AUDIT_REPORT.md"


class AutonomousDiscoveryEngine:
    """
    Automated discovery engine monitoring upcoming movie pipelines.
    """

    def __init__(self):
        self.tmdb_client = ProductionTMDBClient()
        self.enricher = EnrichmentService(self.tmdb_client)

    def load_existing_catalog(self) -> pd.DataFrame:
        """Loads existing upcoming catalog parquet if available."""
        if CATALOG_FILE.exists():
            try:
                df = pd.read_parquet(CATALOG_FILE)
                logger.info(f"Loaded existing catalog with {len(df):,} tracked upcoming movies.")
                return df
            except Exception as e:
                logger.warning(f"Could not load existing catalog ({e}); creating new catalog.")
        return pd.DataFrame()

    def harvest_all_candidates(self) -> List[Dict[str, Any]]:
        """
        Gathers raw movie candidates across all primary and regional endpoints.
        """
        raw_candidates: List[Dict[str, Any]] = []
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        one_year_later = (datetime.now(timezone.utc) + timedelta(days=365)).strftime("%Y-%m-%d")

        # 1. TMDB /movie/upcoming across key territories (IN, US, GB)
        for region in ["IN", "US", "GB"]:
            for page in range(1, 3):
                data = self.tmdb_client.get_upcoming_movies(region=region, page=page)
                items = data.get("results", [])
                for item in items:
                    item["source_channel"] = f"upcoming_{region}"
                    raw_candidates.append(item)

        # 2. TMDB /discover/movie future window (Next 365 Days)
        for page in range(1, 3):
            data = self.tmdb_client.discover_movies_in_range(start_date=today, end_date=one_year_later, page=page)
            items = data.get("results", [])
            for item in items:
                item["source_channel"] = "discover_future"
                raw_candidates.append(item)

        # 3. Dedicated Indian Regional Languages (Hindi, Telugu, Tamil, Malayalam, Kannada)
        indian_langs = ["hi", "te", "ta", "ml", "kn"]
        for lang in indian_langs:
            for page in range(1, 3):
                data = self.tmdb_client.discover_movies_in_range(
                    start_date=today,
                    end_date=one_year_later,
                    original_language=lang,
                    page=page,
                )
                items = data.get("results", [])
                for item in items:
                    item["source_channel"] = f"indian_lang_{lang}"
                    raw_candidates.append(item)

        logger.info(f"Harvested {len(raw_candidates)} total candidate hits across all channels.")
        return raw_candidates

    def run_discovery_cycle(self, max_enrichments: int = 40) -> Dict[str, Any]:
        """
        Executes one complete discovery cycle:
        1. Harvests candidates
        2. Deduplicates by tmdb_id
        3. Identifies new titles and release date shifts
        4. Enriches metadata, credits, and YouTube trailers
        5. Materializes catalog to parquet
        6. Generates audit report
        """
        t0 = time.perf_counter()
        cycle_timestamp = datetime.now(timezone.utc).isoformat()
        logger.info(f"Starting autonomous movie discovery cycle at {cycle_timestamp}...")

        # 1. Harvest
        raw_candidates = self.harvest_all_candidates()

        # 2. Deduplicate
        deduped: Dict[int, Dict[str, Any]] = {}
        for c in raw_candidates:
            tmdb_id = c.get("id")
            if tmdb_id and tmdb_id not in deduped:
                deduped[tmdb_id] = c

        logger.info(f"Unique candidates after deduplication: {len(deduped)}")

        # 3. Compare with Existing Catalog
        existing_df = self.load_existing_catalog()
        existing_map: Dict[int, Dict[str, Any]] = {}
        if not existing_df.empty and "tmdb_id" in existing_df.columns:
            for _, r in existing_df.iterrows():
                existing_map[int(r["tmdb_id"])] = r.to_dict()

        new_candidates: List[Dict[str, Any]] = []
        date_shift_candidates: List[Dict[str, Any]] = []
        unchanged_records: List[Dict[str, Any]] = []

        for tmdb_id, cand in deduped.items():
            cand_rel_date = cand.get("release_date") or ""
            if tmdb_id not in existing_map:
                new_candidates.append(cand)
            else:
                existing_rec = existing_map[tmdb_id]
                old_date = existing_rec.get("release_date") or ""
                if cand_rel_date and old_date and cand_rel_date != old_date:
                    date_shift_candidates.append(cand)
                else:
                    unchanged_records.append(existing_rec)

        logger.info(
            f"Catalog Delta: New={len(new_candidates)} | "
            f"Date Shifts={len(date_shift_candidates)} | Unchanged={len(unchanged_records)}"
        )

        # 4. Enrich new and date-shifted titles (respecting max_enrichments cap to prevent API exhaustion)
        to_enrich = (new_candidates + date_shift_candidates)[:max_enrichments]
        enriched_new_records: List[Dict[str, Any]] = []

        for idx, cand in enumerate(to_enrich, 1):
            logger.info(f"[{idx}/{len(to_enrich)}] Enriching '{cand.get('title')}' (TMDB {cand.get('id')})...")
            res = self.enricher.enrich_movie(cand)
            if res:
                res["discovered_at"] = cycle_timestamp
                res["last_refreshed_at"] = cycle_timestamp
                enriched_new_records.append(res)

        # 5. Merge Catalog
        all_records = unchanged_records + enriched_new_records
        updated_df = pd.DataFrame(all_records)

        # Sort by release date ascending (soonest releases first)
        if not updated_df.empty and "release_date" in updated_df.columns:
            updated_df["release_date_clean"] = pd.to_datetime(updated_df["release_date"], errors="coerce")
            updated_df = updated_df.sort_values(by="release_date_clean", ascending=True)
            updated_df = updated_df.drop(columns=["release_date_clean"])

        # Save to Parquet
        updated_df.to_parquet(CATALOG_FILE, engine="pyarrow", compression="snappy", index=False)
        logger.info(f"Persisted {len(updated_df)} active upcoming releases to {CATALOG_FILE}.")

        duration_sec = round(time.perf_counter() - t0, 2)

        # 6. Audit Summary
        audit_summary = {
            "cycle_timestamp": cycle_timestamp,
            "duration_seconds": duration_sec,
            "total_candidates_scanned": len(raw_candidates),
            "unique_tmdb_candidates": len(deduped),
            "new_titles_discovered": len(new_candidates),
            "date_shifts_detected": len(date_shift_candidates),
            "titles_enriched": len(enriched_new_records),
            "total_catalog_tracked": len(updated_df),
        }

        with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(audit_summary) + "\n")

        # 7. Compile Report
        report_md = self.generate_audit_report(audit_summary, updated_df, enriched_new_records)
        with open(REPORT_FILE, "w", encoding="utf-8") as f:
            f.write(report_md)
        logger.info(f"Generated discovery report at {REPORT_FILE}")

        return audit_summary

    def generate_audit_report(
        self,
        audit: Dict[str, Any],
        catalog_df: pd.DataFrame,
        recently_enriched: List[Dict[str, Any]],
    ) -> str:
        """Constructs markdown report summarizing discovery execution."""
        md = []
        md.append("# CineMetrics — Autonomous Movie Discovery & Radar Report\n")
        md.append(f"**Execution Timestamp:** `{audit['cycle_timestamp']}`  ")
        md.append(f"**Cycle Duration:** `{audit['duration_seconds']}s`  ")
        md.append(f"**Total Upcoming Titles in Live Radar:** `{audit['total_catalog_tracked']:,}` releases  \n")
        md.append("---\n")

        md.append("## 1. Discovery Cycle Execution Metrics\n")
        md.append("| Metric Name | Value | Description |")
        md.append("|---|:---:|---|")
        md.append(f"| **Raw Candidates Harvested** | `{audit['total_candidates_scanned']}` | Across TMDB upcoming (IN, US, GB), Discover 365, and Indian regional queries |")
        md.append(f"| **Unique TMDB Entities** | `{audit['unique_tmdb_candidates']}` | Deduplicated entity count |")
        md.append(f"| **New Titles Discovered** | `{audit['new_titles_discovered']}` | Newly announced theatrical films not previously tracked |")
        md.append(f"| **Date Shifts Detected** | `{audit['date_shifts_detected']}` | Existing tracked films whose release dates moved |")
        md.append(f"| **Enriched in Cycle** | `{audit['titles_enriched']}` | Full credits, directors, cast, and YouTube trailer keys fetched |")
        md.append("\n---\n")

        # Industry Breakdown
        if not catalog_df.empty and "industry" in catalog_df.columns:
            ind_counts = catalog_df["industry"].value_counts().to_dict()
            md.append("## 2. Active Radar Portfolio by Industry\n")
            md.append("| Industry Territory | Active Tracked Films | Percentage Share |")
            md.append("|---|:---:|:---:|")
            total = len(catalog_df)
            for ind, count in ind_counts.items():
                md.append(f"| **{ind}** | `{count}` | `{count / total * 100:.1f}%` |")
            md.append("\n---\n")

        # Lifecycle Stage Breakdown
        if not catalog_df.empty and "prediction_lifecycle_stage" in catalog_df.columns:
            stage_counts = catalog_df["prediction_lifecycle_stage"].value_counts().to_dict()
            md.append("## 3. Prediction Lifecycle Stage Distribution\n")
            md.append("| Lifecycle Stage | Count | Trigger Condition |")
            md.append("|---|:---:|---|")
            for st, cnt in stage_counts.items():
                desc = "Official YouTube trailer linked; buzz tracking active" if "Trailer" in st else "Pre-trailer announcement; structural features only"
                md.append(f"| **{st}** | `{cnt}` | {desc} |")
            md.append("\n---\n")

        # Top 10 Anticipated Releases in Live Radar
        md.append("## 4. Top Anticipated Upcoming Releases (Chronological Live Radar)\n")
        md.append("| Movie Title | Industry | Release Date | Director | Lead Actor | Lifecycle Stage | YouTube Trailer Key |")
        md.append("|---|---|:---:|---|---|:---:|:---:|")

        top_slice = catalog_df.head(12) if not catalog_df.empty else pd.DataFrame()
        for _, r in top_slice.iterrows():
            yt_key = r.get("youtube_trailer_id")
            yt_str = f"[`{yt_key}`](https://youtu.be/{yt_key})" if yt_key else "*Pending drop*"
            md.append(
                f"| **{r.get('primary_title', 'Unknown')}** | {r.get('industry', 'Global')} | "
                f"`{r.get('release_date', 'TBD')}` | {r.get('director', 'TBD')} | "
                f"{r.get('lead_actor', 'TBD')} | `{r.get('prediction_lifecycle_stage', 'Stage 0')}` | {yt_str} |"
            )
        md.append("\n---\n")

        md.append("## 5. Architectural Conclusions & Downstream Trigger\n")
        md.append("1. **Zero Duplicate Inserts:** Deduplication on unique `tmdb_id` guarantees idempotent discovery execution.")
        md.append("2. **DoH Bypass Automation:** Google DNS-over-HTTPS natively integrated into discovery client, preventing ISP connection drops.")
        md.append("3. **Continuous Radar Feed:** Persisted `upcoming_discovery_catalog.parquet` continuously powers Mode 2 (Upcoming Releases Intelligence) and triggers Phase 12 prediction lifecycle updates.\n")

        return "\n".join(md)


def start_discovery_scheduler():
    """Starts the APScheduler background thread for autonomous recurring execution."""
    scheduler = BackgroundScheduler()
    engine = AutonomousDiscoveryEngine()

    # Run daily at 02:00 AM UTC
    scheduler.add_job(
        engine.run_discovery_cycle,
        "cron",
        hour=2,
        minute=0,
        id="autonomous_movie_discovery",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Autonomous Movie Discovery background scheduler started (cron: daily at 02:00 AM UTC).")
    return scheduler


if __name__ == "__main__":
    logger.info("Executing standalone on-demand movie discovery cycle...")
    engine = AutonomousDiscoveryEngine()
    summary = engine.run_discovery_cycle(max_enrichments=35)
    print("\n" + "=" * 60)
    print("PHASE 11 DISCOVERY CYCLE COMPLETE")
    print("=" * 60)
    print(f"Candidates Scanned:   {summary['total_candidates_scanned']}")
    print(f"Unique TMDB Entities: {summary['unique_tmdb_candidates']}")
    print(f"New Titles Found:     {summary['new_titles_discovered']}")
    print(f"Date Shifts Detected: {summary['date_shifts_detected']}")
    print(f"Titles Enriched:      {summary['titles_enriched']}")
    print(f"Total Radar Catalog:  {summary['total_catalog_tracked']}")
    print("=" * 60)

