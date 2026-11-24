[English](AI_LOG.md) · [Português (Brasil)](AI_LOG.pt-BR.md)

# AI Log

Rule: record what the AI generated, what we checked, and what we corrected. Nobody presents code they cannot explain.

## AI in the product

| Where | What the AI does | Guardrail |
|---|---|---|
| `POST /api/ai/describe` | Looks at the photo and suggests type, color, marks, a one-line description and a sensitive flag | Always returned with `needs_review: true`. The form needs a "I reviewed this" checkbox before saving. Output is validated against fixed lists (unknown values become `outro` / `outra`). |
| Sensitive photo alert | AI flags documents, cards or faces | Flagged photos are hidden publicly. The prompt forbids identifying people or transcribing numbers or names. |
| `matching.py` (not an LLM) | Ranks candidates for a loss report | Deterministic scoring, suggestions only. The owner still passes the pickup code and desk check. |
| No API key or API error | Falls back to a local color analyzer | The UI says plainly that only the color was suggested. |

## AI in the process

| Date | Tool | Purpose | What it generated | What we verified or corrected | Reviewed by |
|---|---|---|---|---|---|
| 2026-11-23 | Claude (Anthropic) | First scaffold from the brief | Flask API, SQLite schema, matching, privacy helpers, static front-end, CI workflow, scripts, docs (EN and pt-BR) | Ran 19 back-end tests and 5 front-end tests, a server smoke test, `node --check`. Fixed during generation: the Node test command (`node --test tests/` failed, now `node --test`), an unused parameter, a misnamed test. | _team: fill in_ |

### Not yet verified (honest list)

- `ruff check` and the GitHub Actions workflow were written but **not run** in the environment that generated them. Run them on the first PR and fix anything they report.
- The call to the Anthropic API was **not exercised against the live API**. Test it with a real key and a few real photos, and check the JSON parsing and the sensitive flag.
- The UI was not tested in a browser by the generator. Click through all four tabs on desktop and mobile.
- `setup-github.sh` was not run. Check branch protection and the professor's access in the repository settings.

### Template for new entries

| Date | Tool | Purpose | What it generated | What we verified or corrected | Reviewed by |
|---|---|---|---|---|---|
| | | | | | |

## Lessons (fill in before the demo)

- Where did the AI save us time?
- Where was it wrong or too confident, and how did we notice?
