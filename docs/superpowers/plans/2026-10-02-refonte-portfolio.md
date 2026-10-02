# Refonte du portfolio Tonino Photography — plan de réalisation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construire un site statique de cinq pages (accueil + quatre festivals) dans le design « Fosse », avec visionneuse plein écran, et le mettre en ligne à l'adresse actuelle.

**Architecture:** Un script Python (`outils/generer.py`) lit `outils/festivals.json` et les photos d'origine, écrit les images allégées dans `images/` et les pages HTML à la racine du dépôt à partir de gabarits. Le style tient dans un seul fichier CSS ; deux petits scripts JavaScript indépendants gèrent le menu mobile et la visionneuse. Les pages générées sont enregistrées dans le dépôt et servies telles quelles par Vercel.

**Tech Stack:** HTML, CSS, JavaScript sans dépendance. Python 3.13 + Pillow (WebP) pour la génération. Tests : `unittest` (bibliothèque standard) et Playwright pour Python avec le Chromium déjà installé (`/opt/pw-browsers`).

**Spec:** `docs/superpowers/specs/2026-10-02-refonte-portfolio-design.md`

## Global Constraints

- Aucune installation possible dans l'espace de travail (npm et pip sont bloqués) : uniquement la bibliothèque standard Python, Pillow et Playwright déjà présents.
- Photos d'origine : `/mnt/user-data/uploads/portfolio photo/<dossier du festival>/`. Elles ne vont jamais dans le dépôt.
- Couleurs : fond `#0A0A0A`, texte `#F4F1EA`, texte secondaire `#A8A49B`, filets `#2B2B2B`, accent `#FF4B1F` (texte posé dessus `#0A0A0A`).
- Polices : Big Shoulders Display 900 en capitales pour les titres, Archivo 400–600 pour le texte, chargées depuis Google Fonts avec `display=swap`.
- Seuils d'affichage : téléphone `< 700px`, tablette `700px–1100px`, ordinateur `> 1100px`.
- Galerie : 3 colonnes au-dessus de 1100 px, 2 en dessous, espace de 6 px, photos jamais recadrées.
- Zones cliquables d'au moins 44 px de côté. Aucun défilement horizontal.
- Langue des pages : `fr`. Tous les textes sont ceux de la section 4.2 du spec, sans modification.
- Ordre des festivals : Utopia, Raggamuffin, ZikZac, Astroluna.
- Tout le code, les noms de fichiers et les messages de commit sont en français, sans accent dans les noms de fichiers.
- Rien n'est poussé sur la branche `main` du dépôt GitHub avant la validation d'Anthony.

## Review Focus

