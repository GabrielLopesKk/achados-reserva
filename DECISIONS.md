[English](DECISIONS.md) · [Português (Brasil)](DECISIONS.pt-BR.md)

# Decisions

Format: context, decision, why. Add a dated entry whenever the team changes direction.

## D1. MVP scope (day 1)

**In:** register found item with photo, date, place and status; AI description with mandatory human review; loss reports; search with filters; interest and return flow; status updates; reception panel.
**Extra, included because cheap:** candidate matching for a loss report; sensitive photo alert.
**Out for now:** push or e-mail notifications, map of hot spots, QR pickup receipt, user accounts.
**Out of scope (from the brief):** mail logistics, payment or auctions, facial recognition, police reports.
**Why:** one complete, demonstrable flow beats a long half-finished list.

## D2. Stack

- **Back-end: Python + Flask + SQLite.** Small surface, one process, zero setup for the demo, easy to test with `unittest` and the Flask test client.
- **Front-end: static HTML/CSS and ES modules, no framework or bundler.** Nothing to build, so CI and onboarding stay simple. Logic that can be tested lives in `lib.js` and runs under `node --test`.
- **AI: Anthropic Messages API with an image block, local fallback.** Vision gives useful attributes (type, marks). The fallback keeps the product usable offline or without a key.
- **Trade-off:** no ORM and no SPA framework. If the team outgrows this, migrate the data layer first.

## D3. Who is the right person at pickup?

Showing interest creates a one-time **pickup code**, shown once to the claimant and stored only as a hash. Reception returns the item only after typing that code (and should also check a photo ID). The system never shows the claimant's contact in public, and reception sees it masked.
**Limit:** the code proves possession of the code, not identity. The ID check at the desk is the real safeguard.

## D4. Photos with documents, cards or faces

The AI flags them and the person can also tick "contains document". Such photos are hidden from public search and served only with the reception token. Documents and cards are always treated as sensitive by type. Photos are re-encoded to drop EXIF.
**Not done:** no face detection ourselves (out of scope), we rely on AI flags and the human checkbox.

## D5. Who keeps the physical object?

The reception holds every item. Finders are told to drop it there and are not responsible afterwards. The registry status mirrors the physical state.

## D6. How long is an item visible?

90 days (`VISIBILITY_DAYS`), counted from registration, or until returned. Reception can still see open items. What happens to unclaimed objects after that is a campus policy question, outside this software.

## D7. Search when the person remembers little

Filters are all optional, text search is accent-insensitive, and a loss report returns ranked **candidates** by type, color, place and shared words. Candidates are suggestions, and the owner must still claim and pass the pickup check.

## D8. Reception authentication

A single shared `STAFF_TOKEN` sent in a header. Simple on purpose for a one-week MVP.
**Known limit:** no per-person accounts and no audit log, and there is no rate limiting. First things to add for production.

## D9. Process

Pull requests with 1 review, protected `main`, Conventional Commits, CI on PRs and `main`. Configured by `scripts/setup-github.sh`.
