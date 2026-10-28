// Drag-and-drop ordering. Any element with class "sortable-list" becomes sortable
// and fires an "end" event after a drop, which the element's hx-trigger="end" picks up.
// Needs sortable.min.js and htmx.
htmx.onLoad((content) => {
  const lists = [...content.querySelectorAll('.sortable-list')];
  if (content.matches && content.matches('.sortable-list')) lists.push(content);

  lists.forEach((el) => {
    if (el._sortable) return;
    el._sortable = new Sortable(el, {
      animation: 150,
      handle: '.handle',
      ghostClass: 'bg-orange-50',
      onEnd: () => htmx.trigger(el, 'end'),
    });
  });
});
