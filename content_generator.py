import time
import os
import json
from datetime import datetime
from urllib.parse import quote
import requests
import config

def _call_gemini(prompt: str) -> str:
    """Calls Google Gemini API via REST."""
    api_key = config.GEMINI_API_KEY
    if not api_key or "your_gemini" in api_key:
        return ""
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 8192
        }
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        res_json = response.json()
        return res_json["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return ""

def _call_anthropic(prompt: str) -> str:
    """Calls Anthropic Claude API via REST."""
    api_key = config.ANTHROPIC_API_KEY
    if not api_key or "your_anthropic" in api_key:
        return ""
    
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    payload = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 1000,
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        res_json = response.json()
        return res_json["content"][0]["text"].strip()
    except Exception as e:
        print(f"Error calling Anthropic API: {e}")
        return ""

def _call_groq(prompt: str, max_retries: int = 3) -> str:
    """Calls Groq API with Llama 3.3 70b and retry logic. Falls back to Gemini or Anthropic if key is missing."""
    api_key = config.GROQ_API_KEY
    if not api_key or "your_groq" in api_key:
        # Check Gemini fallback
        if config.GEMINI_API_KEY and "your_gemini" not in config.GEMINI_API_KEY:
            print("Groq key is missing/placeholder. Falling back to Google Gemini...")
            return _call_gemini(prompt)
        # Check Anthropic fallback
        if config.ANTHROPIC_API_KEY and "your_anthropic" not in config.ANTHROPIC_API_KEY:
            print("Groq and Gemini keys are missing/placeholder. Falling back to Anthropic Claude...")
            return _call_anthropic(prompt)
        print("Error: No valid LLM API keys configured.")
        return ""
        
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1000,
        "temperature": 0.8
    }
    
    for attempt in range(max_retries + 1):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            if response.status_code == 429:
                if attempt < max_retries:
                    print(f"Groq API returned 429 (Rate Limit). Retrying in 30 seconds... (Attempt {attempt + 1}/{max_retries})")
                    time.sleep(30)
                    continue
                else:
                    print("Groq API returned 429 (Rate Limit). Max retries exceeded. Falling back...")
                    if config.GEMINI_API_KEY and "your_gemini" not in config.GEMINI_API_KEY:
                        print("Falling back to Google Gemini...")
                        return _call_gemini(prompt)
                    if config.ANTHROPIC_API_KEY and "your_anthropic" not in config.ANTHROPIC_API_KEY:
                        print("Falling back to Anthropic Claude...")
                        return _call_anthropic(prompt)
                    return ""
            if response.status_code == 413:
                print(f"Groq API returned 413 (Payload Too Large). Prompt is too long. Falling back to Gemini...")
                if config.GEMINI_API_KEY and "your_gemini" not in config.GEMINI_API_KEY:
                    return _call_gemini(prompt)
                if config.ANTHROPIC_API_KEY and "your_anthropic" not in config.ANTHROPIC_API_KEY:
                    return _call_anthropic(prompt)
                return ""
            response.raise_for_status()
            result = response.json()["choices"][0]["message"]["content"].strip()
            return result
        except Exception as e:
            if attempt < max_retries:
                print(f"Error calling Groq API: {e}. Retrying in 5 seconds... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(5)
            else:
                print(f"Error calling Groq API: {e}")
                if config.GEMINI_API_KEY and "your_gemini" not in config.GEMINI_API_KEY:
                    print("Falling back to Google Gemini...")
                    return _call_gemini(prompt)
                if config.ANTHROPIC_API_KEY and "your_anthropic" not in config.ANTHROPIC_API_KEY:
                    print("Falling back to Anthropic Claude...")
                    return _call_anthropic(prompt)
                return ""
    return ""

def generate_linkedin_post(category: str, search_results: list[dict]) -> str:
    """
    Generates a LinkedIn post based on the search results and specific rules using Groq (llama-3.1-70b-versatile).
    """
    system_instruction = """System: You are Tarun Srivastava, 14+ year US Staffing expert and AI thought leader.
Write LinkedIn posts that mix:
- Thought leadership (Tarun's personal voice and experience)
- News commentary (react to latest AI/HR news found)
- Data and insights (include stats when available)

Post structure MUST follow:
Line 1: Strong hook (question, bold statement, or shocking stat)
Line 2-3: Empty line for breathing room
Line 4-8: Core insight or story (3-5 short punchy lines)
Line 9: Empty line
Line 10-12: Practical takeaway or call to action
Line 13: Empty line
Line 14: 3-5 relevant hashtags

Keep under 200 words. Professional but human tone.
Never sound like AI wrote it.
Never mention RPO or Recruitment Process Outsourcing anywhere in the post.
"""

    if category == "Agent Announcement":
        prompt = f"""{system_instruction}

Your task: Write a LinkedIn post announcing that you are an autonomous AI agent, built on the Google Antigravity SDK and Google Gemini, acting as a PR assistant for Tarun.

Additional Rules:
- Invite people to comment and interact to test your capabilities.
- Explicitly mention that you will read and reply to comments automatically.
- Do NOT include any placeholder text.
- Do not repeat this prompt or include meta-commentary like "Here is the announcement".
"""
    else:
        # Format search results into a context string, truncated to prevent 413 errors
        MAX_CONTEXT_CHARS = 3000
        context = ""
        for idx, res in enumerate(search_results, 1):
            if isinstance(res, dict):
                entry = f"{idx}. Title: {res.get('title', '')}\nSnippet: {res.get('snippet', '')}\nLink: {res.get('link', '')}\n\n"
            else:
                entry = f"{idx}. {str(res)}\n\n"
            if len(context) + len(entry) > MAX_CONTEXT_CHARS:
                context += f"[...truncated to stay within API limits]\n"
                break
            context += entry

        prompt = f"""{system_instruction}

Your current assigned topic category is: "{category}".

Here are some recent news articles to draw inspiration and stats from:
{context}

Additional Rules:
- Do NOT include any placeholder text.
- Focus on providing valuable, actionable, or inspiring insights.
- Do not repeat this prompt or include meta-commentary like "Here is the post".
"""

    return _call_groq(prompt)

def generate_reply(post_content: str, comment_text: str) -> str:
    """
    Generates a professional reply to a user's comment on a post using Groq (llama-3.1-70b-versatile).
    """
    prompt = f"""You recently posted this on LinkedIn:
"{post_content}"

A user commented:
"{comment_text}"

Write a reply that is short, human, conversational, and direct.
Rules:
- Keep it extremely brief (1-2 sentences, under 30 words).
- Write like a real person, avoiding robotic/corporate buzzwords.
- Be friendly, helpful, and concise.
- Do not include hashtags.
"""
    return _call_groq(prompt)

def generate_post_image(post_content: str) -> tuple[str, str]:
    """
    Generates a premium image for the post using Unsplash API photo fetching.
    First, uses Groq to extract 2-3 search keywords from the post.
    Then, searches Unsplash and downloads the highest resolution landscape image.
    Avoids using any image that was previously used by checking memory.json.
    Returns (file_path, unsplash_id) on success, or (None, None) on failure.
    """
    api_key = config.UNSPLASH_ACCESS_KEY
    if not api_key:
        print("Error: UNSPLASH_ACCESS_KEY is missing from config.")
        return None, None

    # Load memory.json to see what Unsplash IDs were already used
    used_unsplash_ids = set()
    memory_path = os.path.join(os.path.dirname(__file__), "memory.json")
    if os.path.exists(memory_path):
        try:
            with open(memory_path, 'r') as f:
                data = json.load(f)
                for post in data.get("posts", []):
                    u_id = post.get("unsplash_id")
                    if u_id:
                        used_unsplash_ids.add(u_id)
        except Exception as e:
            print(f"Error reading used Unsplash IDs from memory: {e}")

    # Step 1: Use Groq to extract 3-4 search keywords from post
    keyword_prompt = f"""You are an expert photo researcher for LinkedIn content.
Given this LinkedIn post, extract 3-4 VERY SPECIFIC search keywords for finding a perfectly relevant professional photo.

POST: {post_content}

RULES:
- Keywords must reflect the EXACT topic of the post
- Be specific not generic
- NO generic words like 'business', 'technology', 'people'
- Examples:
  Post about AI hiring tools → 'automated resume screening'
  Post about workspace automation → 'robotic process automation software'

Return ONLY the keywords as a comma-separated list, nothing else."""
    print("Generating Unsplash search keywords using Groq...")
    keywords = _call_groq(keyword_prompt)
    if not keywords:
        print("Failed to generate search keywords from post.")
        return None, None

    print(f"Extracted Unsplash keywords: {keywords}")
    
    # Step 2: Search Unsplash
    try:
        url = "https://api.unsplash.com/search/photos"
        params = {
            "query": keywords.strip(),
            "per_page": 5,
            "orientation": "landscape",
            "content_filter": "high"
        }
        headers = {"Authorization": f"Client-ID {api_key}"}
        print(f"Querying Unsplash API for photos with query: '{keywords.strip()}'...")
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        photos = response.json().get("results", [])
        if not photos:
            print("No photo results returned from Unsplash.")
            return None, None
            
        # Step 3: Pick the first unused photo in the search results
        selected_photo = None
        for photo in photos:
            p_id = photo.get("id")
            if p_id not in used_unsplash_ids:
                selected_photo = photo
                break
                
        if not selected_photo:
            print("All search result photos have been used previously. Picking first one as fallback.")
            selected_photo = photos[0]
            
        best_photo_url = selected_photo["urls"]["full"]
        unsplash_id = selected_photo.get("id")
        print(f"Selected Unsplash Photo ID: {unsplash_id}, URL: {best_photo_url}")
        
        # Step 4: Download image
        print("Downloading photo from Unsplash...")
        img_response = requests.get(best_photo_url, timeout=60)
        img_response.raise_for_status()
        
        image_path = "/tmp/linkedin_post_image.jpg"
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        with open(image_path, "wb") as f:
            f.write(img_response.content)
            
        print(f"Successfully downloaded Unsplash image to {image_path}")
        return image_path, unsplash_id
    except Exception as e:
        print(f"Error fetching or downloading Unsplash image: {e}")
        return None, None

if __name__ == "__main__":
    pass
