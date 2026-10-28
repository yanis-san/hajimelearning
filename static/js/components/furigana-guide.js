/**
 * Composant Alpine `furiganaGuide` : fenêtre d'aide à la syntaxe furigana avec copie de modèles.
 * S'ouvre via l'évènement window `open-furigana-guide`.
 */
document.addEventListener('alpine:init', () => {
  Alpine.data('furiganaGuide', () => ({
    open: false,
    copiedIndex: null,

    copyText(text, index) {
      navigator.clipboard.writeText(text).then(() => {
        this.copiedIndex = index;
        setTimeout(() => (this.copiedIndex = null), 1800);
      });
    },
  }));
});
