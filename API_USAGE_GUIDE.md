# SaaS Idea Finder API - Usage Guide for Bots

> **Quick Reference for Bot Developers Calling This API**

---

## Overview

This API runs a 3-stage pipeline to discover trending topics and generate Micro-SaaS ideas:
1. **Discovery** - Aggregate trending topics from 12+ sources (30-60s)
2. **Research** - Deep research using GPT Researcher (2-4 min per topic)
3. **Synthesis** - AI-generated Micro-SaaS ideas with viability scoring (30-60s per topic)

**Total Duration**: ~3-6 minutes per topic

---

## Base URL

### External Access (Production)
```
https://api.letsautomate.work
```

### Local Development
```
http://localhost:8000
```

**Note**: The API is accessible externally via `https://api.letsautomate.work` with automatic HTTPS/TLS provided by Caddy.

---

## Authentication

All requests require the API key in the `X-API-Key` header:

```bash
X-API-Key: saif_prod_a1b2c3d4e5f6789012345678901234567890abcdef
```

---

## Endpoints

| # | Endpoint | Description | Rate Limit |
|---|----------|-------------|------------|
| 1 | `GET /health` | Health check | 100/min |
| 2 | `POST /api/v1/discover/` | Trigger pipeline | 10/min |
| 3 | `GET /api/v1/jobs/{id}/status` | Check job status | 100/min |
| 4 | `GET /api/v1/jobs/{id}/results` | Get job results | 100/min |
| 5 | `GET /api/v1/skills/` | List all skills | 100/min |
| 6 | `GET /api/v1/skills/{name}` | Get skill details | 100/min |
| 7 | `GET /api/v1/skills/{name}/download` | Download skill | 30/min |

---

### 1. Health Check

Check if the API and services are running.

```bash
GET /health
```

**Example:**
```bash
curl -s http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-02-18T23:00:00Z",
  "services": {
    "api": {"status": "up"},
    "redis": {"status": "up"},
    "worker": {"status": "up"}
  },
  "queue": {
    "queued": 0,
    "active": 1,
    "completed": 150
  }
}
```

---

### 2. Trigger Pipeline

Start the SaaS idea discovery process.

```bash
POST /api/v1/discover/
```

**Headers:**
- `X-API-Key`: Your API key
- `Content-Type: application/json`

**Request Body:**
```json
{
  "lens": "Developer Tools Monday",
  "topics": 1,
  "include_viability": true,
  "pain_threshold": 0,
  "min_viability": 0
}
```

**Parameters:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `lens` | string | No | Auto (day-of-week) | Override lens: "Developer Tools Monday", "Business SaaS Tuesday", "AI/ML Wednesday", "Data & Analytics Thursday", "Productivity & Automation Friday", "Design & Frontend Saturday", "Infrastructure & DevOps Sunday" |
| `topics` | int | No | 1 | Number of topics to analyze (1-3) |
| `include_viability` | bool | No | false | Include viability scoring (0-100) |
| `pain_threshold` | int | No | 0 | Minimum pain severity (0-100) |
| `min_viability` | int | No | 0 | Minimum viability score (0-100) |

**Example:**
```bash
curl -s -L -X POST http://localhost:8000/api/v1/discover/ \
  -H "X-API-Key: saif_prod_a1b2c3d4e5f6789012345678901234567890abcdef" \
  -H "Content-Type: application/json" \
  -d '{
    "lens": "Developer Tools Monday",
    "topics": 1,
    "include_viability": true
  }'
```

