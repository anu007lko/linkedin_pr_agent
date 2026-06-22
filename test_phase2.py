import sys
import os
import json

# Add project path to python search path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_dir)

from memory_manager import init_memory, adjust_posting_weights, load_memory, save_memory, get_topic_weights
from content_generator import generate_reply, generate_post_image
from main import send_weekly_report_job
import config

# Set CWD to the project folder so it reads memory.json from there
os.chdir(project_dir)
config.GROQ_API_KEY = "test_groq_key"
config.UNSPLASH_ACCESS_KEY = "test_unsplash_key"


def test_weight_adjustment():
    print("--- Testing Weight Adjustment ---")
    memory_path = "memory.json"
    backup_path = "memory.json.bak"
    has_backup = False
    if os.path.exists(memory_path):
        os.rename(memory_path, backup_path)
        has_backup = True
        
    try:
        init_memory()
        
        mock_posts = [
            {"date": "2026-06-01T09:00:00", "category": "AI tools and breakthroughs", "content": "Post 1 content", "likes": 50, "comments": 10, "engagement_score": 70},
            {"date": "2026-06-02T09:00:00", "category": "AI tools and breakthroughs", "content": "Post 2 content", "likes": 40, "comments": 8, "engagement_score": 56},
            {"date": "2026-06-03T09:00:00", "category": "AI in Human Resources", "content": "Post 3 content", "likes": 20, "comments": 2, "engagement_score": 24},
            {"date": "2026-06-04T09:00:00", "category": "AI in Human Resources", "content": "Post 4 content", "likes": 15, "comments": 3, "engagement_score": 21},
            {"date": "2026-06-05T09:00:00", "category": "New AI product launches", "content": "Post 5 content", "likes": 5, "comments": 0, "engagement_score": 5},
            {"date": "2026-06-06T09:00:00", "category": "New AI product launches", "content": "Post 6 content", "likes": 7, "comments": 1, "engagement_score": 9},
            {"date": "2026-06-07T09:00:00", "category": "AI in Talent Acquisition", "content": "Post 7 content", "likes": 12, "comments": 2, "engagement_score": 16},
            {"date": "2026-06-08T09:00:00", "category": "AI in Talent Acquisition", "content": "Post 8 content", "likes": 10, "comments": 1, "engagement_score": 12},
            {"date": "2026-06-09T09:00:00", "category": "AI tools and breakthroughs", "content": "Post 9 content", "likes": 30, "comments": 5, "engagement_score": 40},
            {"date": "2026-06-10T09:00:00", "category": "AI in Human Resources", "content": "Post 10 content", "likes": 18, "comments": 2, "engagement_score": 22}
        ]
        
        data = load_memory()
        data["posts"] = mock_posts
        save_memory(data)
        
        print("Initial weights:", get_topic_weights())
        adjust_posting_weights()
        adjusted = get_topic_weights()
        print("Adjusted weights:", adjusted)
        
        assert adjusted["AI tools and breakthroughs"] > adjusted["New AI product launches"], "AI tools should have higher weight than launches"
        print("Assert passed: AI tools weight is higher than new launches.")
        
        print("\n--- Testing Weekly Report Generation ---")
        send_weekly_report_job()
        print("Weekly report job executed.")
        
    finally:
        if os.path.exists(memory_path):
            os.remove(memory_path)
        if has_backup:
            os.rename(backup_path, memory_path)

from unittest.mock import patch, MagicMock

def test_groq_reply():
    print("\n--- Testing LLM Reply Generation (Mocked) ---")
    post_text = "AI agents are revolutionizing the workspace by automating administrative tasks, allowing human employees to focus on creative strategy."
    comment_text = "Agreed, but do you think this will lead to major job displacements soon?"
    
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{
            "message": {
                "content": "This is a mocked reply from Groq."
            }
        }]
    }
    
    with patch("content_generator.requests.post", return_value=mock_resp) as mock_post:
        reply = generate_reply(post_text, comment_text)
        assert mock_post.called
        assert reply == "This is a mocked reply from Groq."
        print(f"Generated reply:\n'{reply}'")
        print("Success: Reply generated and verified.")

def test_generate_post_image():
    print("\n--- Testing Post Image Generation via Unsplash (Mocked) ---")
    mock_groq_resp = MagicMock()
    mock_groq_resp.status_code = 200
    mock_groq_resp.json.return_value = {
        "choices": [{
            "message": {
                "content": "artificial intelligence, HR workspace"
            }
        }]
    }
    
    mock_search_resp = MagicMock()
    mock_search_resp.status_code = 200
    mock_search_resp.json.return_value = {
        "results": [
            {
                "id": "mocked_photo_id",
                "urls": {
                    "full": "https://api.unsplash.com/mocked_image_download_url"
                }
            }
        ]
    }
    
    mock_download_resp = MagicMock()
    mock_download_resp.status_code = 200
    mock_download_resp.content = b"fake Unsplash image bytes"
    
    def mock_requests_selector(url, *args, **kwargs):
        if "api.groq.com" in url:
            return mock_groq_resp
        elif "mocked_image_download_url" in url:
            return mock_download_resp
        elif "api.unsplash.com" in url:
            return mock_search_resp
        return MagicMock(status_code=404)
        
    with patch("content_generator.requests.post", side_effect=mock_requests_selector), \
         patch("content_generator.requests.get", side_effect=mock_requests_selector):
        
        img_path, unsplash_id = generate_post_image("Test post text content for imaging")
        expected_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads", "linkedin_post_image.jpg")
        assert img_path == expected_path
        assert unsplash_id == "mocked_photo_id"
        assert os.path.exists(img_path)
        with open(img_path, "rb") as f:
            assert f.read() == b"fake Unsplash image bytes"
        print(f"Success: Unsplash image searched, selected, and downloaded to {img_path}")

if __name__ == "__main__":
    test_weight_adjustment()
    test_groq_reply()
    test_generate_post_image()

