# Viral Waves - Technical Feasibility Assessment

## Executive Summary

Based on comprehensive research, **building Viral Waves using TikTok's official APIs is NOT viable** due to eligibility restrictions, severe rate limits, and data freshness issues. However, **the product is technically feasible** using cost-effective third-party alternatives with a well-architected data pipeline.

### Key Finding

| Aspect | Official TikTok API | Recommended Alternative |
|--------|--------------------|-------------------------|
| **Eligibility** | ❌ Academic/non-profit only | ✅ Commercial-friendly |
| **Rate Limits** | ❌ 1,000 requests/day | ✅ 600 requests/second |
| **Data Freshness** | ❌ 48-hour delay | ✅ Near real-time |
| **Trend Endpoints** | ❌ None available | ✅ Full data access |
| **Cost** | Free (but ineligible) | ~$100-500/month for MVP |

**Revised Recommendation:** ✅ **CONFIRMED: Self-Hosted TikTok-Api** as the primary data source (~$7-45/month with existing VPS + IPRoyal proxies). See `.env` file for configured proxy credentials.

**Note:** JoTucker RapidAPI available as fallback if self-hosted encounters issues.

---

## Part 1: Data Source Analysis

### 1.1 Official TikTok APIs - ASSESSMENT: NOT VIABLE

#### Research API (Primary Data Source)

**Critical Blockers:**

| Requirement | Reality |
|-------------|---------|
| **Eligibility** | Must be academic institution or registered non-profit. Commercial SaaS businesses are **explicitly ineligible**. |
| **Data Freshness** | New videos take **up to 48 hours** to appear; metrics take **up to 10 days** to update |
| **Rate Limits** | **1,000 requests/day** = maximum ~100,000 videos/day |
| **Trend Discovery** | **No trending endpoints**; must query by known hashtags/keywords |
| **Data Lag** | Archived search index, not live platform data |

**Available Endpoints (for context only - not usable):**
```
POST /v2/research/video/query/     # Query by hashtag/keyword
POST /v2/research/user/info/       # User profile data
POST /v2/research/user/followers/  # Follower lists
```

**Video fields available:** id, description, create_time, region_code, share/view/like/comment counts, music_id, hashtag_names, username, voice_to_text

**Why This Won't Work:**
- 48-hour delay makes real-time trend detection impossible
- 100K videos/day is insufficient for platform-wide monitoring
- Commercial use violates terms
- Cannot discover emerging trends organically

#### Business API

**Purpose:** Advertising and campaign management  
**Available Data:** Ad performance, audience targeting, creative assets  
**Missing:** Trending content discovery, hashtag analytics, sound trend data

**Verdict:** Useless for trend detection use case.

#### Developer API (Content & Display)

**Purpose:** Content posting and user authentication  
**Available:** Login Kit, Content Posting API, Share Kit  
**Missing:** All trend and analytics data

**Verdict:** Irrelevant for data collection needs.

---

### 1.2 Recommended Alternative: Apify TikTok Scraper

**ASSESSMENT: HIGHLY VIABLE - PRIMARY RECOMMENDATION**

#### Overview

Apify provides managed TikTok scrapers running on cloud infrastructure with rotating proxies built-in.

| Metric | Value |
|--------|-------|
| **Pricing** | **$0.30 per 1,000 posts** (API Dojo scraper) |
| **Processing Speed** | 600 posts/second |
| **Success Rate** | 98% across 50K+ runs |
| **Data Freshness** | Near real-time |
| **Infrastructure** | Managed (no proxy handling needed) |

#### Data Availability

**Collectable Data Points:**
- Video metadata (views, likes, shares, comments, timestamps)
- Hashtags and hashtag performance
- Music/sound information and usage counts
- Creator profile data (followers, verification status)
- Comments and engagement
- Location data (when available)

#### Specialized Scrapers Available

| Scraper | Price per 1K | Use Case |
|---------|--------------|----------|
| TikTok Scraper (API Dojo) | $0.30 | General posts, profiles, hashtags |
| TikTok Profile Scraper | $5.00 | Detailed profile analytics |
| TikTok Comments Scraper | $5.00 | Comment sentiment analysis |
| TikTok Discover Scraper | $0.003 + $0.001/video | Trend discovery feed |
| TikTok Video Downloader | $10.00 | Video content for visual analysis |

#### Implementation Approach

**Cost Projections:**

| Scale | Daily Volume | Monthly Cost |
|-------|-------------|--------------|
| MVP (testing) | 10K posts/day | ~$90/month |
| Small Scale | 50K posts/day | ~$450/month |
| Medium Scale | 200K posts/day | ~$1,800/month |
| Large Scale | 1M posts/day | ~$9,000/month |

**Legal/Compliance Status:**
- ⚠️ Gray area - scraping public data
- Generally legal in US (hiQ Labs v. LinkedIn precedent)
- Must respect rate limits and robots.txt
- GDPR considerations for EU users

---

### 1.3 Secondary Alternative: Exolyt

**ASSESSMENT: VIABLE - TREND VALIDATION LAYER**

#### Overview

Dedicated TikTok intelligence platform with API access on higher tiers.