1. **Photo d'origine plus petite que les tailles visées** (les photos de public d'Astroluna font 1365 × 2048) : aucune image n'est agrandie, et le `srcset` ne liste que des fichiers qui existent. → test dans la tâche 1.
2. **Noms de fichiers d'origine avec accents, espaces, apostrophes ou double extension** (`weshenfoiré.jpg.jpg`, `La CafeteriaRoja.jpg`, `l'entourloop.jpg`) : les fichiers produits ont des noms simples en ASCII et la photo est bien trouvée. → test dans la tâche 1.
3. **Geste surtout vertical dans la visionneuse** : faire défiler ou glisser en diagonale ne doit pas changer de photo. → test dans la tâche 5.
4. **JavaScript absent ou en échec** : un clic sur une photo ouvre quand même l'image en grand, et le menu reste utilisable. → tests dans les tâches 2 et 4.
5. **Photo listée dans `festivals.json` mais absente du dossier** : la génération s'arrête avec un message qui nomme le fichier, sans produire un site incomplet. → test dans la tâche 1.

---

## Structure des fichiers

| Fichier | Rôle |
|---|---|
| `outils/festivals.json` | Seule source du contenu : festivals, photos, légendes, textes alternatifs, couvertures |
| `outils/generer.py` | Logique : lecture du JSON, préparation des images, répartition en colonnes, rendu des pages |
| `outils/gabarits/accueil.html`, `festival.html`, `404.html` | Balisage et textes fixes de chaque page, avec des emplacements `$nom` |
| `outils/gabarits/_bande.html`, `_photo.html`, `_entete.html`, `_pied.html` | Fragments réutilisés |
| `css/style.css` | Tout le style |
| `js/menu.js` | Menu mobile uniquement |
| `js/visionneuse.js` | Visionneuse uniquement |
| `tests/test_generer.py` | Tests du générateur (`unittest`) |
| `tests/test_site.py` | Tests dans le navigateur (Playwright) |
| `tests/photos_test/` | Petites images créées par les tests, jamais les vraies photos |
| `vercel.json`, `.vercelignore` | Réglages d'hébergement |

Commande de génération : `python3 outils/generer.py --source "/mnt/user-data/uploads/portfolio photo"`
Commande de test : `python3 -m unittest discover -s tests -v`

---

### Task 1 : Données et préparation des images

**Files:**
- Create: `outils/festivals.json`, `outils/generer.py`, `tests/test_generer.py`

**Interfaces:**
- Produces:
  - `festivals.json` : `{"festivals": [{"slug", "nom", "nom_complet", "lieu", "dates", "dossier", "couverture": <n°>, "photos": [{"fichier", "legende", "alt"}]}], "accueil": {"bandeau": {"festival": <slug>, "photo": <n°>}}}`. Les n° commencent à 1 et suivent l'ordre de `photos`.
  - `charger_config(chemin: Path) -> dict`
  - `nom_image(slug: str, numero: int, largeur: int, ext: str) -> str` → `"utopia-01-1000.webp"`
  - `preparer_photo(source: Path, dossier_sortie: Path, slug: str, numero: int) -> dict` → `{"largeur": int, "hauteur": int, "vignettes": [(largeur, nom)], "grands": [(largeur, nom)]}` ; `largeur`/`hauteur` sont celles de l'original après rotation EXIF.
  - `class ErreurGeneration(Exception)`
  - Constantes : `VIGNETTES = (640, 1000)` (largeur), `GRANDS = (1400, 2200)` (plus grand côté), `QUALITE_WEBP = 78`, `QUALITE_JPEG = 80`.

- [ ] **Step 1 : Écrire `outils/festivals.json`**

Reprendre exactement les tableaux des sections 4.1 et 4.3 du spec (noms, lieux, dates, dossiers, fichiers dans l'ordre, légendes, couvertures). Pour chaque photo, rédiger `alt` en regardant la photo : une phrase en français de 20 à 120 caractères qui décrit ce qu'on voit, sans commencer par « Photo de » ni répéter la légende seule.

- [ ] **Step 2 : Écrire les tests qui échouent**

```python
# tests/test_generer.py
class TestConfig(unittest.TestCase):
    def test_quatre_festivals_dans_l_ordre(self):
        cfg = charger_config(RACINE / "outils/festivals.json")
        self.assertEqual([f["slug"] for f in cfg["festivals"]],
                         ["utopia", "raggamuffin", "zikzac", "astroluna"])
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
    # setUp crée dans un dossier temporaire, avec Pillow :
    #   "grande paysage.jpg" 4000x3000, "petite_é'.jpg.jpg" 1365x2048
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
```

- [ ] **Step 3 : Lancer les tests et constater l'échec**

Run: `python3 -m unittest tests.test_generer -v`
Expected: erreur d'import (`generer` n'existe pas).

- [ ] **Step 4 : Écrire `charger_config`, `nom_image`, `preparer_photo`, `ErreurGeneration` dans `outils/generer.py`**

`preparer_photo` applique `ImageOps.exif_transpose`, convertit en RGB, redimensionne avec `Image.LANCZOS`. Une taille visée supérieure à l'original est remplacée par la taille de l'original ; les tailles identiques sont dédoublonnées. Les vignettes sont dimensionnées par la largeur, les grands formats par le plus grand côté. Un fichier déjà présent et plus récent que sa source n'est pas régénéré.

- [ ] **Step 5 : Lancer les tests et constater le succès**

Run: `python3 -m unittest tests.test_generer -v`
Expected: 8 tests OK.

- [ ] **Step 6 : Commit**

```bash
git add outils tests && git commit -m "Ajoute les donnees des festivals et la preparation des images"
```

---

### Task 2 : Génération des pages

**Files:**
- Create: `outils/gabarits/accueil.html`, `festival.html`, `404.html`, `_entete.html`, `_pied.html`, `_bande.html`, `_photo.html`
- Modify: `outils/generer.py`, `tests/test_generer.py`
- Produit par la génération : `index.html`, `utopia/index.html`, `raggamuffin/index.html`, `zikzac/index.html`, `astroluna/index.html`, `404.html`, `images/<slug>/…`

**Interfaces:**
- Consumes: tout le bloc « Produces » de la tâche 1.
- Produces:
  - `repartir_colonnes(photos: list[dict], n: int) -> list[list[dict]]` : parcourt les photos dans l'ordre et place chacune dans la colonne dont la somme des `hauteur / largeur` est la plus petite (la plus à gauche en cas d'égalité).
  - `generer_site(source: Path, racine: Path) -> None` et `main()` avec les options `--source` (obligatoire) et `--racine` (par défaut le dépôt).
  - Contrat HTML utilisé par les tâches 3, 4 et 5 :
    - Menu : `<header class="entete">` contenant `<button class="menu-bouton" aria-expanded="false" aria-controls="menu">` et `<nav id="menu" class="menu">` avec les liens `Festivals` (`/#festivals`), `À propos` (`/#a-propos`), `Contact` (`/#contact`).
    - Accueil : sections `#festivals`, `#a-propos`, `#contact` ; bandes `<a class="bande" href="/<slug>/">`.
    - Galerie : `<div class="galerie" data-galerie>` contenant deux variantes, `<div class="colonnes colonnes-3">` et `<div class="colonnes colonnes-2">`, chacune faite de `<div class="colonne">`. La variante à 2 colonnes porte `aria-hidden="true"` et ses liens `tabindex="-1"` ; le CSS n'en affiche qu'une.
    - Photo : `<a class="photo" href="<grand 2200 jpg>" data-index="<0…n-1>" data-legende="<légende ou vide>" data-grand-srcset="<webp, largeurs réelles>"><img src srcset sizes width height alt loading="lazy"></a>`. Les trois premières photos de chaque variante ont `loading="eager"`.
    - Emplacement de la visionneuse : aucun balisage ; `visionneuse.js` crée son propre élément.

