---
name: linkedin-agent
description: Technical reference, architecture diagrams, locked file structures, API setups, prompt templates, and operational runbooks for the LinkedIn PR & Lead Agent.
---

# Skill: Autonomous LinkedIn PR and Lead Agent

This guide documents the architecture, directory components, credentials, cloud deployment steps, operational updates, and status diagnostics for the Autonomous LinkedIn Agent suite.

---

## 🧠 System Architecture

The suite consists of two separate agents running as continuous background daemons:

```
                  ┌──────────────────────┐
                  │      cron / loop     │
                  └──────────┬───────────┘
                             │
            ┌────────────────┴────────────────┐
            ▼                                 ▼
   PR Agent (main.py)               Lead Agent (lead_agent.py)
   ├── Pick category                ├── Scrape RPO leads
   ├── Research news                ├── Deduplicate leads
   ├── Write copy (Groq)            ├── Save to leads JSON/CSV
   ├── Publish post (API)           └── Email CSV report
   └── Email report
```

1.  **LinkedIn PR Agent (`main.py`)**: Uses RSS feeds to research trending topics, drafts visionary content using the Groq API, publishes it via the LinkedIn REST API, and emails confirmation summaries.
2.  **Lead Generation Agent (`lead_agent.py`)**: Searches Google/Search APIs for RPO business leads, checks against duplicate databases, appends new entries to JSON/CSV files, and sends a daily summary alert.

---

## 📁 File Manifest

| File | Type | Description |
| :--- | :--- | :--- |
| **`main.py`** | Script | Entrypoint and scheduler for the PR Posting Agent. |
| **`lead_agent.py`** | Script | Entrypoint and scheduler for the Lead Generation Agent. |
| **`linkedin_api.py`** | Module | Handles LinkedIn REST API operations (`ugcPosts`, `userinfo`, token checks). |
| **`search_agent.py`** | Module | Queries news sources and RSS feeds for trending articles. |
| **`content_generator.py`** | Module | Calls Groq API (llama-3.3-70b-versatile) to generate under-200-word visionary post copy. |
| **`content_optimizer.py`** | Module | Audits performance and generates optimized Dos and Don'ts via Gemini/Groq. |
| **`memory_manager.py`** | Module | Saves posts, checks 7-day rule, adjusts weights, compiles report, and handles auto-healing database errors. |
| **`memory.json`** | Data | Local database containing logged posts and current topic weights. |
| **`lead_searcher.py`** | Module | Handles scraping operations to extract contact data. |
| **`lead_memory.py`** | Module | Checks for duplicate leads and stores entries in JSON/CSV formats. |
| **`lead_notifier.py`** | Module | Formats lead records and sends HTML summary emails. |
| **`leads.json` / `leads.csv`**| Data | Database containing extracted prospect contacts. |
| **`notifier.py`** | Module | Low-level SMTP client library for sending post and warning notifications. |
| **`config.py`** | Module | Configures credentials and environment settings. |
| **`requirements.txt`** | Setup | Python dependency packages requirement list. |
| **`test_linkedin_bot.py`** | Test | Unit tests for LinkedIn REST API calls and token expiry checks. |
| **`test_lead_agent.py`** | Test | Unit tests for the Lead search and log pipeline. |
| **`test_optimizer.py`** | Test | Unit tests for performance optimizer behavior under mock statistics. |
| **`test_phase2.py`** | Test | Unit tests for topic weights tuning and SMTP report compiler. |

---

## 🔑 Required API Keys & Environment Variables

Create a `.env` file in the root of the project with the following configuration:

```env
# LinkedIn API Credentials
LINKEDIN_ACCESS_TOKEN=your_linkedin_short_lived_or_long_lived_token

# LLM Config
GROQ_API_KEY=your_groq_api_token

# Image Downloader Config
UNSPLASH_ACCESS_KEY=your_unsplash_access_key

# Email Notifications (SMTP settings)
NOTIFICATION_EMAIL=recipient_email@domain.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=465
SMTP_USERNAME=your_gmail_sender_username@gmail.com
SMTP_PASSWORD=your_gmail_app_specific_password
```

---

## ⏰ Scheduler Timings

| Job | Trigger Time | Action |
| :--- | :--- | :--- |
| **PR Post (Mon/Wed/Fri)** | `09:00 AM EST` | Research, generate, and publish post |
| **PR Post (Tue/Thu)** | `12:00 PM EST` | Research, generate, and publish post |
| **Weekly PR Summary** | `Sunday 06:00 PM EST` | Compile weekly stats report and email |
| **Lead Generation** | `Daily 10:00 AM EST` | Scrape leads, deduplicate, save, and email |

---

## 🤖 Locked Prompt Templates

### 1. LinkedIn Post Copy Generation
*   **Model**: `llama-3.3-70b-versatile`
*   **System Prompt**:
    ```
    System: You are Tarun Srivastava, a US Staffing expert and AI thought leader.
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
    Never include the exact phrases '14+ years', '14+ year', '14 years', or '14-year' in the post. Speak from experience implicitly without citing a specific number of years.
    ```

### 2. Unsplash Image Keyword Extraction
*   **Prompt**:
    ```
    You are an expert photo researcher for LinkedIn content.
    Given this LinkedIn post, extract 3-4 VERY SPECIFIC search keywords for finding a perfectly relevant professional photo.

    POST: {post_content}

    RULES:
    - Keywords must reflect the EXACT topic of the post
    - Be specific not generic
    - NO generic words like 'business', 'technology', 'people'
    - Examples:
      Post about AI hiring tools → 'automated resume screening'
      Post about workspace automation → 'robotic process automation software'

    Return ONLY the keywords as a comma-separated list, nothing else.
    ```

