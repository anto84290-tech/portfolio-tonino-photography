"""Génère le site Tonino Photography.

Lit outils/festivals.json et les photos d'origine, écrit les images allégées
dans images/ et les pages HTML à la racine du dépôt.

Usage : python3 outils/generer.py --source "/chemin/vers/portfolio photo"
"""
import argparse
import hashlib
import html
import io
import json
import re
import sys
from pathlib import Path
from string import Template

from PIL import Image, ImageCms, ImageOps, UnidentifiedImageError

Image.MAX_IMAGE_PIXELS = None

VIGNETTES = (640, 1000)   # largeurs, pour la galerie
GRANDS = (1400, 2200)     # plus grand côté, pour la visionneuse et les couvertures
# Des photos de concert sont sombres et pleines de grain : trop compressé, ce grain
# se transforme en pâtés bien visibles en grand. La compression reste donc légère.
# Qualités (WebP, JPEG) essayées dans l'ordre, jusqu'à passer sous le poids visé.
QUALITES_VIGNETTE = ((84, 80, 76), (86, 82, 78))
QUALITES_GRAND = ((90, 86, 82), (90, 86, 82))
POIDS_MAX_VIGNETTE = 300_000   # octets
POIDS_MAX_GRAND = 1_200_000

OUTILS = Path(__file__).resolve().parent
CONFIG = OUTILS / "festivals.json"
GABARITS = OUTILS / "gabarits"
ADRESSE_SITE = "https://portfolio-tonino-photography.vercel.app"
TAILLES_GALERIE = "(min-width: 1101px) 33vw, 50vw"
# Les bandes des festivals sont basses et assombries par un voile : on annonce au
# navigateur une largeur plus petite que l'écran, pour qu'il prenne une version plus légère.
TAILLES_BANDE = "70vw"


class ErreurGeneration(Exception):
    """Erreur qui arrête la génération avec un message lisible."""


