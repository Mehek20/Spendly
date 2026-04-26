# Spec: Registration

## Overview
Implement user registration so new visitors can create a Spendly account. This is the first authentication step in the roadmap — it wires the existing `/register` stub into a working GET/POST route that validates input, hashes the password, and inserts a row into the `users` table. On success the user is shown with a success message and then redirected to the login page; on failure the form is re-rendered with an error message.

## Depends on
- Step 01 — Database setup (`users` table must exist, `get_db()` must work)

## Routes
- `GET  /register` — render the registration form — public
- `POST /register` — validate and create a new user account — public

## Database changes
No new tables or columns. The existing `users` table (`id`, `name`, `email`, `password_hash`, `created_at`) is sufficient.

## Templates
- **Modify:** `templates/register.html` — convert the static placeholder into a real form that:
  - Has fields: Full Name, Email, Password, Confirm Password
  - Posts to `POST /register`
  - Displays a flash error message when validation fails
  - Shows an inline link to `/login` for existing users

## Files to change
- `app.py` — implement `GET` and `POST` logic for `/register`; add `secret_key`, `session`, `flash`, `redirect`, `url_for`, `request` imports from Flask
- `templates/register.html` — add the form and flash message block
- `static/css/style.css` — add form and flash styles if not already present (use CSS variables only)

## Files to create
None.

## New dependencies
No new pip packages. Uses:
- `werkzeug.security.generate_password_hash` (already installed)
- `flask.session`, `flask.flash`, `flask.redirect`, `flask.url_for`, `flask.request` (already installed)

## Rules for implementation
- No SQLAlchemy or ORMs — use raw `sqlite3` via `get_db()`
- Parameterised queries only — no string interpolation in SQL
- Passwords hashed with `werkzeug.security.generate_password_hash`
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- `app.secret_key` must be set (use a hard-coded dev string for now; a comment can note it should come from env in production)
- Validate server-side: name non-empty, valid email format (basic check), password ≥ 8 chars, password == confirm password
- Duplicate email must show a user-friendly flash error (catch `sqlite3.IntegrityError`)
- Do not log the user in after registration — redirect to `/login` with a success flash message

## Definition of done
- [ ] Visiting `/register` renders the form without errors
- [ ] Submitting with all valid fields creates a row in `users` and redirects to `/login`
- [ ] The success flash message is visible on the login page after redirect
- [ ] Submitting with a duplicate email shows an error on the register page (no new row created)
- [ ] Submitting with mismatched passwords shows a validation error and re-renders the form
- [ ] Submitting with a password shorter than 8 characters shows a validation error
- [ ] Submitting with an empty name or missing email shows a validation error
- [ ] Password is stored as a bcrypt hash (not plain text) — verifiable via SQLite browser or Python shell
- [ ] App starts without errors after changes
