/**
 * Composant Alpine `blockNote` : note personnelle d'un étudiant sur un bloc (sauvegarde AJAX).
 *
 * Usage : x-data="blockNote('<url de sauvegarde>', <note existante : bool>)"
 * Le formulaire doit porter x-ref="form".
 */
document.addEventListener('alpine:init', () => {
  const getCookie = (name) =>
    document.cookie
      .split('; ')
      .find((row) => row.startsWith(`${name}=`))
      ?.split('=')[1] ?? '';

  Alpine.data('blockNote', (saveUrl, hasNote) => ({
    open: false,
    saved: hasNote,
    saving: false,
    status: '',

    async save() {
      this.saving = true;
      this.status = '';
      try {
        const res = await fetch(saveUrl, {
          method: 'POST',
          headers: { 'X-CSRFToken': getCookie('csrftoken'), 'X-Requested-With': 'XMLHttpRequest' },
          body: new FormData(this.$refs.form),
        });
        const data = await res.json();
        if (!res.ok || !data.ok) throw new Error('save failed');
        this.saved = data.content.length > 0;
        this.open = false;
        this.status = 'ok';
        setTimeout(() => (this.status = ''), 2000);
      } catch {
        this.status = 'error';
      }
      this.saving = false;
    },
  }));
});
