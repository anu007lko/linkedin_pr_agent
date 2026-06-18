import time
import requests
import config

def search_hunter_discover() -> list:
    """Queries Hunter.io Discover API to find companies in staffing/recruitment industry."""
    if not config.HUNTER_API_KEY or "your_hunter" in config.HUNTER_API_KEY:
        print("HUNTER_API_KEY is missing or placeholder. Skipping Discover API.")
        return []
        
    url = "https://api.hunter.io/v2/discover"
    params = {
        "api_key": config.HUNTER_API_KEY,
        "limit": 10,
        "industry": "staffing recruitment"
    }
    
    try:
        print("Querying Hunter.io Discover API (free, no credits)...")
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json().get("data", [])
        domains = [item.get("domain") for item in data if item.get("domain")]
        print(f"Hunter.io Discover found {len(domains)} company domains.")
        return domains
    except Exception as e:
        print(f"Error calling Hunter.io Discover API: {e}")
        return []

def search_hunter_domain(domain: str) -> list:
    """Queries Hunter.io Domain Search API to find HR/TA contacts at a domain."""
    if not config.HUNTER_API_KEY or "your_hunter" in config.HUNTER_API_KEY:
        return []
        
    url = "https://api.hunter.io/v2/domain-search"
    params = {
        "domain": domain,
        "api_key": config.HUNTER_API_KEY
    }
    
    leads = []
    try:
        print(f"Querying Hunter.io Domain Search for: {domain}")
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json().get("data", {})
        emails = data.get("emails", [])
        company_name = data.get("organization") or domain.split('.')[0].capitalize()
        
        target_terms = ["hr", "talent", "people", "recruiting", "chro", "cpo"]
        for email_info in emails:
            position = email_info.get("position") or ""
            pos_lower = position.lower()
            if any(term in pos_lower for term in target_terms):
                first_name = email_info.get("first_name") or ""
                last_name = email_info.get("last_name") or ""
                full_name = f"{first_name} {last_name}".strip() or "Unknown Contact"
                email_val = email_info.get("value")
                
                lead = {
                    "full_name": full_name,
                    "job_title": position or "HR / Recruiting Specialist",
                    "company": company_name,
                    "email": email_val,
                    "linkedin_url": None, # Hunter Domain Search does not provide LinkedIn URL
                    "source": "Hunter.io Domain Search",
                    "date_found": time.strftime("%Y-%m-%d"),
                    "domain": domain
                }
                leads.append(lead)
    except Exception as e:
        print(f"Error querying Hunter.io Domain Search for {domain}: {e}")
    return leads

def search_prospeo_people(job_title: str) -> list:
    """Queries Prospeo People Search API to locate decision makers."""
    if not config.PROSPEO_API_KEY or "your_prospeo" in config.PROSPEO_API_KEY:
        print("PROSPEO_API_KEY is missing or placeholder. Skipping Prospeo API.")
        return []
        
    url = "https://api.prospeo.io/people-search"
    headers = {
        "Content-Type": "application/json",
        "X-KEY": config.PROSPEO_API_KEY
    }
    payload = {
        "job_title": job_title,
        "location": "United States",
        "limit": 10
    }
    
    leads = []
    try:
        print(f"Querying Prospeo People Search for job title: '{job_title}'...")
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        res_json = response.json()
        results = res_json.get("results", [])
        if not isinstance(results, list):
            results = [res_json] if "person" in res_json else []
            
        for item in results:
            person = item.get("person") or {}
            company_info = item.get("company") or {}
            
            full_name = person.get("full_name") or f"{person.get('first_name', '')} {person.get('last_name', '')}".strip()
            if not full_name:
                full_name = item.get("full_name") or "Unknown Contact"
                
            title = person.get("current_job_title") or person.get("job_title") or item.get("job_title") or job_title
            company = company_info.get("company_name") or item.get("company") or "Unknown Company"
            email = person.get("email") or item.get("email")
            linkedin_url = person.get("linkedin_url") or item.get("linkedin_url")
            
            lead = {
                "full_name": full_name,
                "job_title": title,
                "company": company,
                "email": email,
                "linkedin_url": linkedin_url,
                "source": "Prospeo People Search",
                "date_found": time.strftime("%Y-%m-%d"),
                "domain": company_info.get("company_website") or ""
            }
            leads.append(lead)
    except Exception as e:
        print(f"Error querying Prospeo People Search for '{job_title}': {e}")
    return leads

