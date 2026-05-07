# Spec: Backend Routes For Profile Page

## Overview
This feature replaces the hardcoded dummy data in the `/profile` route with real database queries. Step 4 built the complete profile UI using hardcoded Python dicts; Step 5 wires it up to the `users` and `expenses` tables so every logged-in user sees their own name, email, membership date, spending stats, transaction history, and category breakdown — all pulled live from SQLite.

## Depends on
- Step 1: Database setup (users and expenses tables must exist)
- Step 2: Registration (real user accounts must be in the DB)
- Step 3: Login + Logout (session must carry a valid user_id)
- Step 4: Profile page UI (profile.html template must exist)

## Routes
- `GET /profile` — replace hardcoded context with live DB queries — logged-in only

No new routes. The existing route signature stays the same; only the view body changes.

## Database changes
No database changes. The existing `users` and `expenses` tables are sufficient.

## Templates
- **Modify:** `templates/profile.html` — update any hardcoded values that are now supplied dynamically (e.g. member-since date format, stats, category percentages). The structure and CSS classes must remain unchanged.

## Files to change
- `app.py` — rewrite the `/profile` view function body to:
  1. Look up the logged-in user from `users` where `id = session["user_id"]`
  2. Query all expenses for that user, ordered by date DESC
  3. Compute `total_spent` (SUM of amount), `transaction_count` (COUNT), `top_category` (category with highest total)
  4. Build the per-category breakdown with amount and percentage of total
  5. Format all amounts as `₹{:,.2f}` (Indian rupee, comma-separated)
  6. Format dates as `DD Mon YYYY` (e.g. `12 Apr 2025`) using Python's `strftime`
  7. Pass real `user`, `stats`, `transactions`, and `categories` dicts to `profile.html`

## Files to create
No new files.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — use raw sqlite3 via `get_db()` only
- Parameterised queries only — never string-format SQL
- Passwords hashed with werkzeug (no auth changes in this step)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Close the DB connection after each query block (call `db.close()`)
- Category percentage: `pct = round(cat_total / total_spent * 100)` — clamp to 100 max
- If the user has zero expenses, `stats` should default to zeros and `transactions`/`categories` to empty lists — do not crash
- The `user` dict passed to the template must include: `name`, `email`, `initials` (first letter of each word in name, uppercased), `member_since` (formatted date string)
- Do not change template structure or CSS class names — only update the data source

## Definition of done
- [ ] Visiting `/profile` while logged in shows the real user's name and email (not "Demo User" / "demo@spendly.com" unless that is the logged-in user)
- [ ] The member-since date reflects the actual `created_at` value from the `users` table
- [ ] Total spent matches the sum of all expense amounts for that user in the DB
- [ ] Transaction count matches the number of rows in `expenses` for that user
- [ ] Top category reflects the category with the highest total spend for that user
- [ ] The transaction history table lists the user's real expenses, newest first
- [ ] Category breakdown percentages are relative to the user's own total spend
- [ ] A user with zero expenses sees the profile page without errors (stats show 0, tables are empty or show a "no expenses yet" message)
- [ ] No hardcoded demo data remains in the `/profile` view function
