// Live Markdown preview for the builder editors. Needs marked.js and furigana.js.
(function () {
  const variants = {
    lesson: {
      empty: '<p class="text-gray-500 italic text-sm">L\'aperçu apparaîtra ici…</p>',
      prose: 'prose prose-sm max-w-none prose-headings:text-gray-800 prose-p:text-gray-600 prose-a:text-primary prose-strong:text-gray-800 prose-table:text-sm',
    },
    course: {
      empty: '<p class="text-gray-500 italic">Aucun contenu rédigé pour le moment…</p>',
      prose: 'prose prose-sm max-w-none prose-headings:text-gray-900 prose-headings:font-bold prose-p:text-gray-700 prose-a:text-primary prose-strong:text-gray-900 prose-ul:list-disc prose-ul:pl-5',
    },
    landing: {
      empty: '<p class="text-gray-500 italic text-sm">L\'aperçu apparaîtra ici…</p>',
      prose: 'prose prose-sm max-w-none prose-headings:text-gray-800 prose-p:text-gray-600 prose-a:text-primary prose-strong:text-gray-800',
    },
  };

  function render(variant, src, targetId) {
    const el = document.getElementById(targetId);
    if (!el) return;
    const { empty, prose } = variants[variant];
    if (!src || !src.trim()) {
      el.innerHTML = empty;
      return;
    }
    const text = window.convertFurigana(src);
    const html = window.marked ? window.marked.parse(text) : text;
    el.innerHTML = `<div class="${prose}">${html}</div>`;
  }

  window.renderLessonBlockMarkdown = (src, targetId) => render('lesson', src, targetId);
  window.renderCourseMarkdown = (src, targetId) => render('course', src, targetId);
  window.renderLandingSectionMarkdown = (src, targetId) => render('landing', src, targetId);
})();
