# Portfolio Tonino Photography

Site vitrine d'Anthony Valldecabres, photographe de concerts et de festivals à Marseille.
En ligne : https://portfolio-tonino-photography.vercel.app

Le site est fait de pages HTML simples, sans framework. Elles sont fabriquées par un
petit programme à partir de la liste des festivals et des photos d'origine.

## Ce que contient le dépôt

| Emplacement | Rôle |
|---|---|
| `index.html`, `utopia/`, `raggamuffin/`, `zikzac/`, `astroluna/`, `404.html` | Les pages du site. **Elles sont fabriquées automatiquement : ne pas les modifier à la main.** |
| `images/` | Les photos allégées pour le web (fabriquées automatiquement). |
| `css/style.css` | Toute l'apparence du site. |
| `js/menu.js` | Le menu sur téléphone. |
| `js/visionneuse.js` | L'affichage d'une photo en plein écran. |
| `outils/festivals.json` | **Le contenu** : festivals, lieux, dates, photos retenues, légendes, descriptions. |
| `outils/gabarits/` | Les modèles de pages et les textes fixes (titre, bio, contact). |
| `outils/generer.py` | Le programme qui fabrique les pages et les images. |
| `tests/` | Les vérifications automatiques. |
| `docs/` | Le cahier des charges et le plan de réalisation. |

Les photos d'origine (plusieurs Mo chacune) ne sont pas dans le dépôt. Elles restent dans
le dossier `portfolio photo`, avec un sous-dossier par festival.

## Fabriquer le site

Il faut Python 3 et la bibliothèque Pillow (`pip install pillow`).

```bash
python3 outils/generer.py --source "C:\Users\anto8\Desktop\portfolio photo"
```

Le programme allège chaque photo en plusieurs tailles (WebP et JPEG), puis réécrit toutes
les pages. Une photo déjà préparée n'est pas refaite. S'il manque une photo, il s'arrête
en donnant le nom du fichier, sans toucher aux pages.

## Modifier un texte ou une légende

- Légende, description ou ordre des photos, lieu, dates : dans `outils/festivals.json`.
- Titre d'accueil, bio, matériel, contact : dans `outils/gabarits/accueil.html`.

Relancer ensuite la commande ci-dessus, puis envoyer les changements sur GitHub.

## Ajouter un festival

1. Déposer un nouveau sous-dossier de photos dans `portfolio photo`.
2. Ajouter un bloc dans `outils/festivals.json`, en tête de la liste `festivals` s'il est le
   plus récent, sur le modèle des autres :
   - `slug` : le nom dans l'adresse, en minuscules sans accent (`/mon-festival/`) ;
   - `nom`, `nom_complet`, `lieu`, `dates`, `annee` ;
   - `dossier` : le nom exact du sous-dossier de photos ;
   - `photos` : la liste des photos retenues, dans l'ordre d'affichage, avec pour chacune
     `fichier`, `legende` (vide s'il n'y en a pas) et `alt` (une phrase qui décrit la photo) ;
   - `couverture` : le numéro (à partir de 1) de la photo affichée dans la bande de l'accueil.
3. Relancer la commande de fabrication.
4. Envoyer les changements sur GitHub : Vercel met le site à jour tout seul.

## Vérifier

```bash
python3 -m unittest discover -s tests
```

Les vérifications ouvrent le site dans un navigateur (Chromium, piloté par Playwright) en
largeur téléphone, tablette et ordinateur. Elles contrôlent la mise en page, le menu, la
visionneuse, les liens et le poids des pages.

## Mise en ligne

Le dépôt est relié à Vercel. La branche `main` est le site public ; toute autre branche
est publiée sur une adresse de test. Il n'y a aucune étape de construction : Vercel sert
les fichiers tels quels (voir `vercel.json`).