| Metric | Value |
|--------|-------|
| **Pricing** | $330/month (Basic), $400/month (Essentials), $950/month (Advanced) |
| **Data** | Real-time analytics, social listening, trend tracking |
| **API Access** | Available on Essentials tier and above |
| **Database Claim** | "Largest TikTok database" |

#### Features

- Real-time TikTok analytics
- Social listening projects
- Influencer campaign tracking
- Sentiment and transcription analysis (Advanced tier)
- AI-powered insights

**Use Case for Viral Waves:**
- Validate trends detected via Apify
- Cross-reference hashtag performance
- Sentiment analysis on trending content
- Reduce false positives in alert system

---

### 1.4 Alternative: EchoTik

**ASSESSMENT: VIABLE - TIKTOK SHOP FOCUS**

| Metric | Value |
|--------|-------|
| **Pricing** | Free (100 requests), $139/month (100K), $694/month (500K) |
| **Focus** | TikTok Shop data + general analytics |
| **Data** | Videos, hashtags, trends, live streams, product rankings |

**Use Case:** Good for e-commerce adjacent trend detection; less comprehensive for general viral content.

---

### 1.5 Alternative: Phyllo (Compliance-First)

**ASSESSMENT: VIABLE - ENTERPRISE/COMPLIANCE FOCUS**

| Metric | Value |
|--------|-------|
| **Pricing** | Starting at ~$199/month (custom quotes) |
| **Approach** | Creator-consented data |
| **Compliance** | ✅ SOC 2 Type 1, legally compliant |
| **Platforms** | 20+ platforms including TikTok |

**Use Case:** If compliance is paramount and creator consent model is acceptable (requires creators to connect accounts).

---

## Part 2: Growth Rate Threshold Logic

### 2.1 Core Detection Philosophy

The system must detect trends based on **velocity, not volume**. This requires mathematical detection of exponential growth patterns.

### 2.2 Growth Detection Algorithms

#### Algorithm 1: Exponential Growth Detection

**Formula:**
```
V(t) = V₀ * e^(rt)

Where:
- V(t) = volume at time t
- V₀ = initial volume
- r = growth rate
- t = time
```

**Implementation Logic:**
1. Take log of volume measurements: `ln(V(t))`
2. Fit linear regression to log-transformed data
3. Calculate R² (coefficient of determination)
4. If R² > 0.85, growth is exponential
5. Extract growth rate `r` from slope

**Threshold:**
- **r > 0.5** (50% growth rate) = Early warning
- **r > 1.0** (100% growth rate) = High priority alert
- **r > 2.0** (200% growth rate) = Critical alert

#### Algorithm 2: Doubling Time Analysis

**Formula:**
```
T_double = ln(2) / r ≈ 0.693 / r

Or using Rule of 70:
T_double ≈ 70 / (growth_rate_percentage)
```

**Interpretation:**
- Doubling time < 1 hour = Viral momentum detected
- Doubling time < 30 minutes = Explosive growth (immediate alert)
- Doubling time > 6 hours = Slow burn trend

#### Algorithm 3: Adaptive Percentile Thresholds (BERTrend-Style)

This approach self-adjusts to the data distribution, preventing false positives during high-activity periods.

**Logic:**
1. Calculate percentiles over rolling 7-day window:
   - P10 (10th percentile) = noise floor
   - P50 (50th percentile) = baseline
   - P90 (90th percentile) = elevated activity
   - P99 (99th percentile) = viral threshold

2. Alert Tiers:
   | Percentile | Alert Level | Action |
   |------------|-------------|--------|
   | < P10 | Noise | Ignore |
   | P10-P50 | Weak Signal | Log only |
   | P50-P90 | Moderate | Trending list |
   | P90-P99 | Strong | Alert eligible |
   | > P99 | Viral | Immediate alert |

3. Adaptive adjustment: Percentiles recalculate daily to account for platform-wide activity changes

### 2.3 Multi-Window Time Analysis

Use multiple time windows to distinguish between flash-in-pan and sustained trends:

| Window | Purpose | Threshold Type |
|--------|---------|----------------|
| 15 minutes | Immediate spike detection | Fixed rate |
| 1 hour | Velocity calculation | Growth rate |
| 6 hours | Sustained growth validation | Acceleration |
| 24 hours | Trend confirmation | Volume baseline |
| 7 days | Seasonal adjustment | Percentile |

**Alert Logic:**
- Require positive signal in at least 2 consecutive windows
- 15-min + 1-hour = "Spike detected"
- 1-hour + 6-hour = "Trend emerging"
- 6-hour + 24-hour = "Confirmed trend"

### 2.4 Acceleration Detection

Second derivative analysis to detect trends *before* they peak:

```
Acceleration = d²V/dt²

If acceleration > 0 and growth_rate > threshold:
    → Early stage trend (highest value)
    
If acceleration < 0 but growth_rate > threshold:
    → Late stage trend (still valuable, but window closing)
    
If acceleration = 0:
    → Linear growth (stable trend)
```

---

## Part 3: Niche Clustering Logic

### 3.1 Clustering Objective

