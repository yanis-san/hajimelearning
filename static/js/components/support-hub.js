/**
 * Composant Alpine `supportHub` : navigation par formation et filtre (toutes / mes questions)
 * de la page « Questions & Support ».
 */
document.addEventListener('alpine:init', () => {
  Alpine.data('supportHub', (firstCourse) => ({
    activeCourse: firstCourse,
    filter: 'all',
    select(courseSlug) {
      this.activeCourse = courseSlug;
      this.filter = 'all';
    },
  }));
});
