# TikTok-Scraper7 API Test Plan

## API Limit Constraints
- **10 requests/month** hard limit on free tier
- Must design tests to use minimum requests while verifying all requirements

---

## Viral Waves Data Requirements

### 1. Growth Rate Detection (Algorithm 1-4)
**Needs:**
- Video ID (unique identifier)
- Create timestamp (for velocity calculations)
- View counts over time (play_count)
- Like/share/comment counts

**API Endpoint:** `/user/story` or `/user/posts`

### 2. Niche Clustering (Algorithm 5)
**Needs:**
- Hashtags per video
- Sound/Music ID per video
- Author unique_id (for creator clustering)
- Video description/text

**API Endpoint:** `/user/story` (includes hashtags, music)

### 3. Trend Alerts (Multi-window analysis)
**Needs:**
- Multiple videos from same user
- Timestamps for each video
- Engagement metrics

**API Endpoint:** `/user/story` (returns multiple videos)

### 4. Cross-Niche Detection
**Needs:**
- Multiple users' content
- Same sound appearing across users
- Same hashtags across users

**API Endpoints:** Multiple `/user/story` calls (different user_ids)

---

## Test Strategy (Minimize API Calls)

### Test 1: Data Structure Inspection ✅ READY
**Script:** `tests/inspect_api_data.py`
**Uses:** 1 request
**Verifies:** 
- All required fields present
- Data types correct
- Sufficient fields for algorithms

**Run:**
```bash
cd /root/trendscope
source .venv/bin/activate
python tests/inspect_api_data.py
```

### Test 2: Trending Endpoint Test (PENDING)
**Script:** (to create after Test 1 passes)
**Uses:** 1 request
**Verifies:**
- Can get trending/hashtag data
- Returns videos from multiple users

**Endpoint to find:** Look for `/trending`, `/feed`, or `/discover`

### Test 3: Video Detail Test (PENDING)
**Script:** (to create after Test 1 passes)
**Uses:** 1 request
**Verifies:**
- Can get specific video by ID
- Returns full metadata

**Endpoint to find:** Look for `/video/info` or `/video/detail`

---

## Decision Matrix

### If Test 1 (Data Structure) Passes:
✅ API has required fields for Viral Waves
→ Proceed to Test 2

### If Test 2 (Trending) Passes:
✅ Can get discovery feed
→ API is viable for trend detection
→ Check pricing and subscribe

### If Test 3 (Video Detail) Passes:
✅ Can get specific video metadata
→ Complete solution verified

---

## API Endpoints to Test (in order)

1. ✅ `/user/story` - Get user's videos (TESTED - WORKS)
2. ❓ `/trending` or `/feed` - Get trending content (NEED TO FIND)
3. ❓ `/hashtag` - Get videos by hashtag (NEED TO FIND)
4. ❓ `/video/info` - Get video details (NEED TO FIND)
5. ❓ `/user/info` - Get user profile (NEED TO FIND)

---

## Current Status

| Test | Status | Requests Used |
|------|--------|---------------|
| Basic connectivity | ✅ PASS | 1 |
| Data structure inspection | ⏳ READY | 0 (will use 1) |
| Trending endpoint | ⏳ PENDING | 0 |
| Video detail endpoint | ⏳ PENDING | 0 |
| **Total remaining** | | **9/10** |

---

## Next Steps

1. **Run Test 1** (`inspect_api_data.py`) - Uses 1 request
2. **Analyze results** - Check if all required fields present
3. **If Test 1 passes** - Find trending/hashtag endpoints in RapidAPI dashboard
4. **Test trending** - Verify can get discovery data
5. **Decision point** - Subscribe if all tests pass

---

## Alternative: Manual Dashboard Testing

Since API limit is tight (10/month), also test in RapidAPI dashboard:

1. Find all available endpoints
2. Test each with "Test Endpoint" button (doesn't count against limit!)
3. Document which endpoints return what data
4. Only use API requests for final verification

**Dashboard URL:** https://rapidapi.com/tiktok-scraper7/endpoints

---

## Risk Mitigation

If API limit is exceeded:
- Use self-hosted as backup ($27-55/month)
- Try Apify ($90-450/month)
- Wait for next month's quota

---

*Test plan designed for 10 request/month limit*
