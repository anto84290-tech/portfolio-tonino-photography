"""Tests du générateur du site (outils/generer.py)."""
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "outils"))

from generer import (  # noqa: E402
    ErreurGeneration,
    charger_config,
    nom_image,
    preparer_photo,
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


if __name__ == "__main__":
    unittest.main()
