"""Tests unitaires pour le patch grant_cosmo_role_permissions."""
from pathlib import Path

PATCH_MODULE = "cosmo_erp.patches.v0_2.grant_cosmo_role_permissions"
BASE = Path(__file__).parent.parent


def test_patch_registered_in_patches_txt():
    """Le patch est bien référencé dans patches.txt."""
    content = (BASE / "patches.txt").read_text(encoding="utf-8")
    referenced = [line.strip() for line in content.splitlines() if line.strip()]
    assert PATCH_MODULE in referenced, (
        f"Patch '{PATCH_MODULE}' non référencé dans patches.txt (trouvé : {referenced})"
    )


def test_patch_module_file_exists():
    """Le fichier du patch existe et expose une fonction execute()."""
    patch_file = BASE / "patches/v0_2/grant_cosmo_role_permissions.py"
    assert patch_file.exists(), "Fichier patch grant_cosmo_role_permissions.py manquant"
    src = patch_file.read_text(encoding="utf-8")
    assert "def execute" in src, "Le patch doit exposer une fonction execute()"


def test_grants_cover_cosmo_roles():
    """Les deux rôles Cosmo (Caissière, Manager) ont au moins une permission accordée."""
    patch_file = BASE / "patches/v0_2/grant_cosmo_role_permissions.py"
    src = patch_file.read_text(encoding="utf-8")
    assert "Cosmo Caissière" in src, "Aucune permission accordée à Cosmo Caissière"
    assert "Cosmo Manager" in src, "Aucune permission accordée à Cosmo Manager"
