"""
Tests for spec: 07-add-expense
Covers the GET and POST /expenses/add route for the Spendly expense tracker.
All test logic is derived from the spec, not from reading the implementation.
"""
import sqlite3
from datetime import date

import pytest
from werkzeug.security import generate_password_hash

import database.db as db_module
from app import app as flask_app

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def test_db(tmp_path, monkeypatch):
    """Isolated temp-file SQLite DB patched into db_module for each test."""
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    with flask_app.app_context():
        db_module.init_db()
    return db_path


@pytest.fixture
def client(test_db):
    flask_app.config["TESTING"] = True
    flask_app.config["SECRET_KEY"] = "test-secret"
    return flask_app.test_client()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _add_user(db_path, name="Test User", email="test@example.com", password="password123"):
    """Insert a user directly into the DB and return their id."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        (name, email, generate_password_hash(password)),
    )
    uid = cursor.lastrowid
    conn.commit()
    conn.close()
    return uid


def _login(client, user_id, user_name="Test User"):
    """Inject a session directly — avoids coupling tests to the login route."""
    with client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["user_name"] = user_name


def _count_expenses(db_path, user_id):
    """Return the number of expense rows for a given user."""
    conn = sqlite3.connect(db_path)
    count = conn.execute(
        "SELECT COUNT(*) FROM expenses WHERE user_id = ?", (user_id,)
    ).fetchone()[0]
    conn.close()
    return count


def _fetch_expense(db_path, user_id):
    """Fetch the most-recently inserted expense row for a user."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM expenses WHERE user_id = ? ORDER BY id DESC LIMIT 1",
        (user_id,),
    ).fetchone()
    conn.close()
    return row


VALID_FORM = {
    "amount": "42.50",
    "category": "Food",
    "date": "2026-05-15",
    "description": "Test lunch",
}

VALID_CATEGORIES = [
    "Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"
]


# ---------------------------------------------------------------------------
# TestAuthGuard — unauthenticated access
# ---------------------------------------------------------------------------

class TestAuthGuard:
    def test_unauthenticated_get_redirects_to_login(self, client):
        resp = client.get("/expenses/add")
        assert resp.status_code == 302, "Expected redirect for unauthenticated GET"
        assert "/login" in resp.headers["Location"], "Redirect should point to /login"

    def test_unauthenticated_post_redirects_to_login(self, client):
        resp = client.post("/expenses/add", data=VALID_FORM)
        assert resp.status_code == 302, "Expected redirect for unauthenticated POST"
        assert "/login" in resp.headers["Location"], "Redirect should point to /login"

    def test_unauthenticated_get_does_not_render_form(self, client):
        resp = client.get("/expenses/add", follow_redirects=True)
        assert b"amount" not in resp.data or b"login" in resp.data.lower(), (
            "Unauthenticated user must not see the add-expense form"
        )


# ---------------------------------------------------------------------------
# TestGetForm — authenticated GET renders the form correctly
# ---------------------------------------------------------------------------