Group related hashtags, sounds, and content into "niches" to:
- Detect when trends cross between communities
- Provide contextual alerts ("trending in beauty niche")
- Identify micro-trends before they go mainstream

### 3.2 Similarity Metrics

#### Co-occurrence Similarity (Jaccard)

For hashtag similarity:
```
J(A, B) = |A ∩ B| / |A ∪ B|

Where A, B are sets of videos containing each hashtag
```

**Interpretation:**
- J = 1.0 = Always appear together (same niche)
- J = 0.0 = Never appear together (unrelated)
- J > 0.3 = Strong association
- J > 0.1 = Moderate association

#### Semantic Similarity (Cosine)

For text-based similarity (captions, hashtags):
```
cos(θ) = (A · B) / (||A|| ||B||)

Using TF-IDF vectors of text content
```

#### User Overlap Similarity

```
UserOverlap(A, B) = |Users_A ∩ Users_B| / min(|Users_A|, |Users_B|)
```

Detects when same creators participate in multiple trends.

#### Multi-View Aggregation

Combine multiple similarity signals:
```
Final_Similarity = 
    0.30 * CoOccurrence +
    0.25 * TextSemantic +
    0.20 * UserOverlap +
    0.15 * Temporal +
    0.10 * URL/Link
```

### 3.3 Clustering Algorithms

#### Primary: Leiden Algorithm (Recommended)

**Why Leiden over Louvain:**
- Guarantees connected communities (Louvain can produce disconnected clusters)
- Faster convergence
- O(N log N) complexity
- Better resolution parameter handling

**Parameters:**
- Resolution (γ): Controls cluster granularity
  - γ = 0.5 = Broad categories
  - γ = 1.0 = Default (balanced)
  - γ = 2.0 = Fine-grained niches

**Implementation Flow:**
1. Build similarity graph from co-occurrence data
2. Run Leiden algorithm with resolution γ = 1.0
3. Identify clusters with > 10 nodes as "established niches"
4. Track cluster membership changes over time

#### Alternative: HDBSCAN

**Use case:** When number of clusters is unknown
- Density-based (no preset cluster count)
- Robust to noise
- Good for discovering emerging micro-communities

### 3.4 Cross-Niche Trend Detection

Detect when content bridges multiple communities:

**Bridge Node Detection:**
1. Calculate node betweenness centrality
2. Nodes with high betweenness = potential bridges
3. Content appearing in multiple clusters = cross-niche trend

**Cross-Niche Similarity Matrix:**
```
CrossSimilarity(Ci, Cj) = 
    Σ(similarity(ni, nj)) for all ni ∈ Ci, nj ∈ Cj
```

**Alert Trigger:**
- If content exists in cluster A and suddenly appears in cluster B
- And growth rate in cluster B > threshold
- → "Trend spreading from [niche A] to [niche B]"

---

## Part 4: Visual Similarity Detection

### 4.1 Technical Approach

Detect visual format trends by analyzing video content similarity.

### 4.2 Video Processing Pipeline

#### Step 1: Keyframe Extraction

**Hybrid Approach:**
```
1. Use PySceneDetect to identify scene boundaries
2. Extract frames at scene changes
3. Uniform sampling between scenes (every 2 seconds)
4. Target: 5-10 keyframes per video
```

#### Step 2: Embedding Generation

**Primary Model: CLIP (ViT-L/14)**
- 768-dimensional embeddings
- Trained on image-text pairs
- Excellent for "visual concept" matching
- ~0.80 mAP for visual similarity tasks

**Secondary Model: DINOv2**
- Self-supervised visual features
- Superior pure visual matching
- Good for detecting similar visual patterns without semantic understanding

**Embedding Process:**
```
Frame → CLIP/DINOv2 → 768-dim vector
Video embeddings = mean(frame embeddings)
Segment embeddings = cluster of frame embeddings
```

#### Step 3: Similarity Search

**FAISS (Facebook AI Similarity Search)**

| Index Type | Use Case | Recall |
|------------|----------|--------|
| Flat (brute force) | < 100K videos | 100% |
| IVF-PQ | 100K - 10M videos | ~90% |
| HNSW | Real-time queries | ~95% |
| GPU Index | High-throughput | ~99% |

**Query Flow:**
1. New video arrives → extract keyframes → generate embeddings
2. Query FAISS index for K nearest neighbors (K = 10)
3. If similarity > threshold (e.g., 0.85) to multiple videos
4. → Potential format trend detected

### 4.3 Vector Database

**Recommendation: Milvus (Production) or FAISS (MVP)**

| Feature | FAISS | Milvus |
|---------|-------|--------|
| Setup | Embedded | Separate service |
| Scale | Single node | Distributed cluster |
| Query latency | < 10ms | < 50ms |
| Capacity | Millions | Billions |
| Maintenance | Low | Medium |

### 4.4 Scalability Architecture

