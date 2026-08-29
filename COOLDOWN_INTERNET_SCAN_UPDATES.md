# 🔄 Cooldown & Internet Scanning Updates

## What Changed

### 1. **Cooldown Logic** ✅
Topics now respect their `cooldown_days` setting. Once published, a topic won't be selected again until the cooldown period expires.

**How it works:**
- Each topic in `data/topics.csv` has a `cooldown_days` value (e.g., 30, 60, 90)
- After publishing, the `last_published` date is recorded
- The system won't pick that topic again until `today >= last_published + cooldown_days`
- Once cooldown expires, the topic automatically becomes available again

**Example:**
```
Topic: ChatGPT
Last Published: 2026-08-29
Cooldown Days: 60
Available Again: 2026-10-28
```

### 2. **Internet Scanning** ✅
The system now checks if a topic has been recently covered on the internet before writing about it.

**How it works:**
- Uses Google Custom Search API to scan the internet
- Checks if any competitor/major site wrote about the same tool in the last 7 days
- If found, **skips that topic** and picks the next highest priority one
- If API is not configured, skips scanning and proceeds (safe default)

**What it searches for:**
```
"{tool_name}" OR "{keyword}" -site:your-blog.com
```
Excludes your own blog to avoid false positives.

**Requires Setup:**
```bash
GOOGLE_SEARCH_API_KEY=your-api-key
GOOGLE_SEARCH_ENGINE_ID=your-cse-id
```

Get these free from: https://programmablesearchengine.google.com/

---

## Code Changes

### `tool_research.py`

**Added functions:**
```python
def check_internet_for_recent_coverage(keyword, tool_name, days_back=7)
    # Scans internet for recent coverage
    # Returns: True if recently covered (skip), False if safe
    
def is_cooldown_active(topic)
    # Checks if cooldown period is still active
    # Returns: True if in cooldown, False if safe to use
```

**Modified function:**
```python
def get_ai_tool_topic()
    # Now filters topics by:
    # 1. Marks "published" topics as "unused" if cooldown expired
    # 2. Scans internet for recent coverage before selecting
    # 3. Skips topics if recently covered online
    # 4. Returns first safe topic by priority
```

---

## Usage

### Scenario 1: Cooldown Working
```
Workflow runs: 2026-08-29
Topic "ChatGPT" published 60 days ago (2026-06-29)
Cooldown = 60 days
Status: ✅ Available (can pick again)

Topic "Midjourney" published 10 days ago (2026-08-19)
Cooldown = 30 days
Status: ❌ In cooldown (skip, pick next)
```

### Scenario 2: Internet Scanning
```
Workflow tries to pick: "ChatGPT How to Use"
Internet scan finds: 3 recent articles from Aug 28-29
Status: ⏭️ Skipped (too recent online)
Picks next: "MidJourney Advanced Tips" (not recently covered)
```

---

## Configuration

### Optional: Enable Internet Scanning

1. **Get Google Custom Search API:**
   - Visit: https://programmablesearchengine.google.com/
   - Create a custom search engine for your niches
   - Get `Search Engine ID`

2. **Get Google API Key:**
   - Visit: https://console.cloud.google.com/
   - Create API key
   - Enable "Custom Search API"

3. **Add to GitHub Secrets:**
   ```
   GOOGLE_SEARCH_API_KEY=your-api-key
   GOOGLE_SEARCH_ENGINE_ID=your-cse-id
   ```

4. **Update workflow (`.github/workflows/daily-ai-tools.yml`):**
   ```yaml
   env:
     GOOGLE_SEARCH_API_KEY: ${{ secrets.GOOGLE_SEARCH_API_KEY }}
     GOOGLE_SEARCH_ENGINE_ID: ${{ secrets.GOOGLE_SEARCH_ENGINE_ID }}
   ```

### If NOT using Internet Scanning
- Leave the env vars unset
- The code gracefully skips scanning and proceeds (safe default)

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| All topics in cooldown | ❌ Error: "No available topics..." |
| All topics recently covered | ❌ Error: "All topics recently covered... try tomorrow" |
| Internet scan fails | ⚠️ Warning logged, proceeds anyway |
| API keys missing | ✅ Skips scan, proceeds with topic |

---

## Logs You'll See

```
✅ Syntax OK
⏭️  Skipping 'ChatGPT' (recently covered online) → checking next priority
✅ Selected 'MidJourney' - safe to publish
⚠️  Topic 'Llama' recently covered: https://example.com/...
⚠️  Internet scan failed (OpenAI): timeout - proceeding anyway
```

---

## Testing Locally

```bash
# Test cooldown logic
python3 tool_research.py

# Test with internet scanning (if API keys set)
export GOOGLE_SEARCH_API_KEY="your-key"
export GOOGLE_SEARCH_ENGINE_ID="your-id"
python3 tool_research.py
```

---

## Next Steps

1. **Update `data/topics.csv`** - Ensure all topics have valid `cooldown_days` values
2. **(Optional) Setup Google API** - For internet scanning
3. **Update GitHub Secrets** - Add API keys to GitHub
4. **Test the workflow** - Run manually: GitHub → Actions → "Daily AI Tools" → "Run workflow"
5. **Monitor logs** - Check workflow logs to see cooldown & scanning in action

---

## Benefits

✅ **No duplicate publishing** - Cooldown ensures spacing between topics  
✅ **Stay unique** - Internet scan avoids recently covered topics  
✅ **SEO friendly** - Publishes on less-saturated topics  
✅ **Better reach** - Timing avoids direct competition  
✅ **Automatic** - Runs daily, requires no manual checking  

