import json
import os
from datetime import datetime, timedelta

MEMORY_FILE = os.path.join(os.path.dirname(__file__), "memory.json")

DEFAULT_WEIGHTS = {
    "AI tools and breakthroughs": 0.40,
    "AI in Human Resources": 0.25,
    "New AI product launches": 0.20,
    "AI in Talent Acquisition": 0.15
}

def init_memory():
    """Initializes the local memory JSON file if it doesn't exist."""
    if not os.path.exists(MEMORY_FILE):
        data = {
            "posts": [],
            "topic_weights": DEFAULT_WEIGHTS
        }
        with open(MEMORY_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    else:
        # Read and ensure topic_weights is there
        data = load_memory()
        if "topic_weights" not in data:
            data["topic_weights"] = DEFAULT_WEIGHTS
            save_memory(data)

def load_memory() -> dict:
    if not os.path.exists(MEMORY_FILE):
        init_memory()
    with open(MEMORY_FILE, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            # Re-initialize if corrupted
            init_memory()
            return load_memory()

def save_memory(data: dict):
    with open(MEMORY_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def log_post(category: str, content: str, post_urn: str = None, image_path: str = None, asset_urn: str = None):
    """Logs a new post to the local memory."""
    data = load_memory()
    date_str = datetime.now().isoformat()
    new_post = {
        "date": date_str,
        "category": category,
        "content": content,
        "likes": 0,
        "comments": 0,
        "engagement_score": 0,
        "replied_comments": [],
        "post_urn": post_urn,
        "image_path": image_path,
        "asset_urn": asset_urn
    }
    data["posts"].append(new_post)
    save_memory(data)

def update_post_metrics(scraped_content: str, likes: int, comments: int) -> bool:
    """
    Finds a post matching the scraped content and updates its metrics.
    Returns True if a match was found.
    """
    data = load_memory()
    found = False
    # Clean text to make comparison robust against minor spacing differences
    scraped_clean = "".join(scraped_content.split())[:100].lower()
    
    for post in data.get("posts", []):
        stored_clean = "".join(post["content"].split())[:100].lower()
        
        if stored_clean in scraped_clean or scraped_clean in stored_clean:
            post["likes"] = likes
            post["comments"] = comments
            post["engagement_score"] = likes + (comments * 2)
            if "replied_comments" not in post:
                post["replied_comments"] = []
            found = True
            break
    if found:
        save_memory(data)
    return found

def add_replied_comment(scraped_content: str, comment_sig: str):
    """Logs that a comment has been replied to for a given post."""
    data = load_memory()
    scraped_clean = "".join(scraped_content.split())[:100].lower()
    for post in data.get("posts", []):
        stored_clean = "".join(post["content"].split())[:100].lower()
        if stored_clean in scraped_clean or scraped_clean in stored_clean:
            if "replied_comments" not in post:
                post["replied_comments"] = []
            if comment_sig not in post["replied_comments"]:
                post["replied_comments"].append(comment_sig)
            break
    save_memory(data)

def can_post_category(category: str, days: int = 3) -> bool:
    """Checks if the category was posted in the last N days (defaults to 3 days to avoid deadlocks)."""
    data = load_memory()
    cooldown_period = datetime.now() - timedelta(days=days)
    
    for post in data.get("posts", []):
        if post.get("category") == category:
            try:
                post_date = datetime.fromisoformat(post.get("date"))
                if post_date > cooldown_period:
                    return False
            except ValueError:
                pass
    return True

def get_least_recently_posted_category() -> str:
    """Finds the category that was posted least recently among the default weights."""
    data = load_memory()
    categories = list(DEFAULT_WEIGHTS.keys())
    
    # Track the last post date for each category
    last_post_dates = {}
    for cat in categories:
        last_post_dates[cat] = datetime.min
        
    for post in data.get("posts", []):
        cat = post.get("category")
        if cat in last_post_dates:
            try:
                post_date = datetime.fromisoformat(post.get("date"))
                if post_date > last_post_dates[cat]:
                    last_post_dates[cat] = post_date
            except ValueError:
                pass
                
    # Sort categories by date ascending (oldest first)
    sorted_categories = sorted(categories, key=lambda c: last_post_dates[c])
    return sorted_categories[0]

def get_topic_weights() -> dict:
    """Returns the current topic weights from memory."""
    data = load_memory()
    return data.get("topic_weights", DEFAULT_WEIGHTS)

def adjust_posting_weights():
    """
    Analyzes the engagement of categories and adjusts weights.
    Triggered when total posts >= 10.
    """
    data = load_memory()
    posts = data.get("posts", [])
    if len(posts) < 10:
        print(f"Only {len(posts)} posts in memory. Skipping weight adjustment until 10 posts are reached.")
        return
    
    # Calculate average engagement for all posts first
    total_engagement = sum(p.get("engagement_score", 0) for p in posts)
    overall_avg = total_engagement / len(posts) if posts else 1.0
    if overall_avg < 1.0:
        overall_avg = 1.0
        
    categories = list(DEFAULT_WEIGHTS.keys())
    category_scores = {cat: [] for cat in categories}
    
    for p in posts:
        cat = p.get("category")
        if cat in category_scores:
            category_scores[cat].append(p.get("engagement_score", 0))
            
    # Compute average score per category
    avg_scores = {}
    for cat in categories:
        scores = category_scores[cat]
        if scores:
            avg_scores[cat] = sum(scores) / len(scores)
        else:
            avg_scores[cat] = overall_avg # Assign overall average to unposted categories
            
    # Compute sum of all category averages
    sum_averages = sum(avg_scores.values())
    if sum_averages == 0:
        sum_averages = 1.0
        
    # Compute performance-based weights
    perf_weights = {cat: avg_scores[cat] / sum_averages for cat in categories}
    
    # Blend with baseline weights: 50% baseline, 50% performance
    new_weights = {}
    for cat in categories:
        new_weights[cat] = round(0.5 * DEFAULT_WEIGHTS[cat] + 0.5 * perf_weights[cat], 4)
        
    # Normalize to ensure sum is exactly 1.0 (due to rounding)
    total_weight = sum(new_weights.values())
    if total_weight > 0:
        for cat in categories:
            new_weights[cat] = round(new_weights[cat] / total_weight, 4)
            
    data["topic_weights"] = new_weights
    save_memory(data)
    print(f"Adjusted posting weights successfully: {new_weights}")

if __name__ == "__main__":
    init_memory()
