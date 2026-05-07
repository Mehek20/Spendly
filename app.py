from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from datetime import datetime, date, timedelta
from database.db import get_db, init_db, seed_db
from database.profile_transactions import get_transactions
from database.profile_stats        import get_stats
from database.profile_categories   import get_categories
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "dev-secret-key-change-in-production"

with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Helpers                                                             #
# ------------------------------------------------------------------ #

def _parse_date_filter():
    """Parse and validate ?from=&to= query params. Returns (date, date) or (None, None)."""
    raw_from = request.args.get("from", "").strip()
    raw_to   = request.args.get("to",   "").strip()
    if not raw_from or not raw_to:
        return None, None
    try:
        d_from = datetime.strptime(raw_from, "%Y-%m-%d").date()
        d_to   = datetime.strptime(raw_to,   "%Y-%m-%d").date()
    except ValueError:
        return None, None
    if d_from > d_to:
        return None, None
    return d_from, d_to


def _build_presets():
    today      = date.today()
    first_this = today.replace(day=1)
    last_prev  = first_this - timedelta(days=1)
    first_prev = last_prev.replace(day=1)
    three_ago  = today - timedelta(days=90)
    six_ago    = today - timedelta(days=180)

    # 'from' is a Python keyword so it can't be used as a kwarg directly
    def make_url(d_from, d_to):
        return url_for("profile", **{"from": str(d_from), "to": str(d_to)})

    return {
        "this_month":    make_url(first_this, today),
        "last_3_months": make_url(three_ago,  today),
        "last_6_months": make_url(six_ago,    today),
    }


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    if session.get("user_id"):
        return redirect(url_for("profile"))
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("landing"))
    if request.method == "GET":
        return render_template("register.html")

    name     = request.form.get("name", "").strip()
    email    = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    confirm  = request.form.get("confirm_password", "")

    if not name:
        return render_template("register.html", error="Full name is required.", name=name, email=email)
    if "@" not in email or "." not in email:
        return render_template("register.html", error="Enter a valid email address.", name=name, email=email)
    if len(password) < 8:
        return render_template("register.html", error="Password must be at least 8 characters.", name=name, email=email)
    if password != confirm:
        return render_template("register.html", error="Passwords do not match.", name=name, email=email)

    try:
        db = get_db()
        db.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, generate_password_hash(password)),
        )
        db.commit()
        db.close()
    except sqlite3.IntegrityError:
        return render_template("register.html", error="An account with that email already exists.", name=name, email=email)

    flash("Account created! Please sign in.", "success")
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("landing"))
    if request.method == "GET":
        return render_template("login.html")

    email    = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    db  = get_db()
    row = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    db.close()

    if row is None or not check_password_hash(row["password_hash"], password):
        return render_template("login.html", error="Invalid email or password.", email=email)

    session["user_id"]   = row["id"]
    session["user_name"] = row["name"]
    return redirect(url_for("profile"))


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("landing"))


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    user_id        = session["user_id"]
    date_from, date_to = _parse_date_filter()
    date_from_str  = str(date_from) if date_from else None
    date_to_str    = str(date_to)   if date_to   else None
    presets        = _build_presets()
    db             = get_db()

    try:
        row = db.execute(
            "SELECT name, email, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()

        if row is None:
            session.clear()
            flash("Session expired. Please sign in again.", "error")
            return redirect(url_for("login"))

        try:
            member_since = datetime.strptime(
                row["created_at"][:10], "%Y-%m-%d"
            ).strftime("%d %b %Y")
        except (ValueError, TypeError):
            member_since = "Unknown"

        name = row["name"]
        initials = "".join(part[0].upper() for part in name.split() if part)[:2]

        user = {
            "name":         name,
            "email":        row["email"],
            "initials":     initials,
            "member_since": member_since,
        }

        transactions = get_transactions(db, user_id, date_from_str, date_to_str)
        stats        = get_stats(db, user_id, date_from_str, date_to_str)
        categories   = get_categories(db, user_id, date_from_str, date_to_str)

    finally:
        db.close()

    return render_template(
        "profile.html",
        user=user,
        stats=stats,
        transactions=transactions,
        categories=categories,
        date_from=date_from_str,
        date_to=date_to_str,
        presets=presets,
    )


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
