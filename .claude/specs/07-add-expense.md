# Spec: Add Expense

## Overview
This feature replaces the `/expenses/add` stub route with a fully functional form that lets logged-in users record a new expense. The user fills in an amount, category, date, and optional description; on submission the expense is inserted into the `expenses` table and the user is redirected to their profile page with a success flash message. This is the first write path for expense data and unlocks the edit and delete steps that follow.

## Depends on
- Step 01 — Database schema (`expenses` table must exist)
- Step 03 / 04 — Auth and profile page (session-based login required; profile page is the redirect target)

## Routes
- `GET  /expenses/add` — Render the add-expense form — logged-in only
- `POST /expenses/add` — Validate and insert the new expense, then redirect — logged-in only

## Database changes
No new tables or columns. The existing `expenses` table already has all required columns:
`id`, `user_id`, `amount`, `category`, `date`, `description`, `created_at`.

## Templates
- **Create:** `templates/add_expense.html` — form page extending `base.html`
- **Modify:** none

## Files to change
- `app.py` — replace the `add_expense` stub with GET + POST handling

## Files to create
- `templates/add_expense.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — use raw SQLite via `get_db()`
- Parameterised queries only — never interpolate user input into SQL strings
- Passwords hashed with werkzeug (not applicable here, but maintain the convention)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Redirect unauthenticated users to `/login`
- `amount` must be a positive number; reject zero or negative values
- `category` must be one of the fixed set used in the seed data: Food, Transport, Bills, Health, Entertainment, Shopping, Other
- `date` must be a valid calendar date in `YYYY-MM-DD` format; default the field to today's date
- `description` is optional (max 200 characters)
- On validation failure, re-render the form with the error message and the user's previously entered values so they don't have to retype everything
- On success, flash a confirmation message and redirect to `/profile`
- The route decorator must accept both `GET` and `POST`: `methods=["GET", "POST"]`

## Definition of done
- [ ] Visiting `/expenses/add` while logged out redirects to `/login`
- [ ] Visiting `/expenses/add` while logged in renders a form with fields: amount, category (dropdown), date, description
- [ ] The date field defaults to today's date
- [ ] Submitting the form with a valid amount, category, and date inserts a row into the `expenses` table and redirects to `/profile` with a success flash
- [ ] The new expense appears in the transaction list on the profile page immediately after submission
- [ ] Submitting with a missing or zero amount re-renders the form with an error and the previously entered values preserved
- [ ] Submitting with an invalid date re-renders the form with an error
- [ ] Submitting with a description over 200 characters re-renders the form with an error
