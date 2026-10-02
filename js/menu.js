// Menu mobile : le bouton ouvre et ferme le panneau de navigation.
(function () {
  "use strict";

  var bouton = document.querySelector(".menu-bouton");
  var menu = document.getElementById("menu");
  if (!bouton || !menu) return;

  function regler(ouvert) {
    menu.classList.toggle("ouvert", ouvert);
    document.documentElement.classList.toggle("menu-ouvert", ouvert);
    bouton.setAttribute("aria-expanded", String(ouvert));
    bouton.setAttribute("aria-label", ouvert ? "Fermer le menu" : "Ouvrir le menu");
  }

  function estOuvert() {
    return bouton.getAttribute("aria-expanded") === "true";
  }

  bouton.addEventListener("click", function () {
    regler(!estOuvert());
  });

  menu.addEventListener("click", function (evenement) {
    if (evenement.target.closest("a")) regler(false);
  });

  // Le panneau n'existe que sur téléphone : s'il est ouvert quand l'écran s'élargit
  // (téléphone tourné), on le referme pour ne pas bloquer la page.
  var ecranLarge = window.matchMedia("(min-width: 700px)");
  var auChangement = function (evenement) { if (evenement.matches) regler(false); };
  if (ecranLarge.addEventListener) ecranLarge.addEventListener("change", auChangement);
  else if (ecranLarge.addListener) ecranLarge.addListener(auChangement);

  document.addEventListener("keydown", function (evenement) {
    if (evenement.key === "Escape" && estOuvert()) {
      regler(false);
      bouton.focus();
    }
  });
})();
