def get_stats(db, user_id):
    totals = db.execute(
        """
        SELECT COALESCE(SUM(amount), 0) AS total_spent,
               COUNT(*)                 AS transaction_count
        FROM   expenses
        WHERE  user_id = ?
        """,
        (user_id,),
    ).fetchone()

    top_row = db.execute(
        """
        SELECT   category, SUM(amount) AS cat_total
        FROM     expenses
        WHERE    user_id = ?
        GROUP BY category
        ORDER BY cat_total DESC
        LIMIT    1
        """,
        (user_id,),
    ).fetchone()

    return {
        "total_spent":       f"₹{totals['total_spent']:,.2f}",
        "transaction_count": totals["transaction_count"],
        "top_category":      top_row["category"] if top_row else "—",
    }