**Lambda Architecture:**
```
┌──────────────────────────────────────────────────────┐
│                    DATA INGESTION                     │
│                 (Kafka / Kinesis)                     │
└──────────────────────┬───────────────────────────────┘
                       │
       ┌───────────────┴───────────────┐
       ▼                               ▼
┌──────────────┐              ┌──────────────┐
│ SPEED LAYER  │              │ BATCH LAYER  │
│ (Real-time)  │              │ (Deep Analysis)│
├──────────────┤              ├──────────────┤
│ Extract      │              │ Full video   │
│ keyframes    │              │ processing   │
│ Generate     │              │ Trend        │
│ embeddings   │              │ correlation  │
│ Quick        │              │ Model        │
│ similarity   │              │ refinement   │
└──────┬───────┘              └──────┬───────┘
       │                             │
       └───────────────┬─────────────┘
                       ▼
              ┌──────────────┐
              │  SERVING     │
              │    LAYER     │
              └──────────────┘
```

**Storage Tiers:**
| Tier | Data | Storage | Retention |
|------|------|---------|-----------|
| Hot | Active trends, embeddings | Redis/Milvus | 7 days |
| Warm | Recent videos, metadata | PostgreSQL | 30 days |
| Cold | Historical data | S3/GCS | 1 year |

**Performance Targets:**
- Process 100K+ videos/day
- Visual similarity query < 50ms
- Index update latency < 5 minutes

---

## Part 5: Alert Logic & Delivery

### 5.1 Multi-Layered Alert Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                    ALERT PIPELINE                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. DEDUPLICATION                                           │
│     └── Remove duplicate detections within 1-hour window   │
│                                                             │
│  2. SUPPRESSION                                             │
│     ├── Maintenance window filtering                        │
│     ├── Known campaign exclusion                            │
│     └── Flash crowd detection                               │
│                                                             │
│  3. CORRELATION                                             │
│     ├── Group related trends (same sound + hashtag)        │
│     └── Cross-niche trend linking                           │
│                                                             │
│  4. ENRICHMENT                                              │
│     ├── Add example videos                                  │
│     ├── Calculate confidence score                          │
│     └── Suggest script angles                               │
│                                                             │
│  5. SCORING                                                 │
│     └── Composite alert score calculation                   │
│                                                             │
│  6. AGGREGATION                                             │
│     └── Digest mode for high-volume periods                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Alert Severity Levels

| Level | Criteria | Delivery |
|-------|----------|----------|
| **INFO** | Logged only | Dashboard |
| **LOW** | P50-P75 growth | Daily digest |
| **MEDIUM** | P75-P90 growth | Email |
| **HIGH** | P90-P99 growth | Email + Push |
| **CRITICAL** | >P99 growth, cross-niche | Immediate (SMS/Slack) |

### 5.3 Alert Scoring Formula

```
Alert_Score = 
    0.25 * Growth_Velocity +
    0.20 * Uniqueness (has this been alerted before?) +
    0.20 * Historical_Accuracy (similar past trends succeeded) +
    0.20 * Business_Impact (matches user niche preferences) +
    0.15 * Influencer_Score (quality of accounts adopting)
```

**Thresholds:**
- Score > 0.7 = Send alert
- Score > 0.85 = HIGH priority
- Score > 0.95 = CRITICAL priority

### 5.4 Alert Fatigue Prevention

**Dynamic Throttling:**
```
If analyst_alert_load > 50/hour:
    Increase threshold by 10%
    
If alert_to_action_ratio < 20%:
    Increase threshold by 5%
```

**Progressive Alerting:**
| User State | Alert Level |
|------------|-------------|
| New user | CRITICAL only |
| Active user (2+ weeks) | HIGH and above |
| Power user | MEDIUM and above |
| Expert user | All significant |

**Digest Mode:**
- Group related alerts into single digest
- Send every 4 hours during high-activity periods
- Individual alert if CRITICAL

### 5.5 Delivery Channels

| Channel | Use Case | Latency |
|---------|----------|---------|
| **Email** | Daily digest, detailed reports | < 15 min |
| **Slack** | Team notifications, agency workflows | < 2 min |
| **Discord** | Creator community integration | < 2 min |
| **SMS** | CRITICAL alerts only | < 30 sec |
| **Webhook** | Enterprise integrations | < 1 min |
| **In-app** | Real-time dashboard | Instant |

---

## Part 6: System Architecture Overview

