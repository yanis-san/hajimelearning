/**
 * Composant Alpine `persistScroll` : mémorise la position de scroll d'un conteneur
 * (sessionStorage) pour la restaurer d'une page à l'autre.
 *
 * Usage : x-data="persistScroll('<clé>')" x-init="restore()" @scroll.debounce="save()"
 */
document.addEventListener('alpine:init', () => {
  Alpine.data('persistScroll', (key) => ({
    restore() {
      this.$nextTick(() => {
        const position = sessionStorage.getItem(key);
        if (position) this.$el.scrollTop = position;
      });
    },
    save() {
      sessionStorage.setItem(key, this.$el.scrollTop);
    },
  }));
});