def get_snov_token() -> str:
    """Retrieves access token from Snov.io OAuth endpoint."""
    if not config.SNOV_CLIENT_ID or "your_snov" in config.SNOV_CLIENT_ID:
        print("SNOV_CLIENT_ID or SECRET is missing or placeholder. Skipping Snov.io API.")
        return ""
        
    url = "https://api.snov.io/v1/oauth/access_token"
    payload = {
        "client_id": config.SNOV_CLIENT_ID,
        "client_secret": config.SNOV_CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    
    try:
        print("Getting Snov.io access token...")
        # OAuth client credentials standard requires application/x-www-form-urlencoded
        response = requests.post(url, data=payload, timeout=20)
        if response.status_code != 200:
            # Try JSON body fallback
            response = requests.post(url, json=payload, timeout=20)
        response.raise_for_status()
        return response.json().get("access_token") or ""
    except Exception as e:
        print(f"Error getting Snov.io token: {e}")
        return ""

def search_snov_domain(domain: str, token: str) -> list:
    """Queries Snov.io Domain Search API to list emails and contacts for a domain."""
    if not token:
        return []
        
    url = "https://api.snov.io/v1/get-domain-emails"
    payload = {
        "domain": domain,
        "access_token": token,
        "token": token,
        "limit": 100
    }
    
    leads = []
    try:
        print(f"Querying Snov.io Domain Search for: {domain}")
        # Try application/x-www-form-urlencoded first
        response = requests.post(url, data=payload, timeout=30)
        if response.status_code != 200:
            # Try JSON body fallback
            response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        
        res_json = response.json()
        emails = res_json.get("emails", [])
        company_name = res_json.get("companyName") or domain.split('.')[0].capitalize()
        
        target_terms = ["hr", "talent", "people", "recruiting", "chro", "cpo"]
        for email_info in emails:
            position = email_info.get("position") or ""
            pos_lower = position.lower()
            if any(term in pos_lower for term in target_terms):
                first_name = email_info.get("firstName") or ""
                last_name = email_info.get("lastName") or ""
                full_name = f"{first_name} {last_name}".strip() or "Unknown Contact"
                email_val = email_info.get("email")
                
                # Check for LinkedIn
                linkedin_url = email_info.get("linkedin") or email_info.get("linkedin_url") or None
                
                lead = {
                    "full_name": full_name,
                    "job_title": position or "HR / Recruiting Specialist",
                    "company": company_name,
                    "email": email_val,
                    "linkedin_url": linkedin_url,
                    "source": "Snov.io Domain Search",
                    "date_found": time.strftime("%Y-%m-%d"),
                    "domain": domain
                }
                leads.append(lead)
    except Exception as e:
        print(f"Error querying Snov.io Domain Search for {domain}: {e}")
    return leads

def run_lead_search() -> list[dict]:
    """Runs programmatic search across Hunter, Snov, and Prospeo and returns scored leads."""
    all_leads = []
    
    # 1. Gather domains from Hunter Discover
    discovered_domains = search_hunter_discover()
    
    # 2. Known target companies (known RPO buyers)
    target_domains = [
        "walmart.com", "amazon.com", "target.com", "fedex.com", 
        "salesforce.com", "oracle.com", "ibm.com", "microsoft.com", 
        "jpmorgan.com", "bankofamerica.com", "unitedhealth.com", 
        "mcdonalds.com", "homedepot.com", "cvs.com", "cigna.com", 
        "humana.com", "delta.com", "marriott.com", "hilton.com"
    ]
    
    # Merge and deduplicate domain lists
    domains_to_search = list(dict.fromkeys(target_domains + discovered_domains))
    
    # To respect credit constraints, restrict search to first 10 domains per run
    domains_to_search = domains_to_search[:10]
    
    # Authenticate Snov.io once
    snov_token = get_snov_token()
    
    # Run Domain Searches
    for domain in domains_to_search:
        # Search via Hunter
        hunter_results = search_hunter_domain(domain)
        all_leads.extend(hunter_results)
        
        # Search via Snov
        if snov_token:
            snov_results = search_snov_domain(domain, snov_token)
            all_leads.extend(snov_results)
            
        time.sleep(1) # Small rate limiting buffer
        
    # 3. Run Prospeo People Searches
    target_titles = ["HR Director", "VP Talent Acquisition", "CHRO", "CPO", "Chief People Officer"]
    for title in target_titles:
        prospeo_results = search_prospeo_people(title)
        all_leads.extend(prospeo_results)
        time.sleep(1)
        
    # 4. Filter, score and deduplicate the collected results
    scored_leads = []
    seen_keys = set()
    
    for lead in all_leads:
        full_name = lead.get("full_name") or "Unknown Contact"
        email = lead.get("email")
        company = lead.get("company") or "Unknown Company"
        job_title = lead.get("job_title") or "HR Specialist"
        linkedin_url = lead.get("linkedin_url")
        source = lead.get("source") or "API Search"
        domain = lead.get("domain", "")
        
        # Deduplication key
        dedup_key = f"{full_name.lower()}:{company.lower()}"
        if email:
            dedup_key += f":{email.lower()}"
            
        if dedup_key in seen_keys:
            continue
        seen_keys.add(dedup_key)
        
        # Lead score (HR title + big company = 8+)
        score = 5
        pos_lower = job_title.lower()
        comp_lower = company.lower()
        dom_lower = domain.lower()
        
        is_hr_title = any(term in pos_lower for term in ["hr", "talent", "people", "recruiting", "chro", "cpo", "acquisition"])
        is_big_company = any(c in comp_lower or c in dom_lower for c in target_domains)
        
        if is_hr_title:
            score += 2
        if is_big_company:
            score += 2
        if is_hr_title and is_big_company:
            score = max(score, 8)
            
        scored_lead = {
            "company": company,
            "contact_person": full_name,
            "job_title": job_title,
            "location": "USA", # Target locations are United States
            "email": email,
            "linkedin_url": linkedin_url,
            "context": f"Found via {source} targeting {company}.",
            "date_found": lead.get("date_found") or time.strftime("%Y-%m-%d"),
            "lead_score": score,
            "hot_lead": score >= 7
        }
        scored_leads.append(scored_lead)
        
    return scored_leads
