# AI Grooming Prep

Automatically generate grooming prep reports from JIRA tickets using AI. Surfaces risks, dependencies, and a suggested discussion order — available as a CLI, REST API, or browser UI.

## Features

- Fetches backlog tickets from JIRA with full metadata
- AI-powered summaries via Groq (purpose, technical scope, open questions)
- Risk detection: missing AC, unclear descriptions, stale tickets, blockers
- Suggested discussion order prioritised by severity
- Three interfaces: CLI, FastAPI backend, Streamlit browser UI
- HTML report generation (CLI mode)

## Setup

### 1. Install dependencies

```bash
pip install -e .
# or for API/UI support
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:

```env
JIRA_URL=https://yourcompany.atlassian.net
JIRA_EMAIL=you@company.com
JIRA_API_TOKEN=your_jira_api_token
JIRA_PROJECT=PROJ                     # optional default project
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile    # optional, this is the default
```

## Usage

### CLI

```bash
grooming-prep --project PROJ --status Backlog
grooming-prep --project PROJ --no-ai        # skip AI, faster
grooming-prep --project PROJ --no-browser   # don't auto-open report
```

Generates an HTML report and opens it in your browser.

### API + UI

```bash
# Terminal 1 — start the API
uvicorn grooming_prep.api:app --reload --port 8000

# Terminal 2 — start the UI
streamlit run streamlit_app.py
```

- Streamlit UI: http://localhost:8501
- Swagger docs: http://localhost:8000/docs

### API endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/report` | Generate a grooming report |

**POST `/report` request body:**

```json
{
  "project": "PROJ",
  "status": "Backlog",
  "skip_ai": false
}
```

## Project Structure

```
src/grooming_prep/
├── config.py          # Environment/config loading
├── jira_client.py     # JIRA API client
├── ai_summarizer.py   # Groq-powered ticket summarizer
├── analyzer.py        # Risk detection and ticket ordering
├── models.py          # Pydantic API models
├── api.py             # FastAPI app
├── report.py          # HTML report generator
└── main.py            # CLI entrypoint
streamlit_app.py       # Streamlit browser UI
```

## Requirements

- Python 3.11+
- JIRA Cloud account with API token
- Groq API key (get one at https://console.groq.com)
