/**
 * Composant Alpine `courseForm` : formulaire d'édition d'un cours (onglets, compteurs, aperçus).
 *
 * Usage : x-data="courseForm" sur le <form>. Le champ de scission du Markdown porte x-ref="splitEditor".
 * Dépend de `renderCourseMarkdown` (markdown-preview.js).
 */
document.addEventListener('alpine:init', () => {
  Alpine.data('courseForm', () => ({
    tab: 'infos',
    mdTab: 'edit',
    metaDescLength: 0,
    trailerId: '',
    courseTitle: '',
    courseSlug: '',

    init() {
      // Reflète en direct la valeur de champs Django (ids générés par les widgets)
      const mirror = (id, assign) => {
        const el = document.getElementById(id);
        if (!el) return;
        assign(el.value);
        el.addEventListener('input', () => assign(el.value));
      };
      mirror('id_meta_description', (value) => (this.metaDescLength = value.length));
      mirror('id_trailer_video_id', (value) => (this.trailerId = value.trim()));
      mirror('id_title', (value) => (this.courseTitle = value));
      mirror('id_slug', (value) => (this.courseSlug = value));
    },

    syncSplitPreview() {
      const mainEl = document.getElementById('id_description');
      const splitEl = this.$refs.splitEditor;
      if (mainEl && splitEl) {
        splitEl.value = mainEl.value;
        renderCourseMarkdown(splitEl.value, 'desc-split-preview');
      }
    },

    syncFullPreview() {
      const mainEl = document.getElementById('id_description');
      if (mainEl) renderCourseMarkdown(mainEl.value, 'desc-full-preview');
    },
  }));
});
