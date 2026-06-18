import smtplib
from email.mime.text import MIMEText
import time
import config

def send_lead_summary_notification(new_leads: list[dict]):
    """Sends a daily email summary of new leads found."""
    if not config.GMAIL_ADDRESS or not config.GMAIL_APP_PASSWORD or not config.NOTIFICATION_EMAIL:
        print("Gmail configuration is incomplete. Skipping lead notification.")
        return

    date_str = time.strftime("%Y-%m-%d")
    subject = f"LinkedIn RPO Lead Agent: {len(new_leads)} New Leads Found ({date_str})"
    
    # Build report body
    lines = [
        "LinkedIn RPO Lead Generation Agent",
        "==================================",
        f"Date: {date_str}",
        f"New leads discovered today: {len(new_leads)}",
        "",
        "New Leads Details:",
        "------------------"
    ]
    
    if not new_leads:
        lines.append("No new RPO leads found in today's run.")
    else:
        for idx, lead in enumerate(new_leads, 1):
            is_hot = "🔥 HOT LEAD" if lead.get("hot_lead") else "Normal Intent"
            lines.append(f"{idx}. {lead.get('company')} ({is_hot})")
            lines.append(f"   * Contact: {lead.get('contact_person')} - {lead.get('job_title')}")
            lines.append(f"   * Location: {lead.get('location')}")
            lines.append(f"   * Email: {lead.get('email') or 'None public'}")
            lines.append(f"   * Score: {lead.get('lead_score')}/10")
            lines.append(f"   * Profile/Source: {lead.get('linkedin_url') or 'None'}")
            lines.append(f"   * Context: {lead.get('context')[:200]}...")
            lines.append("")
            
    lines.append("")
    lines.append("Leads have been saved to leads.json and leads.csv in the agent directory.")
    body = "\n".join(lines)
    
    msg = MIMEText(body, 'plain', 'utf-8')
    msg['Subject'] = subject
    msg['From'] = config.GMAIL_ADDRESS
    msg['To'] = config.NOTIFICATION_EMAIL
    
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(config.GMAIL_ADDRESS, config.GMAIL_APP_PASSWORD)
            server.send_message(msg)
        print(f"Lead notification email sent: {subject}")
    except Exception as e:
        print(f"Failed to send lead email notification: {e}")

if __name__ == "__main__":
    # Test stub
    pass
