# CineMetrics — Natural Language Processing & Multilingual Sentiment Architecture

**Document ID:** 12  
**Version:** 1.0  
**Status:** Approved Technical Blueprint  
**Last Updated:** 2026-11  
**Related Docs:** [Feature Engineering](09_FEATURE_ENGINEERING.md) | [Machine Learning Research](10_MACHINE_LEARNING_RESEARCH.md) | [Upcoming Movie Discovery](13_UPCOMING_MOVIE_DISCOVERY.md)

---

## Table of Contents

1. [Architectural Goals & Scope](#1-architectural-goals--scope)
2. [The Leakage Boundary: Pre-Release Buzz vs. Post-Release Reviews](#2-the-leakage-boundary-pre-release-buzz-vs-post-release-reviews)
3. [The Multilingual Challenge in Indian Cinema](#3-the-multilingual-challenge-in-indian-cinema)
   - 3.1 [Script Variation & Romanized Transliteration](#31-script-variation--romanized-transliteration)
   - 3.2 [Code-Mixed Linguistics (Hinglish, Tanglish, Tenglish)](#32-code-mixed-linguistics-hinglish-tanglish-tenglish)
   - 3.3 [Colloquial Cinema Slang & Sarcasm](#33-colloquial-cinema-slang--sarcasm)
4. [Candidate Architecture & Pre-Trained Model Evaluation](#4-candidate-architecture--pre-trained-model-evaluation)
5. [The CineMetrics Multilingual NLP Pipeline Blueprint](#5-the-cinemetrics-multilingual-nlp-pipeline-blueprint)
6. [Training Strategy & Feature Extraction Protocol](#6-training-strategy--feature-extraction-protocol)
7. [Sentiment Feature Synthesis for Tabular ML Models](#7-sentiment-feature-synthesis-for-tabular-ml-models)
8. [Student Hardware Profiling & Compute Feasibility](#8-student-hardware-profiling--compute-feasibility)

---

## 1. Architectural Goals & Scope

The Natural Language Processing (NLP) subsystem within CineMetrics is engineered to extract measurable, objective sentiment and anticipation signals from unstructured public discourse surrounding upcoming and catalog films.

Its primary objectives:
1. **Pre-Release Buzz Quantification**: Quantify audience excitement, skepticism, or controversy from YouTube comments, Reddit threads, and promotional articles.
2. **Multilingual Ingestion**: Process commentary across major Indian film languages and colloquial code-mixed internet slang.
3. **Continuous Feature Feeding**: Transform text streams into fixed-dimensional numerical features consumed directly by the CatBoost/LightGBM revenue regressors.
4. **Student-Feasible Deployment**: Execute inference efficiently on commodity CPU infrastructure without requiring dedicated multi-GPU cloud clusters.

---

## 2. The Leakage Boundary: Pre-Release Buzz vs. Post-Release Reviews

Maintaining temporal integrity is just as critical in NLP as it is in tabular modeling:

```
PRE-RELEASE BUZZ (PERMITTED AS PREDICTIVE FEATURE)
• YouTube Official Trailer Comments (Timestamped prior to release date)
• Reddit Discussion Threads (e.g., r/bollywood, r/tollywood teaser reactions)
• Trade press commentary & buzz articles
─────────────────────────────────────────────────────────────────────────────
[TEMPORAL LEAKAGE BOUNDARY: THEATRICAL RELEASE DAY 00:00]
─────────────────────────────────────────────────────────────────────────────
POST-RELEASE REVIEWS (STRICTLY BANNED AS PREDICTIVE FEATURE)
• IMDb User Reviews & Ratings
• Rotten Tomatoes Critic & Audience Scores
• BookMyShow / Sacnilk Verified Theatrical Reviews
• Post-release Twitter/X public reaction threads
```

**Rule**: All text data utilized to construct features for Stage 1, Stage 2, and Stage 3 predictions must possess source timestamps strictly earlier than the film's verified release date. Post-release reviews are collected exclusively for post-mortem analysis and actuals validation.

---

## 3. The Multilingual Challenge in Indian Cinema

Indian cinema discussions are unique in global cinema analytics due to three profound linguistic phenomena:

### 3.1 Script Variation & Romanized Transliteration
Discussions occur both in native Indic scripts (Devanagari, Telugu, Tamil, Malayalam, Kannada) and, overwhelmingly, in Roman script (Latin alphabet). For example:
- Native Devanagari: *"फिल्म का टीज़र बहुत जबरदस्त है!"*
- Romanized Hindi (Hinglish): *"Film ka teaser bohot zabardast hai, blockbuster pakka!"*

Standard English NLP pipelines (VADER, RoBERTa-English) misclassify Romanized Indic text as gibberish or neutral.

### 3.2 Code-Mixed Linguistics (Hinglish, Tanglish, Tenglish)
Users constantly mix English technical cinema terms with regional grammar:
- *"The BGM in the interval scene is literally goosebumps, theater blast aypothundi"* (Tenglish: Telugu + English).
- *"Climax execution was vera level, vintage Thalaiva mass"* (Tanglish: Tamil + English).

### 3.3 Colloquial Cinema Slang & Sarcasm
Regional cinema cultures employ rich vernacular slang:
- Positive: *Mass*, *Paisa Vasool*, *Veri-thanom*, *Chala Baga Undhi*, *Seeti-Maar*.
- Negative: *Cringe*, *Disaster*, *Rod*, *Lag*, *Borefest*.

---

## 4. Candidate Architecture & Pre-Trained Model Evaluation

| Model Architecture | Source / HuggingFace | Supported Languages | Code-Mixing Capability | Parameter Count | Inference Speed (CPU) | Selection Status |
|---|---|---|---|:---:|:---:|:---:|
| **VADER / TextBlob** | Rule-Based | English Only | Fails completely | N/A | Extremely Fast (<1ms) | Auxiliary English Only |
| **mBERT (multilingual-cased)**| Google (`bert-base-multilingual-cased`)| 104 Languages | Poor on Romanized Indic | 110M | Moderate (60ms) | Rejected |
| **XLM-RoBERTa-base** | Meta (`xlm-roberta-base`) | 100 Languages | Moderate | 125M | Moderate (75ms) | Secondary Candidate |
| **DistilBERT-Multilingual** | HuggingFace (`distilbert-base-multilingual-cased`)| 104 Languages | Poor on Code-Mixed | 66M | Fast (35ms) | Rejected |
| **IndicBERT** | AI4Bharat (`ai4bharat/indic-bert`) | 12 Indian Languages | High on Native Script | 87M | Fast (40ms) | Native Script Specialist |
| **MuRIL (Multilingual Representations for Indian Languages)**| **Google (`google/muril-base-cased`)** | **17 Indian Languages + English** | **Superior on Romanized Code-Mixed (Hinglish/Tanglish)** | **236M** | **Acceptable (95ms)** | **PRIMARY SELECTION** |

### Why Google MuRIL is the Primary Architecture
**MuRIL (Multilingual Representations for Indian Languages)** was pre-trained specifically on monolingual, translated, and **transliterated / code-mixed Indian texts**. It natively recognizes that *"zabardast"* in Roman script corresponds semantically to *"ज़बरदस्त"* in Devanagari and *"fantastic"* in English. This capability makes it the gold standard for Indian entertainment discourse.

---

## 5. The CineMetrics Multilingual NLP Pipeline Blueprint

The production sentiment engine utilizes a staged ensemble router:

```
[Incoming Unstructured Text Stream]
(YouTube Trailer Comments / Reddit Posts)
                   │
                   ▼
[1. Text Preprocessing & Cleaning]
- Strip URLs, emojis (convert to sentiment tokens), HTML tags
- Deduplicate repeated characters (e.g. "goosebumpss!!!!" -> "goosebumps!")
                   │
                   ▼
[2. Script & Language Identification]
- FastText / langdetect identifies Native Indic vs. Latin Script
                   │
         ┌─────────┴─────────┐
         ▼                   ▼
[Latin Script / Code-Mixed]   [Native Indic Script]
         │                   │
         ▼                   ▼
  [Google MuRIL]      [IndicBERT / MuRIL]
         │                   │
         └─────────┬─────────┘
                   │
                   ▼
[3. Sentiment & Anticipation Head]
- Softmax output: [P(Negative), P(Neutral), P(Positive)]
- Compound Polarity Score $S \in [-1.0, +1.0]$
                   │
                   ▼
[4. Aggregation & Feature Store]
- Group by `movie_id` and `snapshot_date`
- Materialize tabular features into `sentiment_observations`
```

---

## 6. Training Strategy & Feature Extraction Protocol

To avoid the high compute overhead and data labeling burden of training a large language model from scratch, CineMetrics adopts a two-phase strategy:

### Phase A: Zero-Shot / Feature Extractor Baseline (Immediate MVP)
- Load pre-trained `google/muril-base-cased`.
- Attach a zero-shot classification head or use pooled token embeddings with a pre-trained sentiment classifier (`cardiffnlp/twitter-roberta-base-sentiment` cross-mapped for English).
- Zero GPU fine-tuning required; immediate student-friendly deployment.

### Phase B: Transfer Learning on Curated Cinema Corpora (Phase 9 Roadmap)
- Fine-tune MuRIL classification head on a consolidated dataset of 25,000 public Indian movie reviews:
  - English: IMDb 50k benchmark subset.
  - Hindi: Hindavi Hindi movie review dataset.
  - Telugu / Tamil: Scraped and labeled YouTube trailer reaction snippets.
- Training executed on free Google Colab T4 GPU (estimated 2.5 hours runtime).

---

## 7. Sentiment Feature Synthesis for Tabular ML Models

The raw comment-level sentiment predictions are aggregated into five standardized continuous tabular features per movie:

1. `sentiment_compound_polarity` ($S_{\text{comp}} \in [-1.0, +1.0]$):
   Weighted average polarity across all pre-release comments:
   $$S_{\text{comp}} = P(\text{Positive}) - P(\text{Negative})$$
2. `sentiment_positive_ratio` ($R_{\text{pos}} \in [0.0, 1.0]$):
   Fraction of analyzed commentary classified as strongly positive ($S_i > +0.3$).
3. `sentiment_controversy_index` ($C_{\text{index}} \in [0.0, 1.0]$):
   Standard deviation of sentiment scores: high values identify polarizing films with intense fan wars.
4. `sentiment_volume_intensity`:
   Total sample size of pre-release comments collected (proxy for digital buzz magnitude).
5. `sentiment_velocity_trend`:
   Slope of sentiment polarity over the 30 days preceding theatrical release (detects whether anticipation is building or deflating).

---

## 8. Student Hardware Profiling & Compute Feasibility

- **Model Weight Storage**: MuRIL base requires $\sim 950\text{MB}$ disk storage (huggingface cache).
- **Inference Optimization**:
  - Model weights quantized to 8-bit dynamic INT8 via `torch.quantization.quantize_dynamic`.
  - Batch size set to 32 comments per batch.
  - Average inference time on modern laptop CPU (AMD Ryzen 7 / Apple M1 / Intel i7): **1.2 seconds per 100 comments**.
- **Batch Architecture**: Sentiment is never calculated synchronously during user HTTP requests. Scheduled background workers process comments in batch at night and cache final scores directly to PostgreSQL. User queries in Movie Explorer read pre-aggregated metrics in $<5\text{ms}$.
