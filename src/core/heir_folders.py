"""
Heir folders — maps each character card ID to its personal folder.

Every Chrysos Heir has their own folder at the project root, named after their
signal code (e.g. `NeiKos496-Phainon`). These folders ARE the Heirs' personal
databases: their memory (bond, history, long-term memories) and their
preferences (aesthetics, tastes, likes, dislikes) live inside them.
"""

from pathlib import Path
from typing import Optional

# character card id -> per-Heir folder name
HEIR_FOLDERS: dict = {
    "aglaea": "KaLos618-Aglaea",
    "anaxa": "SkeMma720-Anaxa",
    "castorice": "EpieiKeia216-Castorice",
    "cerydra": "HubRis504-Cerydra",
    "cipher": "OreXis945-Cipher",
    "cyrene": "PhiLia093-Cyrene",
    "dan-heng-permansor-terrae": "DanHeng-PermansorTerrae",
    "evernight": "Evernight",
    "hyacine": "EleOs252-Hyacine",
    "hysilens": "ApoRia432-Hysilens",
    "mydei": "PoleMos600-Mydei",
    "phainon": "NeiKos496-Phainon",
    "tribbie": "HapLotes405-Tribbie",
}


def resolve_heir_folder(character_id: str, root: str | Path = ".") -> Path:
    """Return the absolute path of a Heir's personal folder (creating it if needed)."""
    root = Path(root)
    name = HEIR_FOLDERS.get(character_id, character_id)
    folder = root / name
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def all_heir_folders(root: str | Path = ".") -> list:
    """Return the list of per-Heir folders that exist."""
    root = Path(root)
    result = []
    for folder in root.iterdir():
        if folder.is_dir() and folder.name in set(HEIR_FOLDERS.values()):
            result.append(folder)
    return sorted(result)
