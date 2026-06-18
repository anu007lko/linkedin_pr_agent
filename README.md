# Autonomous LinkedIn PR and Lead Agent Suite

An autonomous, lightweight background daemon suite designed to run continuously on a cloud server or local machine. The suite contains two independent agents:

1.  **LinkedIn PR Agent (`main.py`)**: Gathers trending tech and HR news using RSS feeds, writes visionary LinkedIn post copies, searches Unsplash for matching high-resolution professional photos, and publishes them via the official LinkedIn UGC API.
2.  **Lead Generation Agent (`lead_agent.py`)**: Programmatically searches for HR and Talent Acquisition prospects, scores leads based on company size/role, deduplicates contacts, and emails a CSV report daily.

---

## 📁 Project Directory Manifest

| File | Type | Description |
| :--- | :--- | :--- |
| **`main.py`** | Script | Entrypoint and scheduler for the PR Posting Agent. |
| **`lead_agent.py`** | Script | Entrypoint and scheduler for the Lead Generation Agent. |
| **`linkedin_api.py`** | Module | Handles LinkedIn REST API operations (`ugcPosts`, `userinfo`, token checks). |
| **`search_agent.py`** | Module | Queries news sources and RSS feeds for trending articles. |
| **`content_generator.py`** | Module | Calls Groq API (llama-3.3-70b-versatile) for copywriting and Unsplash image downloads. |
| **`memory_manager.py`** | Module | Saves posts, checks 7-day rule, adjusts weights, compiles report. |
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
| **`test_phase2.py`** | Test | Unit tests for topic weights tuning and SMTP report compiler. |
| **`.agents/`** | Config | Project-scoped guidelines and skill references. |

---

## 🛠️ Installation & Setup

Follow these steps to set up and run the agent suite on your local machine or cloud server:

### Step 1: Clone the Repository
```bash
git clone https://github.com/anu007lko/linkedin_pr_agent.git
cd linkedin_pr_agent
```

### Step 2: Create a Virtual Environment & Install Dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
Copy `.env.example` to `.env` and fill in your actual API tokens and SMTP credentials:
```bash
cp .env.example .env
nano .env
```

Ensure the following variables are configured:
*   `LINKEDIN_ACCESS_TOKEN`: Your short-lived or long-lived LinkedIn access token.
*   `GROQ_API_KEY`: Groq API token (uses free-tier `llama-3.3-70b-versatile` model).
*   `UNSPLASH_ACCESS_KEY`: Unsplash developer access token.
*   `NOTIFICATION_EMAIL`: Recipient address for job confirmation and warning summaries.
*   `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`: Credentials for the sending Gmail address (requires App Passwords).

---

## 🧪 Run Unit Tests

Confirm everything is configured correctly by running the test suites:

```bash
# Test LinkedIn URN retrieval, token expiry logic, and UGC posting
python3 test_linkedin_bot.py

# Test dynamic weight adjustments and Unsplash downloading mocks
python3 test_phase2.py

# Test contact search APIs (Hunter, Prospeo, Snov) and lead scoring
python3 test_lead_agent.py
```

---

## 🚀 Running the Agents

Both agents run as infinite scheduler loops:

```bash
# Run the PR Posting Scheduler
python3 main.py

# Run the Lead Generation Scheduler
python3 lead_agent.py
```

---

## ☁️ Cloud VM Deployment (Systemd Services)

For continuous 24/7 execution, deploy on a Linux VM (e.g., GCP Compute Engine, AWS EC2, or DigitalOcean) using `systemd` daemon configurations:

### 1. Create PR Agent Service
Create the configuration file:
`sudo nano /etc/systemd/system/linkedin-pr-agent.service`

Add the following configuration (replace `anu007lko` with your VM username):
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

### 2. Create Lead Agent Service
Create the configuration file:
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

### 3. Start and Enable Daemons
Reload systemctl configurations, enable the background processes, and start them:
```bash
sudo systemctl daemon-reload
sudo systemctl enable linkedin-pr-agent linkedin-lead-agent
sudo systemctl start linkedin-pr-agent linkedin-lead-agent
```

### 4. Monitor Daemon Status and Read Logs
```bash
# Check status
sudo systemctl status linkedin-pr-agent
sudo systemctl status linkedin-lead-agent

# Monitor real-time logs (tail -f equivalent)
journalctl -u linkedin-pr-agent -n 100 -f
journalctl -u linkedin-lead-agent -n 100 -f
```
