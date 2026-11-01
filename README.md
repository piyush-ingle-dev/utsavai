# UtsavAI: Celebration & Event Planner

A multi-agent planner for weddings, birthdays and community events. Enter a few details and get an exact
budget split, a dated timeline, a vendor checklist, personalised ideas and risks, and a chat that answers
follow-up questions from a planning knowledge base.

## Stack
- **Backend:** Python 3.12, Flask 3.1 REST API (blueprint), SQLAlchemy 2.0, Flask-Talisman, Flask-Limiter
- **Agents:** LangGraph state graph: Researcher, Planner, Creative, Critic, with a retry loop
- **RAG:** LangChain retriever over a 27-passage planning guide (BM25, works offline)
- **LLM:** LangChain ChatOpenAI against any OpenAI-compatible endpoint (optional; the app works without a key)
- **Frontend:** React 18 + Vite, built into `web/` and served by Flask (one deployment)
- **Quality gates (CI):** ruff, bandit, pip-audit, pytest (53 tests), frontend build

## Project layout
    app.py          application factory, static frontend, error handlers, schema upgrade
    api.py          REST endpoints (blueprint)
    security.py     headers, HTTPS in production, cross-site write check, edit tokens
    config.py       settings from environment variables
    planner.py      rule engine: validation, budget split, dated timeline, vendors
    catalog.py      event data (budget shares, milestones, vendors, ideas)
    models.py       SQLAlchemy model
    agents/         LangGraph pipeline (graph.py), retriever (rag.py), LLM wrapper (llm.py), chat (chat.py)
    frontend/       React source
    tests/          pytest suite

## How the agents work
    retrieve -> structure -> creative -> critic --(failed checks, attempts left)--> creative
                                           \--(passed or out of attempts)--> finalize

- **Researcher** pulls the guide passages that match the event type, theme, city and preferences.
- **Planner** is a rule engine for the budget split, dated timeline and vendor list, so numbers are always exact.
- **Creative** asks the LLM for a summary, ideas, tips and risks grounded in the retrieved passages.
  With no LLM, or on any LLM failure, it builds the same sections from the retrieved passages.
- **Critic** runs deterministic checks (budget adds up, idea quality, dietary preferences respected) and sends
  feedback back to Creative on failure. After 2 attempts the Finalizer strips whatever still fails.

The "How this plan was made" panel in the UI shows every step.

## REST API
| Method | Path | Purpose |
|---|---|---|
| POST | /api/plans | Create a plan; returns `id` and a one-time `edit_token` |
| GET | /api/plans/{id} | Read a plan (`can_edit` is true when a valid `X-Edit-Token` is sent) |
| POST | /api/plans/{id}/toggle | Tick or untick a checklist item (needs `X-Edit-Token`) |
| POST | /api/plans/{id}/ask | Ask a follow-up question (RAG) |
| GET | /api/plans/{id}/calendar.ics | Timeline as a calendar file |
| GET | /api/health | Health check |

## Security
- **Read vs edit access:** the plan id (128-bit random) lets anyone with the link read a plan. Changing it needs
  the edit token, which is shown once to the creator, kept in their browser and stored only as a SHA-256 hash.
- **Cross-site protection:** state-changing requests are rejected unless `Sec-Fetch-Site` says same-origin
  (falling back to an `Origin` check). The API accepts JSON only and uses no cookies.
- **Transport and headers:** in production (Render sets `RENDER`) HTTPS is enforced with HSTS; health checks are exempt.
  Strict CSP (no inline scripts or styles), `X-Frame-Options: DENY`, `nosniff`, and `Cache-Control: no-store` on the API.
- **Input and abuse:** server-side validation, a 32 KB body limit, per-route rate limits, hex-only plan ids.
- **LLM safety:** user text is passed in delimited data blocks, model output is validated and length-limited,
  and numbers and dates never come from the model.
- **Supply chain:** pinned dependencies, `pip-audit` and `bandit` run in CI.

## Accessibility
Semantic landmarks, labelled fields with linked error messages, skip link, focus moved to the main area on
navigation, page titles per view, visible focus, 44px targets, dark mode, reduced-motion support, print styles.
Checked with axe-core (no violations on the form or plan pages).

## Run locally
    python -m venv .venv && .venv\Scripts\activate      # Windows; use source .venv/bin/activate elsewhere
    pip install -r requirements-dev.txt
    python app.py                                        # http://localhost:5000
    pytest -q

Optional LLM: copy `.env.example` to `.env` and set `OPENAI_API_KEY` (plus `OPENAI_BASE_URL` and `OPENAI_MODEL`
for other OpenAI-compatible providers such as Gemini or OpenRouter).

## Change the frontend
    cd frontend && npm install && npm run build          # writes to ../web, commit the result

## Deploy (Render)
The built frontend is committed in `web/`, so Render only needs `pip install -r requirements.txt`. See `render.yaml`.
Set `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL` and `SECRET_KEY` in the dashboard and point an uptime
monitor at `/healthz` to avoid cold starts.
