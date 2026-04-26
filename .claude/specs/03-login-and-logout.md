# Spec: Login and Logout

## Overview
Implement user login and logout so registered Spendly users can authenticate and end their session. Login converts the existing GET-only `/login` stub into a full GET/POST route that validates credentials against the `users` table, verifies the password hash, and stores the user identity in Flask's server-side session. Logout clears the session and redirects to the landing page. Together these two routes complete the authentication loop started by Registration and make the navbar session-aware.

## Depends on
- Step 01 — Database setup (`users` table and `get_db()` must exist)
- Step 02 — Registration (at least one user with a hashed password must exist to test against)

## Routes
- `GET  /login`  — render the login form — public
- `POST /login`  — validate credentials and start a session — public
- `GET  /logout` — clear the session and redirect to landing — logged-in

## Database changes
No database changes. The existing `users` table (`id`, `name`, `email`, `password_hash`, `created_at`) is sufficient.

## Templates
- **Modify:** `templates/login.html` — re-populate the email field on failed login by passing the submitted email back to the template (`value="{{ email or '' }}"`)
- **Modify:** `templates/base.html` — make the navbar session-aware: when `session.user_id` is set, show the user's name and a "Sign out" link; otherwise show the existing "Sign in" / "Get started" links

## Files to change
- `app.py` — (1) add `check_password_hash` to the werkzeug import; (2) add `methods=["GET", "POST"]` to the `/login` route and implement POST logic; (3) implement the `/logout` route with `session.clear()`
- `templates/login.html` — add `value="{{ email or '' }}"` to the email input so it survives a failed submission
- `templates/base.html` — update `.nav-links` to branch on `session.get("user_id")`

## Files to create
None.

## New dependencies
No new pip packages. Uses:
- `werkzeug.security.check_password_hash` (already installed, just not yet imported)
- `flask.session`, `flask.flash`, `flask.redirect`, `flask.url_for`, `flask.request` (all already imported in `app.py`)

## Rules for implementation
- No SQLAlchemy or ORMs — use raw `sqlite3` via `get_db()`
- Parameterised queries only — no string interpolation in SQL
- Passwords verified with `werkzeug.security.check_password_hash`
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- On failed login, show a single generic error: `"Invalid email or password."` — never reveal which field was wrong
- Store only `session["user_id"]` (integer) and `session["user_name"]` (string) — never put the password hash in the session
- Close the DB connection after querying
- After successful login, redirect to `url_for("profile")`
- Logout must use `session.clear()` (not `session.pop`) then `redirect(url_for("landing"))`
- Flash a `"success"` message `"You have been signed out."` after logout

## Definition of done
- [ ] Visiting `/login` renders the form without errors
- [ ] Submitting valid credentials sets `session["user_id"]` and `session["user_name"]` and redirects to `/profile`
- [ ] The "Account created! Please sign in." flash from registration is visible on the login page after redirect
- [ ] Submitting an unknown email shows "Invalid email or password." and re-renders the form
- [ ] Submitting the correct email with a wrong password shows "Invalid email or password." and re-renders the form
- [ ] The email field is pre-filled with the submitted value after a failed login attempt
- [ ] Visiting `/logout` clears the session, shows the "You have been signed out." flash, and lands on the home page
- [ ] After logout, `session.get("user_id")` is `None` (verifiable in Flask shell or by checking the navbar)
- [ ] The navbar shows "Sign out" and the user's name when logged in, and "Sign in" / "Get started" when logged out
- [ ] App starts without errors after changes
