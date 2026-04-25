# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Spendly** is a Flask-based personal expense tracker built as a step-by-step learning project. Features are implemented progressively across numbered steps (database → auth → expense CRUD). The project targets Indian users (rupee currency).

## Commands

```bash
# Activate virtual environment (required before all other commands)
source venv/Scripts/activate        # Windows/Git Bash
source venv/bin/activate            # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Run development server (port 5001)
python app.py

# Run tests
pytest

# Run a single test file
pytest tests/test_auth.py
```

## Architecture

**Stack:** Python 3 · Flask 3.1.3 · SQLite · Jinja2 · vanilla CSS/JS (no build step)

### Key files

| File | Role |
|------|------|
| `app.py` | Flask entry point — all route definitions live here |
| `database/db.py` | `get_db()`, `init_db()`, `seed_db()` — SQLite helpers |
| `templates/base.html` | Base layout (navbar, footer, Google Fonts CDN) |
| `static/css/style.css` | All styling via CSS custom properties |
| `static/js/main.js` | Client-side JS (stub, extended per step) |

### Request flow

Browser → Flask route in `app.py` → calls `database/db.py` helpers → renders a Jinja2 template from `templates/` → response.

### Database

SQLite file (`database/expense_tracker.db`, gitignored). Connection is obtained via `get_db()`, which sets `row_factory = sqlite3.Row` and enables foreign key enforcement. Tables are created by `init_db()` and optionally seeded by `seed_db()`.

### Templates

All templates extend `templates/base.html` using Jinja2 block inheritance (`{% extends "base.html" %}` / `{% block content %}`).

### CSS design tokens

Defined in `static/css/style.css` as CSS custom properties:
- Colors: `--ink`, `--accent`, `--accent-2`, `--danger`, `--paper`
- Fonts: `--font-display` (DM Serif Display), `--font-body` (DM Sans)
- Layout: `--max-width: 1200px`, `--auth-width: 440px`

### Implementation steps (branch context)

1. Database schema & helpers (`feature/database-setup` — current branch)
2. DB migrations / seeding
3. Register
4. Login
5. Logout
6. Profile
7. Add expense
8. Edit expense
9. Delete expense

Routes for steps 3–9 exist in `app.py` as stubs returning placeholder strings until each step is implemented.
