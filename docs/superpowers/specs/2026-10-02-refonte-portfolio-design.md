# Refonte du portfolio Tonino Photography — cahier des charges

Date : 2 octobre 2026
Site actuel : https://portfolio-tonino-photography.vercel.app
Maquette validée : direction A « Fosse » (canevas « Refonte Tonino Photography – 3 directions »)

## 1. Objectif

Remplacer le portfolio actuel (une seule page, 18 photos mélangées) par un site organisé par festival, dans un nouveau design, et parfaitement utilisable sur téléphone.

Le site sert de vitrine à Tonino Photography : Anthony le met en avant sur Instagram pour décrocher des couvertures de concerts et de festivals. Il mentionne aussi son activité de création de sites.

Critères de réussite :

- Un visiteur arrive sur l'accueil, choisit un festival et parcourt ses photos en grand, sur téléphone comme sur ordinateur.
- Chaque festival a sa propre adresse, envoyable telle quelle à un organisateur.
- Le site garde l'adresse actuelle.
- Le code est sauvegardé en ligne et ne dépend plus d'un ordinateur.

## 2. Périmètre

Inclus :

- Une page d'accueil et quatre pages festival.
- Une visionneuse plein écran pour les photos.
- Un affichage adapté au téléphone, à la tablette et à l'ordinateur.
- La préparation des photos (redimensionnement, allègement).
- La mise en ligne à l'adresse actuelle.

Exclus :

- Photo de profil.
- Formulaire de contact (liens e-mail et Instagram uniquement).
- Version anglaise.
- Espace d'administration en ligne.
- Blog, boutique, tarifs.

## 3. Pages et adresses

| Page | Adresse | Contenu |
|---|---|---|
| Accueil | `/` | Photo plein écran, liste des festivals, À propos, Contact |
| Utopia Festival | `/utopia/` | Galerie de 20 photos |
| Raggamuffin Festival | `/raggamuffin/` | Galerie de 11 photos |
| ZikZac | `/zikzac/` | Galerie de 15 photos |
| Astroluna | `/astroluna/` | Galerie de 14 photos |

Une adresse inconnue affiche une page « introuvable » avec un lien vers l'accueil.

### 3.1 Accueil

De haut en bas :

1. **Bandeau photo plein écran.** Photo du DJ bras ouverts (Utopia). Par-dessus : le nom « Tonino Photography », le menu (Festivals, À propos, Contact), le titre « Capturer l'instant où la scène prend feu. » avec « prend feu. » en rouge-orangé, l'accroche, et « Marseille · Disponible pour vos dates 2026 ».
2. **Festivals.** Quatre grandes bandes cliquables, une par festival, du plus récent au plus ancien. Chaque bande montre une photo du festival, son numéro, son nom en très grandes capitales et son nombre de photos.
3. **À propos.** Titre « De la fosse aux backstages. », la bio, la fiche matériel et la mention des sites internet. Texte seul.
4. **Contact.** Bloc rouge-orangé : l'adresse e-mail en très grand (cliquable), le lien Instagram, « Marseille, France ».
5. **Pied de page.** « © 2026 Tonino Photography — Anthony Valldecabres » et un lien « Retour en haut ».

### 3.2 Page festival

De haut en bas :

1. **Barre de menu** (fond noir), avec « Festivals » mis en évidence.
2. **En-tête.** Lien « ← Tous les festivals », nom du festival en capitales géantes, puis une ligne : nom complet, lieu, dates, nombre de photos.
3. **Galerie.** Voir section 5.
4. **Festival suivant.** Une bande cliquable identique à celles de l'accueil. Après le dernier festival, la bande renvoie au premier.
5. **Pied de page.**

## 4. Contenu

### 4.1 Festivals