**Response (202 Accepted):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "created_at": "2026-02-18T21:45:00Z",
  "estimated_duration_seconds": 300,
  "status_url": "/api/v1/jobs/550e8400-e29b-41d4-a716-446655440000/status",
  "results_url": "/api/v1/jobs/550e8400-e29b-41d4-a716-446655440000/results"
}
```

---

### 3. Poll Job Status

Check the progress of a running job.

```bash
GET /api/v1/jobs/{job_id}/status
```

**Example:**
```bash
curl -s -L http://localhost:8000/api/v1/jobs/550e8400-e29b-41d4-a716-446655440000/status \
  -H "X-API-Key: saif_prod_a1b2c3d4e5f6789012345678901234567890abcdef"
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "researching",
  "created_at": "2026-02-18T21:45:00Z",
  "updated_at": "2026-02-18T21:47:30Z",
  "stage": "stage_2_research",
  "progress_percent": 45,
  "message": "Researching topic: local-first software",
  "error": null
}
```

**Status Values:**
- `queued` - Waiting for worker
- `discovering` - Stage 1: Fetching trends
- `researching` - Stage 2: GPT Researcher running
- `synthesizing` - Stage 3: Generating ideas
- `complete` - Ready for results
- `failed` - Error occurred

---

### 4. Get Results

Fetch the complete results (only when status is `complete`).

```bash
GET /api/v1/jobs/{job_id}/results
```

**Example:**
```bash
curl -s -L http://localhost:8000/api/v1/jobs/550e8400-e29b-41d4-a716-446655440000/results \
  -H "X-API-Key: saif_prod_a1b2c3d4e5f6789012345678901234567890abcdef"
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "complete",
  "completed_at": "2026-02-18T21:50:00Z",
  "lens": "Developer Tools Monday",
  "topics_analyzed": 1,
  "results": [
    {
      "topic": "local-first software",
      "topic_score": 85,
      "research": {
        "sources_count": 42,
        "markdown_content": "# Research: Local-First Software\n\n## Executive Summary\n...",
        "key_pain_points": [
          "Developers struggle with sync logic",
          "Offline-first architecture complexity"
        ],
        "market_insights": {
          "market_size": "$2.5B",
          "growth_rate": "25% CAGR"
        }
      },
      "ideas": [
        {
          "name": "SyncBridge",
          "tagline": "Drop-in sync layer for local-first apps",
          "viability_score": 78,
          "viability_rating": "Strong",
          "pain_severity_score": 65,
          "problem_statement": "Developers building local-first apps waste weeks implementing conflict resolution...",
          "target_audience": "Solo developers and small teams building collaborative web apps",
          "solution_approach": "CRDT-based sync layer with Firebase-like API",
          "mvp_features": [
            "Automatic conflict resolution",
            "Offline queue with retry",
            "React/Vue bindings"
          ],
          "tech_stack": {
            "frontend": "TypeScript/React",
            "backend": "Node.js/WebSocket",
            "database": "PostgreSQL + Redis",
            "infrastructure": "AWS/Docker"
          },
          "market_validation": "Post on r/reactjs asking if developers would pay $29/mo for drop-in sync",
          "jtbd_statement": "When building a collaborative app, I want conflict-free sync without backend expertise, so I can launch in days not months",
          "market_metrics": {
            "tam": 2500000000,
            "sam": 500000000,
            "som": 50000000
          },
          "unit_economics": {
            "cac": 200,
            "ltv": 2400,
            "ltv_cac_ratio": 12,
            "target_monthly_price": 49
          },
          "complexity": 3,
          "time_to_mvp": "6-8 weeks",
          "pricing_model": "SaaS subscription at $49/month",
          "red_flags": ["Competing with Firebase (Google)", "CRDT learning curve"],
          "success_boosters": ["Clear pain point", "Growing local-first trend"]
        }
      ]
    }
  ]
}
```

---

## Expected Waiting Times

| Stage | Duration | Cumulative |
|-------|----------|------------|
| Job Creation | < 1 second | 0s |
| Discovery (Stage 1) | 30-60 seconds | 30-60s |
| Research (Stage 2) | 2-4 minutes per topic | 2.5-5 min |
| Synthesis (Stage 3) | 30-60 seconds per topic | 3-6 min |
| **Total for 1 topic** | **~3-6 minutes** | - |
| **Total for 3 topics** | **~8-12 minutes** | - |

**Note**: Research duration varies based on:
- Topic complexity
- Web search results availability
- OpenRouter API response times

---

## Recommended Polling Strategy

### Python Example

```python
import requests
import time

API_URL = "https://api.letsautomate.work"  # External URL
# API_URL = "http://localhost:8000"  # Local development
API_KEY = "saif_prod_xxxxxxxxxxxxxxxx"

headers = {"X-API-Key": API_KEY}

# 1. Trigger discovery
response = requests.post(
    f"{API_URL}/api/v1/discover/",
    headers=headers,
    json={"topics": 1, "include_viability": True}
)
job = response.json()
job_id = job["job_id"]
print(f"Job started: {job_id}")
print(f"Estimated duration: {job['estimated_duration_seconds']} seconds")