### 3. LinkedIn Reply Generation
*   **Prompt**:
    ```
    You recently posted this on LinkedIn:
    "{post_content}"

    A user commented:
    "{comment_text}"

    Write a reply that is short, human, conversational, and direct.
    Rules:
    - Keep it extremely brief (1-2 sentences, under 30 words).
    - Write like a real person, avoiding robotic/corporate buzzwords.
    - Be friendly, helpful, and concise.
    - Do not include hashtags.
    ```

---

## ☁️ Cloud Deployment Guide (Linux Systemd)

Deploying the agent to a Linux VM (e.g. Google Cloud Compute Engine, AWS EC2, or DigitalOcean Droplet) using `systemd` ensures reliability and auto-restart on system reboots.

### Step 1: Copy Code to VM
Upload code files to a directory on your VM, for example:
`/home/anu007lko/linkedin_pr_agent`

### Step 2: Install Python dependencies
```bash
sudo apt update && sudo apt install -y python3-pip python3-venv
cd /home/anu007lko/linkedin_pr_agent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 3: Configure Environment
Copy `.env.example` to `.env` and fill in your API tokens and SMTP passwords:
```bash
cp .env.example .env
nano .env
```

### Step 4: Create Systemd Services
Create a service file for the PR Posting Agent:
`sudo nano /etc/systemd/system/linkedin-pr-agent.service`

Add the following:
```ini
[Unit]
Description=LinkedIn PR Posting Agent Service
After=network.target

[Service]
Type=simple
User=anu007lko
WorkingDirectory=/home/anu007lko/linkedin_pr_agent
ExecStart=/home/anu007lko/linkedin_pr_agent/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Create a service file for the Lead Generation Agent:
`sudo nano /etc/systemd/system/linkedin-lead-agent.service`

Add the following:
```ini
[Unit]
Description=LinkedIn Lead Generation Agent Service
After=network.target

[Service]
Type=simple
User=anu007lko
WorkingDirectory=/home/anu007lko/linkedin_pr_agent
ExecStart=/home/anu007lko/linkedin_pr_agent/venv/bin/python lead_agent.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Step 5: Enable and Start Services
Reload the systemctl daemon, enable the services, and launch them:
```bash
sudo systemctl daemon-reload
sudo systemctl enable linkedin-pr-agent linkedin-lead-agent
sudo systemctl start linkedin-pr-agent linkedin-lead-agent
```

---

## ⚙️ How to Update the Agent

If you make modifications to the codebase or need to pull updates from a Git repository:

1.  Navigate to the project directory:
    ```bash
    cd /home/anu007lko/linkedin_pr_agent
    ```
2.  Pull updates or overwrite source files.
3.  If dependencies changed, update packages inside the virtual environment:
    ```bash
    ./venv/bin/pip install -r requirements.txt
    ```
4.  Restart the background services to apply the updates:
    ```bash
    sudo systemctl restart linkedin-pr-agent linkedin-lead-agent
    ```

---

## 🔍 Commands to Check Agent Status on Cloud

Use the following commands to check running status and read application log output:

### 1. View Service Status (Check if Active/Running)
```bash
sudo systemctl status linkedin-pr-agent
sudo systemctl status linkedin-lead-agent
```

### 2. View Real-Time Logs (Equivalent to tail -f)
```bash
journalctl -u linkedin-pr-agent -n 100 -f
journalctl -u linkedin-lead-agent -n 100 -f
```

### 3. Restart / Stop / Start Services
```bash
# Restart
sudo systemctl restart linkedin-pr-agent linkedin-lead-agent
# Stop
sudo systemctl stop linkedin-pr-agent linkedin-lead-agent
# Start
sudo systemctl start linkedin-pr-agent linkedin-lead-agent
```

---

## 🛠️ Common Errors and Fixes

### Error 1: `LINKEDIN_ACCESS_TOKEN is missing or placeholder`
*   **Symptom**: The agent logs skip posting or report missing token, or you receive warning emails about token expiry.
*   **Cause**: The access token inside `.env` is invalid, expired, or has not been supplied.
*   **Fix**:
    1. Generate a new LinkedIn access token from the Developer Portal.
    2. Edit `.env` and assign `LINKEDIN_ACCESS_TOKEN=your_new_token`.
    3. Restart services: `sudo systemctl restart linkedin-pr-agent`.

### Error 2: SMTP Connection Refused / SMTPAuthenticationError
*   **Symptom**: Status emails are not being received and logs show SMTP exceptions.
*   **Cause**: Port 465 is blocked by your Cloud Provider firewall, or App Passwords are not configured on the sending Gmail account.
*   **Fix**:
    1. Ensure Gmail "App Passwords" is enabled and set up. Paste the 16-character code into `SMTP_PASSWORD` inside `.env`.
    2. Check with your cloud provider (e.g. GCP) to ensure outbound mail ports (like 465 or 587) are not restricted by local egress firewall rules.

### Error 3: EOL while scanning string literal (SyntaxError)
*   **Symptom**: Script fails to parse and throws Python compile syntax error on startup.
*   **Cause**: A typo in code strings.
*   **Fix**: Verify all quotation marks inside the python files (`"`, `'`) match and terminate correctly. Run unit tests (`python3 test_linkedin_bot.py`) to confirm compilation succeeds.
