# Autonomous LinkedIn PR Agent: Skills and Rules

## 🧠 SKILLS
- **Research Skill**: Finds trending AI news using RSS feeds (TechCrunch, VentureBeat, AI News) via the `feedparser` library.
- **Writing Skill**: Generates LinkedIn posts strictly under 200 words with a visionary and professional tone using the Gemini API.
- **Memory Skill**: Uses local `memory.json` to track post history and engagement, ensuring topics are never repeated within a 7-day window.
- **Posting Skill**: Automates direct publishing to LinkedIn using the official LinkedIn UGC REST API.
- **Interaction Skill**: Periodically checks for post metrics and automatically likes user comments using the LinkedIn Social Actions API.
- **Notification Skill**: Sends automated email reports via Gmail SMTP after every successful or failed post.

## 📜 RULES
1. **Content Mix**: 
   - 40% AI tools and breakthroughs
   - 25% AI in Human Resources
   - 20% New AI product launches
   - 15% AI in Talent Acquisition
2. **Hashtags**: Always append exactly 3-5 relevant hashtags at the end of every post.
3. **Repetition**: Never post about the same topic category within 7 days.
4. **LinkedIn API Failures**: If the LinkedIn API request fails, the agent will abort the current run, wait 24 hours (until the next scheduled cron job), and retry with a new post.
5. **Gemini Failures**: If the Gemini API returns an error (e.g., 503), the agent will wait 10 seconds and retry up to 3 times before skipping the post for the day.