# 2. Poll until complete
poll_interval = 15  # seconds
max_wait = 600  # 10 minutes timeout
waited = 0

while waited < max_wait:
    status = requests.get(
        f"{API_URL}/api/v1/jobs/{job_id}/status",
        headers=headers
    ).json()
    
    print(f"[{waited}s] Status: {status['status']} - {status.get('message', '')}")
    
    if status["status"] == "complete":
        print("✅ Job complete!")
        break
    elif status["status"] == "failed":
        print(f"❌ Job failed: {status.get('error')}")
        raise Exception("Job failed")
    
    time.sleep(poll_interval)
    waited += poll_interval

# 3. Fetch results
results = requests.get(
    f"{API_URL}/api/v1/jobs/{job_id}/results",
    headers=headers
).json()

# 4. Process results
for topic_result in results["results"]:
    print(f"\n📋 Topic: {topic_result['topic']}")
    print(f"   Score: {topic_result['topic_score']}")
    
    for idea in topic_result["ideas"]:
        print(f"\n   💡 {idea['name']}")
        print(f"      Tagline: {idea['tagline']}")
        if idea.get('viability_score'):
            print(f"      Viability: {idea['viability_score']}/100 ({idea.get('viability_rating', 'N/A')})")
        print(f"      Complexity: {idea['complexity']}/5")
        print(f"      Time to MVP: {idea['time_to_mvp']}")
```

---

## Error Handling

### 401 Unauthorized
```json
{
  "detail": "Invalid or missing API key"
}
```
**Action**: Check your X-API-Key header

### 404 Job Not Found
```json
{
  "detail": "Job not found or expired"
}
```
**Action**: Results expire after 24 hours. Trigger a new job.

### 400 Job Not Complete
```json
{
  "detail": "Job is not complete (status: researching). Poll /status endpoint."
}
```
**Action**: Continue polling the status endpoint

### 429 Rate Limited
```json
{
  "detail": "Rate limit exceeded",
  "retry_after": 60
}
```
**Action**: Wait for `retry_after` seconds before retrying

---

## Rate Limits

- **Discover endpoint**: 10 requests per minute per API key
- **Status/Results endpoints**: 100 requests per minute per API key

---

## Lens Schedule (Auto-Rotation)

| Day | Lens |
|-----|------|
| Monday | Developer Tools Monday |
| Tuesday | Business SaaS Tuesday |
| Wednesday | AI/ML Wednesday |
| Thursday | Data & Analytics Thursday |
| Friday | Productivity & Automation Friday |
| Saturday | Design & Frontend Saturday |
| Sunday | Infrastructure & DevOps Sunday |

---

## Tips for Bot Developers

1. **Always follow redirects** (`-L` in curl) - some endpoints redirect to trailing slash versions
2. **Poll at 15-30 second intervals** - more frequent polling won't make jobs complete faster
3. **Handle the `failed` status** - jobs can fail due to external API issues
4. **Cache results** - Results are stored for 24 hours, no need to re-run identical queries
5. **Use appropriate lenses** - Match the lens to your target audience for better results
6. **Start with `topics: 1`** - Test with 1 topic before running multiple

---

## Complete Bot Integration Example

```python
#!/usr/bin/env python3
"""Complete bot integration example."""

import requests
import time
import sys