- [ ] **Step 1 : Écrire les tests qui échouent**

Ajouter à `tests/test_generer.py`. `setUpClass` génère un site complet dans un dossier temporaire à partir de `tests/photos_test/` (petites images fabriquées avec Pillow, une par entrée du vrai `festivals.json`, en respectant l'orientation de l'original). Le HTML est lu avec `html.parser`.

```python
class TestColonnes(unittest.TestCase):
    def test_place_dans_la_colonne_la_moins_haute(self):
        photos = [{"id": 1, "largeur": 4, "hauteur": 3}, {"id": 2, "largeur": 3, "hauteur": 4},
                  {"id": 3, "largeur": 4, "hauteur": 3}, {"id": 4, "largeur": 4, "hauteur": 3}]
        cols = repartir_colonnes(photos, 3)
        self.assertEqual([[p["id"] for p in c] for c in cols], [[1, 4], [2], [3]])

    def test_aucune_photo_perdue(self):
        photos = [{"id": i, "largeur": 4, "hauteur": 3} for i in range(20)]
        self.assertEqual(sum(len(c) for c in repartir_colonnes(photos, 2)), 20)

class TestPages(unittest.TestCase):
    def test_six_pages_generees(self):
        for p in ["index.html", "utopia/index.html", "raggamuffin/index.html",
                  "zikzac/index.html", "astroluna/index.html", "404.html"]:
            self.assertTrue((self.site / p).exists(), p)

    def test_accueil_liste_les_festivals_dans_l_ordre(self):
        self.assertEqual(self.hrefs("index.html", "a.bande"),
                         ["/utopia/", "/raggamuffin/", "/zikzac/", "/astroluna/"])

    def test_textes_de_l_accueil(self):
        html = self.lire("index.html")
        for t in ["Capturer l'instant", "prend feu.", "De la fosse", "Canon EOS R50",
                  "Tamron 17-70mm f/2.8", "photobytonino@gmail.com", "@tonino_photography",
                  "20 photos", "11 photos", "15 photos", "14 photos"]:
            self.assertIn(t, html)

    def test_galerie_complete_et_dans_l_ordre(self):
        for slug, n in [("utopia", 20), ("raggamuffin", 11), ("zikzac", 15), ("astroluna", 14)]:
            index = self.attributs(f"{slug}/index.html", ".colonnes-3 a.photo", "data-index")
            self.assertEqual(sorted(int(i) for i in index), list(range(n)))
            index2 = self.attributs(f"{slug}/index.html", ".colonnes-2 a.photo", "data-index")
            self.assertEqual(sorted(int(i) for i in index2), list(range(n)))

    def test_entete_du_festival(self):
        html = self.lire("raggamuffin/index.html")
        for t in ["Raggamuffin Festival", "Nice", "4 août 2026", "11 photos", "Tous les festivals"]:
            self.assertIn(t, html)

    def test_legende_et_alt(self):
        legendes = self.attributs("utopia/index.html", ".colonnes-3 a.photo", "data-legende")
        self.assertEqual(legendes.count("Colin Benders"), 1)
        self.assertEqual(legendes.count(""), 19)
        for alt in self.attributs("utopia/index.html", "a.photo img", "alt"):
            self.assertGreaterEqual(len(alt), 20)

    def test_images_ont_leurs_dimensions(self):
        for attr in ["width", "height"]:
            for v in self.attributs("zikzac/index.html", "a.photo img", attr):
                self.assertTrue(v.isdigit())

    def test_lien_photo_ouvre_le_grand_format_sans_javascript(self):
        for href in self.attributs("astroluna/index.html", ".colonnes-3 a.photo", "href"):
            self.assertTrue((self.site / href.lstrip("/")).exists(), href)

    def test_tous_les_fichiers_references_existent(self):
        # parcourt src, srcset, data-grand-srcset, href internes de toutes les pages
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
```

