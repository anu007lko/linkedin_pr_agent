import random
import time
import schedule
from search_agent import search_topic
from content_generator import generate_linkedin_post, generate_post_image
from linkedin_api import post_to_linkedin
from memory_manager import init_memory, can_post_category, log_post, get_topic_weights, adjust_posting_weights, load_memory
from notifier import send_notification

def pick_topic() -> str:
    """Picks a topic based on defined probabilities stored in memory."""
    weights_dict = get_topic_weights()
    topics = list(weights_dict.keys())
    probabilities = list(weights_dict.values())
    return random.choices(topics, weights=probabilities, k=1)[0]

def job(specific_topic=None):
    """The main daily job that orchestrates the agent."""
    print(f"Starting LinkedIn PR Agent job... (Topic: {specific_topic or 'Dynamic Mix'})")
    
    selected_topic = specific_topic
    
    if not selected_topic:
        # Try up to 10 times to find a topic that hasn't been posted in the last 7 days
        for _ in range(10):
            topic = pick_topic()
            if can_post_category(topic):
                selected_topic = topic
                break
                
    if not selected_topic:
        msg = "Could not find a valid topic that hasn't been posted in the last 7 days. Skipping today."
        print(msg)
        send_notification("LinkedIn Agent: Skipped", msg)
        return

    # Check memory even if specific topic is provided to respect the 7-day rule
    if specific_topic and not can_post_category(selected_topic):
        msg = f"Warning: '{selected_topic}' was posted within the last 7 days. Skipping today to adhere to rules."
        print(msg)
        send_notification("LinkedIn Agent: Skipped", msg)
        return

    print(f"Selected Topic: {selected_topic}")
    
    # 1. Search Web
    if selected_topic == "Agent Announcement":
        print("Special Topic: Agent Announcement. Bypassing news search.")
        search_results = [{"title": "Agent Launch", "snippet": "", "link": ""}]
    else:
        print("Searching for latest news...")
        search_results = search_topic(selected_topic)
    
    if not search_results:
        msg = f"Search failed for topic '{selected_topic}'. Skipping."
        print(msg)
        send_notification("LinkedIn Agent: Error", msg)
        return

    # 2. Generate Post
    print("Generating post...")
    post_content = generate_linkedin_post(selected_topic, search_results)
    
    if not post_content:
        msg = "Post generation failed. Skipping."
        print(msg)
        send_notification("LinkedIn Agent: Error", msg)
        return
        
    print(f"Generated Post:\n{post_content}\n")

    # 3. Generate Image
    print("Generating post image...")
    image_path = generate_post_image(post_content)
    if image_path:
        print(f"Post image generated at: {image_path}")
    else:
        print("No image generated (or generation failed). Proceeding with text-only.")

    # 4. Post to LinkedIn
    print("Posting to LinkedIn...")
    post_urn, asset_urn = post_to_linkedin(post_content, image_path)
    
    if post_urn:
        # 5. Log to Memory
        print("Logging to local memory...")
        log_post(selected_topic, post_content, post_urn, image_path, asset_urn)
        
        # 6. Notify
        notification_body = (
            f"Topic: {selected_topic}\n"
            f"URN: {post_urn}\n"
            f"Asset URN: {asset_urn or 'None (Text Only)'}\n"
            f"Local Image Path: {image_path or 'None'}\n\n"
            f"Content:\n{post_content}"
        )
        send_notification(
            subject="LinkedIn Agent: Successfully Posted", 
            body=notification_body
        )
        print("Job complete.")
    else:
        msg = "Failed to post to LinkedIn. Check logs."
        print(msg)
        send_notification("LinkedIn Agent: Error", msg)


def send_weekly_report_job():
    """Sends a weekly summary of the performance of the posts."""
    print("Generating and sending weekly performance report...")
    data = load_memory()
    posts = data.get("posts", [])
    weights = data.get("topic_weights", {})
    
    # Generate report
    report_lines = [
        "LinkedIn PR Agent - Weekly Performance Report",
        "============================================",
        f"Total posts tracked: {len(posts)}",
        "",
        "Topic Frequency Weights (Posting Probability):",
    ]
    for topic, w in weights.items():
        report_lines.append(f" - {topic}: {w * 100:.2f}%")
        
    report_lines.append("")
    report_lines.append("Category Performance Summary:")
    
    # Category metrics
    categories = list(weights.keys())
    cat_stats = {cat: {"count": 0, "likes": 0, "comments": 0, "engagement": 0} for cat in categories}
    for p in posts:
        cat = p.get("category")
        if cat in cat_stats:
            cat_stats[cat]["count"] += 1
            cat_stats[cat]["likes"] += p.get("likes", 0)
            cat_stats[cat]["comments"] += p.get("comments", 0)
            cat_stats[cat]["engagement"] += p.get("engagement_score", 0)
            
    for cat in categories:
        stats = cat_stats[cat]
        avg_eng = stats["engagement"] / stats["count"] if stats["count"] > 0 else 0
        report_lines.append(f" - {cat}:")
        report_lines.append(f"   * Total posts: {stats['count']}")
        report_lines.append(f"   * Total likes: {stats['likes']}")
        report_lines.append(f"   * Total comments: {stats['comments']}")
        report_lines.append(f"   * Avg engagement: {avg_eng:.2f}")
        
    report_lines.append("")
    report_lines.append("Recent Posts Log:")
    # Show last 7 posts
    for idx, p in enumerate(reversed(posts[-7:]), 1):
        report_lines.append(f" {idx}. Date: {p.get('date')[:10]}")
        report_lines.append(f"    Category: {p.get('category')}")
        report_lines.append(f"    Likes: {p.get('likes')}, Comments: {p.get('comments')} (Engagement: {p.get('engagement_score')})")
        report_lines.append(f"    Content: {p.get('content')[:120]}...")
        report_lines.append("")
        
    body = "\n".join(report_lines)
    send_notification("LinkedIn Agent: Weekly Performance Report", body)
    print("Weekly report sent successfully.")

def start_scheduler():
    """Sets up the schedule and runs it in an infinite loop."""
    print("Setting up schedule...")
    
    # Daily Posting Schedule
    # Times are in UTC (Cloud VM timezone). EST = UTC-4, so add 4 hours to convert.
    # Mon 9:00 AM EST  = 13:00 UTC
    # Tue 12:00 PM EST = 16:00 UTC
    # Wed 9:00 AM EST  = 13:00 UTC
    # Thu 12:00 PM EST = 16:00 UTC
    # Fri 9:00 AM EST  = 13:00 UTC
    schedule.every().monday.at("13:00").do(job)
    schedule.every().tuesday.at("16:00").do(job)
    schedule.every().wednesday.at("13:00").do(job)
    schedule.every().thursday.at("16:00").do(job)
    schedule.every().friday.at("13:00").do(job)

    # Weekly Summary Performance Email (Sunday 6:00 PM EST = 22:00 UTC)
    schedule.every().sunday.at("22:00").do(send_weekly_report_job)
    
    print("Scheduler is running. Press Ctrl+C to exit. Agent is now fully autonomous.")
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    init_memory()
    
    # Check if "Agent Announcement" has already been posted
    data = load_memory()
    has_announced = any(p.get("category") == "Agent Announcement" for p in data.get("posts", []))
    
    if not has_announced:
        print("First-time run: Generating and publishing the 'Agent Announcement' post immediately...")
        try:
            job(specific_topic="Agent Announcement")
            time.sleep(30)
        except Exception as e:
            print(f"Failed to post Agent Announcement on startup: {e}")
            
        
    start_scheduler()
