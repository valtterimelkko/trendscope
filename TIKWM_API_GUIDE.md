# TikWM API Testing Guide

**Status:** API appears functional (returns proper errors, not empty responses)

---

## ✅ What We Know Works

### API Responds Properly
Unlike JoTucker (which returned empty data), TikWM returns:
- ✅ **Error messages** (e.g., "unique_id is invalid")
- ✅ **HTTP 200** with JSON response
- ✅ **Proper error codes** (code: -1 for errors)

This is a **good sign** - the API is working!

---

## 🔍 Parameter Confusion Explained

### TikTok Terminology

| Term | What It Is | Example |
|------|-----------|---------|
| **unique_id** | Username (with or without @) | `sportbible`, `charlidamelio` |
| **video_id** | The number from video URL | `7607868135865060630` |
| **sec_uid** | Internal TikTok user ID | `MS4wLjABAAAA...` |

### Your Test
You used `7607868135865060630` (video ID) in the `unique_id` field (expects username).

That's why you got: `"msg":"unique_id is invalid"`

---

## 🧪 How to Test Correctly

### Step 1: Find the Right Endpoint

In RapidAPI dashboard:
1. Go to https://rapidapi.com/tikwm-tikwm-default/api/tikwm
2. Look at the **Endpoints** tab
3. Find endpoints like:
   - `GET /api/user/info` - for user data
   - `GET /api/feed/info` - for video data
   - `GET /api/user/posts` - for user's videos

### Step 2: Use Correct Parameters

**For User Info:**
```
Parameter: unique_id
Value: sportbible (NOT the video ID!)
```

**For Video Info:**
```
Parameter: url
Value: https://www.tiktok.com/@sportbible/video/7607868135865060630
```

**For User's Videos:**
```
Parameter: unique_id
Value: sportbible
Parameter: count
Value: 10
```

---

## ⚠️ Rate Limits

TikWM free tier likely has:
- **Per-day limit** (probably 20-100 requests)
- **Per-minute limit** (probably 5-10 requests)

We hit `429 Too many requests` - need to wait a few minutes between tests.

---

## 🎯 Recommended Testing Strategy

### Test 1: User Info (wait 2 minutes first)
```
Endpoint: /api/user/info
unique_id: sportbible
```

**Expected success response:**
```json
{
  "code": 0,
  "data": {
    "user": {
      "nickname": "Sportbible",
      "unique_id": "sportbible",
      "follower_count": 1234567
    }
  }
}
```

### Test 2: Video Info (wait 2 more minutes)
```
Endpoint: /api/feed/info
url: https://www.tiktok.com/@sportbible/video/7607868135865060630
```

**Expected success response:**
```json
{
  "code": 0,
  "data": {
    "title": "Video description...",
    "play_count": 123456,
    "digg_count": 5678
  }
}
```

---

## 💰 TikWM Pricing

| Plan | Cost | Requests |
|------|------|----------|
| **Free** | $0 | Limited (likely 20-100/day) |
| **Basic** | ~$5-10/month | Higher limits |
| **Pro** | ~$20-50/month | Much higher limits |

**Recommendation:** Test thoroughly on free tier before subscribing.

---

## ✅ Why This API is Better Than JoTucker

| Aspect | JoTucker | TikWM |
|--------|----------|-------|
| Error messages | ❌ None (empty responses) | ✅ Clear error messages |
| Example data | ❌ Fake (hardcoded) | ✅ Unknown (need to test) |
| API structure | ❌ Unclear | ✅ Proper JSON with codes |
| Trust level | 🚩 Broken | ⚠️ Needs more testing |

---

## 🚀 Next Steps

1. **Wait 5 minutes** (rate limit cooldown)
2. **Test user info endpoint** with `unique_id: sportbible`
3. **If that works** → Test video endpoint
4. **If both work** → This is a viable API!
5. **Check pricing** → Subscribe to appropriate tier

---

## 📝 Current Status

- **API appears functional:** ✅ Yes (proper error responses)
- **Need to verify data quality:** ⏳ Pending
- **Rate limits are strict:** ⚠️ Yes (need to space out tests)
- **Worth further testing:** ✅ Yes

*This API shows promise unlike JoTucker. Test carefully before subscribing.*
