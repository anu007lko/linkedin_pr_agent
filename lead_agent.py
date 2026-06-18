import os
import time
import schedule
import config
from lead_memory import init_memory, add_leads
from lead_searcher import run_lead_search
from lead_notifier import send_lead_summary_notification

def leads_job():
    """Daily RPO lead search job."""
    print("Starting RPO Lead Generation Job (100% API-based)...")
    
    try:
        # Run search and extraction
        scraped_leads = run_lead_search()
        
        print(f"Lead search complete. Scraped {len(scraped_leads)} total prospective leads.")
        
        # Log to memory (JSON and CSV) and filter duplicates
        new_leads = add_leads(scraped_leads)
        print(f"Added {len(new_leads)} new unique leads to memory.")
        
        # Email summary notification
        send_lead_summary_notification(new_leads)
        
        print("Lead Generation Job complete.")
    except Exception as e:
        print(f"Error during lead generation job execution: {e}")

def start_scheduler():
    print("Setting up Lead Agent scheduler...")
    
    # Schedule daily RPO search at 10:00 AM EST (New York)
    schedule.every().day.at("10:00").do(leads_job)
    
    print("Lead Agent scheduler is running. Press Ctrl+C to exit.")
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    init_memory()
    
    # Run once immediately on startup today for verification/immediate check
    print("Performing initial startup lead search check...")
    leads_job()
    
    # Enters schedule loop
    start_scheduler()
