# HUMAN_TODO.md — Manual Steps Required

Items that cannot be performed autonomously:

1. **Pushing to GitHub remote**:
   - Create a GitHub repository (e.g. `ops-copilot`).
   - Add remote: `git remote add origin git@github.com:<your-user>/ops-copilot.git`
   - Push: `git push -u origin main`

2. **Optional Hosted LLM Keys (Zero-cost free tiers)**:
   - For live hosted LLM testing, provide one of the following in `.env`:
     - `GEMINI_API_KEY`: Get a free key at https://aistudio.google.com/
     - `GROQ_API_KEY`: Get a free key at https://console.groq.com/
     - `OPENROUTER_API_KEY`: Get a free key at https://openrouter.ai/
   - Note: The entire system, tests, CI, and evaluation pipeline run out-of-the-box using the built-in deterministic `mock` provider and local RAG without any API keys or paid accounts.