| Ordre | Nom affiché | Nom complet | Lieu | Dates | Photos |
|---|---|---|---|---|---|
| 01 | Utopia | Utopia Festival | Marseille | 26 et 27 septembre 2026 | 20 |
| 02 | Raggamuffin | Raggamuffin Festival | Nice | 4 août 2026 | 11 |
| 03 | ZikZac | ZikZac | Aix-en-Provence | 9 au 11 juillet 2026 | 15 |
| 04 | Astroluna | Astroluna | Marignane | 4 juillet 2026 | 14 |

### 4.2 Textes

Repris du site actuel, sans modification :

- **Titre :** Capturer l'instant où la scène prend feu.
- **Accroche :** Photographe de concerts et de festivals, tous styles de musique confondus — de la fosse aux backstages.
- **Bio :** Je m'appelle Anthony, et je documente les concerts et festivals depuis la fosse — au plus près du son, de la sueur et de la lumière de scène. Pas de style unique : le reggae d'un dimanche après-midi, le rap d'une salle bondée, l'électro d'une nuit de festival. Ce qui m'intéresse, c'est l'instant qui ne se reproduira pas deux fois. Basé à Marseille, disponible pour couvrir vos concerts, festivals et événements — en France comme ailleurs.
- **Matériel :** Canon EOS R50 · Tamron 17-70mm f/2.8 · Marseille · Disponible pour dates 2026
- **Sites internet :** En dehors de la photo, je conçois aussi des sites internet sur mesure — celui-ci en est un exemple.
- **Contact :** photobytonino@gmail.com · Instagram @tonino_photography · Marseille, France

### 4.3 Photos retenues

Les photos viennent du dossier `portfolio photo` (un sous-dossier par festival). L'ordre ci-dessous est l'ordre d'affichage. La colonne « Légende » est le nom affiché dans la visionneuse ; elle est vide pour les photos de public et d'ambiance.

**Utopia Festival** (dossier `Utopia 2026`)

| N° | Fichier | Légende |
|---|---|---|
| 01 | Anthony_Valldercabres_40.jpg | |
| 02 | Anthony_Valldercabres_10.jpg | |
| 03 | Anthony_Valldercabres_12.jpg | |
| 04 | Anthony_Valldercabres_17.jpg | |
| 05 | Anthony_Valldercabres_4.jpg | |
| 06 | Anthony_Valldercabres_47.jpg | |
| 07 | Anthony_Valldercabres_14.jpg | |
| 08 | Anthony_Valldercabres_1.jpg | |
| 09 | Anthony_Valldercabres_18.jpg | |
| 10 | Anthony_Valldercabres_35.jpg | |
| 11 | Anthony_Valldercabres_24.jpg | |
| 12 | Anthony_Valldercabres_7.jpg | |
| 13 | Anthony_Valldercabres_29.jpg | |
| 14 | Anthony_Valldercabres_9.jpg | |
| 15 | Anthony_Valldercabres_11.jpg | |
| 16 | Anthony_Valldercabres_32.jpg | |
| 17 | Anthony_Valldercabres_44.jpg | |
| 18 | Anthony_Valldercabres_51.jpg | |
| 19 | Anthony_Valldercabres_31.jpg | |
| 20 | Anthony_Valldercabres_ColinBenders.jpg | Colin Benders |

**Raggamuffin Festival** (dossier `raggamuffin 2026`)

| N° | Fichier | Légende |
|---|---|---|
| 01 | Tonino_photography_raggamuffin_Cozik.jpg | Cozik |
| 02 | Tonino_photography_raggamuffin_Marcusgad.jpg | Marcus Gad |
| 03 | Tonino_photography_raggamuffin_Vanupié2.jpg | Vanupié |
| 04 | Tonino_photography_raggamuffin_fayapid.jpg | Fayapid |
| 05 | Tonino_photography_raggamuffin_fayapidcozik.jpg | Fayapid & Cozik |
| 06 | Tonino_photography_raggamuffin_l'entourloop.jpg | L'Entourloop |
| 07 | Tonino_photography_raggamuffin_l'entourloop2.jpg | L'Entourloop |
| 08 | Tonino_photography_raggamuffin_l'entourloop3.jpg | L'Entourloop |
| 09 | Tonino_photography_raggamuffin_public1.jpg | |
| 10 | Tonino_photography_raggamuffin_public2.jpg | |
| 11 | Tonino_photography_raggamuffin_public7.jpg | |

