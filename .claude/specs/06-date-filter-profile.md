# Spec: Date Filter For Profile Page

## Overview
This feature adds a date-range filter to the profile page so users can narrow the transaction history, spending stats, and category breakdown to a specific period. Filtering is driven by GET query parameters (`?from=YYYY-MM-DD&to=YYYY-MM-DD`) submitted via a plain HTML form — no JavaScript required. A set of quick-select preset buttons ("This Month", "Last Month", "Last 3 Months", "All Time") populate the date inputs for convenience. When no filter is active all existing data is shown, preserving the current default behaviour.

## Depends on
- Step 1: Database setup (expenses table must exist with a `date` column)
- Step 4: Profile page UI (profile.html must exist)
- Step 5: Backend routes for profile page (live DB queries must replace hardcoded data)

## Routes
- `GET /profile?from=YYYY-MM-DD&to=YYYY-MM-DD` — same route, now reads optional `from` / `to` query params and applies them to all DB queries — logged-in only

No new routes.

## Database changes
No database changes. The `date` column on the `expenses` table is already `TEXT` in `YYYY-MM-DD` format, which supports direct string comparison in SQLite (`WHERE date BETWEEN ? AND ?`).

## Templates
- **Modify:** `templates/profile.html`
  - Add a filter form (method GET, action `/profile`) above the transaction history section
  - Two `<input type="date">` fields: `name="from"` and `name="to"`, pre-populated with the current filter values passed from the route
  - A submit button ("Apply Filter")
  - Three quick-select anchor links that append preset query strings: "This Month", "Last Month", "Last 3 Months", "All Time" (clears params)
  - Display an active-filter notice (e.g. "Showing results from DD Mon YYYY to DD Mon YYYY") when a filter is applied
  - All existing CSS classes and template structure remain unchanged; only new elements are added

## Files to change
- `app.py` — update the `/profile` view to:
  1. Read `request.args.get("from")` and `request.args.get("to")` (both optional)
  2. Validate that if both are provided they are valid `YYYY-MM-DD` strings and `from <= to`; flash an error and ignore invalid values silently
  3. Pass `date_from` and `date_to` through to `get_transactions`, `get_stats`, and `get_categories`
  4. Pass `date_from`, `date_to`, and preset URL helpers back to the template context
- `database/profile_transactions.py` — add optional `date_from=None` and `date_to=None` parameters to `get_transactions()`; extend the SQL `WHERE` clause with `AND date >= ?` / `AND date <= ?` when the values are provided
- `database/profile_stats.py` — add the same optional date params to `get_stats()` and apply them to both sub-queries
- `database/profile_categories.py` — add the same optional date params to `get_categories()` and apply them to the query

## Files to create
No new files.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — use raw sqlite3 via `get_db()` only
- Parameterised queries only — never string-format SQL; append `?` placeholders conditionally
- Passwords hashed with werkzeug (no auth changes in this step)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Date validation: use `datetime.strptime(value, "%Y-%m-%d")` and catch `ValueError`; on failure treat the param as absent (do not crash)
- When only one of `from` / `to` is provided it should be silently ignored (require both or neither)
- SQLite date comparison uses lexicographic string order on `YYYY-MM-DD` which is correct — no casting needed
- Preset quick-select links must be plain `<a href>` tags — no JS required
- The form must submit via GET so the filtered URL is bookmarkable
- `get_transactions` must still apply the existing `LIMIT 10` only when no date filter is active; when a filter is active show all matching rows (no hard limit)
- Stats and category percentages must reflect only the filtered date range, not the all-time totals

## Definition of done
- [ ] Visiting `/profile` with no query params shows the same data as before (no regression)
- [ ] Submitting the date filter form with a valid range shows only transactions whose `date` falls within that range
- [ ] The spending stats (total, count, top category) and category breakdown reflect only the filtered range
- [ ] The date inputs are pre-populated with the currently active filter values after submission
- [ ] An active-filter notice appears when a filter is applied and is absent when no filter is active
- [ ] Supplying only one of `from` / `to` silently ignores the partial filter and shows all-time data
- [ ] Supplying an invalid date string (e.g. `from=not-a-date`) silently ignores the filter and shows all-time data
- [ ] Supplying `from > to` silently ignores the filter and shows all-time data
- [ ] Quick-select "This Month" link correctly filters to the current calendar month
- [ ] Quick-select "Last Month" link correctly filters to the previous calendar month
- [ ] Quick-select "Last 3 Months" link correctly filters to the last 90 days
- [ ] Quick-select "All Time" link removes all filter params and shows full history
- [ ] A date range that matches zero expenses shows the profile with zeros and empty lists (no crash)