class TestGetForm:
    def test_authenticated_get_returns_200(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        resp = client.get("/expenses/add")
        assert resp.status_code == 200, "Expected 200 for authenticated GET"

    def test_form_contains_amount_field(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        html = client.get("/expenses/add").data.decode()
        assert 'name="amount"' in html, "Form must contain an amount input"

    def test_form_contains_category_field(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        html = client.get("/expenses/add").data.decode()
        assert 'name="category"' in html, "Form must contain a category field"

    def test_form_contains_date_field(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        html = client.get("/expenses/add").data.decode()
        assert 'name="date"' in html, "Form must contain a date input"

    def test_form_contains_description_field(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        html = client.get("/expenses/add").data.decode()
        assert 'name="description"' in html, "Form must contain a description input"

    def test_date_field_defaults_to_today(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        html = client.get("/expenses/add").data.decode()
        today = date.today().isoformat()
        assert today in html, f"Date field should default to today ({today})"

    def test_all_valid_categories_present_in_dropdown(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        html = client.get("/expenses/add").data.decode()
        for cat in VALID_CATEGORIES:
            assert cat in html, f"Category '{cat}' should appear in the form dropdown"

    def test_form_uses_post_method(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        html = client.get("/expenses/add").data.decode()
        assert 'method="post"' in html.lower(), "Form must use POST method"

    def test_page_extends_base_template(self, client, test_db):
        """Base template landmarks should be present (nav, footer, or brand name)."""
        uid = _add_user(test_db)
        _login(client, uid)
        html = client.get("/expenses/add").data.decode()
        # base.html includes 'Spendly' in the navbar
        assert "Spendly" in html, "Page must extend base.html (Spendly brand not found)"


# ---------------------------------------------------------------------------
# TestHappyPathPost — valid submission behaviour
# ---------------------------------------------------------------------------

class TestHappyPathPost:
    def test_valid_post_redirects(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        resp = client.post("/expenses/add", data=VALID_FORM)
        assert resp.status_code == 302, "Valid POST must redirect"

    def test_valid_post_redirects_to_profile(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        resp = client.post("/expenses/add", data=VALID_FORM)
        assert "/profile" in resp.headers["Location"], (
            "Successful expense submission must redirect to /profile"
        )

    def test_valid_post_flash_message_on_profile(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        resp = client.post("/expenses/add", data=VALID_FORM, follow_redirects=True)
        assert b"Expense added!" in resp.data, (
            "Flash message 'Expense added!' must appear on the profile page after success"
        )

    def test_valid_post_inserts_row_in_db(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        before = _count_expenses(test_db, uid)
        client.post("/expenses/add", data=VALID_FORM)
        after = _count_expenses(test_db, uid)
        assert after == before + 1, "A new expense row must be inserted on valid POST"

    def test_valid_post_stores_correct_user_id(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        client.post("/expenses/add", data=VALID_FORM)
        row = _fetch_expense(test_db, uid)
        assert row is not None, "Expense row must exist after valid POST"
        assert row["user_id"] == uid, "Expense must be linked to the logged-in user"

    def test_valid_post_stores_correct_amount(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        client.post("/expenses/add", data={**VALID_FORM, "amount": "99.99"})
        row = _fetch_expense(test_db, uid)
        assert row is not None
        assert abs(row["amount"] - 99.99) < 0.001, (
            f"Stored amount should be 99.99, got {row['amount']}"
        )

    def test_valid_post_stores_correct_category(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        client.post("/expenses/add", data={**VALID_FORM, "category": "Transport"})
        row = _fetch_expense(test_db, uid)
        assert row is not None
        assert row["category"] == "Transport", (
            f"Stored category should be 'Transport', got '{row['category']}'"
        )

    def test_valid_post_stores_correct_date(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        client.post("/expenses/add", data={**VALID_FORM, "date": "2026-03-10"})
        row = _fetch_expense(test_db, uid)
        assert row is not None
        assert row["date"] == "2026-03-10", (
            f"Stored date should be '2026-03-10', got '{row['date']}'"
        )

    def test_valid_post_stores_correct_description(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        client.post("/expenses/add", data={**VALID_FORM, "description": "Weekly groceries"})
        row = _fetch_expense(test_db, uid)
        assert row is not None
        assert row["description"] == "Weekly groceries", (
            f"Stored description mismatch: '{row['description']}'"
        )

    def test_valid_post_without_description_succeeds(self, client, test_db):
        """Description is optional — omitting it must still succeed."""
        uid = _add_user(test_db)
        _login(client, uid)
        form_data = {k: v for k, v in VALID_FORM.items() if k != "description"}
        resp = client.post("/expenses/add", data=form_data)
        assert resp.status_code == 302, "POST without description must redirect (success)"
        assert _count_expenses(test_db, uid) == 1, "Row must be inserted even with no description"

    @pytest.mark.parametrize("category", VALID_CATEGORIES)
    def test_each_valid_category_is_accepted(self, client, test_db, category):
        uid = _add_user(test_db)
        _login(client, uid)
        resp = client.post("/expenses/add", data={**VALID_FORM, "category": category})
        assert resp.status_code == 302, (
            f"Category '{category}' should be accepted and result in a redirect"
        )

    def test_expense_visible_on_profile_after_submission(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        client.post(
            "/expenses/add",
            data={**VALID_FORM, "description": "Unique-description-xyz"},
        )
        profile_html = client.get("/profile").data.decode()
        assert "Unique-description-xyz" in profile_html, (
            "New expense must appear in the transaction list on the profile page"
        )


# ---------------------------------------------------------------------------
# TestAmountValidation — invalid amount values
# ---------------------------------------------------------------------------

class TestAmountValidation:
    def test_empty_amount_returns_200(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        resp = client.post("/expenses/add", data={**VALID_FORM, "amount": ""})
        assert resp.status_code == 200, "Empty amount must re-render form (200)"

    def test_zero_amount_returns_200(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        resp = client.post("/expenses/add", data={**VALID_FORM, "amount": "0"})
        assert resp.status_code == 200, "Zero amount must re-render form (200)"

    def test_negative_amount_returns_200(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        resp = client.post("/expenses/add", data={**VALID_FORM, "amount": "-10"})
        assert resp.status_code == 200, "Negative amount must re-render form (200)"

    def test_non_numeric_amount_returns_200(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        resp = client.post("/expenses/add", data={**VALID_FORM, "amount": "abc"})
        assert resp.status_code == 200, "Non-numeric amount must re-render form (200)"

    @pytest.mark.parametrize("bad_amount", [
        "",          # missing entirely
        "0",         # exactly zero
        "0.00",      # zero as float
        "-1",        # negative integer
        "-0.01",     # negative decimal
        "abc",       # alphabetic
        "12.3.4",    # malformed float
        "'; DROP TABLE expenses; --",  # SQL injection attempt
    ])
    def test_invalid_amounts_do_not_insert_row(self, client, test_db, bad_amount):
        uid = _add_user(test_db)
        _login(client, uid)
        client.post("/expenses/add", data={**VALID_FORM, "amount": bad_amount})
        assert _count_expenses(test_db, uid) == 0, (
            f"No expense row should be inserted for invalid amount '{bad_amount}'"
        )

    @pytest.mark.parametrize("bad_amount", [
        "",
        "0",
        "0.00",
        "-1",
        "-0.01",
        "abc",
        "12.3.4",
    ])
    def test_invalid_amounts_return_error_in_response(self, client, test_db, bad_amount):
        uid = _add_user(test_db)
        _login(client, uid)
        resp = client.post("/expenses/add", data={**VALID_FORM, "amount": bad_amount})
        assert resp.status_code == 200, (
            f"Expected 200 re-render for invalid amount '{bad_amount}'"
        )
        # Error text should indicate the problem
        html = resp.data.decode()
        assert "amount" in html.lower() or "error" in html.lower() or "positive" in html.lower(), (
            f"Response for invalid amount '{bad_amount}' must contain an error indicator"
        )


# ---------------------------------------------------------------------------
# TestCategoryValidation — invalid category values
# ---------------------------------------------------------------------------

class TestCategoryValidation:
    @pytest.mark.parametrize("bad_category", [
        "",
        "food",           # wrong case
        "FOOD",           # uppercase
        "Groceries",      # valid-sounding but not in the fixed set
        "Unknown",
        "'; DROP TABLE expenses; --",
    ])
    def test_invalid_category_returns_200(self, client, test_db, bad_category):
        uid = _add_user(test_db)
        _login(client, uid)
        resp = client.post("/expenses/add", data={**VALID_FORM, "category": bad_category})
        assert resp.status_code == 200, (
            f"Invalid category '{bad_category}' must re-render form (200)"
        )

    @pytest.mark.parametrize("bad_category", [
        "",
        "food",
        "FOOD",
        "Groceries",
        "Unknown",
    ])
    def test_invalid_category_does_not_insert_row(self, client, test_db, bad_category):
        uid = _add_user(test_db)
        _login(client, uid)
        client.post("/expenses/add", data={**VALID_FORM, "category": bad_category})
        assert _count_expenses(test_db, uid) == 0, (
            f"No expense row must be inserted for invalid category '{bad_category}'"
        )


# ---------------------------------------------------------------------------
# TestDateValidation — invalid date formats
# ---------------------------------------------------------------------------

class TestDateValidation:
    @pytest.mark.parametrize("bad_date", [
        "",
        "15-05-2026",          # DD-MM-YYYY (wrong order)
        "05/15/2026",          # MM/DD/YYYY (wrong separator)
        "2026/05/15",          # YYYY/MM/DD (wrong separator)
        "20260515",            # no separators
        "not-a-date",
        "2026-13-01",          # month 13 does not exist
        "2026-00-15",          # month 0 does not exist
        "2026-02-30",          # Feb 30 does not exist
        "'; DROP TABLE expenses; --",
    ])
    def test_invalid_date_returns_200(self, client, test_db, bad_date):
        uid = _add_user(test_db)
        _login(client, uid)
        resp = client.post("/expenses/add", data={**VALID_FORM, "date": bad_date})
        assert resp.status_code == 200, (
            f"Invalid date '{bad_date}' must re-render form (200)"
        )

    @pytest.mark.parametrize("bad_date", [
        "",
        "15-05-2026",
        "05/15/2026",
        "not-a-date",
        "2026-13-01",
    ])
    def test_invalid_date_does_not_insert_row(self, client, test_db, bad_date):
        uid = _add_user(test_db)
        _login(client, uid)
        client.post("/expenses/add", data={**VALID_FORM, "date": bad_date})
        assert _count_expenses(test_db, uid) == 0, (
            f"No expense row must be inserted for invalid date '{bad_date}'"
        )


# ---------------------------------------------------------------------------
# TestDescriptionValidation — description length limit
# ---------------------------------------------------------------------------

class TestDescriptionValidation:
    def test_description_at_200_chars_is_accepted(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        exactly_200 = "x" * 200
        resp = client.post("/expenses/add", data={**VALID_FORM, "description": exactly_200})
        assert resp.status_code == 302, (
            "Description of exactly 200 chars must be accepted (redirect)"
        )
        assert _count_expenses(test_db, uid) == 1, (
            "Row must be inserted for description at the 200-char limit"
        )

    def test_description_over_200_chars_returns_200(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        over_200 = "x" * 201
        resp = client.post("/expenses/add", data={**VALID_FORM, "description": over_200})
        assert resp.status_code == 200, (
            "Description over 200 chars must re-render form (200)"
        )

    def test_description_over_200_chars_does_not_insert_row(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        over_200 = "y" * 201
        client.post("/expenses/add", data={**VALID_FORM, "description": over_200})
        assert _count_expenses(test_db, uid) == 0, (
            "No expense row must be inserted when description exceeds 200 chars"
        )

    def test_description_well_over_limit_returns_200(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        very_long = "a" * 500
        resp = client.post("/expenses/add", data={**VALID_FORM, "description": very_long})
        assert resp.status_code == 200, (
            "Description of 500 chars must also re-render form (200)"
        )


# ---------------------------------------------------------------------------
# TestValuePreservation — entered values echo back on validation failure
# ---------------------------------------------------------------------------

class TestValuePreservation:
    def test_amount_preserved_on_category_error(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        resp = client.post(
            "/expenses/add",
            data={**VALID_FORM, "amount": "77.77", "category": "InvalidCat"},
        )
        html = resp.data.decode()
        assert "77.77" in html, (
            "Amount value '77.77' must be preserved in the form on validation failure"
        )

    def test_category_preserved_on_amount_error(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        resp = client.post(
            "/expenses/add",
            data={**VALID_FORM, "amount": "-5", "category": "Health"},
        )
        html = resp.data.decode()
        assert "Health" in html, (
            "Category value 'Health' must be preserved in the form on validation failure"
        )

    def test_date_preserved_on_amount_error(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        resp = client.post(
            "/expenses/add",
            data={**VALID_FORM, "amount": "", "date": "2026-04-01"},
        )
        html = resp.data.decode()
        assert "2026-04-01" in html, (
            "Date value must be preserved in the form on validation failure"
        )

    def test_description_preserved_on_amount_error(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        resp = client.post(
            "/expenses/add",
            data={**VALID_FORM, "amount": "0", "description": "My unique description"},
        )
        html = resp.data.decode()
        assert "My unique description" in html, (
            "Description must be preserved in the form on validation failure"
        )

    def test_amount_preserved_on_date_error(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        resp = client.post(
            "/expenses/add",
            data={**VALID_FORM, "amount": "33.33", "date": "not-a-date"},
        )
        html = resp.data.decode()
        assert "33.33" in html, (
            "Amount value must be preserved in the form when date is invalid"
        )

    def test_description_preserved_on_description_too_long(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        long_desc = "B" * 201
        resp = client.post(
            "/expenses/add",
            data={**VALID_FORM, "description": long_desc},
        )
        html = resp.data.decode()
        assert "B" * 50 in html, (
            "Description text must be preserved in the form when it exceeds the length limit"
        )


# ---------------------------------------------------------------------------
# TestDataIsolation — expenses belong to the correct user only
# ---------------------------------------------------------------------------

class TestDataIsolation:
    def test_expense_belongs_to_submitting_user(self, client, test_db):
        uid1 = _add_user(test_db, name="Alice", email="alice@test.com")
        uid2 = _add_user(test_db, name="Bob", email="bob@test.com")
        _login(client, uid1)
        client.post("/expenses/add", data=VALID_FORM)
        assert _count_expenses(test_db, uid1) == 1, "Alice should have 1 expense"
        assert _count_expenses(test_db, uid2) == 0, "Bob should still have 0 expenses"

    def test_second_user_expense_stored_correctly(self, client, test_db):
        uid1 = _add_user(test_db, name="Alice", email="alice@test.com")
        uid2 = _add_user(test_db, name="Bob", email="bob@test.com")
        _login(client, uid1)
        client.post("/expenses/add", data=VALID_FORM)
        # Log out Alice, log in Bob
        client.get("/logout")
        _login(client, uid2)
        client.post("/expenses/add", data={**VALID_FORM, "amount": "99"})
        row = _fetch_expense(test_db, uid2)
        assert row is not None
        assert row["user_id"] == uid2, "Bob's expense must reference Bob's user_id"

    def test_multiple_expenses_same_user_all_inserted(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        client.post("/expenses/add", data={**VALID_FORM, "amount": "10"})
        client.post("/expenses/add", data={**VALID_FORM, "amount": "20"})
        client.post("/expenses/add", data={**VALID_FORM, "amount": "30"})
        assert _count_expenses(test_db, uid) == 3, (
            "Three separate valid submissions must create three expense rows"
        )