### 6.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           VIRAL WAVES PLATFORM                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                        DATA COLLECTION LAYER                       │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐ │  │
│  │  │ Apify        │  │ Exolyt       │  │ Public Feeds (backup)    │ │  │
│  │  │ (Primary)    │  │ (Validation) │  │                          │ │  │
│  │  └──────┬───────┘  └──────┬───────┘  └────────────┬─────────────┘ │  │
│  │         └──────────────────┴───────────────────────┘               │  │
│  │                              │                                     │  │
│  │                              ▼                                     │  │
│  │                    ┌─────────────────┐                             │  │
│  │                    │  Apache Kafka   │                             │  │
│  │                    │  (Event Stream) │                             │  │
│  │                    └────────┬────────┘                             │  │
│  └─────────────────────────────┼──────────────────────────────────────┘  │
│                                │                                        │
│  ┌─────────────────────────────┼──────────────────────────────────────┐  │
│  │                    PROCESSING LAYER                                │  │
│  │                              │                                     │  │
│  │    ┌─────────────────────────┼─────────────────────────┐          │  │
│  │    │                         │                         │          │  │
│  │    ▼                         ▼                         ▼          │  │
│  │ ┌──────────┐           ┌──────────┐           ┌──────────────┐   │  │
│  │ │ Growth   │           │ Cluster  │           │ Visual       │   │  │
│  │ │ Rate     │           │ Analysis │           │ Similarity   │   │  │
│  │ │ Engine   │           │ Engine   │           │ Engine       │   │  │
│  │ └────┬─────┘           └────┬─────┘           └──────┬───────┘   │  │
│  │      │                      │                        │           │  │
│  │      └──────────────────────┼────────────────────────┘           │  │
│  │                             │                                     │  │
│  │                             ▼                                     │  │
│  │                    ┌─────────────────┐                            │  │
│  │                    │  Trend Store    │                            │  │
│  │                    │  (PostgreSQL)   │                            │  │
│  │                    └────────┬────────┘                            │  │
│  └─────────────────────────────┼──────────────────────────────────────┘  │
│                                │                                        │
│  ┌─────────────────────────────┼──────────────────────────────────────┐  │
│  │                    ALERT & DELIVERY LAYER                          │  │
│  │                              │                                     │  │
│  │                              ▼                                     │  │
│  │                    ┌─────────────────┐                            │  │
│  │                    │  Alert Pipeline │                            │  │
│  │                    │  (dedup, score) │                            │  │
│  │                    └────────┬────────┘                            │  │
│  │                             │                                     │  │
│  │         ┌───────────────────┼───────────────────┐                 │  │
│  │         ▼                   ▼                   ▼                 │  │
│  │    ┌─────────┐        ┌─────────┐        ┌──────────┐            │  │
│  │    │ Email   │        │ Slack   │        │ Webhook  │            │  │
│  │    │ Service │        │ Service │        │ Service  │            │  │
│  │    └─────────┘        └─────────┘        └──────────┘            │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                         USER LAYER                                │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐ │  │
│  │  │ Web Dashboard│  │ Mobile App   │  │ API (Enterprise)       │ │  │
│  │  └──────────────┘  └──────────────┘  └────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Technology Stack Recommendations

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Data Collection** | Apify + Python | Cost-effective, managed infrastructure |
| **Message Queue** | Apache Kafka | High throughput, replay capability |
| **Stream Processing** | Kafka Streams / Faust | Real-time trend detection |
| **Database** | PostgreSQL + TimescaleDB | Time-series data, trend history |
| **Cache** | Redis | Hot data, rate limiting |
| **Vector DB** | Milvus / FAISS | Visual similarity search |
| **Background Jobs** | Celery + Redis | Alert processing, data enrichment |
| **API** | FastAPI | Async Python, OpenAPI docs |
| **Frontend** | React + TypeScript | Component-based, type safety |
| **Infrastructure** | AWS/GCP + Docker + K8s | Scalable, managed services |

### 6.3 MVP vs Production Architecture

| Component | MVP (0-3 months) | Production (3-12 months) |
|-----------|------------------|--------------------------|
| **Data Collection** | Apify only | Apify + Exolyt + custom scrapers |
| **Processing** | Single worker | Distributed workers (Celery) |
| **Visual Analysis** | FAISS (CPU) | Milvus cluster (GPU) |
| **Storage** | Single PostgreSQL | Read replicas, sharding |
| **Queue** | Redis | Kafka cluster |
| **Deployment** | Docker Compose | Kubernetes |

---

## Part 7: Cost Analysis

### 7.1 MVP Phase (Months 1-3)

| Component | Monthly Cost |
|-----------|--------------|
| Apify (50K posts/day) | $450 |
| Exolyt Essentials | $400 |
| AWS/GCP Infrastructure | $200 |
| **Total** | **~$1,050/month** |

### 7.2 Growth Phase (Months 3-6)

| Component | Monthly Cost |
|-----------|--------------|
| Apify (200K posts/day) | $1,800 |
| Exolyt Advanced | $950 |
| Infrastructure (scaled) | $500 |
| **Total** | **~$3,250/month** |

### 7.3 Revenue Requirements

| Phase | Users Needed (avg $50/mo) | Data Costs | Margin |
|-------|---------------------------|------------|--------|
| MVP | 25 subscribers | $1,050 | Break-even |
| Growth | 65 subscribers | $3,250 | Break-even |
| Scale | 200+ subscribers | $5,000+ | 60%+ |

---

## Part 8: Risk Assessment & Mitigations

### 8.1 Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Apify rate limits/blocks** | Medium | High | Multiple data sources, proxy rotation, respectful crawling |
| **TikTok site changes** | High | High | Abstraction layer, monitoring, rapid response team |
| **False positive alerts** | Medium | Medium | Adaptive thresholds, user feedback loop, confidence scoring |
| **Data storage costs** | Low | Medium | Data retention policies, compression, tiered storage |

