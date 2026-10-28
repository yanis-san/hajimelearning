/**
 * Composant Alpine `builderStatus` : indicateur d'enregistrement automatique du builder.
 * Écoute l'évènement window `builder-status` ({ state, time }) émis par block-editor.js.
 */
document.addEventListener('alpine:init', () => {
  Alpine.data('builderStatus', () => ({
    autosaveStatus: 'saved',
    lastSavedTime: '',

    init() {
      window.addEventListener('builder-status', (event) => {
        this.autosaveStatus = event.detail.state;
        if (event.detail.time) this.lastSavedTime = event.detail.time;
      });
    },
  }));
});
