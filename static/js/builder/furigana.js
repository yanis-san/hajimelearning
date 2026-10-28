// Client-side twin of convert_furigana() in courses/templatetags/md.py.
// Keep both in sync: the editor preview must match what the server renders.
(function () {
  const KANJI = '\\u4e00-\\u9fff\\u3400-\\u4dbf\\uf900-\\ufaff々〆ヵヶ';

  function toRuby(base, reading) {
    base = base.trim();
    reading = reading.trim();
    if (reading.includes('|')) {
      const parts = reading.split('|').map((p) => p.trim());
      if (base.length === parts.length) {
        return parts.map((p, i) => `<ruby>${base[i]}<rt>${p}</rt></ruby>`).join('');
      }
    }
    return `<ruby>${base}<rt>${reading}</rt></ruby>`;
  }

  const rules = [
    /\{([^{|\n]+)\|([^{}\n]+)\}/g,                    // {漢字|かんじ}
    /\[([^\]\n]+)\]\{([^{}\n]+)\}/g,                  // [漢字]{かんじ}
    /[｜|]([^《\n]+)《([^》\n]+)》/g,                   // ｜漢字《かんじ》
    new RegExp(`([${KANJI}]+)《([^》\\n]+)》`, 'g'),   // 漢字《かんじ》
  ];

  window.convertFurigana = function (text) {
    if (!text) return '';
    return rules.reduce((out, re) => out.replace(re, (m, base, reading) => toRuby(base, reading)), text);
  };
})();
