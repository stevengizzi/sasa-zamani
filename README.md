# Sasa/Zamani

A tool for finding out what your life is mythologically about.

Sasa/Zamani takes raw lived experience — Telegram messages, conversation transcripts — and, through AI-assisted semantic clustering and myth generation, helps individuals and communities see what their life is mythologically about. Grounded in Mbiti's philosophy of Bantu time, where the past pools in front of you organized by resonance rather than chronology.

## Tech Stack

- **Backend:** Python 3.12 + FastAPI
- **Database:** Supabase (Postgres 15 + pgvector)
- **Embeddings:** OpenAI text-embedding-3-small (1536 dim)
- **Myth generation:** Claude Sonnet via Anthropic SDK
- **Telegram:** python-telegram-bot (webhook mode)
- **Frontend:** Single HTML/JS/Canvas file
- **Deployment:** Railway (auto-deploy from GitHub)

## Setup

```bash
git clone git@github.com:YOUR_USERNAME/sasa-zamani.git
cd sasa-zamani
pip install -r requirements.txt
cp .env.example .env
# Fill in your API keys in .env
uvicorn app.main:app --reload
```

Visit http://localhost:8000 to see the Sasa Map.

## Methodology

This project uses the claude-workflow methodology for development.
