import sys
import os
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add project path to python search path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_dir)

from memory_manager import init_memory, load_memory, save_memory, log_post
from linkedin_api import (
    check_linkedin_token_expiry,
    _get_person_urn,
    post_to_linkedin
)
import config

# Set CWD to the project folder
os.chdir(project_dir)

# Set dummy credentials for testing
config.LINKEDIN_ACCESS_TOKEN = "test_linkedin_token"
config.NOTIFICATION_EMAIL = "test_email@gmail.com"

def test_token_expiry_no_warning():
    print("--- Testing Token Expiry Check (No Warning) ---")
    
    # Reset memory file to blank state for testing
    backup_memory = "memory.json.bak"
    if os.path.exists("memory.json"):
        os.rename("memory.json", backup_memory)
        
    try:
        init_memory()
        
        # Verify checking on new token sets the timestamp
        with patch("notifier.send_notification") as mock_notify:
            check_linkedin_token_expiry()
            assert not mock_notify.called, "Should not send warning email for fresh token"
            
            data = load_memory()
            assert data.get("linkedin_last_access_token") == "test_linkedin_token"
            assert "linkedin_token_created_at" in data
            print("Successfully initialized token timestamp in memory.")
    finally:
        if os.path.exists("memory.json"):
            os.remove("memory.json")
        if os.path.exists(backup_memory):
            os.rename(backup_memory, "memory.json")

def test_token_expiry_warning():
    print("\n--- Testing Token Expiry Check (Warning Triggered) ---")
    backup_memory = "memory.json.bak"
    if os.path.exists("memory.json"):
        os.rename("memory.json", backup_memory)
        
    try:
        init_memory()
        data = load_memory()
        
        # Set token age to 54 days ago (>= 53 days)
        old_time = datetime.now() - timedelta(days=54)
        data["linkedin_last_access_token"] = "test_linkedin_token"
        data["linkedin_token_created_at"] = old_time.isoformat()
        save_memory(data)
        
        with patch("notifier.send_notification") as mock_notify:
            check_linkedin_token_expiry()
            assert mock_notify.called, "Should trigger warning email for 54-day-old token"
            call_args = mock_notify.call_args[0]
            assert "Access Token Expiry Warning" in call_args[0]
            print("Successfully sent expiry warning email!")
    finally:
        if os.path.exists("memory.json"):
            os.remove("memory.json")
        if os.path.exists(backup_memory):
            os.rename(backup_memory, "memory.json")

def test_get_person_urn():
    print("\n--- Testing Userinfo URN Retrieve ---")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"sub": "12345abcdef"}
    
    with patch("linkedin_api.requests.get", return_value=mock_resp) as mock_get:
        person_urn = _get_person_urn()
        assert mock_get.called
        assert person_urn == "urn:li:person:12345abcdef"
        print(f"Retrieved Person URN: {person_urn}")

def test_post_to_linkedin():
    print("\n--- Testing Post to LinkedIn UGC API ---")
    mock_urn_resp = MagicMock()
    mock_urn_resp.status_code = 200
    mock_urn_resp.json.return_value = {"sub": "my_person_id"}
    
    mock_post_resp = MagicMock()
    mock_post_resp.status_code = 201
    mock_post_resp.json.return_value = {"id": "urn:li:share:987654321"}
    
    def mock_requests_selector(url, *args, **kwargs):
        if "userinfo" in url:
            return mock_urn_resp
        elif "ugcPosts" in url:
            return mock_post_resp
        return MagicMock(status_code=404)
        
    with patch("linkedin_api.requests.get", side_effect=mock_requests_selector), \
         patch("linkedin_api.requests.post", side_effect=mock_requests_selector):
        post_urn, asset_urn = post_to_linkedin("Hello world LinkedIn API!")
        assert post_urn == "urn:li:share:987654321"
        assert asset_urn == ""
        print(f"Published Post URN: {post_urn}")

def test_post_to_linkedin_with_image():
    print("\n--- Testing Post to LinkedIn UGC API with Image ---")
    mock_urn_resp = MagicMock()
    mock_urn_resp.status_code = 200
    mock_urn_resp.json.return_value = {"sub": "my_person_id"}
    
    mock_reg_resp = MagicMock()
    mock_reg_resp.status_code = 200
    mock_reg_resp.json.return_value = {
        "value": {
            "uploadMechanism": {
                "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest": {
                    "uploadUrl": "https://api.linkedin.com/mediaUploadUrl"
                }
            },
            "asset": "urn:li:digitalmediaAsset:C4D04AQE_mocked"
        }
    }
    
    mock_put_resp = MagicMock()
    mock_put_resp.status_code = 201
    
    mock_post_resp = MagicMock()
    mock_post_resp.status_code = 201
    mock_post_resp.json.return_value = {"id": "urn:li:share:987654321_with_img"}
    
    # Create a dummy image file for testing
    dummy_img_path = "/tmp/test_dummy_image.jpg"
    with open(dummy_img_path, "wb") as f:
        f.write(b"dummy binary data")
        
    try:
        def mock_get(url, *args, **kwargs):
            if "userinfo" in url:
                return mock_urn_resp
            return MagicMock(status_code=404)
            
        def mock_post(url, *args, **kwargs):
            if "registerUpload" in url:
                return mock_reg_resp
            elif "ugcPosts" in url:
                return mock_post_resp
            return MagicMock(status_code=404)
            
        def mock_put(url, *args, **kwargs):
            if "mediaUploadUrl" in url:
                return mock_put_resp
            return MagicMock(status_code=404)
            
        with patch("linkedin_api.requests.get", side_effect=mock_get), \
             patch("linkedin_api.requests.post", side_effect=mock_post), \
             patch("linkedin_api.requests.put", side_effect=mock_put):
            post_urn, asset_urn = post_to_linkedin("Hello world LinkedIn API with image!", dummy_img_path)
            assert post_urn == "urn:li:share:987654321_with_img"
            assert asset_urn == "urn:li:digitalmediaAsset:C4D04AQE_mocked"
            print(f"Published Post URN with Image: {post_urn}, Asset URN: {asset_urn}")
            
        # Test fallback when registerUpload fails
        def mock_post_fail(url, *args, **kwargs):
            if "registerUpload" in url:
                return MagicMock(status_code=500)
            elif "ugcPosts" in url:
                return mock_post_resp
            return MagicMock(status_code=404)
            
        with patch("linkedin_api.requests.get", side_effect=mock_get), \
             patch("linkedin_api.requests.post", side_effect=mock_post_fail):
            post_urn, asset_urn = post_to_linkedin("Hello world LinkedIn API with image fallback!", dummy_img_path)
            assert post_urn == "urn:li:share:987654321_with_img"
            assert asset_urn == ""
            print("Successfully verified fallback to text-only post when image upload fails.")
    finally:
        if os.path.exists(dummy_img_path):
            os.remove(dummy_img_path)

if __name__ == "__main__":
    test_token_expiry_no_warning()
    test_token_expiry_warning()
    test_get_person_urn()
    test_post_to_linkedin()
    test_post_to_linkedin_with_image()
