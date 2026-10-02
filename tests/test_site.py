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
        page.set_default_timeout(8000)
        page.goto(self.base + chemin, wait_until="load")
        return page

    def glisser(self, page, dx, dy, duree_ms=150):
        """Glisse un doigt depuis le centre de l'écran, en huit pas."""
        cdp = page.context.new_cdp_session(page)
        taille = page.viewport_size
        x0, y0 = taille["width"] / 2, taille["height"] / 2
        cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x0, "y": y0}]})
        for i in range(1, 9):
            page.wait_for_timeout(duree_ms / 8)
            cdp.send("Input.dispatchTouchEvent", {
                "type": "touchMove", "touchPoints": [{"x": x0 + dx * i / 8, "y": y0 + dy * i / 8}]})
        cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        page.wait_for_timeout(50)


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


class TestVisionneuse(SiteTestCase):
    def ouvrir(self, chemin="/utopia/", largeur=1440, index=0, **options):
        p = self.page(chemin, largeur, **options)
        p.locator(f".colonnes:visible a.photo[data-index='{index}']").click()
        p.wait_for_selector(".visionneuse[open]")
        return p

    def compteur(self, p):
        return p.locator(".visionneuse-compteur").inner_text()

    def attendre_image(self, p):
        p.wait_for_function("""() => { const i = document.querySelector('.visionneuse-image');
            return i && i.complete && i.naturalWidth > 0 }""")

    def test_clic_ouvre_la_bonne_photo(self):
        p = self.ouvrir(index=6)
        self.assertEqual(self.compteur(p), "07 / 20")
        self.assertFalse(p.url.endswith(".jpg"))
        self.attendre_image(p)
        self.assertIn("utopia-07-", p.evaluate("document.querySelector('.visionneuse-image').currentSrc"))

    def test_entree_ouvre_aussi(self):
        p = self.page("/utopia/", 1440)
        p.locator(".colonnes-3 a.photo[data-index='0']").focus()
        p.keyboard.press("Enter")
        self.assertEqual(self.compteur(p), "01 / 20")

    def test_fleches_du_clavier(self):
        p = self.ouvrir(index=0)
        p.keyboard.press("ArrowRight")
        self.assertEqual(self.compteur(p), "02 / 20")
        p.keyboard.press("ArrowLeft")
        self.assertEqual(self.compteur(p), "01 / 20")

    def test_boucle_aux_extremites(self):
        p = self.ouvrir(index=0)
        p.keyboard.press("ArrowLeft")
        self.assertEqual(self.compteur(p), "20 / 20")
        p.keyboard.press("ArrowRight")
        self.assertEqual(self.compteur(p), "01 / 20")

    def test_boutons_precedent_et_suivant(self):
        p = self.ouvrir(index=3)
        p.locator(".visionneuse-suivant").click()
        self.assertEqual(self.compteur(p), "05 / 20")
        p.locator(".visionneuse-precedent").click()
        self.assertEqual(self.compteur(p), "04 / 20")

    def test_glisser_au_doigt(self):
        p = self.ouvrir(largeur=390, hauteur=844, index=4, tactile=True)
        self.glisser(p, dx=-120, dy=5)   # vers la gauche : photo suivante
        self.assertEqual(self.compteur(p), "06 / 20")
        self.glisser(p, dx=120, dy=-5)   # vers la droite : photo précédente
        self.assertEqual(self.compteur(p), "05 / 20")

    def test_petit_glissement_revient_en_place(self):
        p = self.ouvrir(largeur=390, hauteur=844, index=4, tactile=True)
        self.glisser(p, dx=-30, dy=0, duree_ms=600)
        self.assertEqual(self.compteur(p), "05 / 20")
        p.wait_for_timeout(350)
        self.assertIn(p.evaluate("getComputedStyle(document.querySelector('.visionneuse-image')).transform"),
                      ["none", "matrix(1, 0, 0, 1, 0, 0)"])

    def test_geste_rapide_et_court_change_de_photo(self):
        # 40 px seulement (moins que le seuil de distance) mais d'un coup sec.
        p = self.ouvrir(largeur=390, hauteur=844, index=4, tactile=True)
        p.evaluate("""() => {
            const scene = document.querySelector('.visionneuse-scene');
            const ev = (type, x) => scene.dispatchEvent(new PointerEvent(type, {
                pointerId: 7, pointerType: 'touch', isPrimary: true, bubbles: true, clientX: x, clientY: 400 }));
            ev('pointerdown', 200); ev('pointermove', 180); ev('pointerup', 160);
        }""")
        self.assertEqual(self.compteur(p), "06 / 20")

    def test_geste_vertical_ne_change_pas_de_photo(self):
        p = self.ouvrir(largeur=390, hauteur=844, index=4, tactile=True)
        self.glisser(p, dx=-70, dy=200)
        self.assertEqual(self.compteur(p), "05 / 20")
        self.assertEqual(p.locator(".visionneuse[open]").count(), 1)

    def test_glisser_a_la_souris(self):
        p = self.ouvrir(index=4)
        p.mouse.move(800, 450)
        p.mouse.down()
        p.mouse.move(600, 455, steps=8)
        p.mouse.up()
        self.assertEqual(self.compteur(p), "06 / 20")
        self.assertEqual(p.locator(".visionneuse[open]").count(), 1)

    def test_fermetures(self):
        for action in [lambda p: p.keyboard.press("Escape"),
                       lambda p: p.locator(".visionneuse-fermer").click(),
                       lambda p: p.mouse.click(8, 450)]:
            p = self.ouvrir(index=2)
            action(p)
            p.wait_for_selector(".visionneuse", state="hidden")

    def test_photo_entiere_quelle_que_soit_l_orientation(self):
        for chemin, index, l, h in [("/utopia/", 1, 1440, 900), ("/utopia/", 0, 390, 844),
                                    ("/utopia/", 1, 390, 844), ("/utopia/", 0, 1440, 900)]:
            p = self.ouvrir(chemin, l, index, hauteur=h)
            self.attendre_image(p)
            b = p.locator(".visionneuse-image").bounding_box()
            self.assertGreater(b["width"], 200, (index, l))
            self.assertTrue(b["x"] >= 0 and b["y"] >= 0 and b["x"] + b["width"] <= l
                            and b["y"] + b["height"] <= h, (index, l, b))
            proportions = p.evaluate("""() => { const i = document.querySelector('.visionneuse-image');
                return [i.clientWidth / i.clientHeight, i.naturalWidth / i.naturalHeight] }""")
            self.assertAlmostEqual(proportions[0], proportions[1], places=1)

    def test_legende(self):
        p = self.ouvrir(index=19)
        self.assertEqual(p.locator(".visionneuse-legende").inner_text(), "Colin Benders")
        p = self.ouvrir(index=0)
        self.assertFalse(p.locator(".visionneuse-legende").is_visible())

    def test_texte_alternatif_repris_de_la_vignette(self):
        p = self.ouvrir(index=19)
        self.assertIn("Colin Benders", p.locator(".visionneuse-image").get_attribute("alt"))

    def test_page_bloquee_puis_focus_rendu(self):
        p = self.ouvrir(index=10)
        self.assertTrue(p.evaluate("document.documentElement.classList.contains('visionneuse-ouverte')"))
        p.keyboard.press("ArrowRight")
        p.keyboard.press("Escape")
        # La fermeture est signalée par le navigateur juste après la touche : on l'attend.
        p.wait_for_function("!document.documentElement.classList.contains('visionneuse-ouverte')")
        self.assertEqual(p.evaluate("document.activeElement.dataset.index"), "11")
        self.assertTrue(p.evaluate("""(() => { const r = document.activeElement.getBoundingClientRect();
            return r.top >= 0 && r.bottom <= innerHeight })()"""))

    def test_tab_reste_dans_la_visionneuse(self):
        p = self.ouvrir(index=0)
        for _ in range(6):
            p.keyboard.press("Tab")
            self.assertTrue(p.evaluate("!!document.activeElement.closest('.visionneuse')"))
        for _ in range(4):
            p.keyboard.press("Shift+Tab")
            self.assertTrue(p.evaluate("!!document.activeElement.closest('.visionneuse')"))

    def test_voisines_prechargees(self):
        p = self.ouvrir(index=5)
        p.wait_for_load_state("networkidle")
        charges = p.evaluate("""performance.getEntriesByType('resource').map(r => r.name)
            .filter(n => /utopia-0[57]-(1400|2200)\\.webp/.test(n)).length""")
        self.assertGreaterEqual(charges, 2)

    def test_galerie_d_une_seule_photo(self):
        p = self.ouvrir("/tests/une_photo.html", 1440, 0)
        p.keyboard.press("ArrowRight")
        self.assertEqual(self.compteur(p), "01 / 01")
        self.assertFalse(p.locator(".visionneuse-suivant").is_visible())
        self.assertFalse(p.locator(".visionneuse-precedent").is_visible())

    def test_fleches_masquees_sur_telephone(self):
        p = self.ouvrir(largeur=390, hauteur=844, index=0)
        self.assertFalse(p.locator(".visionneuse-suivant").is_visible())
        self.assertTrue(p.locator(".visionneuse-fermer").is_visible())

    def test_sans_animation_si_demande(self):
        p = self.ouvrir(index=0, mouvement_reduit=True)
        self.assertEqual(p.evaluate(
            "getComputedStyle(document.querySelector('.visionneuse-image')).transitionDuration"), "0s")

    def test_seconde_ouverture_fonctionne(self):
        p = self.ouvrir(index=1)
        p.keyboard.press("Escape")
        p.wait_for_selector(".visionneuse", state="hidden")
        p.locator(".colonnes:visible a.photo[data-index='8']").click()
        self.assertEqual(self.compteur(p), "09 / 20")
        self.assertEqual(p.locator(".visionneuse").count(), 1)


if __name__ == "__main__":
    unittest.main()
