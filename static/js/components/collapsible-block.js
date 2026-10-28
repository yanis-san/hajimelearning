/**
 * Composant Alpine `collapsibleBlock` : bloc de leçon repliable, ouvert par défaut.
 * Réagit aux évènements window `expand-all-blocks` / `collapse-all-blocks` (bouton « Tout replier »).
 */
document.addEventListener('alpine:init', () => {
  Alpine.data('collapsibleBlock', () => ({
    open: true,
    init() {
      window.addEventListener('expand-all-blocks', () => (this.open = true));
      window.addEventListener('collapse-all-blocks', () => (this.open = false));
    },
  }));
});