def charger_config(chemin: Path) -> dict:
    """Lit le fichier de contenu (festivals, photos, légendes)."""
    try:
        with open(chemin, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise ErreurGeneration(f"Fichier de contenu introuvable : {chemin}") from None
    except json.JSONDecodeError as erreur:
        raise ErreurGeneration(
            f"{Path(chemin).name} est mal formé, ligne {erreur.lineno}, colonne {erreur.colno} "
            f"(souvent une virgule en trop ou un guillemet manquant) : {erreur.msg}") from None


CHAMPS_FESTIVAL = ("slug", "nom", "nom_complet", "lieu", "dates", "annee", "dossier", "couverture", "photos")
CHAMPS_PHOTO = ("fichier", "legende", "alt")
SLUG_VALIDE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def valider_config(cfg: dict) -> None:
    """Vérifie le contenu avant tout travail, pour signaler une erreur de saisie en clair."""
    festivals = cfg.get("festivals") if isinstance(cfg, dict) else None
    if not isinstance(festivals, list) or not festivals:
        raise ErreurGeneration("festivals.json doit contenir une liste « festivals » non vide.")
    slugs = []
    for position, festival in enumerate(festivals, 1):
        nom = festival.get("nom") or festival.get("slug") or f"n° {position}"
        for champ in CHAMPS_FESTIVAL:
            if champ not in festival:
                raise ErreurGeneration(f"Festival « {nom} » : il manque le champ « {champ} ».")
        slug = festival["slug"]
        if not isinstance(slug, str) or not SLUG_VALIDE.match(slug):
            raise ErreurGeneration(
                f"Festival « {nom} » : le slug « {slug} » n'est pas valide. "
                "Utiliser seulement des minuscules, des chiffres et des tirets (exemple : mon-festival).")
        if slug in slugs:
            raise ErreurGeneration(f"Le slug « {slug} » est utilisé par deux festivals.")
        slugs.append(slug)
        photos = festival["photos"]
        if not isinstance(photos, list) or not photos:
            raise ErreurGeneration(f"Festival « {nom} » : la liste « photos » est vide.")
        for numero, photo in enumerate(photos, 1):
            for champ in CHAMPS_PHOTO:
                if champ not in photo:
                    repere = photo.get("fichier", f"n° {numero}")
                    raise ErreurGeneration(f"Festival « {nom} », photo {repere} : il manque le champ « {champ} ».")
        couverture = festival["couverture"]
        if not isinstance(couverture, int) or not 1 <= couverture <= len(photos):
            raise ErreurGeneration(
                f"Festival « {nom} » : « couverture » vaut {couverture}, "
                f"il faut un numéro de photo entre 1 et {len(photos)}.")
    bandeau = cfg.get("accueil", {}).get("bandeau", {})
    if bandeau.get("festival") not in slugs:
        raise ErreurGeneration(
            f"Accueil : le bandeau désigne le festival « {bandeau.get('festival')} », qui n'existe pas "
            f"(festivals connus : {', '.join(slugs)}).")
    nombre = len(festivals[slugs.index(bandeau["festival"])]["photos"])
    if not isinstance(bandeau.get("photo"), int) or not 1 <= bandeau["photo"] <= nombre:
        raise ErreurGeneration(
            f"Accueil : le bandeau désigne la photo {bandeau.get('photo')}, il faut un numéro entre 1 et {nombre}.")


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


# Les images préparées portent le numéro de la photo dans la galerie, pas son nom
# d'origine. Un registre par festival retient donc de quelle photo vient chaque
# numéro : si l'ordre change ou si une photo est remplacée, ses images sont refaites.
REGISTRE = "empreintes.json"


def _empreinte(source: Path) -> str:
    """Identifie le contenu d'une photo d'origine et les réglages utilisés pour la préparer."""
    reglages = repr((VIGNETTES, GRANDS, QUALITES_VIGNETTE, QUALITES_GRAND, POIDS_MAX_VIGNETTE, POIDS_MAX_GRAND, "sRGB"))
    condense = hashlib.sha256(reglages.encode())
    condense.update(source.read_bytes())
    return condense.hexdigest()


def _lire_registre(dossier: Path) -> dict:
    try:
        return json.loads((dossier / REGISTRE).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _ecrire_registre(dossier: Path, registre: dict) -> None:
    contenu = json.dumps(registre, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    (dossier / REGISTRE).write_text(contenu, encoding="utf-8", newline="\n")


def _fichiers(entree: dict) -> list[str]:
    noms = [nom for _, nom in entree["vignettes"] + entree["grands"]]
    return noms + [nom.rsplit(".", 1)[0] + ".jpg" for nom in noms]


def _ouvrir_en_srgb(source: Path) -> Image.Image:
    """Charge une photo droite (rotation EXIF appliquée) et dans l'espace de couleur du web."""
    try:
        with Image.open(source) as brute:
            profil = brute.info.get("icc_profile")
            image = ImageOps.exif_transpose(brute).convert("RGB")
    except (UnidentifiedImageError, OSError) as erreur:
        raise ErreurGeneration(f"Photo illisible : {source.name} ({erreur})") from None
    if profil:
        try:
            origine = ImageCms.ImageCmsProfile(io.BytesIO(profil))
            if "srgb" not in ImageCms.getProfileDescription(origine).lower():
                image = ImageCms.profileToProfile(image, origine, ImageCms.createProfile("sRGB"), outputMode="RGB")
        except ImageCms.PyCMSError:
            pass  # profil inexploitable : on garde les couleurs telles quelles
    return image


def preparer_photo(source: Path, dossier_sortie: Path, slug: str, numero: int) -> dict:
    """Écrit les versions allégées d'une photo (WebP + JPEG) et décrit le résultat."""
    source = Path(source)
    if not source.is_file():
        raise ErreurGeneration(f"Photo introuvable : {source.name} (cherchée dans {source.parent})")
    dossier_sortie = Path(dossier_sortie)
    dossier_sortie.mkdir(parents=True, exist_ok=True)

    cle = f"{numero:02d}"
    empreinte = _empreinte(source)
    registre = _lire_registre(dossier_sortie)
    entree = registre.get(cle)
    if entree and entree.get("empreinte") == empreinte and all((dossier_sortie / f).is_file() for f in _fichiers(entree)):
        return _resultat(entree)

    image = _ouvrir_en_srgb(source)
    for ancien in dossier_sortie.glob(f"{slug}-{cle}-*"):
        ancien.unlink()
    largeur, hauteur = image.size
    vignettes, grands = _tailles(largeur, hauteur)

    def ecrire(taille: tuple[int, int], qualites: tuple, poids_max: int) -> list:
        nom = nom_image(slug, numero, taille[0], "webp")
        cibles = [
            (dossier_sortie / nom, qualites[0], {"format": "WEBP", "method": 6}),
            (dossier_sortie / nom_image(slug, numero, taille[0], "jpg"), qualites[1],
             {"format": "JPEG", "optimize": True, "progressive": True}),
        ]
        reduite = image if taille == image.size else image.resize(taille, Image.LANCZOS)
        for chemin, essais, options in cibles:
            for qualite in essais:
                tampon = io.BytesIO()
                reduite.save(tampon, quality=qualite, **options)
                if tampon.tell() <= poids_max:
                    break
            chemin.write_bytes(tampon.getvalue())
        return [taille[0], nom]

    entree = {
        "source": source.name,
        "empreinte": empreinte,
        "largeur": largeur,
        "hauteur": hauteur,
        "vignettes": [ecrire(t, QUALITES_VIGNETTE, POIDS_MAX_VIGNETTE) for t in vignettes],
        "grands": [ecrire(t, QUALITES_GRAND, POIDS_MAX_GRAND) for t in grands],
    }
    registre = _lire_registre(dossier_sortie)
    registre[cle] = entree
    _ecrire_registre(dossier_sortie, registre)
    return _resultat(entree)


def _resultat(entree: dict) -> dict:
    return {
        "largeur": entree["largeur"],
        "hauteur": entree["hauteur"],
        "vignettes": [(l, nom) for l, nom in entree["vignettes"]],
        "grands": [(l, nom) for l, nom in entree["grands"]],
    }


def _nettoyer(dossier: Path, nombre_photos: int) -> None:
    """Supprime les images qui ne correspondent plus à aucune photo du festival."""
    registre = _lire_registre(dossier)
    garde = {cle: e for cle, e in registre.items() if int(cle) <= nombre_photos}
    attendus = {REGISTRE} | {f for e in garde.values() for f in _fichiers(e)}
    for fichier in dossier.iterdir():
        if fichier.is_file() and fichier.name not in attendus:
            fichier.unlink()
    if garde != registre:
        _ecrire_registre(dossier, garde)


def repartir_colonnes(photos: list[dict], n: int) -> list[list[dict]]:
    """Place chaque photo, dans l'ordre, dans la colonne la moins haute (la plus à gauche si égalité)."""
    colonnes = [[] for _ in range(n)]
    hauteurs = [0.0] * n
    for photo in photos:
        i = hauteurs.index(min(hauteurs))
        colonnes[i].append(photo)
        hauteurs[i] += photo["hauteur"] / photo["largeur"]
    return colonnes


# ---------------------------------------------------------------------------
# Rendu HTML
# ---------------------------------------------------------------------------

def _gabarit(nom: str) -> Template:
    return Template((GABARITS / nom).read_text(encoding="utf-8"))


def _e(valeur) -> str:
    return html.escape(str(valeur), quote=True)


def _srcset(slug: str, versions: list, ext: str) -> str:
    return ", ".join(f"/images/{slug}/{nom.rsplit('.', 1)[0]}.{ext} {largeur}w" for largeur, nom in versions)


def _image(slug: str, versions: list, photo: dict, *, classe: str = "", alt: str, tailles: str,
           differe: bool = True, prioritaire: bool = False) -> str:
    """Balise <picture> : WebP d'abord, JPEG pour les navigateurs anciens."""
    largeur_ref = versions[-1][0]
    hauteur_ref = round(photo["hauteur"] * largeur_ref / photo["largeur"])
    secours = f"/images/{slug}/{versions[0][1].rsplit('.', 1)[0]}.jpg"
    attributs = [
        f'class="{classe}"' if classe else "",
        f'src="{secours}"',
        f'srcset="{_srcset(slug, versions, "jpg")}"',
        f'sizes="{tailles}"',
        f'width="{largeur_ref}"',
        f'height="{hauteur_ref}"',
        f'alt="{_e(alt)}"',
        'loading="lazy"' if differe else "",
        'fetchpriority="high"' if prioritaire else "",
        'decoding="async"',
    ]
    return (
        f'<picture><source type="image/webp" srcset="{_srcset(slug, versions, "webp")}" sizes="{tailles}">'
        f'<img {" ".join(a for a in attributs if a)}></picture>'
    )


def _bande(festival: dict, etiquette: str) -> str:
    couverture = festival["photos"][festival["couverture"] - 1]
    return _gabarit("_bande.html").substitute(
        slug=festival["slug"],
        image=_image(festival["slug"], couverture["grands"], couverture, classe="bande-photo", alt="", tailles=TAILLES_BANDE),
        etiquette=_e(etiquette),
        nom=_e(festival["nom"]),
        nombre=len(festival["photos"]),
    )


def _colonnes(festival: dict, n: int) -> str:
    morceau = _gabarit("_photo.html")
    blocs = []
    for colonne in repartir_colonnes(festival["photos"], n):
        liens = "".join(
            morceau.substitute(
                grand=f"/images/{festival['slug']}/{p['grands'][-1][1].rsplit('.', 1)[0]}.jpg",
                index=p["index"],
                legende=_e(p["legende"]),
                grand_srcset=_srcset(festival["slug"], p["grands"], "webp"),
                image=_image(festival["slug"], p["vignettes"], p, alt=p["alt"], tailles=TAILLES_GALERIE),
            )
            for p in colonne
        )
        blocs.append(f'<div class="colonne">\n{liens}</div>')
    return "\n".join(blocs)


def _page(corps: str, *, titre: str, description: str, chemin: str, apercu: str, classe: str,
          scripts: str = "", festivals_actif: bool = False) -> str:
    entete = _gabarit("_entete.html").substitute(
        titre=_e(titre),
        description=_e(description),
        url=ADRESSE_SITE + chemin,
        apercu=ADRESSE_SITE + apercu,
        classe_page=classe,
        scripts=scripts,
        festivals_actif=' aria-current="true"' if festivals_actif else "",
    )
    return entete + corps + _gabarit("_pied.html").substitute()


def _apercu(festival: dict, numero: int) -> str:
    photo = festival["photos"][numero - 1]
    return f"/images/{festival['slug']}/{photo['grands'][0][1].rsplit('.', 1)[0]}.jpg"


def rendre_accueil(cfg: dict) -> str:
    festivals = cfg["festivals"]
    par_slug = {f["slug"]: f for f in festivals}
    bandeau = cfg["accueil"]["bandeau"]
    festival_bandeau = par_slug[bandeau["festival"]]
    photo = festival_bandeau["photos"][bandeau["photo"] - 1]
    corps = _gabarit("accueil.html").substitute(
        bandeau_image=_image(festival_bandeau["slug"], photo["grands"], photo, classe="bandeau-photo",
                             alt=photo["alt"], tailles="100vw", differe=False, prioritaire=True),
        nombre_festivals=len(festivals),
        bandes="".join(_bande(f, f"{i:02d}") for i, f in enumerate(festivals, 1)),
    )
    return _page(
        corps,
        titre="Tonino Photography — Photographe de concerts et de festivals à Marseille",
        description="Photographe de concerts et de festivals, tous styles de musique confondus — de la fosse aux backstages. Basé à Marseille.",
        chemin="/",
        apercu=_apercu(festival_bandeau, bandeau["photo"]),
        classe="page-accueil",
    )


def rendre_festival(festival: dict, suivant: dict) -> str:
    nombre = len(festival["photos"])
    corps = _gabarit("festival.html").substitute(
        nom=_e(festival["nom"]),
        lettres=len(festival["nom"]),
        nom_complet=_e(festival["nom_complet"]),
        lieu=_e(festival["lieu"]),
        dates=_e(festival["dates"]),
        nombre=nombre,
        colonnes_3=_colonnes(festival, 3),
        colonnes_2=_colonnes(festival, 2),
        bande_suivante=_bande(suivant, "Festival suivant"),
    )
    return _page(
        corps,
        titre=f"{festival['nom_complet']} {festival['annee']}, {festival['lieu']} — Tonino Photography",
        description=f"{festival['nom_complet']}, {festival['lieu']}, {festival['dates']} : {nombre} photos de concert par Tonino Photography.",
        chemin=f"/{festival['slug']}/",
        apercu=_apercu(festival, festival["couverture"]),
        classe="page-festival",
        scripts='<script src="/js/visionneuse.js" defer></script>',
        festivals_actif=True,
    )


def rendre_introuvable(cfg: dict) -> str:
    bandeau = cfg["accueil"]["bandeau"]
    festival = {f["slug"]: f for f in cfg["festivals"]}[bandeau["festival"]]
    return _page(
        _gabarit("404.html").substitute(),
        titre="Page introuvable — Tonino Photography",
        description="Cette page n'existe pas ou a été déplacée.",
        chemin="/404.html",
        apercu=_apercu(festival, bandeau["photo"]),
        classe="page-introuvable",
    )


def generer_site(source: Path, racine: Path) -> None:
    """Prépare toutes les images puis écrit toutes les pages dans `racine`."""
    source, racine = Path(source), Path(racine)
    cfg = charger_config(CONFIG)
    valider_config(cfg)
    festivals = cfg["festivals"]

    # 1. Images. Une photo manquante arrête tout avant l'écriture de la moindre page.
    for festival in festivals:
        sortie = racine / "images" / festival["slug"]
        for index, photo in enumerate(festival["photos"]):
            photo.update(preparer_photo(source / festival["dossier"] / photo["fichier"],
                                        sortie, festival["slug"], index + 1))
            photo["index"] = index
        _nettoyer(sortie, len(festival["photos"]))

    # 2. Pages.
    pages = {"index.html": rendre_accueil(cfg), "404.html": rendre_introuvable(cfg)}
    for i, festival in enumerate(festivals):
        suivant = festivals[(i + 1) % len(festivals)]
        pages[f"{festival['slug']}/index.html"] = rendre_festival(festival, suivant)
    for chemin, contenu in pages.items():
        fichier = racine / chemin
        fichier.parent.mkdir(parents=True, exist_ok=True)
        fichier.write_text(contenu, encoding="utf-8", newline="\n")


def main() -> int:
    analyse = argparse.ArgumentParser(description="Génère le site Tonino Photography.")
    analyse.add_argument("--source", required=True, type=Path,
                         help="dossier « portfolio photo » contenant un sous-dossier par festival")
    analyse.add_argument("--racine", type=Path, default=OUTILS.parent,
                         help="dossier où écrire le site (par défaut : le dépôt)")
    options = analyse.parse_args()
    try:
        generer_site(options.source, options.racine)
    except ErreurGeneration as erreur:
        print(f"Erreur : {erreur}", file=sys.stderr)
        return 1
    print(f"Site généré dans {options.racine}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
