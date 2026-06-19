import os
import json
import config
from memory_manager import load_memory, save_style_guidelines
from content_generator import _call_gemini, _call_groq

def optimize_style_guidelines():
    """
    Analyzes historical post performance and uses LLM to generate
    optimized content generation rules (Dos and Don'ts).
    """
    print("Starting Social Media Performance Optimization...")
    data = load_memory()
    posts = data.get("posts", [])
    
    # We need at least 5 posts to have enough data to learn
    if len(posts) < 5:
        print(f"Only {len(posts)} posts in memory. Skipping optimization until at least 5 posts are recorded.")
        return
        
    # Sort posts by engagement_score (descending)
    valid_posts = [p for p in posts if p.get("category") and p.get("content")]
    if len(valid_posts) < 5:
        print("Not enough valid posts for optimization.")
        return
        
    sorted_posts = sorted(valid_posts, key=lambda x: x.get("engagement_score", 0), reverse=True)
    
    # Split into top performing and bottom performing
    num_to_select = min(3, len(sorted_posts) // 2)
    if num_to_select < 1:
        num_to_select = 1
        
    top_posts = sorted_posts[:num_to_select]
    bottom_posts = sorted_posts[-num_to_select:]
    
    top_posts_str = ""
    for idx, p in enumerate(top_posts, 1):
        top_posts_str += f"Post {idx} (Category: {p['category']}, Likes: {p.get('likes', 0)}, Comments: {p.get('comments', 0)}, Engagement: {p.get('engagement_score', 0)}):\n{p['content']}\n\n"
        
    bottom_posts_str = ""
    for idx, p in enumerate(bottom_posts, 1):
        bottom_posts_str += f"Post {idx} (Category: {p['category']}, Likes: {p.get('likes', 0)}, Comments: {p.get('comments', 0)}, Engagement: {p.get('engagement_score', 0)}):\n{p['content']}\n\n"
        
    prompt = f"""You are an advanced social media growth strategist and AI thought leader.
Analyze these top-performing and bottom-performing LinkedIn posts to discover what drives maximum engagement and reach.

TOP-PERFORMING POSTS:
{top_posts_str}

BOTTOM-PERFORMING POSTS:
{bottom_posts_str}

Identify:
1. What writing style, formatting, visual hooks, or content structures made the top posts successful.
2. What patterns, tone issues, or formatting mistakes caused the bottom posts to underperform.

Generate a JSON object with two keys:
- "dos": A list of 4-5 highly specific, actionable rules to write better posts (e.g., "Use stats or numbers in the first line", "Structure with single-sentence bullet points for readability").
- "donts": A list of 4-5 pitfalls to avoid (e.g., "Avoid generic questions in hooks", "Avoid using too many emojis").

Output ONLY valid JSON, no markdown codeblocks, no extra explanation. Keep rules concise and actionable.
"""
    print("Calling LLM to generate style insights...")
    response_text = ""
    try:
        response_text = _call_groq(prompt)
    except Exception as e:
        print(f"Error calling Groq for optimization: {e}")
        
    if not response_text:
        print("Groq optimization failed/unavailable. Trying Gemini...")
        try:
            response_text = _call_gemini(prompt)
        except Exception as e:
            print(f"Error calling Gemini for optimization: {e}")
            
    if not response_text:
        print("Optimization failed. Could not reach LLM.")
        return

    cleaned_response = response_text.strip()
    if cleaned_response.startswith("```json"):
        cleaned_response = cleaned_response[7:]
    if cleaned_response.startswith("```"):
        cleaned_response = cleaned_response[3:]
    if cleaned_response.endswith("```"):
        cleaned_response = cleaned_response[:-3]
    cleaned_response = cleaned_response.strip()
    
    try:
        rules = json.loads(cleaned_response)
        dos = rules.get("dos", [])
        donts = rules.get("donts", [])
        if dos or donts:
            save_style_guidelines(dos, donts)
            print("Successfully optimized style guidelines and saved to memory!")
            print(f"Dos: {dos}")
            print(f"Donts: {donts}")
        else:
            print(f"Invalid JSON returned (no dos or donts): {response_text}")
    except Exception as e:
        print(f"Failed to parse optimization response: {e}. Raw response: {response_text}")

if __name__ == "__main__":
    optimize_style_guidelines()