**ZikZac** (dossier `zikzac 2026`)

| N° | Fichier | Légende |
|---|---|---|
| 01 | Tonino_photography_DaCruz2.jpg | Da Cruz |
| 02 | Tonino_photography_Dance.jpg | |
| 03 | Tonino_photography_DjZakir.jpg | DJ Zakir |
| 04 | Tonino_photography_Graph.jpg | |
| 05 | Tonino_photography_KinGongoloKiniata.jpg.jpg | Kin'Gongolo Kiniata |
| 06 | Tonino_photography_La CafeteriaRoja.jpg | La Cafetera Roja |
| 07 | Tonino_photography_MrBu.jpg | Mr Bu |
| 08 | Tonino_photography_Sidiaz2.jpg | Sidiaz |
| 09 | Tonino_photography_TOPmouvementee.jpg | |
| 10 | Tonino_photography_Valpiniste.jpg | Le Valpiniste |
| 11 | Tonino_photography_Vanupié2.jpg.jpg | Vanupié |
| 12 | Tonino_photography_Vaudoogame2.jpg | Vaudou Game |
| 13 | Tonino_photography_amphiplein.jpg | |
| 14 | Tonino_photography_dancepublique.jpg | |
| 15 | Tonino_photography_publiqueportrait.jpg | |

**Astroluna** (dossier `Astroluna 2026`)

| N° | Fichier | Légende |
|---|---|---|
| 01 | Tonino_photographie_Gambino.jpg | Gambino |
| 02 | Tonino_photographie_Gradur2.jpg | Gradur |
| 03 | Tonino_photography_Andyman2.jpg.jpg | Andyman |
| 04 | Tonino_photography_BLV.jpg.jpg | BLV |
| 05 | Tonino_photography_Carla.jpg.jpg | Carla |
| 06 | Tonino_photography_Dr.Bisous.jpg.jpg | Docteur Bisous |
| 07 | Tonino_photography_Eniah.jpg.jpg | Eniah |
| 08 | Tonino_photography_Lesram.jpg.jpg | Lesram |
| 09 | Tonino_photography_Leto.jpg.jpg | Leto |
| 10 | Tonino_photography_Vin-G.jpg.jpg | Vin-G |
| 11 | Tonino_photography_publique2.jpg.jpg | |
| 12 | Tonino_photography_publique5.jpg.jpg | |
| 13 | Tonino_photography_publique7.jpg.jpg | |
| 14 | Tonino_photography_weshenfoiré.jpg.jpg | |

Photos de couverture :

| Usage | Photo |
|---|---|
| Bandeau de l'accueil | Utopia n° 01 |
| Bande Utopia | Utopia n° 03 |
| Bande Raggamuffin | Raggamuffin n° 08 |
| Bande ZikZac | ZikZac n° 12 |
| Bande Astroluna | Astroluna n° 13 |

## 5. Galerie et visionneuse

### 5.1 Galerie

- Les photos gardent leurs proportions d'origine, sans recadrage.
- 3 colonnes sur ordinateur, 2 sur tablette et téléphone, avec un espace de 6 px entre les photos.
- Les photos sont placées dans l'ordre de la section 4.3, chacune dans la colonne la moins haute à ce moment-là, pour que les colonnes finissent à peu près à la même hauteur.
- Chaque photo est un bouton : un clic, un appui ou la touche Entrée ouvre la visionneuse sur cette photo.
- Les photos situées plus bas que l'écran se chargent au fur et à mesure du défilement.

