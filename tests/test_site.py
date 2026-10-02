"""Tests du site dans un vrai navigateur (Chromium piloté par Playwright).

Le dépôt est servi en local ; les polices Google sont bloquées pour que les
tests ne dépendent pas du réseau (le site utilise alors sa police de secours).
"""
import http.server
import threading
import unittest
from functools import partial
from pathlib import Path

from playwright.sync_api import sync_playwright

RACINE = Path(__file__).resolve().parent.parent
CHROMIUM = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

LARGEURS = [390, 820, 1440]
PAGES = ["/", "/utopia/", "/raggamuffin/", "/zikzac/", "/astroluna/", "/404.html"]


class _Silencieux(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class SiteTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.serveur = http.server.ThreadingHTTPServer(
            ("127.0.0.1", 0), partial(_Silencieux, directory=str(RACINE)))
        threading.Thread(target=cls.serveur.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.serveur.server_address[1]}"
        cls.playwright = sync_playwright().start()
        options = {"executable_path": CHROMIUM} if Path(CHROMIUM).exists() else {}
        cls.navigateur = cls.playwright.chromium.launch(**options)

    @classmethod
    def tearDownClass(cls):
        cls.navigateur.close()
        cls.playwright.stop()
        cls.serveur.shutdown()
        cls.serveur.server_close()

    def setUp(self):
        self._contextes = []

    def tearDown(self):
        for contexte in self._contextes:
            contexte.close()

    def page(self, chemin, largeur, hauteur=900, tactile=False, javascript=True, mouvement_reduit=False):
        """Ouvre `chemin` dans une fenêtre de la taille donnée et renvoie la page chargée."""
        contexte = self.navigateur.new_context(
            viewport={"width": largeur, "height": hauteur},
            has_touch=tactile,
            java_script_enabled=javascript,
            reduced_motion="reduce" if mouvement_reduit else "no-preference",
        )
        self._contextes.append(contexte)
        contexte.route("**/fonts.googleapis.com/**", lambda route: route.abort())
        contexte.route("**/fonts.gstatic.com/**", lambda route: route.abort())
        page = contexte.new_page()
        page.goto(self.base + chemin, wait_until="load")
        return page


class TestMiseEnPage(SiteTestCase):
    def test_pas_de_defilement_horizontal(self):
        for chemin in PAGES:
            for l in LARGEURS:
                p = self.page(chemin, l)
                self.assertLessEqual(p.evaluate("document.documentElement.scrollWidth"), l, (chemin, l))

    def test_aucun_titre_ne_deborde(self):
        for chemin in PAGES:
            for l in LARGEURS:
                p = self.page(chemin, l)
                trop = p.evaluate("""() => [...document.querySelectorAll('h1,h2,.bande-nom,.contact-mail')]
                    .filter(e => e.scrollWidth > e.clientWidth + 1 || e.getBoundingClientRect().right > innerWidth + 1)
                    .map(e => e.textContent.trim())""")
                self.assertEqual(trop, [], (chemin, l))

    def test_noms_de_festival_sur_une_seule_ligne(self):
        # Avec la police de secours calibrée, aucun nom n'est coupé au milieu d'un mot.
        for l in LARGEURS:
            p = self.page("/", l)
            lignes = p.evaluate("""() => [...document.querySelectorAll('.bande-nom')].map(e =>
                Math.round(e.getBoundingClientRect().height / parseFloat(getComputedStyle(e).lineHeight)))""")
            self.assertEqual(lignes, [1, 1, 1, 1], l)

    def test_nombre_de_colonnes(self):
        for l, n in [(390, 2), (820, 2), (1440, 3)]:
            p = self.page("/utopia/", l)
            self.assertEqual(p.locator(".colonnes:visible .colonne").count(), n, l)

    def test_photos_non_recadrees(self):
        for l, variante in [(1440, ".colonnes-3"), (390, ".colonnes-2")]:
            p = self.page("/raggamuffin/", l)
            ecarts = p.evaluate("""(v) => [...document.querySelectorAll(v + ' .photo img')].map(i =>
                Math.abs(i.clientWidth / i.clientHeight - i.getAttribute('width') / i.getAttribute('height')))""", variante)
            self.assertEqual(len(ecarts), 11)
            self.assertTrue(all(e < 0.02 for e in ecarts), ecarts)

    def test_espace_de_6px_entre_les_photos(self):
        p = self.page("/utopia/", 1440)
        self.assertEqual(p.evaluate("getComputedStyle(document.querySelector('.colonnes-3')).columnGap"), "6px")
        self.assertEqual(p.evaluate("getComputedStyle(document.querySelector('.colonnes-3 .colonne')).rowGap"), "6px")

    def test_couleurs(self):
        p = self.page("/", 1440)
        self.assertEqual(p.evaluate("getComputedStyle(document.body).backgroundColor"), "rgb(10, 10, 10)")
        self.assertEqual(p.evaluate("getComputedStyle(document.body).color"), "rgb(244, 241, 234)")
        self.assertEqual(p.evaluate("getComputedStyle(document.querySelector('#contact')).backgroundColor"), "rgb(255, 75, 31)")
        self.assertEqual(p.evaluate("getComputedStyle(document.querySelector('.accent')).color"), "rgb(255, 75, 31)")

    def test_zones_cliquables_de_44px(self):
        for chemin in ["/", "/utopia/"]:
            p = self.page(chemin, 390)
            petites = p.evaluate("""() => [...document.querySelectorAll('a:not(.sr), button')]
                .filter(e => e.offsetParent && (e.getBoundingClientRect().height < 44))
                .map(e => e.textContent.trim().slice(0, 30))""")
            self.assertEqual(petites, [], chemin)

    def test_a_propos_en_colonnes(self):
        for l, colonnes in [(390, 1), (820, 1), (1440, 2)]:
            p = self.page("/", l)
            n = p.evaluate("getComputedStyle(document.querySelector('#a-propos')).gridTemplateColumns.split(' ').length")
            self.assertEqual(n, colonnes, l)

    def test_bandes_lisibles_sur_telephone(self):
        p = self.page("/", 390)
        h = p.evaluate("document.querySelector('.bande').getBoundingClientRect().height")
        self.assertTrue(150 <= h <= 200, h)

    def test_bande_en_grand_sur_ordinateur(self):
        p = self.page("/", 1440)
        self.assertEqual(p.evaluate("document.querySelector('.bande').getBoundingClientRect().height"), 300)
        self.assertEqual(p.evaluate("document.querySelector('.bandeau').getBoundingClientRect().height"), 860)

    def test_titres_en_capitales(self):
        p = self.page("/", 1440)
        self.assertEqual(p.evaluate("getComputedStyle(document.querySelector('.bandeau-titre')).textTransform"), "uppercase")
        self.assertIn("Big Shoulders Display", p.evaluate("getComputedStyle(document.querySelector('.bande-nom')).fontFamily"))


class TestMenu(SiteTestCase):
    def test_bouton_visible_seulement_sur_telephone(self):
        self.assertTrue(self.page("/", 390).locator(".menu-bouton").is_visible())
        self.assertFalse(self.page("/", 1440).locator(".menu-bouton").is_visible())
        self.assertTrue(self.page("/", 820).locator("#menu a").first.is_visible())

    def test_ouvre_et_ferme(self):
        p = self.page("/", 390)
        b = p.locator(".menu-bouton")
        self.assertFalse(p.locator("#menu a").first.is_visible())
        b.click()
        self.assertEqual(b.get_attribute("aria-expanded"), "true")
        self.assertEqual(p.locator("#menu a:visible").count(), 3)
        p.keyboard.press("Escape")
        self.assertEqual(b.get_attribute("aria-expanded"), "false")
        self.assertFalse(p.locator("#menu a").first.is_visible())
        self.assertTrue(b.evaluate("e => e === document.activeElement"))

    def test_le_bouton_referme_le_menu(self):
        p = self.page("/utopia/", 390)
        b = p.locator(".menu-bouton")
        b.click()
        self.assertTrue(p.locator(".menu-bouton .icone-fermer").is_visible())
        self.assertTrue(p.evaluate("document.documentElement.classList.contains('menu-ouvert')"))
        b.click()
        self.assertFalse(p.locator("#menu a").first.is_visible())
        self.assertTrue(p.locator(".menu-bouton .icone-ouvrir").is_visible())
        self.assertFalse(p.evaluate("document.documentElement.classList.contains('menu-ouvert')"))

    def test_se_ferme_au_choix_d_un_lien(self):
        p = self.page("/", 390)
        p.locator(".menu-bouton").click()
        p.locator("#menu a", has_text="Contact").click()
        self.assertFalse(p.locator("#menu a").first.is_visible())
        self.assertIn("#contact", p.url)

    def test_liens_depuis_une_page_festival(self):
        p = self.page("/zikzac/", 1440)
        p.locator("#menu a", has_text="À propos").click()
        p.wait_for_url("**/#a-propos")
        self.assertTrue(p.url.endswith("/#a-propos"))

    def test_menu_utilisable_sans_javascript(self):
        p = self.page("/", 390, javascript=False)
        self.assertEqual(p.locator("#menu a:visible").count(), 3)
        self.assertFalse(p.locator(".menu-bouton").is_visible())


if __name__ == "__main__":
    unittest.main()
