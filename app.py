from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from database.db import get_db, init_db, seed_db
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "dev-secret-key-change-in-production"

with app.app_context():
    init_db()
    seed_db()


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

    user = {
        "name": "Demo User",
        "email": "demo@spendly.com",
        "initials": "DU",
        "member_since": "15 Jan 2025",
    }
    stats = {
        "total_spent": "₹12,450.75",
        "transaction_count": 8,
        "top_category": "Food",
    }
    transactions = [
        {"date": "12 Apr 2025", "description": "Groceries",          "category": "Food",          "amount": "₹850.00"},
        {"date": "11 Apr 2025", "description": "Metro card recharge", "category": "Transport",     "amount": "₹500.00"},
        {"date": "10 Apr 2025", "description": "Electricity bill",    "category": "Bills",         "amount": "₹2,200.00"},
        {"date": "09 Apr 2025", "description": "Doctor visit",        "category": "Health",        "amount": "₹800.00"},
        {"date": "08 Apr 2025", "description": "Movie tickets",       "category": "Entertainment", "amount": "₹1,150.00"},
        {"date": "05 Apr 2025", "description": "New clothing",        "category": "Shopping",      "amount": "₹3,200.00"},
        {"date": "03 Apr 2025", "description": "Miscellaneous",       "category": "Other",         "amount": "₹2,801.75"},
        {"date": "01 Apr 2025", "description": "Grocery shopping",    "category": "Food",          "amount": "₹949.00"},
    ]
    categories = [
        {"name": "Shopping",      "amount": "₹3,200.00", "pct": 100},
        {"name": "Other",         "amount": "₹2,801.75", "pct": 88},
        {"name": "Food",          "amount": "₹2,300.00", "pct": 72},
        {"name": "Bills",         "amount": "₹2,200.00", "pct": 69},
        {"name": "Entertainment", "amount": "₹1,150.00", "pct": 36},
        {"name": "Health",        "amount": "₹800.00",   "pct": 25},
        {"name": "Transport",     "amount": "₹500.00",   "pct": 16},
    ]
    return render_template("profile.html", user=user, stats=stats,
                           transactions=transactions, categories=categories)


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