- [ ] **Step 2 : Lancer les tests et constater l'échec**

Run: `python3 -m unittest tests.test_generer -v`
Expected: `repartir_colonnes` et `generer_site` non définis.

- [ ] **Step 3 : Écrire les gabarits**

Les textes fixes viennent de la section 4.2 du spec. `accueil.html` suit la section 3.1, `festival.html` la section 3.2. `_entete.html` charge `/css/style.css`, les polices Google (`Archivo:wght@400;500;600` et `Big+Shoulders+Display:wght@900`, `display=swap`, avec `preconnect`) et `/js/menu.js` en `defer` ; `festival.html` ajoute `/js/visionneuse.js` en `defer`. Tous les chemins sont absolus (`/css/…`, `/images/…`). L'attribut `sizes` des vignettes est `(min-width: 1101px) 33vw, 50vw`. La photo du bandeau est une `<img>` avec `fetchpriority="high"`, `srcset` des grands formats et `sizes="100vw"`.

- [ ] **Step 4 : Écrire `repartir_colonnes`, `generer_site`, `main` dans `outils/generer.py`**

Les gabarits sont remplis avec `string.Template`. Toute valeur issue du JSON passe par `html.escape`. `generer_site` appelle `preparer_photo` pour chaque photo et lève `ErreurGeneration` avant d'écrire la moindre page si une photo manque.

- [ ] **Step 5 : Lancer les tests et constater le succès**

Run: `python3 -m unittest tests.test_generer -v`
Expected: tous les tests OK.

- [ ] **Step 6 : Générer le vrai site et contrôler**

Run: `python3 outils/generer.py --source "/mnt/user-data/uploads/portfolio photo" && find images -name "*.webp" | wc -l && du -sh images`
Expected: aucune erreur ; au moins 220 fichiers WebP ; `images/` sous 60 Mo. Vérifier que chaque vignette pèse moins de 150 Ko et chaque grand format moins de 500 Ko (`find images -size +500k`), sinon baisser `QUALITE_WEBP` de 4 points et relancer.

- [ ] **Step 7 : Commit**

```bash
git add outils tests index.html 404.html utopia raggamuffin zikzac astroluna images
git commit -m "Genere les pages et les images du site"
```

---

### Task 3 : Style (direction « Fosse »)

**Files:**
- Create: `css/style.css`, `tests/test_site.py`

**Interfaces:**
- Consumes: le contrat HTML de la tâche 2.
- Produces: `tests/test_site.py` fournit `class SiteTestCase(unittest.TestCase)` qui, dans `setUpClass`, sert la racine du dépôt avec `http.server` sur un port libre et lance Chromium (`executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome"`), et la méthode `self.page(chemin, largeur, hauteur=900, tactile=False)`. Les requêtes vers `fonts.googleapis.com` et `fonts.gstatic.com` sont interceptées et annulées. Classes d'état que le CSS définit pour les tâches 4 et 5 : `.menu.ouvert`, `html.visionneuse-ouverte` (bloque le défilement), `.visionneuse`, `.visionneuse-image`, `.visionneuse-compteur`, `.visionneuse-legende`, `.visionneuse-precedent`, `.visionneuse-suivant`, `.visionneuse-fermer`.

- [ ] **Step 1 : Écrire les tests qui échouent**

