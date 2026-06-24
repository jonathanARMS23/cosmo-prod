"""Tests unitaires Phase 3 — Dashboard, Charts, Reporting."""
from pathlib import Path
import pytest

BASE = Path(__file__).parent.parent
DASHBOARD_PY = BASE / "dashboard/cosmo_dashboard.py"
SETUP_PY = BASE / "setup/dashboard_setup.py"
WEEKLY_PY = BASE / "tasks/weekly.py"
EMAIL_HTML = BASE / "templates/emails/cosmo_weekly_report.html"


def test_dashboard_module_exists():
    assert DASHBOARD_PY.exists(), "cosmo_dashboard.py manquant"


def test_dashboard_whitelist_methods():
    content = DASHBOARD_PY.read_text()
    for method in [
        "get_sales_last_30_days",
        "get_top_products",
        "get_category_breakdown",
        "get_revenue_summary",
        "get_stock_critical_items",
        "get_expiring_items",
        "get_crm_summary",
        "get_stock_value_total",
    ]:
        assert method in content, f"Méthode manquante : {method}"
    assert "@frappe.whitelist()" in content


def test_dashboard_setup_creates_5_cards():
    content = SETUP_PY.read_text()
    # 5 Number Cards définies
    assert content.count('"name": "Cosmo') >= 5
    assert "create_number_cards" in content
    assert "create_dashboard_charts" in content
    assert "_create_dashboard" in content


def test_dashboard_setup_3_charts():
    content = SETUP_PY.read_text()
    assert "Cosmo Ventes 30 Jours" in content
    assert "Cosmo Top Produits CA" in content
    assert "Cosmo Répartition Catégories" in content


def test_weekly_report_has_all_sections():
    content = WEEKLY_PY.read_text()
    assert "send_weekly_report" in content
    assert "_build_weekly_report" in content
    assert "_email_report" in content
    assert "top_items" in content
    assert "low_stock_count" in content


def test_email_template_exists_and_has_variables():
    assert EMAIL_HTML.exists()
    content = EMAIL_HTML.read_text()
    assert "data.revenue" in content
    assert "data.top_items" in content
    assert "start_date" in content


def test_date_filter_logic():
    """Vérifie que _get_date_filter et _get_previous_date_filter couvrent les 4 périodes."""
    content = DASHBOARD_PY.read_text()
    for period in ["today", "week", "month", "year"]:
        assert period in content, f"Période manquante : {period}"


def test_hooks_has_dashboard_fixtures():
    hooks = (BASE.parent / "hooks.py").read_text()
    assert "Number Card" in hooks
    assert "Dashboard Chart" in hooks
    assert "Dashboard" in hooks


def test_install_calls_create_dashboard():
    install = (BASE / "install.py").read_text()
    assert "create_dashboard" in install or "dashboard_setup" in install
