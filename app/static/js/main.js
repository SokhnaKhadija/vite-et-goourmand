/**
 * Vite & Gourmand — Script JavaScript principal
 */

'use strict';

/**
 * Affiche ou masque le contenu d'un champ mot de passe.
 * @param {string} inputId - L'id du champ <input type="password">
 * @param {HTMLButtonElement} btn - Le bouton déclencheur
 */
function toggleMDP(inputId, btn) {
  const input = document.getElementById(inputId);
  if (!input) return;

  const icone = btn.querySelector('i');
  if (input.type === 'password') {
    input.type = 'text';
    icone.classList.replace('bi-eye', 'bi-eye-slash');
    btn.setAttribute('aria-label', 'Masquer le mot de passe');
  } else {
    input.type = 'password';
    icone.classList.replace('bi-eye-slash', 'bi-eye');
    btn.setAttribute('aria-label', 'Afficher le mot de passe');
  }
}

/**
 * Ferme automatiquement les alertes Bootstrap après 5 secondes.
 */
function fermerAlertes() {
  document.querySelectorAll('.alert.alert-success, .alert.alert-info').forEach(alerte => {
    setTimeout(() => {
      const bsAlerte = bootstrap.Alert.getOrCreateInstance(alerte);
      if (bsAlerte) bsAlerte.close();
    }, 5000);
  });
}

/**
 * Active les tooltips Bootstrap sur tous les éléments data-bs-toggle="tooltip".
 */
function activerTooltips() {
  document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
    bootstrap.Tooltip.getOrCreateInstance(el);
  });
}

/**
 * Ajoute un lien d'évitement (skip link) pour l'accessibilité RGAA.
 */
function ajouterSkipLink() {
  if (document.getElementById('skip-link')) return;
  const lien = document.createElement('a');
  lien.id = 'skip-link';
  lien.href = '#contenu-principal';
  lien.className = 'skip-link visually-hidden-focusable';
  lien.textContent = 'Aller au contenu principal';
  document.body.prepend(lien);
}

// ── Initialisation au chargement du DOM ──────────────
document.addEventListener('DOMContentLoaded', () => {
  fermerAlertes();
  activerTooltips();
  ajouterSkipLink();
});