```python
LARGEURS = [390, 820, 1440]
PAGES = ["/", "/utopia/", "/raggamuffin/", "/zikzac/", "/astroluna/", "/404.html"]

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
                trop = p.evaluate("""() => [...document.querySelectorAll('h1,h2,.bande-nom')]
                    .filter(e => e.scrollWidth > e.clientWidth + 1 || e.getBoundingClientRect().right > innerWidth + 1)
                    .map(e => e.textContent.trim())""")
                self.assertEqual(trop, [], (chemin, l))

    def test_nombre_de_colonnes(self):
        for l, n in [(390, 2), (820, 2), (1440, 3)]:
            p = self.page("/utopia/", l)
            self.assertEqual(p.locator(".colonnes:visible .colonne").count(), n, l)

    def test_photos_non_recadrees(self):
        p = self.page("/raggamuffin/", 1440)
        ecarts = p.evaluate("""() => [...document.querySelectorAll('.colonnes-3 .photo img')].map(i =>
            Math.abs(i.clientWidth / i.clientHeight - i.width / i.height))""")
        self.assertTrue(all(e < 0.02 for e in ecarts))

    def test_espace_de_6px_entre_les_photos(self):
        p = self.page("/utopia/", 1440)
        self.assertEqual(p.evaluate("getComputedStyle(document.querySelector('.colonnes-3')).columnGap"), "6px")

    def test_couleurs(self):
        p = self.page("/", 1440)
        self.assertEqual(p.evaluate("getComputedStyle(document.body).backgroundColor"), "rgb(10, 10, 10)")
        self.assertEqual(p.evaluate("getComputedStyle(document.querySelector('#contact')).backgroundColor"), "rgb(255, 75, 31)")

    def test_zones_cliquables_de_44px(self):
        p = self.page("/", 390)
        petites = p.evaluate("""() => [...document.querySelectorAll('a:not(.sr), button')]
            .filter(e => e.offsetParent && (e.getBoundingClientRect().height < 44))
            .map(e => e.textContent.trim().slice(0, 30))""")
        self.assertEqual(petites, [])

    def test_a_propos_en_colonnes(self):
        for l, colonnes in [(390, 1), (820, 1), (1440, 2)]:
            p = self.page("/", l)
            n = p.evaluate("getComputedStyle(document.querySelector('#a-propos')).gridTemplateColumns.split(' ').length")
            self.assertEqual(n, colonnes, l)

    def test_bandes_lisibles_sur_telephone(self):
        p = self.page("/", 390)
        h = p.evaluate("document.querySelector('.bande').getBoundingClientRect().height")
        self.assertTrue(150 <= h <= 200)
```

- [ ] **Step 2 : Lancer les tests et constater l'échec**

Run: `python3 -m unittest tests.test_site -v`
Expected: échecs (pas de feuille de style).

- [ ] **Step 3 : Écrire `css/style.css`**

Reprendre les valeurs de la maquette A (`Main.dc.html`, `A-Festival.dc.html`, `A-Mobile.dc.html` du canevas) : bandeau de 860 px de haut (640 px sur téléphone), bandes de 300 px (176 px sur téléphone, nombre de photos au-dessus du nom), voiles en dégradé sombre sous tout texte posé sur une photo, bloc contact sur fond d'accent. Tailles de titre en `clamp()` : titre du bandeau `clamp(54px, 9vw, 132px)`, nom de bande `clamp(52px, 11vw, 160px)`, titre de festival `clamp(72px, 22vw, 320px)`, e-mail `clamp(28px, 7.6vw, 110px)` avec `overflow-wrap: anywhere`. Pile de secours des titres : `'Big Shoulders Display', 'Arial Narrow', 'Impact', sans-serif`. Survol d'une bande : la photo s'éclaircit. `@media (prefers-reduced-motion: reduce)` supprime toutes les transitions. Le menu et la visionneuse sont stylés ici (états listés dans Interfaces), y compris la règle `@media (max-width: 699px)` qui masque `.menu` tant qu'il n'a pas la classe `ouvert` **uniquement si** `html` porte la classe `js`.

- [ ] **Step 4 : Lancer les tests et constater le succès**

Run: `python3 -m unittest tests.test_site -v`
Expected: tous les tests OK.

- [ ] **Step 5 : Contrôle visuel**

Capturer `/` et `/utopia/` en 390, 820 et 1440 px (`page.screenshot(full_page=True)`) et les comparer à la maquette A : mêmes proportions, pas de texte superposé, voiles suffisants sur les quatre bandes.

- [ ] **Step 6 : Commit**

```bash
git add css tests && git commit -m "Ajoute le style du site (direction Fosse)"
```

---

### Task 4 : Menu mobile