class SaaSIdeaFinderBot:
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url.rstrip('/')
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }
    
    def health_check(self) -> bool:
        """Check if API is healthy."""
        try:
            resp = requests.get(f"{self.api_url}/health", timeout=5)
            data = resp.json()
            return data.get("status") == "healthy"
        except Exception as e:
            print(f"Health check failed: {e}")
            return False
    
    def discover(self, lens: str = None, topics: int = 1) -> dict:
        """Trigger discovery and return results."""
        # Start job
        resp = requests.post(
            f"{self.api_url}/api/v1/discover/",
            headers=self.headers,
            json={
                "lens": lens,
                "topics": topics,
                "include_viability": True
            },
            timeout=30
        )
        resp.raise_for_status()
        job = resp.json()
        job_id = job["job_id"]
        
        print(f"Job {job_id} started. Estimated: {job['estimated_duration_seconds']}s")
        
        # Poll for completion
        waited = 0
        while waited < 600:  # 10 min timeout
            time.sleep(15)
            waited += 15
            
            status_resp = requests.get(
                f"{self.api_url}/api/v1/jobs/{job_id}/status",
                headers=self.headers,
                timeout=10
            )
            status = status_resp.json()
            
            print(f"  [{waited}s] {status['status']}: {status.get('message', '')}")
            
            if status["status"] == "complete":
                break
            elif status["status"] == "failed":
                raise Exception(f"Job failed: {status.get('error')}")
        
        # Get results
        results_resp = requests.get(
            f"{self.api_url}/api/v1/jobs/{job_id}/results",
            headers=self.headers,
            timeout=30
        )
        return results_resp.json()
    
    def print_results(self, results: dict):
        """Pretty print results."""
        print("\n" + "="*60)
        print(f"✅ Pipeline Complete: {results['lens']}")
        print(f"   Topics Analyzed: {results['topics_analyzed']}")
        print("="*60)
        
        for result in results["results"]:
            print(f"\n📊 Topic: {result['topic']} (Score: {result['topic_score']})")
            print(f"   Research sources: {result['research']['sources_count']}")
            
            for idea in result["ideas"]:
                print(f"\n   💡 {idea['name']}")
                print(f"      {idea['tagline']}")
                if idea.get('viability_score'):
                    print(f"      Viability: {idea['viability_score']}/100")
                print(f"      MVP: {idea['time_to_mvp']}")
                print(f"      Pricing: {idea['pricing_model']}")


def main():
    bot = SaaSIdeaFinderBot(
        api_url="http://localhost:8000",
        api_key="saif_prod_a1b2c3d4e5f6789012345678901234567890abcdef"
    )
    
    # Check health
    if not bot.health_check():
        print("API is not healthy. Exiting.")
        sys.exit(1)
    
    # Run discovery
    print("Starting discovery...")
    results = bot.discover(lens="Developer Tools Monday", topics=1)
    
    # Print results
    bot.print_results(results)


if __name__ == "__main__":
    main()
```

---

## Support

For issues or questions:
1. Check the logs: `/tmp/api.log` and `/tmp/worker.log`
2. Review PROGRESS.md for known issues
3. Verify all services are running (API, Redis, Worker)

---

## Skills API (NEW)

The Skills API allows bots to discover and download skills from the global skills folder.

### 5. List All Skills

Returns a list of all available skills with metadata.

```bash
GET /api/v1/skills/
```

**Example (Local):**
```bash
curl -s -L http://localhost:8000/api/v1/skills/ \
  -H "X-API-Key: saif_prod_a1b2c3d4e5f6789012345678901234567890abcdef"
```

**Example (External):**
```bash
curl -s -L https://api.letsautomate.work/api/v1/skills/ \
  -H "X-API-Key: saif_prod_a1b2c3d4e5f6789012345678901234567890abcdef"
```

**Response:**
```json
{
  "count": 59,
  "skills": [
    {
      "name": "github-push",
      "description": "Push git commits to GitHub with intelligent protocol selection",
      "has_scripts": true,
      "has_references": false,
      "has_assets": false,
      "has_node_modules": false,
      "total_files": 4,
      "size_bytes": 12068,
      "size_human": "11.8 KB"
    },
    {
      "name": "canvas-design",
      "description": "Create beautiful visual art in .png and .pdf documents",
      "has_scripts": false,
      "has_references": false,
      "has_assets": true,
      "has_node_modules": false,
      "total_files": 83,
      "size_bytes": 5554015,
      "size_human": "5.3 MB"
    }
  ],
  "skills_dir": "/root/.skills-global/skills-global"
}
```

**Fields:**
- `has_scripts`: Skill includes executable scripts (Python/JS)
- `has_references`: Skill includes reference documentation
- `has_assets`: Skill includes templates/fonts/images
- `has_node_modules`: Skill requires `npm install` (Node.js dependencies)

---

### 6. Get Skill Details

Returns detailed information about a specific skill, including file listings and cross-dependencies.

```bash
GET /api/v1/skills/{skill_name}
```

**Example (Local):**
```bash
curl -s -L http://localhost:8000/api/v1/skills/github-push \
  -H "X-API-Key: saif_prod_a1b2c3d4e5f6789012345678901234567890abcdef"
