# UtsavAI: Celebration & Event Planner

A multi-agent event planner for weddings, birthdays and community events.

## Stack
- **Backend:** Python, Flask REST API, SQLAlchemy 2.0, Flask-Talisman (CSP), Flask-Limiter
- **Agents:** LangGraph state graph with four agents (Researcher, Planner, Creative, Critic) and a retry loop
- **RAG:** LangChain retriever over a 27-passage planning knowledge base (BM25, no embedding service needed)
- **LLM:** LangChain ChatOpenAI (any OpenAI-compatible endpoint). Optional: the app works fully without a key
- **Frontend:** React 18 + Vite, served by Flask as static files (one deployment)
- **Tests:** pytest, 39 tests

## How the agents work
    retrieve -> structure -> creative -> critic --(failed checks, attempts left)--> creative
                                           \--(passed or out of attempts)--> finalize

- **Researcher** pulls the most relevant guide passages for the event type, theme, city and preferences.
- **Planner** is a rule engine for the budget split, dated timeline and vendor list, so numbers are always exact.
- **Creative** asks the LLM for a summary, ideas, tips and risks grounded in the retrieved passages.
  With no LLM, or on any LLM failure, it builds the same sections straight from the passages.
- **Critic** runs deterministic checks (budget adds up, idea quality, dietary preferences respected).
  On failure it sends feedback back to Creative. After 2 attempts the Finalizer strips what still fails.

The "How this plan was made" panel in the UI shows each step.

## REST API
| Method | Path | Purpose |
|---|---|---|
| POST | /api/plans | Create a plan (JSON body) |
| GET | /api/plans/{id} | Read a plan |
| POST | /api/plans/{id}/toggle | Tick or untick a checklist item |
| POST | /api/plans/{id}/ask | Ask a follow-up question (RAG) |
| GET | /api/plans/{id}/calendar.ics | Timeline as a calendar file |
| GET | /api/health | Health check |

## Security notes
The API accepts JSON only and has no cookies or logins, so there is no session for a cross-site request
to abuse. Plan links are 128-bit random ids. CSP blocks inline scripts and styles. Input is validated and
size-limited, endpoints are rate limited, and user text is passed to the LLM inside delimited data blocks.

## Run locally
    pip install -r requirements.txt
    python app.py                 # http://localhost:5000
    pytest -q

Optional LLM: set `OPENAI_API_KEY` (and `OPENAI_BASE_URL`, `OPENAI_MODEL` for other providers).

## Change the frontend
    cd frontend && npm install && npm run build   # writes to ../web, commit the result

## Deploy (Render)
The built frontend is committed in `web/`, so Render only needs `pip install`. See `render.yaml`.
Add `OPENAI_API_KEY` in the dashboard and point an uptime monitor at `/healthz` to avoid cold starts.