### 5.2 Visionneuse

Ouverture : la photo s'affiche en grand sur fond noir, entière, quelle que soit son orientation.

Navigation entre les photos du festival :

| Action | Téléphone / tablette | Ordinateur |
|---|---|---|
| Photo suivante | Glisser vers la gauche | Flèche droite du clavier, bouton « › », ou glisser à la souris |
| Photo précédente | Glisser vers la droite | Flèche gauche du clavier, bouton « ‹ », ou glisser à la souris |
| Fermer | Bouton « × » | Bouton « × », touche Échap, ou clic sur le fond noir |

Comportement détaillé :

- Pendant le glissement, la photo suit le doigt. Au-delà de 50 px ou d'un geste rapide, on passe à la photo voisine ; sinon la photo revient en place.
- Après la dernière photo, on revient à la première, et inversement.
- Un compteur « 07 / 20 » et la légende (quand elle existe) s'affichent en bas.
- Les photos voisines sont préchargées pour que le passage soit immédiat.
- Tant que la visionneuse est ouverte, la page derrière ne défile pas.
- À la fermeture, on retrouve la galerie à l'endroit de la dernière photo vue.
- Si le visiteur a demandé à réduire les animations sur son appareil, les transitions sont instantanées.

## 6. Design (direction A « Fosse »)

Esprit : affiche de concert. Fond noir, titres énormes en capitales, une seule couleur d'accent.

| Élément | Valeur |
|---|---|
| Fond | `#0A0A0A` |
| Texte principal | `#F4F1EA` |
| Texte secondaire | `#A8A49B` |
| Filets | `#2B2B2B` |
| Accent | `#FF4B1F` (texte posé dessus : `#0A0A0A`) |
| Police des titres | Big Shoulders Display, graisse 900, en capitales |
| Police du texte | Archivo, graisses 400 à 600 |
| Chargement des polices | Google Fonts, avec une police de secours le temps du chargement |

Règles :

- Les titres s'adaptent à la largeur de l'écran et ne débordent jamais.
- Tout texte posé sur une photo repose sur un voile sombre, pour rester lisible quelle que soit la photo.
- Les liens passent en rouge-orangé au survol.
- Le survol d'une bande festival éclaircit légèrement sa photo.

## 7. Affichage selon l'écran

| Largeur | Mise en page |
|---|---|
| Moins de 700 px (téléphone) | Menu replié derrière un bouton ; bandes festival moins hautes avec le nombre de photos au-dessus du nom ; À propos sur une colonne ; galerie sur 2 colonnes |
| 700 à 1100 px (tablette) | Menu visible ; À propos sur une colonne ; galerie sur 2 colonnes |
| Plus de 1100 px (ordinateur) | Conforme à la maquette : À propos sur 2 colonnes ; galerie sur 3 colonnes |

Sur téléphone, le bouton de menu ouvre un panneau plein écran avec les trois liens ; il se ferme au choix d'un lien, au bouton « × » ou à la touche Échap. Toutes les zones cliquables font au moins 44 px de côté. Aucune page ne défile horizontalement.

## 8. Technique

### 8.1 Choix

Site statique en HTML, CSS et JavaScript, sans framework ni dépendance à installer, comme le dépôt `portfolio-bulma`.

Pourquoi ce choix plutôt qu'Astro ou Next.js : le site compte cinq pages et aucun contenu dynamique. Un site statique se charge plus vite, ne demande aucune maintenance et reste lisible par Anthony.

### 8.2 Organisation des fichiers

```
portfolio-tonino-photography/
├── index.html                 accueil
├── utopia/index.html          une page par festival
├── raggamuffin/index.html
├── zikzac/index.html
├── astroluna/index.html
├── 404.html
├── css/style.css              tout le style
├── js/menu.js                 menu mobile
├── js/visionneuse.js          visionneuse plein écran
├── images/<festival>/         photos préparées
├── outils/
│   ├── festivals.json         festivals, photos, légendes, textes alternatifs
│   └── generer.py             prépare les photos et génère les pages
└── docs/                      ce document
```

