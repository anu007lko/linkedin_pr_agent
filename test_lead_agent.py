import sys
import os
import json
import time
from unittest.mock import patch, MagicMock

# Add project path to python search path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_dir)

from lead_memory import init_memory, add_leads, load_leads
from lead_searcher import (
    run_lead_search,
    search_hunter_discover,
    search_hunter_domain,
    search_prospeo_people,
    get_snov_token,
    search_snov_domain
)
from lead_notifier import send_lead_summary_notification
import config

# Set CWD to the project folder
os.chdir(project_dir)

# Set dummy credentials
config.HUNTER_API_KEY = "test_hunter_key"
config.PROSPEO_API_KEY = "test_prospeo_key"
config.SNOV_CLIENT_ID = "test_snov_id"
config.SNOV_CLIENT_SECRET = "test_snov_secret"

def test_hunter_discover():
    print("--- Testing Hunter.io Discover API ---")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "data": [
            {"domain": "recruitmentcorp.com", "organization": "Recruitment Corp"},
            {"domain": "hiringflow.com", "organization": "Hiring Flow"}
        ]
    }
    with patch("requests.get", return_value=mock_resp) as mock_get:
        domains = search_hunter_discover()
        assert mock_get.called
        assert len(domains) == 2
        assert "recruitmentcorp.com" in domains
        print("Discover API test passed!")

def test_hunter_domain_search():
    print("\n--- Testing Hunter.io Domain Search API ---")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "data": {
            "organization": "Walmart",
            "emails": [
                {
                    "value": "alice.johnson@walmart.com",
                    "first_name": "Alice",
                    "last_name": "Johnson",
                    "position": "VP Talent Acquisition"
                },
                {
                    "value": "bob.smith@walmart.com",
                    "first_name": "Bob",
                    "last_name": "Smith",
                    "position": "Software Engineer" # Should be ignored (no HR term)
                }
            ]
        }
    }
    with patch("requests.get", return_value=mock_resp) as mock_get:
        leads = search_hunter_domain("walmart.com")
        assert mock_get.called
        assert len(leads) == 1
        lead = leads[0]
        assert lead["full_name"] == "Alice Johnson"
        assert lead["job_title"] == "VP Talent Acquisition"
        assert lead["company"] == "Walmart"
        assert lead["email"] == "alice.johnson@walmart.com"
        print("Hunter Domain Search test passed!")

def test_prospeo_people_search():
    print("\n--- Testing Prospeo People Search API ---")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "results": [
            {
                "person": {
                    "full_name": "Jane Doe",
                    "current_job_title": "CHRO",
                    "linkedin_url": "https://linkedin.com/in/janedoe",
                    "email": "jane.doe@cigna.com"
                },
                "company": {
                    "company_name": "Cigna",
                    "company_website": "cigna.com"
                }
            }
        ]
    }
    with patch("requests.post", return_value=mock_resp) as mock_post:
        leads = search_prospeo_people("CHRO")
        assert mock_post.called
        assert len(leads) == 1
        lead = leads[0]
        assert lead["full_name"] == "Jane Doe"
        assert lead["job_title"] == "CHRO"
        assert lead["company"] == "Cigna"
        assert lead["email"] == "jane.doe@cigna.com"
        assert lead["linkedin_url"] == "https://linkedin.com/in/janedoe"
        print("Prospeo People Search test passed!")

def test_snov_token_and_search():
    print("\n--- Testing Snov.io Token and Search API ---")
    mock_token_resp = MagicMock()
    mock_token_resp.status_code = 200
    mock_token_resp.json.return_value = {"access_token": "snov_test_access_token"}
    
    mock_search_resp = MagicMock()
    mock_search_resp.status_code = 200
    mock_search_resp.json.return_value = {
        "companyName": "Amazon",
        "emails": [
            {
                "email": "charlie@amazon.com",
                "firstName": "Charlie",
                "lastName": "Brown",
                "position": "Director of Recruiting",
                "linkedin": "https://linkedin.com/in/charlie"
            }
        ]
    }
    
    def mock_post_selector(url, *args, **kwargs):
        if "access_token" in url:
            return mock_token_resp
        elif "get-domain-emails" in url:
            return mock_search_resp
        return MagicMock(status_code=404)
        
    with patch("requests.post", side_effect=mock_post_selector) as mock_post:
        token = get_snov_token()
        assert token == "snov_test_access_token"
        
        leads = search_snov_domain("amazon.com", token)
        assert len(leads) == 1
        lead = leads[0]
        assert lead["full_name"] == "Charlie Brown"
        assert lead["job_title"] == "Director of Recruiting"
        assert lead["company"] == "Amazon"
        assert lead["email"] == "charlie@amazon.com"
        assert lead["linkedin_url"] == "https://linkedin.com/in/charlie"
        print("Snov.io Token & Search test passed!")