```

**Example (External):**
```bash
curl -s -L https://api.letsautomate.work/api/v1/skills/github-push \
  -H "X-API-Key: saif_prod_a1b2c3d4e5f6789012345678901234567890abcdef"
```

**Response:**
```json
{
  "name": "github-push",
  "description": "Push git commits to GitHub...",
  "metadata": {"name": "github-push", "description": "..."},
  "has_scripts": true,
  "has_references": false,
  "has_assets": false,
  "has_node_modules": false,
  "total_files": 4,
  "size_bytes": 12068,
  "size_human": "11.8 KB",
  "files": [
    {"path": "SKILL.md", "size_bytes": 7099, "file_type": "markdown"},
    {"path": "scripts/github_push.py", "size_bytes": 21079, "file_type": "python"},
    {"path": "QUICK_REFERENCE.md", "size_bytes": 5135, "file_type": "markdown"},
    {"path": "IMPROVEMENTS.md", "size_bytes": 8535, "file_type": "markdown"}
  ],
  "cross_dependencies": [],
  "download_url": "/api/v1/skills/github-push/download"
}
```

**Cross-Skill Dependencies:**

Some skills reference other skills (e.g., `gmail-send` uses `../gmail-search/`). Check the `cross_dependencies` field and download those skills too if needed.

---

### 7. Download Skill

Downloads a skill as a compressed tar.gz archive.

```bash
GET /api/v1/skills/{skill_name}/download
```

**Query Parameters:**
- `include_node_modules` (bool, default: false): Include node_modules folder (can be very large!)

**Example (Local):**
```bash
# Download skill
curl -s -L http://localhost:8000/api/v1/skills/github-push/download \
  -H "X-API-Key: saif_prod_a1b2c3d4e5f6789012345678901234567890abcdef" \
  -o github-push.tar.gz

# Extract
tar -xzf github-push.tar.gz

# Result: github-push/ folder with all skill files
```

**Example (External):**
```bash
# Download skill from external API
curl -s -L https://api.letsautomate.work/api/v1/skills/github-push/download \
  -H "X-API-Key: saif_prod_a1b2c3d4e5f6789012345678901234567890abcdef" \
  -o github-push.tar.gz

# Extract
tar -xzf github-push.tar.gz
```

**Rate Limit:** 30 requests per minute (due to archive generation)

---

### Skills Bot Integration Example

```python
#!/usr/bin/env python3
"""Example bot that discovers and downloads skills."""

import requests
import tarfile
import io
import os

# Use external URL for production, localhost for development
API_URL = "https://api.letsautomate.work"  # External
# API_URL = "http://localhost:8000"        # Local development

API_KEY = "saif_prod_xxxxxxxx"

headers = {"X-API-Key": API_KEY}

# 1. List all skills
response = requests.get(f"{API_URL}/api/v1/skills/", headers=headers)
skills = response.json()["skills"]

print(f"Found {len(skills)} skills:")
for skill in skills:
    print(f"  - {skill['name']}: {skill['description'][:50]}...")

# 2. Get details for a specific skill
skill_name = "github-push"
detail = requests.get(f"{API_URL}/api/v1/skills/{skill_name}", headers=headers).json()

print(f"\nSkill: {detail['name']}")
print(f"Files: {detail['total_files']}")
if detail['cross_dependencies']:
    print(f"⚠️  Cross-dependencies: {detail['cross_dependencies']}")

# 3. Download the skill
download = requests.get(
    f"{API_URL}/api/v1/skills/{skill_name}/download",
    headers=headers,
    stream=True
)

# Save to file
with open(f"{skill_name}.tar.gz", "wb") as f:
    for chunk in download.iter_content(chunk_size=8192):
        f.write(chunk)

print(f"\n✅ Downloaded {skill_name}.tar.gz")

# 4. Extract
tar = tarfile.open(f"{skill_name}.tar.gz", "r:gz")
tar.extractall()
tar.close()

print(f"✅ Extracted to ./{skill_name}/")
```

---

**Document Version**: 1.1  
**Last Updated**: 2026-02-19  
**API Version**: 1.1.0
