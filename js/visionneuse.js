// Visionneuse plein écran de la galerie d'un festival.
// Un clic sur une photo l'ouvre en grand ; on passe à la suivante ou à la
// précédente en glissant, avec les flèches du clavier ou avec les boutons.
(function () {
  "use strict";

  var galerie = document.querySelector("[data-galerie]");
  if (!galerie || typeof HTMLDialogElement === "undefined") return;

  var SEUIL_DISTANCE = 50;   // px : au-delà, on change de photo
  var SEUIL_VITESSE = 0.5;   // px par ms : un geste rapide suffit aussi
  var SEUIL_MOUVEMENT = 6;   // px : en dessous, c'est un clic et non un glissement

  var dialogue = null;
  var scene, source, image, compteur, legende, precedent, suivant, fermer;
  var photos = [];
  var courant = 0;
  var geste = null;
  var ignorerClic = false;

  // ---------------------------------------------------------------- données

  function lirePhotos() {
    var variantes = galerie.querySelectorAll(".colonnes");
    var visible = null;
    for (var i = 0; i < variantes.length; i++) {
      if (variantes[i].offsetParent !== null) { visible = variantes[i]; break; }
    }
    var liens = Array.prototype.slice.call((visible || galerie).querySelectorAll("a.photo"));
    liens.sort(function (a, b) { return Number(a.dataset.index) - Number(b.dataset.index); });
    return liens.map(function (lien) {
      var vignette = lien.querySelector("img");
      return {
        lien: lien,
        jpeg: lien.getAttribute("href"),
        webp: lien.dataset.grandSrcset || "",
        legende: lien.dataset.legende || "",
        alt: vignette ? vignette.getAttribute("alt") || "" : ""
      };
    });
  }

  function deuxChiffres(n) {
    return (n < 10 ? "0" : "") + n;
  }

  // ------------------------------------------------------------ construction

  function bouton(classe, etiquette, trace) {
    var b = document.createElement("button");
    b.type = "button";
    b.className = classe;
    b.setAttribute("aria-label", etiquette);
    b.innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
      'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="' + trace + '"/></svg>';
    return b;
  }

  function construire() {
    dialogue = document.createElement("dialog");
    dialogue.className = "visionneuse";
    dialogue.setAttribute("aria-label", "Photo en grand");

    fermer = bouton("visionneuse-fermer", "Fermer", "M5 5l14 14M19 5L5 19");
    precedent = bouton("visionneuse-precedent", "Photo précédente", "M15 5l-7 7 7 7");
    suivant = bouton("visionneuse-suivant", "Photo suivante", "M9 5l7 7-7 7");

    scene = document.createElement("div");
    scene.className = "visionneuse-scene";
    var cadre = document.createElement("picture");
    source = document.createElement("source");
    source.type = "image/webp";
    source.sizes = "100vw";
    image = document.createElement("img");
    image.className = "visionneuse-image";
    image.draggable = false;
    image.decoding = "async";
    cadre.appendChild(source);
    cadre.appendChild(image);
    scene.appendChild(cadre);

    var bas = document.createElement("div");
    bas.className = "visionneuse-bas";
    compteur = document.createElement("span");
    compteur.className = "visionneuse-compteur";
    compteur.setAttribute("aria-live", "polite");
    legende = document.createElement("span");
    legende.className = "visionneuse-legende";
    bas.appendChild(compteur);
    bas.appendChild(legende);

    dialogue.appendChild(fermer);
    dialogue.appendChild(precedent);
    dialogue.appendChild(suivant);
    dialogue.appendChild(scene);
    dialogue.appendChild(bas);
    document.body.appendChild(dialogue);

    fermer.addEventListener("click", function () { dialogue.close(); });
    precedent.addEventListener("click", function () { aller(-1); });
    suivant.addEventListener("click", function () { aller(1); });
    dialogue.addEventListener("close", auFermer);
    dialogue.addEventListener("keydown", auClavier);
    dialogue.addEventListener("click", auClicSurLeFond);
    scene.addEventListener("pointerdown", debutGeste);
    scene.addEventListener("pointermove", suiteGeste);
    scene.addEventListener("pointerup", finGeste);
    scene.addEventListener("pointercancel", annulerGeste);
  }

  // --------------------------------------------------------------- affichage

  function precharger(index) {
    var photo = photos[index];
    if (!photo || photo.prechargee) return;
    photo.prechargee = true;
    var tampon = new Image();
    tampon.sizes = "100vw";
    if (photo.webp) tampon.srcset = photo.webp;
    tampon.src = photo.jpeg;
  }

  function afficher(index) {
    courant = index;
    var photo = photos[courant];
    image.style.transform = "";
    source.srcset = photo.webp;
    image.src = photo.jpeg;
    image.alt = photo.alt;
    compteur.textContent = deuxChiffres(courant + 1) + " / " + deuxChiffres(photos.length);
    legende.textContent = photo.legende;
    legende.hidden = !photo.legende;
    if (photos.length > 1) {
      precharger((courant + 1) % photos.length);
      precharger((courant - 1 + photos.length) % photos.length);
    }
  }

  function aller(pas) {
    if (photos.length < 2) return;
    afficher((courant + pas + photos.length) % photos.length);
  }

  function ouvrir(index) {
    if (!dialogue) construire();
    photos = lirePhotos();
    if (!photos.length) return;
    var seule = photos.length < 2;
    precedent.hidden = seule;
    suivant.hidden = seule;
    afficher(Math.max(0, Math.min(index, photos.length - 1)));
    document.documentElement.classList.add("visionneuse-ouverte");
    dialogue.showModal();
    fermer.focus();
  }

  function auFermer() {
    document.documentElement.classList.remove("visionneuse-ouverte");
    image.removeAttribute("src");
    source.removeAttribute("srcset");
    var photo = photos[courant];
    if (photo && photo.lien) {
      photo.lien.scrollIntoView({ block: "center", behavior: "instant" });
      photo.lien.focus({ preventScroll: true });
    }
  }

  // ----------------------------------------------------------------- clavier

  function auClavier(evenement) {
    if (evenement.key === "ArrowRight") { evenement.preventDefault(); aller(1); }
    else if (evenement.key === "ArrowLeft") { evenement.preventDefault(); aller(-1); }
    else if (evenement.key === "Tab") { garderLeFocus(evenement); }
  }

  // Le focus tourne entre les boutons visibles et ne sort jamais de la visionneuse.
  function garderLeFocus(evenement) {
    var boutons = [fermer, precedent, suivant].filter(function (b) { return b.offsetParent !== null; });
    if (!boutons.length) return;
    var position = boutons.indexOf(document.activeElement);
    var prochain = evenement.shiftKey
      ? (position <= 0 ? boutons.length - 1 : position - 1)
      : (position === boutons.length - 1 ? 0 : position + 1);
    evenement.preventDefault();
    boutons[prochain].focus();
  }

  // ----------------------------------------------------------------- pointeur

  function auClicSurLeFond(evenement) {
    if (ignorerClic) { ignorerClic = false; return; }
    if (evenement.target === dialogue || evenement.target === scene) dialogue.close();
  }

  function debutGeste(evenement) {
    if (evenement.pointerType === "mouse" && evenement.button !== 0) return;
    ignorerClic = false;
    geste = { id: evenement.pointerId, x: evenement.clientX, y: evenement.clientY, t: evenement.timeStamp, dx: 0, dy: 0 };
    if (scene.setPointerCapture) {
      try { scene.setPointerCapture(evenement.pointerId); } catch (erreur) { /* pointeur déjà relâché */ }
    }
    if (evenement.pointerType === "mouse") evenement.preventDefault();
  }

  function suiteGeste(evenement) {
    if (!geste || evenement.pointerId !== geste.id) return;
    geste.dx = evenement.clientX - geste.x;
    geste.dy = evenement.clientY - geste.y;
    if (Math.abs(geste.dx) > SEUIL_MOUVEMENT || Math.abs(geste.dy) > SEUIL_MOUVEMENT) ignorerClic = true;
    if (photos.length > 1 && Math.abs(geste.dx) > Math.abs(geste.dy)) {
      image.classList.add("en-glissement");
      image.style.transform = "translateX(" + geste.dx + "px)";
    } else {
      image.style.transform = "";
    }
  }

  function finGeste(evenement) {
    if (!geste || evenement.pointerId !== geste.id) return;
    var dx = evenement.clientX - geste.x;
    var dy = evenement.clientY - geste.y;
    var duree = Math.max(1, evenement.timeStamp - geste.t);
    geste = null;
    image.classList.remove("en-glissement");
    image.style.transform = "";
    var horizontal = Math.abs(dx) > Math.abs(dy);
    var assezLoin = Math.abs(dx) > SEUIL_DISTANCE;
    var assezVite = Math.abs(dx) > SEUIL_MOUVEMENT * 2 && Math.abs(dx) / duree > SEUIL_VITESSE;
    if (horizontal && (assezLoin || assezVite)) aller(dx < 0 ? 1 : -1);
  }

  function annulerGeste() {
    geste = null;
    image.classList.remove("en-glissement");
    image.style.transform = "";
  }

  // ------------------------------------------------------------------ entrée

  galerie.addEventListener("click", function (evenement) {
    var lien = evenement.target.closest("a.photo");
    if (!lien || evenement.button !== 0 || evenement.ctrlKey || evenement.metaKey || evenement.shiftKey || evenement.altKey) return;
    evenement.preventDefault();
    ouvrir(Number(lien.dataset.index));
  });
})();
