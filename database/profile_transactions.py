from datetime import datetime


def get_transactions(db, user_id):
    rows = db.execute(
        """
        SELECT date, description, category, amount
        FROM   expenses
        WHERE  user_id = ?
        ORDER  BY date DESC, id DESC
        LIMIT  10
        """,
        (user_id,),
    ).fetchall()

    result = []
    for row in rows:
        try:
            formatted_date = datetime.strptime(row["date"][:10], "%Y-%m-%d").strftime("%d %b %Y")
        except (ValueError, TypeError):
            formatted_date = row["date"]
        result.append({
            "date":        formatted_date,
            "description": row["description"] or "",
            "category":    row["category"],
            "amount":      f"₹{row['amount']:,.2f}",
        })
    return result
