import feedparser

RSS_FEEDS = [
    "http://feeds.feedburner.com/TechCrunch",
    "https://venturebeat.com/feed/",
    "https://www.artificialintelligence-news.com/feed/"
]

KEYWORDS = [
    "AI", "HR", "Talent Acquisition", "AI tools", "machine learning", "Agentic AI", "AI agents", "agentic"
]

def search_topic(topic_query: str, max_results: int = 5) -> list[dict]:
    """
    Parses RSS feeds and returns recent articles matching the topic query and general keywords.
    """
    print(f"Fetching RSS feeds for topic: {topic_query}")
    results = []
    
    # We add the specific topic query to the list of keywords to look for
    search_terms = KEYWORDS + [topic_query]
    # Convert to lowercase for case-insensitive matching
    search_terms = [term.lower() for term in search_terms]

    try:
        for feed_url in RSS_FEEDS:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                title = entry.get('title', '')
                snippet = entry.get('summary', '') or entry.get('description', '')
                link = entry.get('link', '')
                
                content_to_check = f"{title} {snippet}".lower()
                
                # Check if any of our keywords exist in the title or snippet
                if any(term in content_to_check for term in search_terms):
                    results.append({
                        "title": title,
                        "link": link,
                        "snippet": snippet
                    })
                    
                    if len(results) >= max_results:
                        return results
    except Exception as e:
        print(f"Error fetching RSS feeds: {e}")
    
    return results

if __name__ == "__main__":
    # Test
    res = search_topic("AI tools and breakthroughs")
    for r in res:
        print(r['title'])