### 8.2 Legal/Compliance Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **TikTok ToS concerns** | Medium | High | Only public data, respectful rate limits, legal review |
| **GDPR compliance** | Medium | Medium | Data minimization, deletion protocols, EU data handling |
| **Data provider shutdown** | Low | High | Multiple provider strategy, data portability |

---

## Part 9: Unanswered Research Questions

The following areas require additional research before finalizing architecture:

### 9.1 Data Source Validation

1. **Apify Rate Limit Testing:**
   - What is the actual sustained throughput before blocks?
   - How does Apify handle TikTok rate limiting on their end?
   - What is the cost per request at scale (>500K posts/day)?

2. **Exolyt API Specifics:**
   - What exact endpoints are available on Essentials tier?
   - Does Exolyt provide sound/music trend data?
   - What is the latency of their trend detection vs Apify?

3. **Alternative Validation:**
   - Are there other providers (Data365, Phyllo) with better TikTok trend data?
   - What is the data freshness comparison across providers?

### 9.2 Algorithm Validation

4. **Growth Detection Calibration:**
   - What are the actual growth rate distributions on TikTok?
   - What R² threshold provides the best precision/recall for exponential detection?
   - How do seasonal patterns affect threshold settings?

5. **Clustering Optimization:**
   - What is the optimal resolution parameter (γ) for TikTok niches?
   - How stable are hashtag clusters over time?
   - What is the minimum cluster size for meaningful niche detection?

6. **Visual Similarity Benchmarks:**
   - What CLIP similarity threshold best identifies format trends?
   - How computationally expensive is DINOv2 vs CLIP at scale?
   - What is the false positive rate for visual trend detection?

### 9.3 Operational Questions

7. **Alert Quality Metrics:**
   - What is the acceptable false positive rate for creator audiences?
   - How do we measure "trend prediction accuracy" in production?
   - What is the optimal alert frequency per user per day?

8. **Scaling Challenges:**
   - At what volume does FAISS become insufficient?
   - What are the query latency requirements for real-time alerts?
   - How do we handle viral events (platform-wide spikes)?

### 9.4 Recommended Next Research Actions

- [ ] **Spike Test:** Run Apify scraper for 1 week at 100K posts/day to measure actual costs and reliability
- [ ] **Algorithm Benchmark:** Collect 30 days of TikTok data and test growth detection algorithms against known viral trends
- [ ] **User Research:** Interview 10 TikTok creators about their current trend discovery process and alert preferences
- [ ] **Legal Review:** Consult with legal counsel on data scraping compliance in target markets

---

## Part 10: Recommended Starting Architecture (Self-Hosted)

### 10.0 Key Architectural Insight: "Smoke Detector, Not Library"

Viral Waves is a **trend detection and alerting system**, not a video library. This fundamentally changes our storage and processing approach:

| Aspect | Video Library | Trend Alert System |
|--------|---------------|-------------------|
| **User gets** | Searchable video database | Notifications when trends emerge |
| **Data needed** | Everything, forever | Recent window only (24-72 hours) |
| **Storage** | Petabytes | Gigabytes |
| **Query pattern** | Random access | Time-series streaming |

**Implication:** We discard 90%+ of scraped data after processing, keeping only trend metadata and alert history.

---

### 10.1 Recommended Stack: Self-Hosted (Primary) ✅ SELECTED

**For founders with existing VPS + proxy infrastructure**

> **Credentials:** Proxy credentials are pre-configured in `.env` file at project root. The scraper implementation should read from this file.

#### Stack Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    SELF-HOSTED SCRAPING STACK                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  SCRAPING          PROCESSING              STORAGE         ALERTS       │
│                                                                          │
│  ┌──────────┐     ┌──────────────┐       ┌──────────┐    ┌──────────┐  │
│  │ TikTok-  │────▶│ Stream       │──────▶│ Redis    │───▶│ Alert    │  │
│  │ Api      │     │ Processor    │       │ (Hot)    │    │ Pipeline │  │
│  │ (Python) │     │ (Python)     │       │ 72hr TTL │    │          │  │
│  └──────────┘     └──────────────┘       └────┬─────┘    └────┬─────┘  │
│       │                  │                    │               │        │
│       │                  │                    ▼               │        │
│       │                  │             ┌──────────┐          │        │
│       │                  │             │ PostgreSQL         │        │
│       │                  │             │ (Trends) │          │        │
│       │                  │             └──────────┘          │        │
│       │                  │                                   │        │
│       ▼                  ▼                                   ▼        │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │              DISCARD (90% of data after processing)               │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

#### Components

| Component | Technology | Purpose | Cost |
|-----------|-----------|---------|------|
| **Scraper** | TikTok-Api (Python) + Playwright | Extract TikTok metadata | $0 (open source) |
| **Proxies** | IPRoyal (existing - see `.env`) | Rotate IPs to avoid blocks | ~$7.50/GB used |
| **Hot Cache** | Redis with TTL | 72-hour rolling window | $0 (on existing VPS) |
| **Trend DB** | PostgreSQL | Persistent trend + alert history | $0 (on existing VPS) |
| **Processing** | Python asyncio | Stream processing | $0 (existing compute) |

#### Cost Calculation (With Your Existing Infrastructure)