**Files:**
- Create: `js/menu.js`
- Modify: `tests/test_site.py`, `outils/gabarits/_entete.html` (script en ligne d'une ligne qui ajoute la classe `js` à `<html>`)

**Interfaces:**
- Consumes: `.menu-bouton`, `#menu`, `.menu.ouvert`, `html.js` (tâches 2 et 3).
- Produces: rien d'utilisé ailleurs.

- [ ] **Step 1 : Écrire les tests qui échouent**

```python
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
        self.assertTrue(b.evaluate("e => e === document.activeElement"))

    def test_se_ferme_au_choix_d_un_lien(self):
        p = self.page("/", 390)
        p.locator(".menu-bouton").click()
        p.locator("#menu a", has_text="Contact").click()
        self.assertFalse(p.locator("#menu a").first.is_visible())
        self.assertIn("#contact", p.url)

    def test_liens_depuis_une_page_festival(self):
        p = self.page("/zikzac/", 1440)
        p.locator("#menu a", has_text="À propos").click()
        self.assertTrue(p.url.endswith("/#a-propos"))

    def test_menu_utilisable_sans_javascript(self):
        p = self.page("/", 390, javascript=False)
        self.assertEqual(p.locator("#menu a:visible").count(), 3)
```

Ajouter le paramètre `javascript=True` à `SiteTestCase.page` (`java_script_enabled` du contexte Playwright).

- [ ] **Step 2 : Lancer les tests et constater l'échec**

Run: `python3 -m unittest tests.test_site.TestMenu -v`
Expected: échecs sur l'ouverture et la fermeture.

- [ ] **Step 3 : Écrire `js/menu.js`**

Un seul gestionnaire : bascule la classe `ouvert` et `aria-expanded`, ferme sur Échap (en rendant le focus au bouton) et au clic sur un lien. Régénérer les pages après la modification de `_entete.html`.

- [ ] **Step 4 : Lancer les tests et constater le succès**

Run: `python3 -m unittest tests.test_site.TestMenu -v`
Expected: 5 tests OK.

- [ ] **Step 5 : Commit**

```bash
git add js outils tests *.html utopia raggamuffin zikzac astroluna && git commit -m "Ajoute le menu mobile"
```

---

### Task 5 : Visionneuse

**Files:**
- Create: `js/visionneuse.js`
- Modify: `tests/test_site.py`

**Interfaces:**
- Consumes: `[data-galerie]`, `a.photo` et ses attributs `href`, `data-index`, `data-legende`, `data-grand-srcset`, l'`alt` de son `<img>` ; les classes `.visionneuse*` et `html.visionneuse-ouverte` (tâches 2 et 3).
- Produces: rien d'utilisé ailleurs.

- [ ] **Step 1 : Écrire les tests qui échouent**

```python
class TestVisionneuse(SiteTestCase):
    def ouvrir(self, chemin="/utopia/", largeur=1440, index=0, **kw):
        p = self.page(chemin, largeur, **kw)
        p.locator(f".colonnes:visible a.photo[data-index='{index}']").click()
        p.wait_for_selector(".visionneuse[open], .visionneuse.ouverte")
        return p
    def compteur(self, p): return p.locator(".visionneuse-compteur").inner_text()

    def test_clic_ouvre_la_bonne_photo(self):
        p = self.ouvrir(index=6)
        self.assertEqual(self.compteur(p), "07 / 20")
        self.assertFalse(p.url.endswith(".jpg"))

    def test_entree_ouvre_aussi(self):
        p = self.page("/utopia/", 1440)
        p.locator(".colonnes-3 a.photo[data-index='0']").focus()
        p.keyboard.press("Enter")
        self.assertEqual(self.compteur(p), "01 / 20")

    def test_fleches_du_clavier(self):
        p = self.ouvrir(index=0)
        p.keyboard.press("ArrowRight"); self.assertEqual(self.compteur(p), "02 / 20")
        p.keyboard.press("ArrowLeft");  self.assertEqual(self.compteur(p), "01 / 20")

    def test_boucle_aux_extremites(self):
        p = self.ouvrir(index=0)
        p.keyboard.press("ArrowLeft");  self.assertEqual(self.compteur(p), "20 / 20")
        p.keyboard.press("ArrowRight"); self.assertEqual(self.compteur(p), "01 / 20")

    def test_boutons_precedent_et_suivant(self):
        p = self.ouvrir(index=3)
        p.locator(".visionneuse-suivant").click();   self.assertEqual(self.compteur(p), "05 / 20")
        p.locator(".visionneuse-precedent").click(); self.assertEqual(self.compteur(p), "04 / 20")

    def test_glisser_au_doigt(self):
        p = self.ouvrir(largeur=390, index=4, tactile=True)
        self.glisser(p, dx=-120, dy=5);  self.assertEqual(self.compteur(p), "06 / 20")   # vers la gauche = suivante
        self.glisser(p, dx=120, dy=-5);  self.assertEqual(self.compteur(p), "05 / 20")   # vers la droite = précédente

    def test_petit_glissement_revient_en_place(self):
        p = self.ouvrir(largeur=390, index=4, tactile=True)
        self.glisser(p, dx=-30, dy=0, duree_ms=600)
        self.assertEqual(self.compteur(p), "05 / 20")

    def test_geste_vertical_ne_change_pas_de_photo(self):
        p = self.ouvrir(largeur=390, index=4, tactile=True)
        self.glisser(p, dx=-70, dy=200)
        self.assertEqual(self.compteur(p), "05 / 20")

    def test_glisser_a_la_souris(self):
        p = self.ouvrir(index=4)
        p.mouse.move(800, 450); p.mouse.down(); p.mouse.move(600, 455, steps=8); p.mouse.up()
        self.assertEqual(self.compteur(p), "06 / 20")

    def test_fermetures(self):
        for action in [lambda p: p.keyboard.press("Escape"),
                       lambda p: p.locator(".visionneuse-fermer").click(),
                       lambda p: p.mouse.click(8, 450)]:
            p = self.ouvrir(index=2); action(p)
            self.assertEqual(p.locator(".visionneuse:visible").count(), 0)

    def test_photo_entiere_quelle_que_soit_l_orientation(self):
        for chemin, index, l, h in [("/utopia/", 1, 1440, 900), ("/utopia/", 0, 390, 844)]:
            p = self.ouvrir(chemin, l, index, hauteur=h)
            b = p.locator(".visionneuse-image").bounding_box()
            self.assertTrue(b["x"] >= 0 and b["y"] >= 0 and b["x"] + b["width"] <= l and b["y"] + b["height"] <= h)

    def test_legende(self):
        p = self.ouvrir(index=19); self.assertEqual(p.locator(".visionneuse-legende").inner_text(), "Colin Benders")
        p = self.ouvrir(index=0);  self.assertFalse(p.locator(".visionneuse-legende").is_visible())

    def test_page_bloquee_puis_focus_rendu(self):
        p = self.ouvrir(index=10)
        self.assertTrue(p.evaluate("document.documentElement.classList.contains('visionneuse-ouverte')"))
        p.keyboard.press("ArrowRight"); p.keyboard.press("Escape")
        self.assertFalse(p.evaluate("document.documentElement.classList.contains('visionneuse-ouverte')"))
        self.assertEqual(p.evaluate("document.activeElement.dataset.index"), "11")
        self.assertTrue(p.evaluate("(() => { const r = document.activeElement.getBoundingClientRect(); return r.top >= 0 && r.bottom <= innerHeight })()"))

    def test_tab_reste_dans_la_visionneuse(self):
        p = self.ouvrir(index=0)
        for _ in range(6):
            p.keyboard.press("Tab")
            self.assertTrue(p.evaluate("!!document.activeElement.closest('.visionneuse')"))

    def test_voisines_prechargees(self):
        p = self.ouvrir(index=5)
        charges = p.evaluate("performance.getEntriesByType('resource').map(r => r.name).filter(n => /utopia-0[57]-/.test(n)).length")
        self.assertGreaterEqual(charges, 2)

    def test_galerie_d_une_seule_photo(self):
        # page de test fabriquée dans tests/ avec un seul a.photo
        p = self.ouvrir("/tests/une_photo.html", 1440, 0)
        p.keyboard.press("ArrowRight")
        self.assertEqual(self.compteur(p), "01 / 01")
        self.assertFalse(p.locator(".visionneuse-suivant").is_visible())

    def test_sans_animation_si_demande(self):
        p = self.ouvrir(index=0, mouvement_reduit=True)
        self.assertEqual(p.evaluate("getComputedStyle(document.querySelector('.visionneuse-image')).transitionDuration"), "0s")
```

Ajouter à `SiteTestCase` : `glisser(page, dx, dy, duree_ms=150)` (événements tactiles envoyés par le protocole CDP `Input.dispatchTouchEvent`, en 8 pas depuis le centre de l'écran), et les paramètres `tactile` (`has_touch=True`) et `mouvement_reduit` (`reduced_motion="reduce"`) de `page`.

- [ ] **Step 2 : Lancer les tests et constater l'échec**

Run: `python3 -m unittest tests.test_site.TestVisionneuse -v`
Expected: échecs (un clic ouvre le fichier JPEG).

- [ ] **Step 3 : Écrire `js/visionneuse.js`**

Comportement fixé par la section 5.2 du spec. Décisions à respecter :
- La liste des photos vient des `a.photo` de la variante de colonnes visible, triés par `data-index`.
- L'élément créé est un `<dialog class="visionneuse">` ouvert avec `showModal()` (focus enfermé et Échap gérés par le navigateur).
- Glissement avec les événements `pointer` et `touch-action: none` sur l'image : l'image suit le pointeur ; au relâchement, changement de photo si `|dx| > 50` **ou** vitesse `> 0,5 px/ms`, et seulement si `|dx| > |dy|` ; sinon retour en place.
- Compteur sur deux chiffres : `"07 / 20"`.
- Préchargement des deux voisines avec `new Image()` en reprenant `data-grand-srcset` et `sizes="100vw"`.
- À la fermeture : focus sur le `a.photo` de la dernière photo vue, amené à l'écran avec `scrollIntoView({block: "center"})`.
- Avec une seule photo : boutons précédent/suivant masqués, flèches et glissement sans effet.

- [ ] **Step 4 : Lancer les tests et constater le succès**

Run: `python3 -m unittest tests.test_site.TestVisionneuse -v`
Expected: 17 tests OK.

- [ ] **Step 5 : Commit**

```bash
git add js tests && git commit -m "Ajoute la visionneuse plein ecran"
```

---

### Task 6 : Vérification d'ensemble et aperçu pour Anthony

**Files:**
- Modify: `tests/test_site.py`
- Create: `README.md`

**Interfaces:**
- Consumes: le site généré complet.

- [ ] **Step 1 : Écrire les tests d'ensemble**

```python
class TestEnsemble(SiteTestCase):
    def test_poids_au_premier_affichage(self):
        for chemin in ["/", "/utopia/", "/raggamuffin/", "/zikzac/", "/astroluna/"]:
            for l in [390, 1440]:
                p = self.page(chemin, l)
                poids = p.evaluate("performance.getEntriesByType('resource').reduce((s, r) => s + r.transferSize, 0)")
                self.assertLess(poids, 1_500_000, (chemin, l))

    def test_tous_les_liens_internes_repondent(self):
        # suit chaque href interne de chaque page et vérifie le code 200
        self.assertEqual(self.liens_casses(), [])

    def test_adresse_inconnue(self):
        p = self.page("/404.html", 1440)
        p.locator("a[href='/']").first.click()
        self.assertTrue(p.url.endswith("/"))

    def test_aucune_erreur_dans_la_console(self):
        for chemin in ["/", "/utopia/"]:
            self.assertEqual(self.erreurs_console(chemin, 1440), [])
```

- [ ] **Step 2 : Lancer toute la suite**

Run: `python3 -m unittest discover -s tests -v`
Expected: tous les tests OK. Si le poids dépasse 1,5 Mo, corriger la cause (photo du bandeau trop lourde, chargement différé manquant) et relancer.

- [ ] **Step 3 : Écrire `README.md`**

Une page : à quoi sert chaque dossier, la commande de génération, la marche à suivre pour ajouter un festival (section 8.6 du spec), la commande de test.

- [ ] **Step 4 : Envoyer un aperçu à Anthony**

Capturer l'accueil et chaque page festival en 390 et 1440 px, plus la visionneuse ouverte sur téléphone et sur ordinateur, et lui envoyer les images avec la liste des légendes à relire (point 1 de la section 10 du spec). Attendre ses retours avant la tâche 7 ; les intégrer dans `festivals.json` puis régénérer et relancer la suite.

- [ ] **Step 5 : Commit**

```bash
git add -A && git commit -m "Ajoute les verifications d'ensemble et la notice"
```

---

### Task 7 : Mise en ligne

**Files:**
- Create: `vercel.json`, `.vercelignore`

**Interfaces:**
- Consumes: le dépôt complet et validé.

- [ ] **Step 1 : Écrire les réglages d'hébergement**

`vercel.json` :

```json
{ "framework": null, "buildCommand": null, "installCommand": null, "outputDirectory": ".", "cleanUrls": true, "trailingSlash": true }
```

`.vercelignore` : `docs`, `outils`, `tests`, `README.md`.

- [ ] **Step 2 : Créer le dépôt GitHub (avec Anthony)**

Anthony crée sur github.com un dépôt vide `portfolio-tonino-photography` sur le compte `anto84290-tech` et autorise Claude à y accéder. L'attacher ensuite à la session en écriture.

- [ ] **Step 3 : Pousser la branche de test**

```bash
git checkout -b refonte && git push -u origin refonte
```

Ne pas pousser `main`.

- [ ] **Step 4 : Relier Vercel (avec Anthony)**

Anthony ouvre le projet `portfolio` de l'équipe `tonino-photography` : Settings › Git › Connect Git Repository › `anto84290-tech/portfolio-tonino-photography`. Relier le dépôt ne déclenche aucune publication.

Avant tout nouveau push, Anthony vérifie dans Settings › Environments › Production que la branche de production est `main`, et la règle sur `main` si Vercel a choisi `refonte` (c'est le seul moyen d'éviter qu'un push sur `refonte` remplace le site en ligne).

- [ ] **Step 5 : Déclencher et vérifier la prévisualisation**

```bash
git commit --allow-empty -m "Declenche la previsualisation" && git push
```

Dans l'onglet Deployments, la publication doit porter l'étiquette « Preview », pas « Production ». Si elle est partie en production par erreur, Anthony rétablit l'ancienne version depuis Deployments › ancienne publication › Promote to Production (ou Instant Rollback).

Ouvrir l'adresse de prévisualisation : les six pages répondent, les polices Google sont chargées (vérifier qu'aucun titre ne déborde ni ne se coupe avec la vraie police en 320, 360, 375, 390, 768, 820 et 1440 px), la visionneuse fonctionne. Transmettre l'adresse à Anthony pour validation sur son téléphone.

- [ ] **Step 6 : Basculer après validation**

Seulement après le « ok » d'Anthony :

```bash
git checkout main && git merge --ff-only refonte && git push -u origin main
```

Vérifier que `https://portfolio-tonino-photography.vercel.app/` affiche le nouveau site et que `/utopia/` répond.
