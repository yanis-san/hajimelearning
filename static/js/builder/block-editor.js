// Alpine component for the lesson block editor: tabs plus debounced autosave.
// Usage: x-data="blockEditor('/url/to/post/to')". Load before Alpine starts.
document.addEventListener('alpine:init', () => {
  const notify = (detail) => window.dispatchEvent(new CustomEvent('builder-status', { detail }));

  Alpine.data('blockEditor', (postUrl) => ({
    tab: 'edit',
    autosaveState: 'saved',
    lastSavedText: 'Tous les changements sont enregistrés',
    saveTimer: null,
    hasUnsaved: false,
    postUrl,

    init() {
      window.addEventListener('beforeunload', (e) => {
        if (!this.hasUnsaved) return;
        this.autosave();
        e.preventDefault();
        e.returnValue = '';
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

    async autosave() {
      if (!this.hasUnsaved && this.autosaveState === 'saved') return;
      clearTimeout(this.saveTimer);
      this.autosaveState = 'saving';
      this.lastSavedText = 'Sauvegarde automatique…';
      notify({ state: 'saving' });

      const formEl = this.$refs.blockForm;
      if (!formEl) return;
      const formData = new FormData(formEl);
      formData.append('is_autosave', '1');

      try {
        const res = await fetch(this.postUrl, {
          method: 'POST',
          headers: { 'X-Autosave': 'true', 'X-Requested-With': 'XMLHttpRequest' },
          body: formData,
        });
        if (!res.ok) throw new Error();
        const data = await res.json();
        if (!data.ok) throw new Error();

        this.hasUnsaved = false;
        this.autosaveState = 'saved';
        this.lastSavedText = '✓ Enregistré automatiquement à ' + data.saved_at;
        notify({ state: 'saved', time: data.saved_at });

        // First save of a new block: later saves must go to the edit URL.
        if (data.created && data.edit_url) {
          this.postUrl = data.edit_url;
          formEl.setAttribute('hx-post', data.edit_url);
        }
        if (data.block_list_html) {
          const list = document.getElementById('block-list');
          if (list) list.innerHTML = data.block_list_html;
        }
      } catch (e) {
        this.autosaveState = 'error';
        this.lastSavedText = '⚠️ Erreur de sauvegarde, nouvel essai…';
        notify({ state: 'error' });
        this.saveTimer = setTimeout(() => this.autosave(), 3000);
      }
    },
  }));
});