**Assumptions:**
- You already have a VPS with spare compute
- You already use IPRoyal at $7.50/GB
- Only scraping metadata (not downloading videos)

**Data usage:** ~2-5KB per video (metadata only)

| Phase | Videos/Day | Monthly Volume | Proxy Usage | Monthly Cost |
|-------|-----------|----------------|-------------|--------------|
| **Testing** | 1,000 | 30K | ~150MB | **~$1-2** |
| **Beta** | 10,000 | 300K | ~1.5GB | **~$7.50** |
| **Early Users** | 50,000 | 1.5M | ~7.5GB | **~$45** |
| **Growth** | 200,000 | 6M | ~30GB | **~$225** |

**Cost per 1,000 videos:** ~$0.015 (1.5 cents)

**Comparison to API alternatives:**
- JoTucker RapidAPI: $0.167 per 1K videos (11x more expensive)
- ScrapeCreators: $1.88 per 1K videos (125x more expensive)
- Apify: ~$0.30 per 1K videos (20x more expensive)

---

### 10.2 Fallback Option: JoTucker RapidAPI

**For founders without infrastructure or if self-hosted fails**

#### When to Use This

- No existing VPS/proxy setup
- Want zero maintenance
- Self-hosted scraper breaking frequently
- Need to validate idea before investing in infrastructure

#### Specifications

