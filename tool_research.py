import csv
import os
from datetime import datetime, timedelta
import requests

TOPICS_FILE = "data/topics.csv"
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY", "")
GOOGLE_SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID", "")


def check_internet_for_recent_coverage(keyword, tool_name, days_back=7):
    """
    Check if a topic has been recently covered on the internet.
    Returns True if it was recently covered (skip it), False if safe to cover.

    Requires GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_ENGINE_ID env vars.
    If not set, returns False (assumes safe to proceed).
    """
    if not GOOGLE_SEARCH_API_KEY or not GOOGLE_SEARCH_ENGINE_ID:
        # API not configured - skip scanning, proceed with topic
        return False

    try:
        # Search for recent articles about this tool
        query = f'"{tool_name}" OR "{keyword}" -site:your-blog.com'  # Exclude your own blog

        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "q": query,
            "key": GOOGLE_SEARCH_API_KEY,
            "cx": GOOGLE_SEARCH_ENGINE_ID,
            "sort": "date",  # Sort by date (most recent first)
            "num": 5  # Check top 5 results
        }

        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()

        results = response.json().get("items", [])

        # Check if any result is from the last N days
        cutoff_date = datetime.now() - timedelta(days=days_back)

        for result in results:
            pub_date_str = result.get("pagemap", {}).get("metatags", [{}])[0].get("article:published_time")

            if pub_date_str:
                try:
                    pub_date = datetime.fromisoformat(pub_date_str.replace("Z", "+00:00"))
                    if pub_date > cutoff_date:
                        print(f"⚠️  Topic '{tool_name}' recently covered: {result.get('title')}")
                        return True  # Recently covered, skip it
                except ValueError:
                    pass

        return False  # Safe to proceed

    except Exception as e:
        print(f"⚠️  Internet scan failed ({tool_name}): {e} - proceeding anyway")
        return False  # On error, proceed (don't skip the topic)


def is_cooldown_active(topic):
    """Check if topic is still in cooldown period (can't be published again yet)"""
    last_published = topic.get("last_published", "")
    cooldown_days = int(topic.get("cooldown_days", 0))

    if not last_published or cooldown_days == 0:
        return False

    try:
        last_pub_date = datetime.strptime(last_published, "%Y-%m-%d")
        cooldown_end_date = last_pub_date + timedelta(days=cooldown_days)
        today = datetime.now()

        if today < cooldown_end_date:
            return True  # Still in cooldown
    except ValueError:
        return False

    return False


def get_ai_tool_topic():
    with open(TOPICS_FILE, newline="", encoding="utf-8") as file:
        topics = list(csv.DictReader(file))

    # Filter: topics that are marked as "unused" OR published but cooldown has expired
    available_topics = []

    for topic in topics:
        status = topic.get("status", "").lower()

        # Unused topics are available (but check internet coverage)
        if status == "unused":
            available_topics.append(topic)

        # Published topics can be re-used if cooldown expired
        elif status == "published":
            if not is_cooldown_active(topic):
                # Change status back to "unused" so it can be picked again
                topic["status"] = "unused"
                available_topics.append(topic)

    if not available_topics:
        raise Exception("No available topics. All topics are in cooldown period.")

    # Sort by priority (highest first)
    available_topics.sort(
        key=lambda x: int(x.get("priority", 0)),
        reverse=True
    )

    # Pick first topic that hasn't been recently covered on the internet
    for topic in available_topics:
        tool_name = topic.get("tool_name", "")
        keyword = topic.get("keyword", "")

        # Check if this topic was recently covered online
        if check_internet_for_recent_coverage(keyword, tool_name, days_back=7):
            print(f"⏭️  Skipping '{tool_name}' (recently covered online) → checking next priority")
            continue  # Skip and try the next one

        # Safe to use this topic
        return {
            "id": topic["id"],
            "title": topic["title"],
            "keyword": topic["keyword"],
            "tool_name": topic["tool_name"],
            "audience": topic.get("audience", "AI tool users"),
            "problem": topic["title"],
            "category": topic["category"],
            "cluster": topic.get("cluster", ""),
            "search_intent": topic.get("search_intent", ""),
            "difficulty": topic.get("difficulty", ""),
            "search_volume": topic.get("search_volume", ""),
            "affiliate_program": topic.get("affiliate_program", ""),
            "source": topic.get("source", "")
        }

    # If all topics were skipped due to recent coverage, raise error
    raise Exception("All available topics were recently covered online. Try again tomorrow.")
