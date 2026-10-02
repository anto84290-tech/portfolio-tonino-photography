"""Tests du générateur du site (outils/generer.py)."""
import sys
import tempfile
import unittest
import unittest.mock
from html.parser import HTMLParser
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter, ImageStat

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "outils"))

import generer  # noqa: E402
from generer import (  # noqa: E402
    ErreurGeneration,
    charger_config,
    generer_site,
    nom_image,
    preparer_photo,
    repartir_colonnes,
)


class TestConfig(unittest.TestCase):
    def test_quatre_festivals_dans_l_ordre(self):
        cfg = charger_config(RACINE / "outils/festivals.json")
        self.assertEqual(
            [f["slug"] for f in cfg["festivals"]],
            ["utopia", "raggamuffin", "zikzac", "astroluna"],
        )
        self.assertEqual([len(f["photos"]) for f in cfg["festivals"]], [20, 11, 15, 14])

    def test_chaque_photo_a_un_alt_descriptif(self):
        for f in charger_config(RACINE / "outils/festivals.json")["festivals"]:
            for p in f["photos"]:
                self.assertTrue(20 <= len(p["alt"]) <= 120, p["fichier"])
                self.assertFalse(p["alt"].lower().startswith("photo"), p["fichier"])

    def test_photo_du_bandeau_retouchee(self):
        utopia = charger_config(RACINE / "outils/festivals.json")["festivals"][0]
        self.assertEqual(utopia["photos"][0]["fichier"], "Anthony_Valldercabres_kloud.jpg")

    def test_lieux_et_dates(self):
        f = {x["slug"]: x for x in charger_config(RACINE / "outils/festivals.json")["festivals"]}
        self.assertEqual((f["utopia"]["lieu"], f["utopia"]["dates"]), ("Marseille", "26 et 27 septembre 2026"))
        self.assertEqual((f["raggamuffin"]["lieu"], f["raggamuffin"]["dates"]), ("Nice", "4 août 2026"))
        self.assertEqual((f["zikzac"]["lieu"], f["zikzac"]["dates"]), ("Aix-en-Provence", "9 au 11 juillet 2026"))
        self.assertEqual((f["astroluna"]["lieu"], f["astroluna"]["dates"]), ("Marignane", "4 juillet 2026"))


