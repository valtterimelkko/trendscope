# RapidAPI / JoTucker TikTok Scraper Test Results

**Date:** 2026-02-17  
**API Key:** Configured in `.env`  
**Free Tier Limit:** 20 requests/day

---

## ✅ Test Summary

| Test | Endpoint | Status | Requests Used |
|------|----------|--------|---------------|
| 1 | video/info_v2 | ⚠️ 204 No Content | 1/20 |
| 2 | feed/list | ❌ 404 Not Found | 1/20 |
| 3 | user/info | ✅ 200 OK (empty) | 1/20 |
| **Total** | | | **3/20** |

**Remaining:** 17 requests today

---

## 🔑 Configuration Added to `.env`

```bash
# RapidAPI / JoTucker TikTok Scraper Credentials
RAPIDAPI_KEY=8710e2cdb1msh72b30bdecb99b5bp1fb537jsn33825799b519
RAPIDAPI_HOST=tiktok-scraper2.p.rapidapi.com

# Free Tier Limits:
# - 20 requests per day
# - 1,000 requests per hour (when on paid tier)
```

---

## 🧪 Test Results

### Test 1: Video Info Endpoint
```
URL: /video/info_v2
Video: @tiktok/video/6974862859000073478
Status: 204 No Content
```

**Analysis:** The video ID may be invalid or the video was deleted. The API is responding but has no data for this video.

---

### Test 2: Trending Feed Endpoint
```
URL: /feed/list
Status: 404 Not Found
Response: {"message":"Endpoint '\/feed\/list' does not exist"}
```

**Analysis:** This endpoint doesn't exist in the API. Need to check the correct endpoint in RapidAPI dashboard.

---

### Test 3: User Info Endpoint
```
URL: /user/info
User: charlidamelio
Status: 200 OK
Response Size: 2 bytes (empty JSON)
```

**Analysis:** API key is valid and authenticated. Empty response may indicate:
- Free tier data limitations
- User not found
- Different parameter format needed

---

## ✅ What's Confirmed Working

1. **API Key Valid:** ✅ Responds with 200/204 (not 401 Unauthorized)
2. **Rate Limits:** ✅ 3 requests made, no 429 errors
3. **Authentication:** ✅ Headers accepted correctly

---

## 🔍 Next Steps to Verify Full Functionality

### Option 1: Check RapidAPI Dashboard
1. Visit: https://rapidapi.com/JoTucker/api/tiktok-scraper2/endpoints
2. Find the correct endpoint URLs
3. Test in their web interface (doesn't count against quota)

### Option 2: Try Different Parameters
Common parameter variations to test:
```python
# Try with sec_uid instead of user_id
params = {"sec_uid": "MS4wLjABAAAA...