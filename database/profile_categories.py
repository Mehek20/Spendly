def get_categories(db, user_id):
    rows = db.execute(
        """
        SELECT   category, SUM(amount) AS cat_total
        FROM     expenses
        WHERE    user_id = ?
        GROUP BY category
        ORDER BY cat_total DESC
        """,
        (user_id,),
    ).fetchall()

    if not rows:
        return []

    max_total = rows[0]["cat_total"]
    result = []
    for row in rows:
        pct = round((row["cat_total"] / max_total) * 100) if max_total > 0 else 0
        result.append({
            "name":   row["category"],
            "amount": f"₹{row['cat_total']:,.2f}",
            "pct":    pct,
        })
    return result
