"""
Tests for spec: 06-date-filter-profile
Date-range filter on the /profile page via GET query params.
"""
import pytest
import sqlite3
from datetime import date, timedelta
from werkzeug.security import generate_password_hash

import database.db as db_module
from app import app as flask_app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def test_db(tmp_path, monkeypatch):
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


def _add_expense(db_path, user_id, amount, category, date_str, description="test"):
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        (user_id, amount, category, date_str, description),
    )
    conn.commit()
    conn.close()


def _login(client, user_id, user_name="Test User"):
    with client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["user_name"] = user_name


# ---------------------------------------------------------------------------
# TestAuthGuard
# ---------------------------------------------------------------------------

class TestAuthGuard:
    def test_unauthenticated_get_redirects_to_login(self, client):
        resp = client.get("/profile")
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]

    def test_unauthenticated_with_date_params_redirects_to_login(self, client):
        resp = client.get("/profile?from=2026-01-01&to=2026-01-31")
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]

    def test_authenticated_get_returns_200(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        resp = client.get("/profile")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# TestNoFilterBaseline
# ---------------------------------------------------------------------------

class TestNoFilterBaseline:
    def test_filter_form_has_get_method(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        html = client.get("/profile").data.decode()
        assert 'method="GET"' in html

    def test_filter_form_action_is_profile(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        html = client.get("/profile").data.decode()
        assert 'action="/profile"' in html

    def test_from_input_present(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        html = client.get("/profile").data.decode()
        assert 'name="from"' in html

    def test_to_input_present(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        html = client.get("/profile").data.decode()
        assert 'name="to"' in html

    def test_apply_filter_button_present(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        html = client.get("/profile").data.decode()
        assert "Apply" in html

    def test_this_month_preset_link_present(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        html = client.get("/profile").data.decode()
        assert "This Month" in html

    def test_last_6_months_preset_link_present(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        html = client.get("/profile").data.decode()
        assert "Last 6 Months" in html

    def test_last_3_months_preset_link_present(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        html = client.get("/profile").data.decode()
        assert "Last 3 Months" in html

    def test_all_time_preset_link_present(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        html = client.get("/profile").data.decode()
        assert "All Time" in html

    def test_all_time_link_points_to_profile_no_params(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        html = client.get("/profile").data.decode()
        assert 'href="/profile"' in html

    def test_no_filter_notice_without_params(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        html = client.get("/profile").data.decode()
        assert "filter-notice" not in html

    def test_recent_transactions_heading_shown(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        html = client.get("/profile").data.decode()
        assert "Recent Transactions" in html

    def test_stats_section_rendered(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        html = client.get("/profile").data.decode()
        assert "Total Spent" in html
        assert "Top Category" in html


# ---------------------------------------------------------------------------
# TestValidDateRangeFilter
# ---------------------------------------------------------------------------

class TestValidDateRangeFilter:
    def test_in_range_transactions_shown(self, client, test_db):
        uid = _add_user(test_db)
        _add_expense(test_db, uid, 100, "Food", "2026-01-15", "in-range-expense")
        _add_expense(test_db, uid, 200, "Bills", "2026-03-01", "out-of-range-expense")
        _login(client, uid)
        html = client.get("/profile?from=2026-01-01&to=2026-01-31").data.decode()
        assert "in-range-expense" in html
        assert "out-of-range-expense" not in html

    def test_transactions_heading_not_recent(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        html = client.get("/profile?from=2026-01-01&to=2026-01-31").data.decode()
        assert "Recent Transactions" not in html
        assert "Transactions" in html

    def test_date_inputs_prepopulated_with_filter_values(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        html = client.get("/profile?from=2026-01-01&to=2026-01-31").data.decode()
        assert "2026-01-01" in html
        assert "2026-01-31" in html

    def test_from_input_prepopulated(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        html = client.get("/profile?from=2026-01-01&to=2026-01-31").data.decode()
        assert 'value="2026-01-01"' in html

    def test_to_input_prepopulated(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        html = client.get("/profile?from=2026-01-01&to=2026-01-31").data.decode()
        assert 'value="2026-01-31"' in html

    def test_stats_total_reflects_filtered_range(self, client, test_db):
        uid = _add_user(test_db)
        _add_expense(test_db, uid, 100, "Food", "2026-01-15", "in")
        _add_expense(test_db, uid, 500, "Bills", "2026-03-01", "out")
        _login(client, uid)
        html = client.get("/profile?from=2026-01-01&to=2026-01-31").data.decode()
        assert "₹100.00" in html
        assert "₹600.00" not in html

    def test_no_limit_when_filter_active(self, client, test_db):
        uid = _add_user(test_db)
        for i in range(12):
            _add_expense(test_db, uid, 10 + i, "Food", f"2026-01-{i + 1:02d}", f"tx-{i + 1:02d}")
        _login(client, uid)
        html = client.get("/profile?from=2026-01-01&to=2026-01-31").data.decode()
        assert "tx-01" in html
        assert "tx-12" in html

    def test_limit_10_without_filter(self, client, test_db):
        uid = _add_user(test_db)
        for i in range(12):
            _add_expense(test_db, uid, 10 + i, "Food", f"2026-01-{i + 1:02d}", f"tx-{i + 1:02d}")
        _login(client, uid)
        html = client.get("/profile").data.decode()
        assert "tx-12" in html
        assert "tx-01" not in html

    def test_categories_reflect_only_filtered_range(self, client, test_db):
        uid = _add_user(test_db)
        _add_expense(test_db, uid, 100, "Food", "2026-01-15", "food-in")
        _add_expense(test_db, uid, 500, "Bills", "2026-03-01", "bills-out")
        _login(client, uid)
        html = client.get("/profile?from=2026-01-01&to=2026-01-31").data.decode()
        assert "Food" in html
        assert "₹500.00" not in html


# ---------------------------------------------------------------------------
# TestPartialFilterInputs
# ---------------------------------------------------------------------------

class TestPartialFilterInputs:
    def test_only_from_silently_ignored(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        html = client.get("/profile?from=2026-01-01").data.decode()
        assert "Recent Transactions" in html
        assert "filter-notice" not in html

    def test_only_to_silently_ignored(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        html = client.get("/profile?to=2026-01-31").data.decode()
        assert "Recent Transactions" in html
        assert "filter-notice" not in html

    def test_only_from_returns_200(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        resp = client.get("/profile?from=2026-01-01")
        assert resp.status_code == 200

    def test_only_to_returns_200(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        resp = client.get("/profile?to=2026-01-31")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# TestInvalidDateStrings
# ---------------------------------------------------------------------------

class TestInvalidDateStrings:
    @pytest.mark.parametrize("bad_from,bad_to", [
        ("not-a-date", "2026-01-31"),
        ("2026-01-01", "not-a-date"),
        ("2026-13-01", "2026-01-31"),
        ("2026/01/01", "2026/01/31"),
        ("01-01-2026", "31-01-2026"),
        ("20260101",   "20260131"),
        ("'; DROP TABLE expenses; --", "2026-01-31"),
    ])
    def test_invalid_date_silently_ignored(self, client, test_db, bad_from, bad_to):
        uid = _add_user(test_db)
        _login(client, uid)
        resp = client.get(f"/profile?from={bad_from}&to={bad_to}")
        assert resp.status_code == 200
        html = resp.data.decode()
        assert "Recent Transactions" in html
        assert "filter-notice" not in html


# ---------------------------------------------------------------------------
# TestReversedDateRange
# ---------------------------------------------------------------------------

class TestReversedDateRange:
    def test_from_greater_than_to_silently_ignored(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        html = client.get("/profile?from=2026-01-31&to=2026-01-01").data.decode()
        assert "Recent Transactions" in html
        assert "filter-notice" not in html

    def test_from_greater_than_to_returns_200(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        resp = client.get("/profile?from=2026-01-31&to=2026-01-01")
        assert resp.status_code == 200

    def test_from_equal_to_to_is_valid(self, client, test_db):
        uid = _add_user(test_db)
        _add_expense(test_db, uid, 100, "Food", "2026-01-15", "on-the-day")
        _add_expense(test_db, uid, 200, "Bills", "2026-01-20", "other-day")
        _login(client, uid)
        html = client.get("/profile?from=2026-01-15&to=2026-01-15").data.decode()
        assert "Transactions" in html
        assert "on-the-day" in html
        assert "other-day" not in html


# ---------------------------------------------------------------------------
# TestZeroResultsFilter
# ---------------------------------------------------------------------------

class TestZeroResultsFilter:
    def test_zero_match_filter_returns_200(self, client, test_db):
        uid = _add_user(test_db)
        _add_expense(test_db, uid, 100, "Food", "2026-04-01", "april")
        _login(client, uid)
        resp = client.get("/profile?from=2026-01-01&to=2026-01-31")
        assert resp.status_code == 200

    def test_empty_state_message_shown(self, client, test_db):
        uid = _add_user(test_db)
        _add_expense(test_db, uid, 100, "Food", "2026-04-01", "april")
        _login(client, uid)
        html = client.get("/profile?from=2026-01-01&to=2026-01-31").data.decode()
        assert "No transactions" in html

    def test_zero_total_spent_shown(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        html = client.get("/profile?from=2026-01-01&to=2026-01-31").data.decode()
        assert "₹0.00" in html

    def test_user_with_no_expenses_is_safe(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        resp = client.get("/profile?from=2026-01-01&to=2026-01-31")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# TestPresetLinks
# ---------------------------------------------------------------------------

class TestPresetLinks:
    def test_this_month_link_contains_first_of_month(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        first_of_month = date.today().replace(day=1).isoformat()
        html = client.get("/profile").data.decode()
        assert first_of_month in html

    def test_this_month_link_contains_today(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        today = date.today().isoformat()
        html = client.get("/profile").data.decode()
        assert today in html

    def test_last_6_months_dates_in_presets(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        six_ago = (date.today() - timedelta(days=180)).isoformat()
        html = client.get("/profile").data.decode()
        assert six_ago in html

    def test_last_3_months_date_in_presets(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        three_ago = (date.today() - timedelta(days=90)).isoformat()
        html = client.get("/profile").data.decode()
        assert three_ago in html

    def test_all_time_link_is_anchor_with_no_params(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        html = client.get("/profile").data.decode()
        assert 'href="/profile"' in html

    def test_preset_links_are_anchor_tags(self, client, test_db):
        uid = _add_user(test_db)
        _login(client, uid)
        html = client.get("/profile").data.decode()
        assert 'href="/profile?from=' in html

    def test_following_this_month_filters_correctly(self, client, test_db):
        uid = _add_user(test_db)
        today = date.today()
        first_this = today.replace(day=1)
        _add_expense(test_db, uid, 50, "Food", today.isoformat(), "this-month-tx")
        last_month_date = (first_this - timedelta(days=1)).isoformat()
        _add_expense(test_db, uid, 99, "Bills", last_month_date, "last-month-tx")
        _login(client, uid)
        url = f"/profile?from={first_this.isoformat()}&to={today.isoformat()}"
        html = client.get(url).data.decode()
        assert "this-month-tx" in html
        assert "last-month-tx" not in html


# ---------------------------------------------------------------------------
# TestDbSideEffects
# ---------------------------------------------------------------------------

class TestDbSideEffects:
    def test_two_users_data_not_mixed(self, client, test_db):
        uid1 = _add_user(test_db, name="User One", email="one@test.com")
        uid2 = _add_user(test_db, name="User Two", email="two@test.com")
        _add_expense(test_db, uid1, 100, "Food", "2026-01-15", "user1-expense")
        _add_expense(test_db, uid2, 999, "Bills", "2026-01-15", "user2-expense")
        _login(client, uid1)
        html = client.get("/profile").data.decode()
        assert "user1-expense" in html
        assert "user2-expense" not in html

    def test_boundary_from_date_inclusive(self, client, test_db):
        uid = _add_user(test_db)
        _add_expense(test_db, uid, 100, "Food", "2026-01-01", "on-from-boundary")
        _add_expense(test_db, uid, 200, "Food", "2025-12-31", "before-from")
        _login(client, uid)
        html = client.get("/profile?from=2026-01-01&to=2026-01-31").data.decode()
        assert "on-from-boundary" in html
        assert "before-from" not in html

    def test_boundary_to_date_inclusive(self, client, test_db):
        uid = _add_user(test_db)
        _add_expense(test_db, uid, 100, "Food", "2026-01-31", "on-to-boundary")
        _add_expense(test_db, uid, 200, "Food", "2026-02-01", "after-to")
        _login(client, uid)
        html = client.get("/profile?from=2026-01-01&to=2026-01-31").data.decode()
        assert "on-to-boundary" in html
        assert "after-to" not in html

    def test_filtered_stats_total_matches_expenses_sum(self, client, test_db):
        uid = _add_user(test_db)
        _add_expense(test_db, uid, 100, "Food", "2026-01-15", "a")
        _add_expense(test_db, uid, 150, "Food", "2026-01-20", "b")
        _add_expense(test_db, uid, 999, "Bills", "2026-03-01", "out")
        _login(client, uid)
        html = client.get("/profile?from=2026-01-01&to=2026-01-31").data.decode()
        assert "₹250.00" in html

    def test_filtered_top_category_reflects_filtered_range(self, client, test_db):
        uid = _add_user(test_db)
        _add_expense(test_db, uid, 100, "Food", "2026-01-15", "food-in-range")
        _add_expense(test_db, uid, 9999, "Bills", "2026-03-01", "huge-bills-out")
        _login(client, uid)
        html = client.get("/profile?from=2026-01-01&to=2026-01-31").data.decode()
        assert "Food" in html
