"""Tests unitaires pour l'hydratation du stock initial Ravaka (patch v0_2).

Style aligné sur les autres tests : lecture de fichiers JSON/txt en local, sans
dépendance à un environnement Frappe/bench.
"""
import json
from pathlib import Path

BASE = Path(__file__).parent.parent
FIXTURE = BASE / "fixtures/ravaka_initial_stock.json"
PATCHES_TXT = BASE / "patches.txt"
PATCH_MODULE = "cosmo_erp.patches.v0_2.hydrate_ravaka_initial_stock"


def test_fixture_exists_and_non_empty():
    assert FIXTURE.exists(), "Fixture ravaka_initial_stock.json manquante"
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert isinstance(data, list), "Le fixture doit être une liste JSON"
    assert len(data) > 0, "Le fixture ne doit pas être vide"


def test_fixture_entries_structure():
    """Chaque entrée : item_code non vide + qty entier >= 0."""
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    for idx, entry in enumerate(data):
        assert isinstance(entry, dict), f"Entrée {idx} n'est pas un objet"
        assert "item_code" in entry, f"Entrée {idx} sans item_code"
        assert "qty" in entry, f"Entrée {idx} sans qty"
        code = entry["item_code"]
        assert isinstance(code, str) and code.strip(), f"Entrée {idx} item_code vide"
        qty = entry["qty"]
        assert isinstance(qty, int) and not isinstance(qty, bool), (
            f"Entrée {idx} ({code}) qty doit être un entier, trouvé {type(qty).__name__}"
        )
        assert qty >= 0, f"Entrée {idx} ({code}) qty négative : {qty}"


def test_fixture_no_duplicate_item_codes():
    """Le fichier final est déjà dédupliqué/agrégé : aucun item_code en double."""
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    codes = [e["item_code"].strip() for e in data]
    dupes = sorted({c for c in codes if codes.count(c) > 1})
    assert not dupes, f"item_code(s) dupliqué(s) dans le fixture final : {dupes}"


def test_patch_registered_in_patches_txt():
    """Le patch d'hydratation doit être référencé dans patches.txt."""
    assert PATCHES_TXT.exists(), "patches.txt manquant"
    content = PATCHES_TXT.read_text(encoding="utf-8")
    referenced = [
        line.strip()
        for line in content.splitlines()
        if line.strip() and not line.strip().startswith("#")
        and not line.strip().startswith("[")
    ]
    assert PATCH_MODULE in referenced, (
        f"Patch '{PATCH_MODULE}' non référencé dans patches.txt (trouvé : {referenced})"
    )


def test_patch_module_file_exists():
    """Le fichier du patch existe au chemin attendu par patches.txt."""
    patch_file = BASE / "patches/v0_2/hydrate_ravaka_initial_stock.py"
    assert patch_file.exists(), "Fichier patch hydrate_ravaka_initial_stock.py manquant"
    src = patch_file.read_text(encoding="utf-8")
    assert "def execute" in src, "Le patch doit exposer une fonction execute()"
