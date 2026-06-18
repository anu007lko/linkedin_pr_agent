import os
import json
import csv

LEADS_JSON = os.path.join(os.path.dirname(__file__), "leads.json")
LEADS_CSV = os.path.join(os.path.dirname(__file__), "leads.csv")

def init_memory():
    """Initializes the local leads JSON and CSV files if they don't exist."""
    if not os.path.exists(LEADS_JSON):
        with open(LEADS_JSON, 'w') as f:
            json.dump([], f, indent=4)
            
    if not os.path.exists(LEADS_CSV):
        with open(LEADS_CSV, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                "Company", "Contact Person", "Job Title", "Location", 
                "Email", "LinkedIn URL", "Post Context", "Date Found", 
                "Lead Score", "Hot Lead"
            ])

def load_leads() -> list[dict]:
    init_memory()
    with open(LEADS_JSON, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            # Re-initialize if corrupted
            init_memory()
            return []

def save_leads(leads: list[dict]):
    with open(LEADS_JSON, 'w') as f:
        json.dump(leads, f, indent=4)
        
    # Write to CSV
    with open(LEADS_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            "Company", "Contact Person", "Job Title", "Location", 
            "Email", "LinkedIn URL", "Post Context", "Date Found", 
            "Lead Score", "Hot Lead"
        ])
        for lead in leads:
            writer.writerow([
                lead.get("company") or "",
                lead.get("contact_person") or "",
                lead.get("job_title") or "",
                lead.get("location") or "",
                lead.get("email") or "",
                lead.get("linkedin_url") or "",
                lead.get("context") or "",
                lead.get("date_found") or "",
                lead.get("lead_score") or 0,
                "TRUE" if lead.get("hot_lead") else "FALSE"
            ])

def add_leads(new_leads: list[dict]) -> list[dict]:
    """
    Adds new leads if they are not duplicates.
    Returns the list of leads that were actually added (newly discovered).
    """
    existing_leads = load_leads()
    added_leads = []
    
    # Track existing keys for deduplication
    existing_keys = set()
    existing_urls = set()
    
    for lead in existing_leads:
        co = (lead.get("company") or "").strip().lower()
        cp = (lead.get("contact_person") or "").strip().lower()
        if co and cp:
            existing_keys.add(f"{co}:{cp}")
        url = lead.get("linkedin_url")
        if url:
            existing_urls.add(url.strip().lower())
            
    # Process new leads
    merged_leads = list(existing_leads)
    for lead in new_leads:
        co = (lead.get("company") or "").strip().lower()
        cp = (lead.get("contact_person") or "").strip().lower()
        url = (lead.get("linkedin_url") or "").strip().lower()
        
        key = f"{co}:{cp}"
        is_duplicate = False
        
        if key in existing_keys:
            is_duplicate = True
        if url and url in existing_urls:
            is_duplicate = True
            
        if not is_duplicate:
            # Ensure hot_lead flag is computed correctly
            score = int(lead.get("lead_score") or 0)
            lead["hot_lead"] = score >= 7
            
            merged_leads.append(lead)
            added_leads.append(lead)
            
            # Update tracking sets
            if co and cp:
                existing_keys.add(key)
            if url:
                existing_urls.add(url)
                
    if added_leads:
        save_leads(merged_leads)
        
    return added_leads

if __name__ == "__main__":
    init_memory()
