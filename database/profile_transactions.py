from datetime import datetime
from database.db import build_date_filter


def get_transactions(db, user_id, date_from=None, date_to=None):
    where, params = build_date_filter(user_id, date_from, date_to)

    sql = (
        "SELECT date, description, category, amount"
        " FROM expenses"
        " WHERE " + where +
        " ORDER BY date DESC, id DESC"
    )
    if not (date_from and date_to):
        sql += " LIMIT 10"

    rows = db.execute(sql, params).fetchall()

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
