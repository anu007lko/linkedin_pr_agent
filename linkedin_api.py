import json
import os
import time
import requests
from datetime import datetime
import config
from memory_manager import load_memory, save_memory

def check_linkedin_token_expiry():
    """Checks if the LinkedIn Access Token is nearing its 2-month expiry (warns at 7 days remaining)."""
    token = config.LINKEDIN_ACCESS_TOKEN
    if not token or "test_access_token" in token:
        return
        
    data = load_memory()
    last_token = data.get("linkedin_last_access_token")
    token_created_at = data.get("linkedin_token_created_at")
    
    current_time = datetime.now()
    
    # Reset timestamp if token changes
    if last_token != token or not token_created_at:
        data["linkedin_last_access_token"] = token
        data["linkedin_token_created_at"] = current_time.isoformat()
        save_memory(data)
        token_created_at = current_time.isoformat()
        print("Detected new/updated LINKEDIN_ACCESS_TOKEN. Resetting creation timestamp.")
        
    try:
        created_dt = datetime.fromisoformat(token_created_at)
        days_elapsed = (current_time - created_dt).days
        print(f"LinkedIn Access Token age: {days_elapsed} days.")
        
        # 2 months (60 days) total lifetime. Warn at 7 days remaining -> >= 53 days elapsed.
        if days_elapsed >= 53:
            from notifier import send_notification
            days_left = max(0, 60 - days_elapsed)
            subject = "LinkedIn PR Agent: Access Token Expiry Warning"
            body = (
                f"Your LinkedIn Access Token was created/updated on {created_dt.strftime('%Y-%m-%d')} ({days_elapsed} days ago).\n"
                f"It is estimated to expire in {days_left} days.\n"
                f"Please update the LINKEDIN_ACCESS_TOKEN in your .env file."
            )
            print(f"Token near expiry: sending warning notification to {config.NOTIFICATION_EMAIL}...")
            send_notification(subject, body)
    except Exception as e:
        print(f"Error checking token expiry: {e}")

def _get_person_urn() -> str:
    """Retrieves the person URN of the authenticated member."""
    if not config.LINKEDIN_ACCESS_TOKEN or "test_access_token" in config.LINKEDIN_ACCESS_TOKEN:
        print("LINKEDIN_ACCESS_TOKEN is missing or placeholder.")
        return ""
        
    url = "https://api.linkedin.com/v2/userinfo"
    headers = {
        "Authorization": f"Bearer {config.LINKEDIN_ACCESS_TOKEN}"
    }
    
    try:
        res = requests.get(url, headers=headers, timeout=20)
        res.raise_for_status()
        person_id = res.json().get("sub")
        if person_id:
            return f"urn:li:person:{person_id}"
    except Exception as e:
        print(f"Error fetching LinkedIn userinfo URN: {e}")
        if 'res' in locals():
            print(f"Raw userinfo response: {res.text}")
    return ""

def post_to_linkedin(content: str, image_path: str = None) -> tuple[str, str]:
    """
    Posts the given content to LinkedIn using official API.
    If image_path is provided, registers and uploads the image first, then includes it.
    If image upload fails, falls back to text-only post.
    Returns (post_urn, asset_urn) on success, or ("", "") on failure.
    """
    check_linkedin_token_expiry()
    
    person_urn = _get_person_urn()
    if not person_urn:
        print("Failed to retrieve actor Person URN. Skipping post.")
        return "", ""
        
    asset_urn = None
    
    if image_path and os.path.exists(image_path):
        try:
            print(f"Registering image upload with LinkedIn Assets API...")
            register_url = "https://api.linkedin.com/v2/assets?action=registerUpload"
            register_headers = {
                "Authorization": f"Bearer {config.LINKEDIN_ACCESS_TOKEN}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0"
            }
            register_payload = {
                "registerUploadRequest": {
                    "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                    "owner": person_urn,
                    "serviceRelationships": [{
                        "relationshipType": "OWNER",
                        "identifier": "urn:li:userGeneratedContent"
                    }]
                }
            }
            res_reg = requests.post(register_url, headers=register_headers, json=register_payload, timeout=30)
            res_reg.raise_for_status()
            reg_json = res_reg.json()
            
            upload_url = reg_json["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
            asset_urn = reg_json["value"]["asset"]
            print(f"Registered Asset URN: {asset_urn}")
            
            print(f"Uploading image binary data to {upload_url}...")
            with open(image_path, "rb") as f:
                image_data = f.read()
            
            upload_headers = {
                "Authorization": f"Bearer {config.LINKEDIN_ACCESS_TOKEN}",
                "Content-Type": "image/jpeg"
            }
            res_upload = requests.put(upload_url, headers=upload_headers, data=image_data, timeout=60)
            res_upload.raise_for_status()
            print("Successfully uploaded image bytes to LinkedIn.")
        except Exception as e:
            print(f"Image upload failed: {e}. Falling back to text-only post.")
            asset_urn = None
            
    url = "https://api.linkedin.com/v2/ugcPosts"
    headers = {
        "Authorization": f"Bearer {config.LINKEDIN_ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }
    
    if asset_urn:
        payload = {
            "author": person_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": content
                    },
                    "shareMediaCategory": "IMAGE",
                    "media": [{
                        "status": "READY",
                        "description": {"text": ""},
                        "media": asset_urn,
                        "title": {"text": ""}
                    }]
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
    else:
        payload = {
            "author": person_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": content
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
        
    try:
        print("Publishing post via LinkedIn official API...")
        res = requests.post(url, headers=headers, json=payload, timeout=30)
        res.raise_for_status()
        post_urn = res.json().get("id")
        if post_urn:
            print(f"Post published successfully via API. URN: {post_urn}")
            return post_urn, asset_urn or ""
    except Exception as e:
        print(f"Error posting to LinkedIn via API: {e}")
        if 'res' in locals():
            print(f"Raw response: {res.text}")
            
        if asset_urn:
            print("Failed publishing with image. Retrying with text-only post...")
            fallback_payload = {
                "author": person_urn,
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": content
                        },
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }
            try:
                res_fb = requests.post(url, headers=headers, json=fallback_payload, timeout=30)
                res_fb.raise_for_status()
                post_urn = res_fb.json().get("id")
                if post_urn:
                    print(f"Text-only fallback post published successfully. URN: {post_urn}")
                    return post_urn, ""
            except Exception as e_fb:
                print(f"Text-only fallback post also failed: {e_fb}")
                
    return "", ""
