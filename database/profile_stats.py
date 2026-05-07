from database.db import build_date_filter


def get_stats(db, user_id, date_from=None, date_to=None):
    where, params = build_date_filter(user_id, date_from, date_to)

    totals = db.execute(
        "SELECT COALESCE(SUM(amount), 0) AS total_spent, COUNT(*) AS transaction_count"
        " FROM expenses"
        " WHERE " + where,
        params,
    ).fetchone()

    top_row = db.execute(
        "SELECT category, SUM(amount) AS cat_total"
        " FROM expenses"
        " WHERE " + where +
        " GROUP BY category"
        " ORDER BY cat_total DESC"
        " LIMIT 1",
        params,
    ).fetchone()

    return {
        "total_spent":       f"₹{totals['total_spent']:,.2f}",
        "transaction_count": totals["transaction_count"],
        "top_category":      top_row["category"] if top_row else "—",
    }