| Feature | Details |
|---------|---------|
| **Free Tier** | **20 requests/day** (600/month) |
| **First Paid Tier** | **$5/month** for 1,000 requests/day |
| **Rate Limit** | 1,000 requests/hour |
| **Data Available** | User info, videos, followers, hashtags, music, no-watermark videos, comments |
| **Where** | [RapidAPI](https://rapidapi.com/JoTucker/api/tiktok-scraper2) |

#### Cost Progression

| Phase | Volume | Cost |
|-------|--------|------|
| **Validation** | 600/month | **$0** |
| **Beta** | 30K/month | **$5/month** |
| **Early Traction** | 150K/month | **$20/month** |
| **Growth** | 1M+/month | **$100+/month** |

#### Why This Over Other RapidAPI Options

| API | Free Tier | First Paid | Verdict |
|-----|-----------|------------|---------|
| JoTucker | 600/month | $5/month | ✅ Best for startups |
| ScrapTik | 50/month | $99/month | ❌ Too expensive |
| TikWM | 300/month | $59/month | ❌ Expensive jump |
| TTAPI | 50/month | $49/month | ❌ Average |

---

### 10.3 Data Architecture: Process and Discard

#### The 72-Hour Hot Window

**What we keep in Redis (rolling TTL):**

```
┌─────────────────────────────────────────────────────────┐
│  HOT WINDOW (Redis) - Rolling 72 hours                 │
├─────────────────────────────────────────────────────────┤
│  • Video ID                                             │
│  • Timestamp                                            │
│  • View count (at ingestion time)                       │
│  • Like/share/comment counts                            │
│  • Hashtags                                             │
│  • Sound/Music ID                                       │
│  • Creator follower count                               │
│  • Niche/cluster assignment                             │
└─────────────────────────────────────────────────────────┘

Size: ~500 bytes × 50K videos × 3 days = ~75MB
```

#### Persistent Storage (PostgreSQL)

**What we keep forever (minimal):**

```
┌─────────────────────────────────────────────────────────┐
│  TREND DATABASE (PostgreSQL)                            │
├─────────────────────────────────────────────────────────┤
│  • Trend ID (sound/hashtag/format)                      │
│  • First detected timestamp                             │
│  • Peak timestamp                                       │
│  • Growth rate history (hourly snapshots)               │
│  • Alert sent (boolean)                                 │
│  • Accuracy feedback (user reports)                     │
└─────────────────────────────────────────────────────────┘

Size: ~100 trends/day × 90 days × 2KB = ~18MB
```

**Alert log (for user history):**

```
┌─────────────────────────────────────────────────────────┐
│  ALERT LOG (PostgreSQL)                                 │
├─────────────────────────────────────────────────────────┤
│  • User ID                                              │
│  • Trend ID                                             │
│  • Alert timestamp                                      │
│  • Alert type                                           │
│  • Confidence score                                     │
│  • User action (clicked/ignored)                        │
└─────────────────────────────────────────────────────────┘
```

#### What We Discard

| Data | Action | Rationale |
|------|--------|-----------|
| Video descriptions | Discard after hashtag extraction | Not needed for trends |
| Video thumbnails | Discard | Not needed (unless visual similarity) |
| Full user profiles | Keep only follower count | Minimal needed |
| Comments | Discard | Not needed for MVP |
| Video files | Never download | Never needed |
| Raw API responses | Parse and discard | Processed into structured data |
| 72hr+ old video data | Auto-expire (Redis TTL) | Velocity calculated, no longer needed |

#### Storage Requirements Summary

| Phase | Videos/Day | Hot Storage | Trend DB | Total |
|-------|-----------|-------------|----------|-------|
| **MVP** | 10K | ~15MB (Redis) | ~2MB | **~20MB** |
| **Beta** | 50K | ~75MB (Redis) | ~10MB | **~100MB** |
| **Growth** | 200K | ~300MB (Redis) | ~40MB | **~350MB** |
| **Scale** | 1M | ~1.5GB (Redis) | ~200MB | **~2GB** |

**Key insight:** You don't need S3, object storage, or a large database. Everything fits on your existing VPS.

---

### 10.4 Real-Time vs Near Real-Time

#### What "Real-Time" Means for Viral Waves

| Metric | Target | Why This is Sufficient |
|--------|--------|------------------------|
| **Ingestion delay** | < 5 minutes | TikTok trends last hours/days, not seconds |
| **Alert latency** | < 2 minutes | Fast enough for creators to act |
| **Trend window** | 24-72 hours | Captures full trend lifecycle |

**This is NOT true streaming** - it's near real-time batch processing. And that's perfectly fine.

#### Processing Pipeline

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────┐
│  Scraper    │───▶│  Stream      │───▶│  Trend      │───▶│  Discard │
│  (TikTok)   │    │  Processor   │    │  Detector   │    │  (70%)   │
└─────────────┘    └──────────────┘    └──────┬──────┘    └──────────┘
                                              │
                                              ▼
                                       ┌─────────────┐
                                       │  Alert?     │
                                       └──────┬──────┘
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    │                         │                         │
                    ▼                         ▼                         ▼
             ┌──────────┐            ┌──────────────┐          ┌──────────┐
             │  YES     │            │  NO (boring) │          │  Maybe   │
             │  Store   │            │  Discard     │          │  Keep    │
             │  trend   │            │              │          │  24hr    │
             └──────────┘            └──────────────┘          └──────────┘
```

#### Simplified Processing Logic

```python
HOT_WINDOW = 72 hours  # How far back we look

def process_video(video_data):
    # 1. Store in hot window (Redis with TTL)
    redis.setex(f"video:{video.id}", HOT_WINDOW, video_data)
    
    # 2. Check if this video triggers any trends
    trends = check_trends(video_data)
    
    # 3. Update trend metrics
    for trend in trends:
        update_trend_velocity(trend, video_data)
        
        # 4. Should we alert?
        if should_alert(trend):
            send_alert(trend)
            store_trend(trend)  # To PostgreSQL for history
    
    # 5. Done - video_data expires from Redis automatically
```

---

### 10.5 When to Consider Visual Similarity

**For MVP:** Skip it. Focus on sound and hashtag trends.

**Add later if needed:**
- Requires video frame extraction (~100KB per video in embeddings)
- Adds ~5GB storage for 50K videos
- Increases processing complexity significantly

**Alternative:** Use format detection via hashtag clustering (e.g., "#greenscreen" + specific sound = format trend)

---

### 10.6 Decision Matrix: Which Stack to Choose?

| Situation | Recommendation | Monthly Cost |
|-----------|----------------|--------------|
| **Have VPS + proxy already** | Self-hosted TikTok-Api | ~$7-45 |
| **No infrastructure** | JoTucker RapidAPI | $0-20 |
| **Need zero maintenance** | JoTucker RapidAPI | $5-100+ |
| **Validating idea only** | JoTucker free tier | $0 |
| **Scale >500K videos/day** | Hybrid: Self-hosted + Exolyt | $200-500 |

---

## Part 11: Conclusion & Recommendations

### 11.1 Feasibility Verdict

| Aspect | Verdict | Confidence |
|--------|---------|------------|
| **Overall Technical Feasibility** | ✅ **FEASIBLE** | High |
| **Data Source Availability** | ✅ **AVAILABLE** (via alternatives) | High |
| **Algorithm Implementation** | ✅ **WELL-UNDERSTOOD** | High |
| **Cost Viability** | ✅ **VIABLE** at scale | Medium |
| **Timeline** | ⚠️ **3-4 months to MVP** | Medium |

### 11.2 Key Recommendations

1. **Use Self-Hosted TikTok-Api as primary** - Lowest cost (~$7-45/month with existing infrastructure)
2. **Keep JoTucker RapidAPI as fallback** - Zero-cost validation, $5/month if needed
3. **Implement 72-hour hot window architecture** - Process and discard, minimal storage
4. **Skip visual similarity for MVP** - Focus on sound/hashtag trends first
5. **Use adaptive thresholds** - Self-adjusting system reduces manual tuning
6. **Build for your infrastructure** - No new VPS, no managed databases needed

### 11.3 Go/No-Go Criteria

**Proceed if:**
- ✅ Have existing VPS with spare compute (or can get one for $5-10/month)
- ✅ Have proxy access (IPRoyal, Webshare, etc. at ~$7-15/month)
- ✅ Team has Python/data engineering expertise
- ✅ Can launch within 2-3 months to capture market window
- ✅ Legal review confirms acceptable risk level
- ✅ Can cover ~$10-50/month data costs during MVP phase

**Delay if:**
- ❌ Cannot secure data budget
- ❌ TikTok makes significant API/access changes during build
- ❌ Competitor launches with similar offering before we can release

---

*Document Version: 2.0*  
*Last Updated: 2026-02-16*  
*Next Review: After initial scraper implementation and validation*
