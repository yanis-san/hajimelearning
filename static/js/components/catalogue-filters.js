/**
 * Composant Alpine `catalogueFilters` : état des filtres du catalogue (catégorie active, tri).
 * Usage : x-data="catalogueFilters('<catégorie>', '<tri>')". Les requêtes HTMX sont déclarées dans le template.
 */
document.addEventListener('alpine:init', () => {
  Alpine.data('catalogueFilters', (category, sort) => ({
    active: category,
    sort,
    sortNext(current, asc, desc) {
      return current === asc ? desc : asc;
    },
  }));
});
