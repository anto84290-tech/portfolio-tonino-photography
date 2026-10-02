"""Génère le site Tonino Photography.

Lit outils/festivals.json et les photos d'origine, écrit les images allégées
dans images/ et les pages HTML à la racine du dépôt.

Usage : python3 outils/generer.py --source "/chemin/vers/portfolio photo"
"""
import json
from pathlib import Path

from PIL import Image, ImageOps

Image.MAX_IMAGE_PIXELS = None

VIGNETTES = (640, 1000)   # largeurs, pour la galerie
GRANDS = (1400, 2200)     # plus grand côté, pour la visionneuse et les couvertures
QUALITE_WEBP = 78
QUALITE_JPEG = 80


class ErreurGeneration(Exception):
    """Erreur qui arrête la génération avec un message lisible."""


def charger_config(chemin: Path) -> dict:
    """Lit le fichier de contenu (festivals, photos, légendes)."""
    with open(chemin, encoding="utf-8") as f:
        return json.load(f)


def nom_image(slug: str, numero: int, largeur: int, ext: str) -> str:
    """Nom simple d'une image préparée, par exemple utopia-01-1000.webp."""
    return f"{slug}-{numero:02d}-{largeur}.{ext}"


def _tailles(largeur: int, hauteur: int) -> tuple[list, list]:
    """Dimensions à produire, sans jamais dépasser l'original ni se répéter."""
    vignettes, grands = [], []
    for cible in VIGNETTES:
        l = min(cible, largeur)
        taille = (l, round(hauteur * l / largeur))
        if taille not in vignettes:
            vignettes.append(taille)
    grand_cote = max(largeur, hauteur)
    for cible in GRANDS:
        echelle = min(cible, grand_cote) / grand_cote
        taille = (round(largeur * echelle), round(hauteur * echelle))
        if taille not in grands:
            grands.append(taille)
    return vignettes, grands


def preparer_photo(source: Path, dossier_sortie: Path, slug: str, numero: int) -> dict:
    """Écrit les versions allégées d'une photo (WebP + JPEG) et décrit le résultat."""
    source = Path(source)
    if not source.is_file():
        raise ErreurGeneration(f"Photo introuvable : {source.name} (cherchée dans {source.parent})")
    dossier_sortie = Path(dossier_sortie)
    dossier_sortie.mkdir(parents=True, exist_ok=True)
    date_source = source.stat().st_mtime

    with Image.open(source) as brute:
        image = ImageOps.exif_transpose(brute).convert("RGB")
    largeur, hauteur = image.size
    vignettes, grands = _tailles(largeur, hauteur)

    def ecrire(taille: tuple[int, int]) -> tuple[int, str]:
        nom = nom_image(slug, numero, taille[0], "webp")
        cibles = [
            (dossier_sortie / nom, {"format": "WEBP", "quality": QUALITE_WEBP, "method": 6}),
            (dossier_sortie / nom_image(slug, numero, taille[0], "jpg"),
             {"format": "JPEG", "quality": QUALITE_JPEG, "optimize": True, "progressive": True}),
        ]
        a_faire = [(c, o) for c, o in cibles if not c.exists() or c.stat().st_mtime < date_source]
        if a_faire:
            reduite = image if taille == image.size else image.resize(taille, Image.LANCZOS)
            for chemin, options in a_faire:
                reduite.save(chemin, **options)
        return taille[0], nom

    return {
        "largeur": largeur,
        "hauteur": hauteur,
        "vignettes": [ecrire(t) for t in vignettes],
        "grands": [ecrire(t) for t in grands],
    }