class TestImages(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.src = base / "source"
        self.out = base / "sortie"
        self.src.mkdir()
        self.out.mkdir()
        Image.new("RGB", (4000, 3000), (40, 60, 200)).save(self.src / "grande paysage.jpg", quality=60)
        Image.new("RGB", (1365, 2048), (200, 60, 40)).save(self.src / "petite_é'.jpg.jpg", quality=60)

    def tearDown(self):
        self._tmp.cleanup()

    def test_nom_image(self):
        self.assertEqual(nom_image("utopia", 1, 1000, "webp"), "utopia-01-1000.webp")

    def test_grande_photo_produit_toutes_les_tailles(self):
        r = preparer_photo(self.src / "grande paysage.jpg", self.out, "test", 1)
        self.assertEqual([l for l, _ in r["vignettes"]], [640, 1000])
        self.assertEqual([l for l, _ in r["grands"]], [1400, 2200])
        for _, nom in r["vignettes"] + r["grands"]:
            self.assertTrue((self.out / nom).exists())
            self.assertTrue((self.out / nom.replace(".webp", ".jpg")).exists())
            self.assertRegex(nom, r"^[a-z0-9.-]+$")

    def test_petite_photo_n_est_jamais_agrandie(self):
        r = preparer_photo(self.src / "petite_é'.jpg.jpg", self.out, "test", 2)
        for largeur, nom in r["vignettes"] + r["grands"]:
            self.assertRegex(nom, r"^[a-z0-9.-]+$")
            with Image.open(self.out / nom) as im:
                self.assertLessEqual(im.width, 1365)
                self.assertLessEqual(im.height, 2048)
        self.assertEqual(len({l for l, _ in r["grands"]}), len(r["grands"]))  # pas de doublon

    def test_proportions_conservees(self):
        r = preparer_photo(self.src / "grande paysage.jpg", self.out, "test", 1)
        with Image.open(self.out / r["vignettes"][0][1]) as im:
            self.assertAlmostEqual(im.width / im.height, 4000 / 3000, places=2)

    def test_photo_absente_arrete_avec_le_nom_du_fichier(self):
        with self.assertRaises(ErreurGeneration) as ctx:
            preparer_photo(self.src / "inexistante.jpg", self.out, "test", 3)
        self.assertIn("inexistante.jpg", str(ctx.exception))

    def test_photo_trop_lourde_est_davantage_compressee(self):
        # Une image très détaillée dépasse le poids visé à la qualité de départ.
        Image.effect_noise((2400, 1800), 90).convert("RGB").save(self.src / "detaillee.jpg", quality=95)
        normal, serre = self.out / "normal", self.out / "serre"
        with unittest.mock.patch.object(generer, "POIDS_MAX_VIGNETTE", 10**9), \
                unittest.mock.patch.object(generer, "POIDS_MAX_GRAND", 10**9):
            r = preparer_photo(self.src / "detaillee.jpg", normal, "test", 4)
        with unittest.mock.patch.object(generer, "POIDS_MAX_VIGNETTE", 1), \
                unittest.mock.patch.object(generer, "POIDS_MAX_GRAND", 1):
            preparer_photo(self.src / "detaillee.jpg", serre, "test", 4)
        for _, nom in r["vignettes"] + r["grands"]:
            for fichier in (nom, nom.replace(".webp", ".jpg")):
                self.assertLess((serre / fichier).stat().st_size, (normal / fichier).stat().st_size, fichier)


def _scene_sombre(grain: int) -> Image.Image:
    """Photo de concert simulée : fond sombre en dégradé, couvert du grain du capteur."""
    taille = (2600, 1733)
    fond = Image.linear_gradient("L").resize(taille).point(lambda v: 12 + v // 6)
    clair = ImageChops.add(fond, Image.effect_noise(taille, grain), 1, -128)
    return Image.merge("RGB", (clair, clair.point(lambda v: int(v * .8)), clair.point(lambda v: min(255, int(v * 1.3)))))


def _grain(image: Image.Image) -> float:
    """Force du grain : ce qui reste de l'image une fois ses grandes formes retirées."""
    gris = image.convert("L")
    return ImageStat.Stat(ImageChops.subtract(gris, gris.filter(ImageFilter.GaussianBlur(2)), 1, 128)).stddev[0]


class TestFidelite(unittest.TestCase):
    """Une photo sombre et granuleuse ne doit pas ressortir en pâtés (« pixelisation »)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _grain_conserve(self, grain: int, sorte: str) -> dict:
        """Part du grain d'origine encore présente dans la plus grande version, par format."""
        origine = _scene_sombre(grain)
        origine.save(self.base / "sombre.png")
        largeur, nom = preparer_photo(self.base / "sombre.png", self.base / "sortie", "test", 1)[sorte][-1]
        reference = _grain(origine.resize((largeur, round(origine.height * largeur / origine.width)), Image.LANCZOS))
        conserve = {}
        for fichier in (nom, nom.replace(".webp", ".jpg")):
            with Image.open(self.base / "sortie" / fichier) as image:
                conserve[fichier.rsplit(".", 1)[1]] = _grain(image) / reference
        return conserve

    def test_grand_format_garde_le_grain(self):
        for ext, part in self._grain_conserve(6, "grands").items():
            self.assertGreater(part, .9, ext)

    def test_vignette_garde_le_grain(self):
        for ext, part in self._grain_conserve(14, "vignettes").items():
            self.assertGreater(part, .8, ext)


class _SiteMiniature(unittest.TestCase):
    """Base : un festival de test « t » dont on choisit les photos, généré dans un dossier temporaire."""

    COULEURS = {"rouge": (220, 30, 30), "vert": (30, 200, 30), "bleu": (30, 30, 220)}

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        base = Path(self._tmp.name)
        self.source, self.site, self.config = base / "source", base / "site", base / "festivals.json"
        (self.source / "d").mkdir(parents=True)
        self.site.mkdir()
        for nom, couleur in self.COULEURS.items():
            Image.new("RGB", (1200, 900), couleur).save(self.source / "d" / f"{nom}.jpg", quality=90)
        correctif = unittest.mock.patch.object(generer, "CONFIG", self.config)
        correctif.start()
        self.addCleanup(correctif.stop)

    def festival(self, noms, **champs):
        f = {"slug": "t", "nom": "Test", "nom_complet": "Festival de test", "lieu": "Marseille",
             "dates": "1er janvier 2026", "annee": 2026, "dossier": "d", "couverture": 1,
             "photos": [{"fichier": f"{n}.jpg", "legende": "", "alt": f"Aplat de couleur {n} pour les tests"}
                        for n in noms]}
        f.update(champs)
        return f

    def ecrire(self, festival, bandeau=None):
        import json
        cfg = {"accueil": {"bandeau": bandeau or {"festival": festival["slug"], "photo": 1}}, "festivals": [festival]}
        self.config.write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf-8")

    def couleur(self, numero):
        with Image.open(self.site / "images" / "t" / f"t-{numero:02d}-640.webp") as im:
            r, v, b = im.convert("RGB").getpixel((320, 240))
        return {max(r, v, b): nom for nom, (r, v, b) in zip(["rouge", "vert", "bleu"], [(r, 0, 0), (0, v, 0), (0, 0, b)])}[max(r, v, b)]


class TestRegeneration(_SiteMiniature):
    def test_changer_l_ordre_des_photos_change_les_images(self):
        self.ecrire(self.festival(["rouge", "vert"]))
        generer_site(self.source, self.site)
        self.assertEqual([self.couleur(1), self.couleur(2)], ["rouge", "vert"])
        self.ecrire(self.festival(["bleu", "rouge", "vert"]))
        generer_site(self.source, self.site)
        self.assertEqual([self.couleur(1), self.couleur(2), self.couleur(3)], ["bleu", "rouge", "vert"])

    def test_remplacer_une_photo_sous_le_meme_nom_regenere_ses_images(self):
        self.ecrire(self.festival(["rouge"]))
        generer_site(self.source, self.site)
        Image.new("RGB", (1200, 900), self.COULEURS["vert"]).save(self.source / "d" / "rouge.jpg", quality=90)
        generer_site(self.source, self.site)
        self.assertEqual(self.couleur(1), "vert")

    def test_photo_retiree_supprime_ses_images(self):
        self.ecrire(self.festival(["rouge", "vert"]))
        generer_site(self.source, self.site)
        self.ecrire(self.festival(["rouge"]))
        generer_site(self.source, self.site)
        restes = [f.name for f in (self.site / "images" / "t").iterdir() if f.name.startswith("t-02-")]
        self.assertEqual(restes, [])

    def test_rien_n_est_refait_si_rien_ne_change(self):
        self.ecrire(self.festival(["rouge", "vert"]))
        generer_site(self.source, self.site)
        images = [f for f in (self.site / "images" / "t").iterdir() if f.suffix in (".webp", ".jpg")]
        dates = {f.name: f.stat().st_mtime_ns for f in images}
        generer_site(self.source, self.site)
        self.assertEqual({f.name: f.stat().st_mtime_ns for f in images}, dates)


class TestValidation(_SiteMiniature):
    def echec(self):
        with self.assertRaises(ErreurGeneration) as ctx:
            generer_site(self.source, self.site)
        self.assertFalse((self.site / "index.html").exists())
        return str(ctx.exception)

    def test_json_mal_forme(self):
        self.config.write_text('{"festivals": [ {"slug": "t",} ]}', encoding="utf-8")
        message = self.echec()
        self.assertIn("festivals.json", message)
        self.assertIn("ligne", message)

    def test_champ_manquant_dans_une_photo(self):
        f = self.festival(["rouge"])
        del f["photos"][0]["alt"]
        self.ecrire(f)
        message = self.echec()
        self.assertIn("alt", message)
        self.assertIn("rouge.jpg", message)

    def test_champ_manquant_dans_un_festival(self):
        f = self.festival(["rouge"])
        del f["annee"]
        self.ecrire(f)
        self.assertIn("annee", self.echec())

    def test_slug_invalide(self):
        self.ecrire(self.festival(["rouge"], slug="Mon Festival"), bandeau={"festival": "Mon Festival", "photo": 1})
        self.assertIn("slug", self.echec())

    def test_couverture_hors_limites(self):
        self.ecrire(self.festival(["rouge", "vert"], couverture=5))
        self.assertIn("couverture", self.echec())

    def test_bandeau_vers_un_festival_inconnu(self):
        self.ecrire(self.festival(["rouge"]), bandeau={"festival": "inconnu", "photo": 1})
        self.assertIn("bandeau", self.echec())

    def test_fichier_qui_n_est_pas_une_image(self):
        (self.source / "d" / "rouge.jpg").write_text("ceci n'est pas une image", encoding="utf-8")
        self.ecrire(self.festival(["rouge"]))
        self.assertIn("rouge.jpg", self.echec())


PHOTO_P3 = Path("/mnt/user-data/uploads/portfolio photo/Astroluna 2026/Tonino_photography_publique7.jpg.jpg")


@unittest.skipUnless(PHOTO_P3.is_file(), "photo d'origine au profil Display P3 indisponible")
class TestCouleurs(unittest.TestCase):
    def test_profil_display_p3_converti_en_srgb(self):
        import io
        from PIL import ImageCms, ImageStat
        with tempfile.TemporaryDirectory() as tmp:
            r = preparer_photo(PHOTO_P3, Path(tmp), "test", 1)
            with Image.open(Path(tmp) / r["vignettes"][0][1]) as sortie:
                sortie = sortie.convert("RGB")
                moyenne = ImageStat.Stat(sortie).mean
            with Image.open(PHOTO_P3) as brute:
                profil = ImageCms.ImageCmsProfile(io.BytesIO(brute.info["icc_profile"]))
                brute = brute.convert("RGB")
                sans_conversion = ImageStat.Stat(brute.resize(sortie.size)).mean
                attendu = ImageStat.Stat(ImageCms.profileToProfile(
                    brute, profil, ImageCms.createProfile("sRGB"), outputMode="RGB").resize(sortie.size)).mean
        ecart = lambda a, b: max(abs(x - y) for x, y in zip(a, b))
        self.assertGreater(ecart(attendu, sans_conversion), 2)   # la conversion change réellement les couleurs
        self.assertLess(ecart(moyenne, attendu), 1.5)            # et le résultat est bien en sRGB


# ---------------------------------------------------------------------------
# Petit lecteur de HTML pour interroger les pages générées
# ---------------------------------------------------------------------------

VIDES = {"meta", "link", "img", "br", "source", "input", "hr"}


class Noeud:
    def __init__(self, tag, attrs, parent):
        self.tag, self.attrs, self.parent, self.enfants = tag, dict(attrs), parent, []

    def classes(self):
        return (self.attrs.get("class") or "").split()

    def tous(self):
        for e in self.enfants:
            yield e
            yield from e.tous()


class Lecteur(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.racine = Noeud("#racine", [], None)
        self.courant = self.racine

    def handle_starttag(self, tag, attrs):
        n = Noeud(tag, [(k, v if v is not None else "") for k, v in attrs], self.courant)
        self.courant.enfants.append(n)
        if tag not in VIDES:
            self.courant = n

    def handle_endtag(self, tag):
        n = self.courant
        while n is not None and n.tag != tag:
            n = n.parent
        if n is not None and n.parent is not None:
            self.courant = n.parent


def _correspond(noeud, simple):
    tag, *classes = simple.split(".")
    return (not tag or noeud.tag == tag) and all(c in noeud.classes() for c in classes)


def selectionner(racine, selecteur):
    """Sélecteur minimal : « tag.classe » séparés par des espaces (descendance)."""
    parties = selecteur.split()
    resultat = []
    for n in racine.tous():
        if not _correspond(n, parties[-1]):
            continue
        ancetre, reste = n.parent, parties[:-1]
        while reste and ancetre is not None:
            if _correspond(ancetre, reste[-1]):
                reste = reste[:-1]
            ancetre = ancetre.parent
        if not reste:
            resultat.append(n)
    return resultat


class TestColonnes(unittest.TestCase):
    def test_place_dans_la_colonne_la_moins_haute(self):
        photos = [{"id": 1, "largeur": 4, "hauteur": 3}, {"id": 2, "largeur": 3, "hauteur": 4},
                  {"id": 3, "largeur": 4, "hauteur": 3}, {"id": 4, "largeur": 4, "hauteur": 3}]
        cols = repartir_colonnes(photos, 3)
        self.assertEqual([[p["id"] for p in c] for c in cols], [[1, 4], [2], [3]])

    def test_aucune_photo_perdue(self):
        photos = [{"id": i, "largeur": 4, "hauteur": 3} for i in range(20)]
        self.assertEqual(sum(len(c) for c in repartir_colonnes(photos, 2)), 20)


PAGES = ["index.html", "utopia/index.html", "raggamuffin/index.html",
         "zikzac/index.html", "astroluna/index.html", "404.html"]


class TestPages(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        base = Path(cls._tmp.name)
        source, cls.site = base / "source", base / "site"
        cfg = charger_config(RACINE / "outils/festivals.json")
        for f in cfg["festivals"]:
            (source / f["dossier"]).mkdir(parents=True)
            for i, p in enumerate(f["photos"]):
                taille = (900, 1200) if i % 3 == 1 else (1200, 900)
                Image.new("RGB", taille, (30 + i * 9, 40, 90)).save(source / f["dossier"] / p["fichier"], quality=50)
        cls.site.mkdir()
        generer_site(source, cls.site)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def lire(self, page):
        return (self.site / page).read_text(encoding="utf-8")

    def dom(self, page):
        lecteur = Lecteur()
        lecteur.feed(self.lire(page))
        return lecteur.racine

    def attributs(self, page, selecteur, attribut):
        return [n.attrs.get(attribut) for n in selectionner(self.dom(page), selecteur)]

    def hrefs(self, page, selecteur):
        return self.attributs(page, selecteur, "href")

    def references_manquantes(self):
        """Images et pages internes citées par le site mais absentes du dossier généré."""
        manquantes = []
        for page in PAGES:
            for n in self.dom(page).tous():
                cibles = []
                for attr in ("src", "href"):
                    if attr in n.attrs:
                        cibles.append(n.attrs[attr])
                for attr in ("srcset", "data-grand-srcset"):
                    if n.attrs.get(attr):
                        cibles += [c.strip().split(" ")[0] for c in n.attrs[attr].split(",")]
                if n.tag == "meta" and n.attrs.get("property") == "og:image":
                    cibles.append("/" + n.attrs["content"].split("/", 3)[3])
                for c in cibles:
                    chemin = c.split("#")[0]
                    # Les feuilles de style et scripts vivent dans le dépôt, pas dans le dossier généré.
                    if not chemin.startswith("/") or chemin.startswith(("/css/", "/js/")):
                        continue
                    fichier = self.site / chemin.lstrip("/")
                    if chemin.endswith("/"):
                        fichier = fichier / "index.html"
                    if not fichier.is_file():
                        manquantes.append((page, c))
        return manquantes

    def test_six_pages_generees(self):
        for p in PAGES:
            self.assertTrue((self.site / p).exists(), p)

    def test_accueil_liste_les_festivals_dans_l_ordre(self):
        self.assertEqual(self.hrefs("index.html", "a.bande"),
                         ["/utopia/", "/raggamuffin/", "/zikzac/", "/astroluna/"])

    def test_textes_de_l_accueil(self):
        html = self.lire("index.html")
        for t in ["Capturer l'instant", "prend feu.", "De la fosse", "Canon EOS R50", "Sony A7 II",
                  "Tamron 17-70mm f/2.8", "Sony 50mm f/1.9", "Boîtiers", "Objectifs", "photobytonino@gmail.com", "@tonino_photography",
                  "20 photos", "11 photos", "15 photos", "14 photos"]:
            self.assertIn(t, html)

    def test_galerie_complete_et_dans_l_ordre(self):
        for slug, n in [("utopia", 20), ("raggamuffin", 11), ("zikzac", 15), ("astroluna", 14)]:
            index = self.attributs(f"{slug}/index.html", ".colonnes-3 a.photo", "data-index")
            self.assertEqual(sorted(int(i) for i in index), list(range(n)))
            index2 = self.attributs(f"{slug}/index.html", ".colonnes-2 a.photo", "data-index")
            self.assertEqual(sorted(int(i) for i in index2), list(range(n)))

    def test_nombre_de_colonnes_dans_chaque_variante(self):
        d = self.dom("utopia/index.html")
        self.assertEqual(len(selectionner(d, ".colonnes-3 .colonne")), 3)
        self.assertEqual(len(selectionner(d, ".colonnes-2 .colonne")), 2)

    def test_entete_du_festival(self):
        html = self.lire("raggamuffin/index.html")
        for t in ["Raggamuffin Festival", "Nice", "4 août 2026", "11 photos", "Tous les festivals"]:
            self.assertIn(t, html)

    def test_titre_du_festival_indique_son_nombre_de_lettres(self):
        # Le style s'en sert pour que le nom occupe la largeur sans jamais déborder.
        for slug, n in [("utopia", 6), ("raggamuffin", 11), ("zikzac", 6), ("astroluna", 9)]:
            styles = self.attributs(f"{slug}/index.html", "h1.festival-titre", "style")
            self.assertEqual(styles, [f"--car: {n}"])

    def test_legende_et_alt(self):
        legendes = self.attributs("utopia/index.html", ".colonnes-3 a.photo", "data-legende")
        self.assertEqual(legendes.count("Colin Benders"), 1)
        self.assertEqual(legendes.count("Kloud"), 1)
        for artiste, nombre in {"Koboyo": 1, "2bonmat": 1, "Evänder": 1, "Justine Perry": 2, "Roüge": 2,
                                "KX CHR": 2, "EXC": 1, "Nona": 1}.items():
            self.assertEqual(legendes.count(artiste), nombre, artiste)
        self.assertEqual(legendes.count(""), 7)  # public et ambiances
        for alt in self.attributs("utopia/index.html", "a.photo img", "alt"):
            self.assertGreaterEqual(len(alt), 20)

    def test_apostrophe_dans_une_legende(self):
        legendes = self.attributs("raggamuffin/index.html", ".colonnes-3 a.photo", "data-legende")
        self.assertEqual(legendes.count("L'Entourloop"), 3)

    def test_images_ont_leurs_dimensions(self):
        for attr in ["width", "height"]:
            for v in self.attributs("zikzac/index.html", "a.photo img", attr):
                self.assertTrue(v.isdigit())

    def test_lien_photo_ouvre_le_grand_format_sans_javascript(self):
        for href in self.attributs("astroluna/index.html", ".colonnes-3 a.photo", "href"):
            self.assertTrue(href.endswith(".jpg"), href)
            self.assertTrue((self.site / href.lstrip("/")).exists(), href)

    def test_tous_les_fichiers_references_existent(self):
        self.assertEqual(self.references_manquantes(), [])

    def test_festival_suivant_boucle(self):
        self.assertEqual(self.hrefs("utopia/index.html", "a.bande"), ["/raggamuffin/"])
        self.assertEqual(self.hrefs("astroluna/index.html", "a.bande"), ["/utopia/"])

    def test_titre_description_et_apercu(self):
        html = self.lire("utopia/index.html")
        self.assertIn("<title>Utopia Festival 2026, Marseille — Tonino Photography</title>", html)
        self.assertIn('property="og:image"', html)
        self.assertIn('<html lang="fr">', html)

    def test_page_introuvable(self):
        self.assertIn('href="/"', self.lire("404.html"))

    def test_photo_manquante_n_ecrit_aucune_page(self):
        with tempfile.TemporaryDirectory() as tmp:
            vide, site = Path(tmp) / "source", Path(tmp) / "site"
            vide.mkdir()
            site.mkdir()
            with self.assertRaises(ErreurGeneration):
                generer_site(vide, site)
            self.assertFalse((site / "index.html").exists())


if __name__ == "__main__":
    unittest.main()
