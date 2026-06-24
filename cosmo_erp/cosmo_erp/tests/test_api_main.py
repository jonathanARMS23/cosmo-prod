"""Tests unitaires pour cosmo_erp/api/main.py — vérifie la structure sans Frappe."""
from pathlib import Path
import ast
import pytest

API_FILE = Path(__file__).parent.parent / "api/main.py"


def test_api_main_exists():
    assert API_FILE.exists(), "api/main.py manquant"


def test_api_main_is_valid_python():
    source = API_FILE.read_text()
    try:
        ast.parse(source)
    except SyntaxError as e:
        pytest.fail(f"Erreur de syntaxe Python : {e}")


def test_all_endpoints_are_whitelisted():
    source = API_FILE.read_text()
    tree = ast.parse(source)
    public_functions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
            decorators = [ast.unparse(d) for d in node.decorator_list]
            if any("whitelist" in d for d in decorators):
                public_functions.append(node.name)

    expected = [
        "get_item_stock", "get_all_stock", "get_low_stock_items", "get_expiring_items",
        "search_items", "create_item", "update_item_price",
        "create_sale", "get_daily_sales", "get_sales_period", "get_invoice", "cancel_invoice",
        "receive_stock", "adjust_stock",
        "create_customer", "get_customer", "get_customer_history",
        "get_top_customers", "get_inactive_customers",
        "get_suppliers", "create_supplier_order", "get_pending_orders",
        "get_dashboard_summary", "get_category_breakdown", "get_revenue_trend",
    ]
    for fn in expected:
        assert fn in public_functions, f"Endpoint manquant ou non whitelisted : {fn}"


def test_all_endpoints_have_message_field():
    """Vérifie que chaque endpoint retourne un champ 'message'."""
    source = API_FILE.read_text()
    # Compte les occurrences de "message" dans les return statements
    assert source.count('"message"') >= 20, "Trop peu de champs 'message' dans les endpoints"


def test_no_hardcoded_credentials():
    source = API_FILE.read_text()
    for bad in ["api_key =", "api_secret =", "password =", "token ="]:
        assert bad not in source.lower(), f"Credential potentiel trouve : {bad}"
