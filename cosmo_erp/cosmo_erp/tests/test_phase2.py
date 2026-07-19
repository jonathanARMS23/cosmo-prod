"""Tests unitaires Phase 2 — POS et Print Format."""
import json
from pathlib import Path
import pytest

BASE = Path(__file__).parent.parent


def test_cosmo_pos_page_json_exists():
    p = BASE / "cosmo_erp/page/cosmo_pos/cosmo_pos.json"
    assert p.exists()
    data = json.loads(p.read_text())
    assert data["doctype"] == "Page"
    assert data["name"] == "cosmo-pos"
    assert any(r["role"] == "Cosmo Caissière" for r in data.get("roles", []))


def test_cosmo_pos_js_has_page_hook():
    p = BASE / "cosmo_erp/page/cosmo_pos/cosmo_pos.js"
    assert p.exists()
    content = p.read_text()
    assert "frappe.pages['cosmo-pos'].on_page_load" in content
    assert "class CosmoPOS" in content


def test_cosmo_pos_py_has_whitelisted_endpoints():
    p = BASE / "cosmo_erp/page/cosmo_pos/cosmo_pos.py"
    assert p.exists()
    content = p.read_text()
    for fn in ["get_items_with_stock", "create_sale", "get_daily_summary", "close_register"]:
        assert fn in content, f"Endpoint manquant : {fn}"
    assert "@frappe.whitelist()" in content


def test_print_format_fixture_exists():
    p = BASE / "fixtures/print_format.json"
    assert p.exists()
    data = json.loads(p.read_text())
    assert isinstance(data, list) and len(data) == 1
    assert data[0]["name"] == "Cosmo Invoice"
    assert data[0]["doc_type"] == "Sales Invoice"


def test_cosmo_invoice_html_template_exists():
    p = BASE / "cosmo_erp/print_format/cosmo_invoice.html"
    assert p.exists()
    content = p.read_text()
    assert "doc.items" in content
    assert "grand_total" in content
    assert "boutique" in content.lower()


def test_custom_field_fixture_includes_sales_invoice():
    p = BASE / "fixtures/custom_field.json"
    data = json.loads(p.read_text())
    si_fields = [f for f in data if f.get("dt") == "Sales Invoice"]
    assert len(si_fields) >= 1, "Aucun custom field Sales Invoice trouve"
    assert any(f["fieldname"] == "cosmo_payment_mode" for f in si_fields)