def test_full_lead_search_scoring():
    print("\n--- Testing Full Lead Search & Scoring (HR + Big Company = 8+) ---")
    
    def mock_get(url, params=None, *args, **kwargs):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        if "discover" in url:
            mock_resp.json.return_value = {"data": []}
        elif "domain-search" in url:
            # We will mock Hunter domain search for fedex.com (Big Company)
            if params and params.get("domain") == "fedex.com":
                mock_resp.json.return_value = {
                    "data": {
                        "organization": "FedEx",
                        "emails": [
                            {
                                "value": "hr_lead@fedex.com",
                                "first_name": "Fred",
                                "last_name": "Smith",
                                "position": "HR Director" # Big Company + HR Title -> Score >= 8
                            }
                        ]
                    }
                }
            else:
                mock_resp.json.return_value = {"data": {"emails": []}}
        return mock_resp
        
    def mock_post(url, *args, **kwargs):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        if "oauth/access_token" in url:
            mock_resp.json.return_value = {"access_token": "token"}
        elif "get-domain-emails" in url:
            mock_resp.json.return_value = {"emails": []}
        elif "people-search" in url:
            # We mock Prospeo search result
            mock_resp.json.return_value = {
                "results": [
                    {
                        "person": {
                            "full_name": "Sarah Connor",
                            "current_job_title": "VP Talent Acquisition", # HR Title
                            "linkedin_url": "https://linkedin.com/in/sarah"
                        },
                        "company": {
                            "company_name": "Small Tech Inc", # Small Company -> Score < 8
                            "company_website": "smalltech.com"
                        }
                    }
                ]
            }
        return mock_resp

    with patch("requests.get", side_effect=mock_get), patch("requests.post", side_effect=mock_post):
        leads = run_lead_search()
        
        # We expect 2 leads: Fred Smith (FedEx) and Sarah Connor (Small Tech)
        assert len(leads) == 2
        
        fedex_lead = next(l for l in leads if l["company"] == "FedEx")
        small_lead = next(l for l in leads if l["company"] == "Small Tech Inc")
        
        # FedEx: HR Title + FedEx (Big Company) -> Score 8 or 9
        print(f"FedEx Lead Score: {fedex_lead['lead_score']}")
        assert fedex_lead["lead_score"] >= 8
        
        # Small Tech: HR Title + Small Company -> Score around 7
        print(f"Small Tech Lead Score: {small_lead['lead_score']}")
        assert small_lead["lead_score"] < 8
        
        print("Scoring logic test passed!")

def test_deduplication():
    print("\n--- Testing Local Deduplication & Memory Logging ---")
    for filepath in ["leads.json", "leads.csv"]:
        if os.path.exists(filepath):
            os.rename(filepath, filepath + ".bak")
            
    try:
        init_memory()
        
        lead_1 = {
            "company": "Walmart",
            "contact_person": "Fred Smith",
            "job_title": "HR VP",
            "location": "USA",
            "email": "fred@walmart.com",
            "linkedin_url": "https://linkedin.com/in/fred",
            "context": "API search",
            "date_found": "2026-06-17",
            "lead_score": 8,
            "hot_lead": True
        }
        
        # Duplicate by name + company
        lead_2 = {
            "company": "Walmart",
            "contact_person": "Fred Smith",
            "job_title": "HR VP",
            "location": "USA",
            "email": "fred_other@walmart.com",
            "linkedin_url": "https://linkedin.com/in/fred",
            "context": "API search (duplicate)",
            "date_found": "2026-06-17",
            "lead_score": 8,
            "hot_lead": True
        }
        
        added = add_leads([lead_1])
        assert len(added) == 1
        
        added_dup = add_leads([lead_2])
        assert len(added_dup) == 0
        
        leads = load_leads()
        assert len(leads) == 1
        
        print("Deduplication test passed!")
    finally:
        for filename in ["leads.json", "leads.csv"]:
            if os.path.exists(filename):
                os.remove(filename)
            if os.path.exists(filename + ".bak"):
                os.rename(filename + ".bak", filename)

if __name__ == "__main__":
    test_hunter_discover()
    test_hunter_domain_search()
    test_prospeo_people_search()
    test_snov_token_and_search()
    test_full_lead_search_scoring()
    test_deduplication()