Chaque fichier a un seul rôle :

- `festivals.json` est la seule source du contenu des galeries (section 4).
- `generer.py` lit `festivals.json` et les photos d'origine, écrit les images préparées et les pages HTML. Il ne contient aucun contenu.
- `visionneuse.js` ne connaît que la galerie de la page où il est chargé ; il lit la liste des photos dans le HTML.
- `menu.js` ne gère que le menu mobile.

Les pages générées sont enregistrées dans le dépôt : Vercel les sert telles quelles, sans étape de construction.

### 8.3 Préparation des photos

Les originaux pèsent 0,3 à 16 Mo et restent sur l'ordinateur d'Anthony ; ils ne vont pas dans le dépôt.

Pour chaque photo, `generer.py` produit :

| Version | Largeur | Usage |
|---|---|---|
| Vignette | 640 px et 1000 px | Galerie (le navigateur choisit selon l'écran) |
| Grand format | 1400 px et 2200 px (plus grand côté) | Visionneuse, bandeau, bandes |

Chaque version existe en WebP, avec une copie JPEG pour les navigateurs anciens. Poids visé : moins de 150 Ko par vignette, moins de 500 Ko par grand format. Les fichiers portent des noms simples (`utopia-01-1000.webp`). Les dimensions sont inscrites dans le HTML pour que la page ne saute pas pendant le chargement.

### 8.4 Référencement et partage

- Chaque page a son titre et sa description (« Utopia Festival 2026, Marseille — Tonino Photography »).
- Chaque page a une image d'aperçu pour le partage sur les réseaux sociaux et les messageries (la photo de couverture du festival).
- Chaque photo a un texte alternatif en français qui la décrit.
- Langue déclarée : français.

### 8.5 Hébergement

1. Le code est poussé dans un nouveau dépôt GitHub du compte `anto84290-tech`, nommé `portfolio-tonino-photography`.
2. Le projet Vercel existant est relié à ce dépôt. Chaque modification poussée met le site à jour automatiquement.
3. L'adresse `portfolio-tonino-photography.vercel.app` est conservée.

Le nouveau site est d'abord poussé sur une branche `refonte`, que Vercel publie sur une adresse de prévisualisation. Il ne remplace l'ancien site (branche `main`) qu'après validation par Anthony.

### 8.6 Ajouter un festival plus tard

1. Anthony dépose un nouveau sous-dossier dans `portfolio photo`.
2. Une entrée est ajoutée à `festivals.json` (nom, lieu, dates, photos retenues, légendes).
3. `generer.py` est relancé ; il crée les images et la nouvelle page, et met à jour l'accueil et les liens « festival suivant ».

## 9. Vérification avant mise en ligne

- Chaque page est ouverte en 390 px, 820 px et 1440 px de large : pas de défilement horizontal, pas de texte coupé ni superposé.
- La visionneuse est testée au doigt (glisser, fermer), au clavier (flèches, Échap, Entrée, Tab) et à la souris, sur la première, la dernière et une photo au milieu de chaque galerie.
- Tous les liens internes fonctionnent, y compris les liens du menu depuis une page festival et la page « introuvable ».
- Les 60 photos s'affichent, dans l'ordre de la section 4.3, avec la bonne légende.
- Le poids de chaque page au premier affichage reste sous 1,5 Mo.
- Anthony valide le site sur l'adresse de prévisualisation avant le remplacement de l'ancien.

## 10. Points à confirmer par Anthony

1. L'orthographe des légendes de la section 4.3, déduite des noms de fichiers.
2. La sélection de photos, s'il souhaite en changer.
3. L'accès à son compte Vercel au moment de la mise en ligne, pour relier le projet au nouveau dépôt.
