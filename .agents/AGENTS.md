# Behavioral Guidelines for future agents on LinkedIn PR & Lead Agent

This project runs a lightweight background daemon suite. Please adhere to the following rules when contributing code:

1.  **Browserless Stack (Locked)**:
    - Keep the codebase 100% lightweight Python + REST APIs.
    - NEVER re-introduce Playwright, scrapers, headless browsers, or browser configuration keys.
    - All actions must query the LinkedIn UGC API or official endpoints directly.

2.  **No RPO Mentions (Locked)**:
    - Never write or let the LLM generate posts mentioning "RPO" or "Recruitment Process Outsourcing".
    - Persona is strictly: "14+ year US Staffing expert and AI thought leader".

3.  **Strict Layout constraints (Locked)**:
    - The generated LinkedIn post copy must adhere to:
      - Line 1: Strong hook
      - Lines 2-3: Empty breathing room
      - Lines 4-8: Core insight/story (3-5 short punchy lines)
      - Line 9: Empty line
      - Lines 10-12: Practical takeaway or CTA
      - Line 13: Empty line
      - Line 14: 3-5 relevant hashtags
      - Length: Under 200 words.

4.  **Unsplash Search Integration (Locked)**:
    - All image postings must extract keywords using the specific photo researcher Groq prompt, search Unsplash orientations, select the first highest resolution landscape photo, and download it locally.
    - Fallback to text-only UGC post if the Unsplash request fails.

5.  **Quality Verification**:
    - Always execute `python3 test_linkedin_bot.py` and `python3 test_phase2.py` to confirm compile correctness before committing structure modifications.
