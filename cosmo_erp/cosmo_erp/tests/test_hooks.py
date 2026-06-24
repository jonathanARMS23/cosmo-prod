"""Tests unitaires pour vérifier la structure de hooks.py."""
import importlib
import pytest


def test_hooks_app_metadata():
    """Vérifie que les métadonnées app sont correctement définies."""
    hooks = importlib.import_module("cosmo_erp.hooks")
    assert hooks.app_name == "cosmo_erp"
    assert hooks.app_title == "Cosmo ERP"
    assert hasattr(hooks, "app_version")


def test_hooks_scheduler_events_defined():
    """Vérifie que les scheduler events sont définis."""
    hooks = importlib.import_module("cosmo_erp.hooks")
    assert "daily" in hooks.scheduler_events
    assert "weekly" in hooks.scheduler_events
    assert len(hooks.scheduler_events["daily"]) >= 2


def test_hooks_fixtures_defined():
    """Vérifie que la liste des fixtures est définie."""
    hooks = importlib.import_module("cosmo_erp.hooks")
    assert isinstance(hooks.fixtures, list)
    assert "Custom Field" in hooks.fixtures


def test_hooks_doc_events_sales_invoice():
    """Vérifie les doc_events pour Sales Invoice."""
    hooks = importlib.import_module("cosmo_erp.hooks")
    assert "Sales Invoice" in hooks.doc_events
    assert "on_submit" in hooks.doc_events["Sales Invoice"]
    assert "on_cancel" in hooks.doc_events["Sales Invoice"]
