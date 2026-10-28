// Alpine component for the lesson block editor: tabs plus debounced autosave through HTMX.
// Usage: x-data="blockEditor('/url/to/post/to')" on the wrapper; the <form> carries
//   x-ref="blockForm", hx-trigger="submit, autosave" and x-on:builder-saved="onSaved($event.detail)".
// The server answers autosave requests (header X-Autosave) with the refreshed block list and an
// HX-Trigger `builder-saved` event ({ savedAt, blockId, editUrl? }). Load before Alpine starts.
document.addEventListener('alpine:init', () => {
  const notify = (detail) => window.dispatchEvent(new CustomEvent('builder-status', { detail }));

  Alpine.data('blockEditor', () => ({
    tab: 'edit',
    autosaveState: 'saved',
    lastSavedText: 'Tous les changements sont enregistrés',
    saveTimer: null,
    hasUnsaved: false,

    init() {
      const form = this.$refs.blockForm;
      const isAutosave = (event) => event.detail.requestConfig?.triggeringEvent?.type === 'autosave';

      form.addEventListener('htmx:configRequest', (event) => {
        if (event.detail.triggeringEvent?.type === 'autosave') event.detail.headers['X-Autosave'] = 'true';
      });
      form.addEventListener('htmx:responseError', (event) => isAutosave(event) && this.onError());
      form.addEventListener('htmx:sendError', (event) => isAutosave(event) && this.onError());

      window.addEventListener('beforeunload', (event) => {
        if (!this.hasUnsaved) return;
        this.autosave();
        event.preventDefault();
        event.returnValue = '';
      });
      document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'hidden' && this.hasUnsaved) this.autosave();
      });
    },

    markDirty() {
      this.hasUnsaved = true;
      this.autosaveState = 'dirty';
      this.lastSavedText = 'Modifications en cours…';
      notify({ state: 'dirty' });
      clearTimeout(this.saveTimer);
      this.saveTimer = setTimeout(() => this.autosave(), 1200);
    },

    autosave() {
      if (!this.hasUnsaved && this.autosaveState === 'saved') return;
      clearTimeout(this.saveTimer);
      this.autosaveState = 'saving';
      this.lastSavedText = 'Sauvegarde automatique…';
      notify({ state: 'saving' });
      htmx.trigger(this.$refs.blockForm, 'autosave');
    },

    onSaved({ savedAt, editUrl }) {
      this.hasUnsaved = false;
      this.autosaveState = 'saved';
      this.lastSavedText = `✓ Enregistré automatiquement à ${savedAt}`;
      notify({ state: 'saved', time: savedAt });
      // Premier enregistrement d'un nouveau bloc : les suivants vont vers l'URL d'édition.
      if (editUrl) this.$refs.blockForm.setAttribute('hx-post', editUrl);
    },

    onError() {
      this.autosaveState = 'error';
      this.lastSavedText = '⚠️ Erreur de sauvegarde, nouvel essai…';
      notify({ state: 'error' });
      this.saveTimer = setTimeout(() => this.autosave(), 3000);
    },
  }));
});
