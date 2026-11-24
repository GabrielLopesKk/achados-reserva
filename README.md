[English](README.md) · [Português (Brasil)](README.pt-BR.md)

# Lost & Found (Achados e Perdidos)

Hack com IA: Codando com Inteligência · Senac na Prática · TDS · Canoas

A small web system to register, describe and find lost objects on the Senac campus. A photo of a found item goes through AI, which suggests a structured description (type, color, visible marks). A person reviews it before publishing. Owners can search, show interest and pick the item up with a one-time code, without any phone number or document ever appearing in a public list.

## Features (MVP)

| Requirement | Where |
|---|---|
| Register a found item (photo, date, approximate place, initial status) | `POST /api/items`, tab "Achei algo" |
| AI description from the photo, reviewed by a human | `POST /api/ai/describe`, mandatory review checkbox |
| Register a loss report | `POST /api/reports`, tab "Perdi algo" |
| Search and filter by type, color, place, words | `GET /api/items`, tab "Procurar" |
| Interest and return flow, no public contact data | `POST /api/items/<id>/claims` + pickup code |
| Status updates (found, awaiting pickup, returned) | `PATCH /api/items/<id>/status` (reception only) |
| Extra: AI-suggested candidates for a loss report | `GET /api/reports/<id>/matches` |
| Extra: sensitive photo alert and hiding | documents, cards and faces are hidden from the public |

## Run locally

Requirements: Python 3.12+, Node 22+ (only for the front-end tests).

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
export STAFF_TOKEN="a-long-random-token"      # reception access
export ANTHROPIC_API_KEY="..."                # optional, see below
python wsgi.py                                # http://localhost:5000
```

Flask serves both the API and the static front-end, so one command runs everything. Without `ANTHROPIC_API_KEY` the app still works: the AI step falls back to a local analyzer that only suggests the dominant color, and the user fills in the rest.

## Tests, lint, CI

```bash
cd backend  && python -m unittest discover -s tests -t . && ruff check .
cd frontend && npm run lint && npm test
```

GitHub Actions (`.github/workflows/ci.yml`) runs build, lint and tests for back-end and front-end on every PR and on `main`, plus a Conventional Commits check on PRs.

## Repository setup (day 1)

```bash
gh auth login
scripts/setup-github.sh OWNER/REPO   # adds the professor as collaborator and protects main
```

## Structure

```
backend/   Flask API, SQLite, AI integration, matching, privacy helpers, tests
frontend/  Static HTML/CSS/ES modules, pure logic in lib.js with tests
scripts/   GitHub setup and commit checks
```

## Privacy by design

- Contacts are stored but never returned by public endpoints. Reception sees a masked contact (`a***@mail.com`, `••••-1234`).
- Pickup codes and report tokens are stored only as SHA-256 hashes.
- Photos are re-encoded on upload, which removes EXIF data such as GPS location.
- Photos of documents, cards and faces are served only to reception.
- Items leave public search after 90 days (`VISIBILITY_DAYS`) or when returned.
- AI output is always a suggestion: nothing is published without a human confirming it.

## Team

Fill in names, roles and GitHub users here.
