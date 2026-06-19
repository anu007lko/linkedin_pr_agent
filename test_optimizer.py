import sys
import os
import json
from unittest.mock import patch, MagicMock

# Add project path to python search path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_dir)

from memory_manager import init_memory, load_memory, save_memory, get_style_guidelines
from content_optimizer import optimize_style_guidelines

# Set CWD to project folder
os.chdir(project_dir)

def test_optimizer_flow():
    print("--- Testing Content Optimizer Loop ---")
    memory_path = "memory.json"
    backup_path = "memory.json.bak"
    has_backup = False
    if os.path.exists(memory_path):
        os.rename(memory_path, backup_path)
        has_backup = True
        
    try:
        init_memory()
        
        # Populate with 10 mock posts with varying engagement
        mock_posts = [
            {"date": "2026-06-01T09:00:00", "category": "AI tools and breakthroughs", "content": "Visual hooks drive maximum conversion.", "likes": 100, "comments": 20, "engagement_score": 140},
            {"date": "2026-06-02T09:00:00", "category": "AI tools and breakthroughs", "content": "Case study of automation success.", "likes": 90, "comments": 15, "engagement_score": 120},
            {"date": "2026-06-03T09:00:00", "category": "AI in Human Resources", "content": "Simple post about recruiter tips.", "likes": 5, "comments": 0, "engagement_score": 5},
            {"date": "2026-06-04T09:00:00", "category": "AI in Human Resources", "content": "Uninformative summary of generic news.", "likes": 2, "comments": 0, "engagement_score": 2},
            {"date": "2026-06-05T09:00:00", "category": "New AI product launches", "content": "Announcement of a new LLM model launch.", "likes": 50, "comments": 10, "engagement_score": 70},
            {"date": "2026-06-06T09:00:00", "category": "New AI product launches", "content": "Boring product feature list.", "likes": 4, "comments": 1, "engagement_score": 6},
            {"date": "2026-06-07T09:00:00", "category": "AI in Talent Acquisition", "content": "Recruiting agency stats and hire metrics.", "likes": 80, "comments": 12, "engagement_score": 104},
            {"date": "2026-06-08T09:00:00", "category": "AI in Talent Acquisition", "content": "Generic job search advice.", "likes": 10, "comments": 1, "engagement_score": 12},
            {"date": "2026-06-09T09:00:00", "category": "AI tools and breakthroughs", "content": "Detailed analysis of transformer architectures.", "likes": 110, "comments": 25, "engagement_score": 160},
            {"date": "2026-06-10T09:00:00", "category": "AI in Human Resources", "content": "Standard compliance list post.", "likes": 8, "comments": 1, "engagement_score": 10}
        ]
        
        data = load_memory()
        data["posts"] = mock_posts
        save_memory(data)
        
        # Mock LLM response representing the Dos and Don'ts JSON format
        mock_llm_json = {
            "dos": [
                "Use specific case study metrics",
                "Highlight visual hook frameworks",
                "Write deep-dive technical analysis"
            ],
            "donts": [
                "Avoid boring bullet point feature lists",
                "Do not post compliance rules",
                "Avoid general advice without data"
            ]
        }
        
        mock_llm_resp = json.dumps(mock_llm_json)
        
        # Patch the LLM calls to return our mock response
        with patch("content_optimizer._call_groq", return_value=mock_llm_resp) as mock_groq:
            optimize_style_guidelines()
            assert mock_groq.called
            
            # Verify guidelines were saved correctly
            guidelines = get_style_guidelines()
            assert len(guidelines["dos"]) == 3
            assert len(guidelines["donts"]) == 3
            assert guidelines["dos"][0] == "Use specific case study metrics"
            assert guidelines["donts"][0] == "Avoid boring bullet point feature lists"
            print("Assert passed: Style optimization completed and verified successfully!")
            
    finally:
        if os.path.exists(memory_path):
            os.remove(memory_path)
        if has_backup:
            os.rename(backup_path, memory_path)

if __name__ == "__main__":
    test_optimizer_flow()
